"""
embeddings/embedder.py — Ultra-Lightweight Text Embedding Generator (FastEmbed)

Converts text into 384-dimensional numerical vectors using FastEmbed (ONNX).
Uses ~30MB of RAM without PyTorch dependencies, preventing any Out-of-Memory (OOM)
crashes on 512MB cloud hosting instances.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_model: Optional[object] = None


def get_model():
    """
    Returns the FastEmbed embedding model, loading it on first call.
    Subsequent calls return the cached instance instantly.
    """
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
            logger.info("Loading lightweight ONNX embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
            _model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
            logger.info("✅ ONNX Embedding model loaded successfully (<35MB RAM)")
        except Exception as e:
            logger.warning(f"FastEmbed failed ({e}), attempting sentence_transformers fallback...")
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Converts a list of text strings into 384-dimensional embedding vectors.
    """
    if not texts:
        return []

    model = get_model()

    if hasattr(model, "embed"):
        # FastEmbed ONNX engine
        embeddings = list(model.embed(texts))
        return [e.tolist() for e in embeddings]
    else:
        # SentenceTransformers fallback
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """
    Embeds a single query string.
    """
    results = embed_texts([query])
    return results[0] if results else [0.0] * 384

