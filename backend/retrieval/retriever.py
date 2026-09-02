"""
retrieval/retriever.py — Combined Retrieval

Combines semantic + exact search results, deduplicates them,
and returns the final ranked list of code chunks.

Student note:
  Neither semantic nor exact search is perfect on its own.
  For "Where is X used?", exact search wins.
  For "How does X work?", semantic search wins.
  The query router decides which to emphasize.
"""

import logging
from typing import List, Dict, Any
from retrieval.semantic_retriever import semantic_search
from retrieval.exact_retriever import exact_search

logger = logging.getLogger(__name__)


def retrieve_chunks(
    repository_id: str,
    query: str,
    query_type: str = "conceptual",
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    Main retrieval function — picks strategy based on query type.

    Args:
        repository_id: Which repo to search
        query: User's question
        query_type: "conceptual" or "exact_reference"
        top_k: Max chunks to return

    Returns:
        Ranked list of chunk dicts
    """
    if query_type == "exact_reference":
        # Start with exact search, supplement with semantic
        exact_results = exact_search(repository_id, query, top_k=top_k)
        semantic_results = semantic_search(repository_id, query, top_k=top_k // 2)

        # Merge: exact results first, then semantic (without duplicates)
        combined = _merge_results(exact_results, semantic_results, top_k)

    else:
        # Conceptual query: rely primarily on semantic search
        combined = semantic_search(repository_id, query, top_k=top_k)

    logger.info(f"Final retrieval: {len(combined)} chunks (type={query_type})")
    return combined


def _merge_results(
    primary: List[Dict[str, Any]],
    secondary: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """
    Merges two result lists, deduplicating by file_path + start_line.
    Primary list results take priority over secondary.
    """
    seen = set()
    merged = []

    for chunk in primary + secondary:
        # Use file + line as a dedup key
        key = f"{chunk.get('file_path')}:{chunk.get('start_line')}"
        if key not in seen:
            seen.add(key)
            merged.append(chunk)

        if len(merged) >= top_k:
            break

    return merged
