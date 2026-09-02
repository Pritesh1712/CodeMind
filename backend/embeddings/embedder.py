"""
embeddings/embedder.py — Text Embedding Generator

Converts text into numerical vectors (embeddings) using
sentence-transformers. These vectors capture semantic meaning —
two similar pieces of code will have similar vectors.

How embeddings work (simple explanation):
  "authenticate user" → [0.12, -0.34, 0.87, ..., 0.01]  (384 numbers)
  "login validation" →  [0.13, -0.31, 0.85, ..., 0.02]  (similar!)
  "database query"  →  [-0.45, 0.12, -0.23, ..., 0.89]  (different)

Student note:
  We use all-MiniLM-L6-v2 because it's:
  - Small (22M parameters, downloads in seconds)
  - Fast (runs on CPU)
  - Surprisingly good for code similarity tasks
"""

import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)

# Module-level model instance — loaded once and reused
# Loading a model takes a few seconds, so we only do it once
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """
    Returns the embedding model, loading it on first call (lazy loading).
    Subsequent calls return the cached instance instantly.
    """
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Converts a list of text strings into embedding vectors.

    Args:
        texts: List of strings to embed

    Returns:
        List of embedding vectors (each is a list of floats)

    Example:
        embed_texts(["def login(user):...", "class Auth:..."])
        → [[0.12, -0.34, ...], [0.45, 0.21, ...]]
    """
    if not texts:
        return []

    model = get_model()

    # encode() returns a numpy array; we convert to Python lists for JSON compatibility
    embeddings = model.encode(
        texts,
        batch_size=32,          # process 32 texts at a time (memory-efficient)
        show_progress_bar=False,
        normalize_embeddings=True,  # normalize to unit length for cosine similarity
    )

    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """
    Embeds a single query string.
    We separate this from embed_texts() for clarity — queries are
    always single strings, while documents are batched.
    """
    model = get_model()
    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )
    return embedding.tolist()
