#!/usr/bin/env python3
"""
Vyoma Offline Medical AI Assistant - Standalone RAG Indexing & Benchmarking CLI.
Ingests MedlinePlus XML + Indian clinical protocols, benchmarks chunking strategies
(Whole-Topic vs 350-500 Token Chunking), precomputes dense embeddings, and generates
the embedded SQLite FTS5 database and FAISS index.
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.logging import logger
from app.rag.medline_ingest import MedlinePlusIngestor
from app.rag.protocol_ingest import IndianProtocolIngestor
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.evaluator import RAGEvaluator


def build_and_benchmark_rag(benchmark_only: bool = False, force_strategy: str = None):
    print("========================================================================")
    print("      Vyoma Offline Medical AI Assistant - Dual-Corpus RAG Ingestion    ")
    print("========================================================================")

    # 1. Resolve Data Paths
    xml_path = settings.resolve_path(settings.MEDLINEPLUS_XML_PATH)
    if not xml_path.exists():
        # Fallback to root mplus xml if present
        root_xml = settings.resolve_path("mplus_topics_2026-09-08.xml")
        if root_xml.exists():
            xml_path = root_xml

    protocols_dir = settings.resolve_path(settings.INDIAN_PROTOCOLS_DIR)

    print(f"[*] MedlinePlus XML: {xml_path}")
    print(f"[*] Indian Protocols: {protocols_dir}")

    # 2. Ingest Indian Clinical Protocols (Official Standard Treatment Guidelines)
    protocol_ingestor = IndianProtocolIngestor(str(protocols_dir))
    indian_docs = protocol_ingestor.parse_all_protocols()
    print(f"[*] Ingested {len(indian_docs)} official Indian clinical protocol records.")

    # 3. Benchmark Chunking Strategies if not forced
    strategies = ["whole_doc", "chunked"] if not force_strategy else [force_strategy]
    best_strategy = "whole_doc"
    best_mrr = -1.0

    print("\n[*] Benchmarking RAG Chunking Strategies against Golden QA Set:")

    for strat in strategies:
        print(f"\n--- Testing Strategy: {strat.upper()} ---")
        t0 = time.time()
        medline_ingestor = MedlinePlusIngestor(str(xml_path))
        medline_docs = medline_ingestor.parse_records(strategy=strat)
        all_docs = indian_docs + medline_docs

        print(f"  Total Corpus Size: {len(all_docs)} documents.")

        # Build in-memory / temporary test retriever
        test_db = f"indexes/test_{strat}.db"
        test_faiss = f"indexes/test_faiss_{strat}"
        retriever = HybridRetriever(db_path=test_db, faiss_dir=test_faiss)
        retriever.build_indexes(all_docs)

        # Run evaluation
        evaluator = RAGEvaluator(retriever)
        metrics = evaluator.evaluate()

        print(f"  Recall@1: {metrics['recall_at_1']:.2f}")
        print(f"  Recall@5: {metrics['recall_at_5']:.2f}")
        print(f"  MRR:      {metrics['mrr']:.4f}")
        print(f"  Groundedness: {metrics['mean_groundedness']:.2f}")
        print(f"  Build & Eval Duration: {time.time() - t0:.2f}s")

        if metrics['mrr'] > best_mrr:
            best_mrr = metrics['mrr']
            best_strategy = strat

    print(f"\n[+] Optimal Strategy Determined: {best_strategy.upper()} (MRR: {best_mrr:.4f})")

    # 4. Final Production Index Build using Best Strategy
    if not benchmark_only:
        print(f"\n[*] Generating final production index using '{best_strategy}'...")
        medline_ingestor = MedlinePlusIngestor(str(xml_path))
        final_medline_docs = medline_ingestor.parse_records(strategy=best_strategy)
        final_corpus = indian_docs + final_medline_docs

        prod_retriever = HybridRetriever(
            db_path=settings.SQLITE_DB_PATH,
            faiss_dir=settings.FAISS_INDEX_DIR
        )
        prod_retriever.build_indexes(final_corpus)

        print("========================================================================")
        print(f"[SUCCESS] Production RAG database created at {settings.SQLITE_DB_PATH}")
        print(f"[SUCCESS] Production FAISS index created at {settings.FAISS_INDEX_DIR}")
        print(f"[SUCCESS] Total active clinical records: {len(final_corpus)}")
        print("========================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and evaluate Vyoma Medical RAG database.")
    parser.add_argument("--benchmark-only", action="store_true", help="Run strategy benchmarks without overwriting production index.")
    parser.add_argument("--strategy", choices=["whole_doc", "chunked"], help="Force specific chunking strategy.")
    args = parser.parse_args()

    build_and_benchmark_rag(benchmark_only=args.benchmark_only, force_strategy=args.strategy)
