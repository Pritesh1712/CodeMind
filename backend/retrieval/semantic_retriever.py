"""
retrieval/semantic_retriever.py — Semantic Search

Uses embedding similarity to find code chunks relevant to a question.
This is the main retrieval method for "conceptual" questions like:
  "How does authentication work?"
  "Explain the database schema."

How it works:
  1. Embed the user's question into a vector
  2. Find the closest vectors in ChromaDB (cosine similarity)
  3. Return the top-K most similar chunks

Student note:
  "Semantic" means we match by meaning, not exact words.
  "authentication" and "login" are semantically similar,
  so searching for "authentication" can find code about "login".
"""

import logging
from typing import List, Dict, Any, Optional
from embeddings.chroma_store import query_chunks
from config import settings

logger = logging.getLogger(__name__)


OVERVIEW_KEYWORDS = [
    "about", "overview", "what is this", "explain this project",
    "what does this", "purpose", "architecture", "introduction",
    "summary", "what is the project"
]


def semantic_search(
    repository_id: str,
    query: str,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Finds code chunks semantically similar to the query.

    Args:
        repository_id: Which repository to search
        query: User's question or search text
        top_k: Number of results (defaults to settings.top_k)

    Returns:
        List of chunk dicts sorted by similarity (highest first)
    """
    k = top_k or settings.top_k

    logger.info(f"Semantic search for: '{query}' (top_k={k})")

    results = query_chunks(repository_id, query, top_k=k)

    # If it's a broad overview question, also retrieve readme/documentation chunks
    query_lower = query.lower()
    if any(kw in query_lower for kw in OVERVIEW_KEYWORDS):
        overview_query = f"README project overview description {query}"
        overview_results = query_chunks(repository_id, overview_query, top_k=k // 2)
        
        # Merge results without duplicates
        seen_keys = {f"{r.get('file_path')}:{r.get('start_line')}" for r in results}
        for chunk in overview_results:
            key = f"{chunk.get('file_path')}:{chunk.get('start_line')}"
            if key not in seen_keys:
                seen_keys.add(key)
                results.append(chunk)

    # Sort by similarity score (highest first)
    results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

    logger.info(f"Semantic search returned {len(results)} results")
    return results[:k]
