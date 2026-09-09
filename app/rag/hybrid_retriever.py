import os
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

from app.core.config import settings
from app.core.logging import logger
from app.rag.schema import MedicalDocument
from app.rag.embeddings import EmbeddingEngine


class HybridRetriever:
    """
    Embedded hybrid retrieval system uniting:
    1. SQLite FTS5 (BM25 keyword search on title, aliases, summary).
    2. FAISS IndexFlatIP (Cosine similarity on normalized dense vectors).
    3. Deterministic Reciprocal Rank Fusion (RRF) for robust multi-signal retrieval.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        faiss_dir: Optional[str] = None,
        embedding_engine: Optional[EmbeddingEngine] = None
    ):
        self.db_path = settings.resolve_path(db_path or settings.SQLITE_DB_PATH)
        self.faiss_dir = settings.resolve_path(faiss_dir or settings.FAISS_INDEX_DIR)
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        
        self.faiss_index = None
        self.faiss_doc_ids: List[str] = []
        
        # Ensure directories
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)

        self._init_sqlite()
        self._load_faiss()

    def _init_sqlite(self):
        """Initializes SQLite database and FTS5 full-text search table."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    aliases TEXT,
                    summary TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    source TEXT,
                    authority TEXT,
                    source_url TEXT,
                    document_type TEXT,
                    version_date TEXT
                )
            """)
            # Create FTS5 virtual table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    id UNINDEXED,
                    title,
                    aliases,
                    summary,
                    content='documents',
                    content_rowid='rowid'
                )
            """)
            conn.commit()

    def _load_faiss(self) -> bool:
        """Loads FAISS index and ID mapping from disk."""
        index_file = self.faiss_dir / "index.faiss"
        ids_file = self.faiss_dir / "doc_ids.json"

        if not index_file.exists() or not ids_file.exists():
            logger.warning(f"FAISS index not found at {self.faiss_dir}. Ingestion required.")
            return False

        if not HAS_FAISS:
            logger.warning("FAISS not installed. Dense retrieval will operate in fallback mode.")
            return False

        try:
            self.faiss_index = faiss.read_index(str(index_file))
            with open(ids_file, "r", encoding="utf-8") as f:
                self.faiss_doc_ids = json.load(f)
            logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors.")
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}", exc_info=True)
            return False

    def build_indexes(self, documents: List[MedicalDocument]):
        """
        Builds both SQLite FTS5 and FAISS vector indexes offline during ingestion.
        Precomputes all dense embeddings.
        """
        if not documents:
            logger.warning("No documents provided for indexing.")
            return

        logger.info(f"Starting index build for {len(documents)} medical documents...")

        # 1. Populate SQLite & FTS5
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM documents_fts")
            
            for doc in documents:
                aliases_str = ", ".join(doc.aliases)
                cursor.execute("""
                    INSERT INTO documents (
                        id, title, aliases, summary, language, source, authority, source_url, document_type, version_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.id, doc.title, aliases_str, doc.summary, doc.language,
                    doc.source, doc.authority, doc.source_url, doc.document_type, doc.version_date
                ))
            
            # Rebuild FTS5 index from documents table
            cursor.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
            conn.commit()

        logger.info(f"SQLite FTS5 populated with {len(documents)} records.")

        # 2. Precompute Dense Embeddings & Build FAISS
        texts = [doc.to_full_text() for doc in documents]
        embeddings = self.embedding_engine.encode_batch(texts, batch_size=32)

        if HAS_FAISS:
            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings)

            # Persist to disk
            faiss.write_index(index, str(self.faiss_dir / "index.faiss"))
            doc_ids = [doc.id for doc in documents]
            with open(self.faiss_dir / "doc_ids.json", "w", encoding="utf-8") as f:
                json.dump(doc_ids, f)

            self.faiss_index = index
            self.faiss_doc_ids = doc_ids
            logger.info(f"FAISS index built and saved ({index.ntotal} vectors).")
        else:
            logger.warning("FAISS not available. Saving doc_ids only.")
            with open(self.faiss_dir / "doc_ids.json", "w", encoding="utf-8") as f:
                json.dump([doc.id for doc in documents], f)

    def search_bm25(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Performs BM25 search against SQLite FTS5."""
        # Sanitize query for FTS5 syntax
        clean_query = "".join([c if c.isalnum() or c.isspace() else " " for c in query]).strip()
        tokens = [t for t in clean_query.split() if len(t) > 2]
        if not tokens:
            return []

        fts_query = " OR ".join(tokens)
        results = []

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, bm25(documents_fts) as score
                    FROM documents_fts
                    WHERE documents_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (fts_query, top_k))
                for row in cursor.fetchall():
                    # Lower score in SQLite FTS5 BM25 is better match, convert to positive relevance
                    relevance = max(0.01, 100.0 / (abs(row[1]) + 1.0))
                    results.append((row[0], relevance))
        except Exception as e:
            logger.debug(f"BM25 query failed for '{clean_query}': {e}")

        return results

    def search_dense(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Performs dense cosine similarity search with pre-loaded FAISS index."""
        if self.faiss_index is None or not self.faiss_doc_ids:
            return []

        query_vec = self.embedding_engine.encode_text(query).reshape(1, -1)
        distances, indices = self.faiss_index.search(query_vec, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.faiss_doc_ids):
                results.append((self.faiss_doc_ids[idx], float(dist)))
        return results

    def get_document_by_id(self, doc_id: str) -> Optional[MedicalDocument]:
        """Fetches full MedicalDocument record from SQLite."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, aliases, summary, language, source, authority, source_url, document_type, version_date
                FROM documents WHERE id = ?
            """, (doc_id,))
            row = cursor.fetchone()
            if not row:
                return None

            aliases = [a.strip() for a in row[2].split(",") if a.strip()] if row[2] else []
            return MedicalDocument(
                id=row[0],
                title=row[1],
                aliases=aliases,
                summary=row[3],
                language=row[4],
                source=row[5],
                authority=row[6],
                source_url=row[7],
                document_type=row[8],
                version_date=row[9]
            )

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval combining BM25 keyword score and dense semantic score
        fused via Reciprocal Rank Fusion (RRF).
        """
        bm25_matches = self.search_bm25(query, top_k=top_k * 2)
        dense_matches = self.search_dense(query, top_k=top_k * 2)

        # Reciprocal Rank Fusion (RRF)
        # RRF(d) = w_bm25 / (60 + rank_bm25) + w_dense / (60 + rank_dense)
        rrf_scores: Dict[str, float] = {}
        const_k = 60

        for rank, (doc_id, _) in enumerate(bm25_matches):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (const_k + rank + 1))

        for rank, (doc_id, _) in enumerate(dense_matches):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.2 / (const_k + rank + 1))

        # Sort by fused score descending
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        retrieved_records = []
        for doc_id, score in sorted_candidates:
            doc = self.get_document_by_id(doc_id)
            if doc:
                retrieved_records.append({
                    "id": doc.id,
                    "title": doc.title,
                    "summary": doc.summary,
                    "source": doc.source,
                    "authority": doc.authority,
                    "source_url": doc.source_url,
                    "document_type": doc.document_type,
                    "retrieval_score": round(score, 4),
                    "citation": f"{doc.authority} — {doc.title}"
                })

        logger.info(f"Retrieved {len(retrieved_records)} evidence records for query: '{query}'")
        return retrieved_records
