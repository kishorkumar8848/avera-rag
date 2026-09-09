from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from app.core.config import settings
from app.core.logging import logger


class EmbeddingEngine:
    """
    Manages lightweight local English embedding models (BGE-small-en-v1.5 / all-MiniLM-L6-v2).
    Precomputes dense vector embeddings on CPU to preserve Jetson unified RAM.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: Optional[str] = None, device: str = "cpu"):
        if self._initialized:
            return
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.device = device
        self.model = None
        self._load_model()
        self._initialized = True

    def _load_model(self):
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not installed. Using synthetic mock embedding engine.")
            return

        try:
            logger.info(f"Loading embedding model '{self.model_name}' on device '{self.device}'...")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Embedding model '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load '{self.model_name}': {e}. Trying fallback 'all-MiniLM-L6-v2'...")
            try:
                self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=self.device)
                self.model_name = "all-MiniLM-L6-v2"
                logger.info("Fallback embedding model loaded successfully.")
            except Exception as e2:
                logger.error(f"All embedding model loads failed: {e2}. Mock embedding engine active.")
                self.model = None

    def encode_text(self, text: str) -> np.ndarray:
        """Encodes a single query text into a normalized 1D float32 numpy vector."""
        if self.model is None:
            # 384-dimensional synthetic vector for mock testing
            vec = np.zeros(384, dtype=np.float32)
            vec[hash(text) % 384] = 1.0
            return vec

        embedding = self.model.encode(
            text,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embedding.astype(np.float32)

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encodes a list of documents in batches during offline precomputation."""
        if self.model is None:
            vectors = np.zeros((len(texts), 384), dtype=np.float32)
            for i, t in enumerate(texts):
                vectors[i, hash(t) % 384] = 1.0
            return vectors

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embeddings.astype(np.float32)

    @property
    def embedding_dim(self) -> int:
        if self.model is not None:
            return self.model.get_sentence_embedding_dimension()
        return 384
