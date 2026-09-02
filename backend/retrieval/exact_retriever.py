"""
retrieval/exact_retriever.py — Exact / Reference Search

For queries like "Where is authenticate() called?" or "Find all usages of UserService",
embedding similarity isn't the best tool. We need exact string/symbol search.

This module:
  1. Scans all indexed files in the repo for exact or regex matches
  2. Returns chunks containing those matches with line numbers

Student note:
  This is basically grep-over-the-codebase, but smart enough to
  return structured CodeChunk-like objects with line ranges.
  Combining this with semantic search gives us the best of both worlds.
"""

import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from ingestion.cloner import get_clone_path
from ingestion.filters import should_index_file, get_language
from chunking.chunker import read_file_safely

logger = logging.getLogger(__name__)

# How many lines of context to include around each match
CONTEXT_LINES = 15


def exact_search(
    repository_id: str,
    query: str,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    Searches repository files for exact string matches of the query.

    Strategy:
      1. Extract the most likely "symbol" from the query
         (e.g., "Where is authenticate() used?" → "authenticate")
      2. Search all files for that string
      3. Return surrounding context as chunks

    Args:
        repository_id: Which repository to search
        query: The user's question (we extract the symbol from it)
        top_k: Max results to return

    Returns:
        List of chunk-like dicts with match info
    """
    # Extract the term to search for
    search_term = _extract_search_term(query)
    if not search_term:
        logger.debug("Could not extract search term from query")
        return []

    logger.info(f"Exact search for '{search_term}' in repo {repository_id}")

    repo_path = get_clone_path(repository_id)
    if not repo_path.exists():
        logger.warning(f"Repo path not found: {repo_path}")
        return []

    results = []

    # Walk all files in the repo
    for dirpath, dirnames, filenames in os.walk(repo_path):
        # Skip hidden/build directories
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in {
                "node_modules", "venv", "__pycache__", "build", "dist"
            }
        ]

        for filename in filenames:
            abs_path = Path(dirpath) / filename
            if not should_index_file(abs_path):
                continue

            rel_path = str(abs_path.relative_to(repo_path)).replace("\\", "/")
            language = get_language(abs_path)

            # Search this file
            file_matches = _search_file(
                abs_path, rel_path, language, repository_id, search_term
            )
            results.extend(file_matches)

            if len(results) >= top_k * 3:
                break  # found enough candidates

    # Sort by score (exact matches first) and return top_k
    results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
    return results[:top_k]


def _extract_search_term(query: str) -> str:
    """
    Extracts the most likely symbol name from a query.

    Examples:
      "Where is authenticate() used?" → "authenticate"
      "Find references to UserService" → "UserService"
      "Which files import axios?" → "axios"
    """
    # Try to find a quoted identifier
    quoted = re.findall(r"['\"`](\w+)['\"`]", query)
    if quoted:
        return quoted[0]

    # Try to find function call pattern: word()
    func_call = re.findall(r"(\w+)\(\)", query)
    if func_call:
        return func_call[0]

    # Try to find CamelCase words (likely class names)
    camel_case = re.findall(r"\b([A-Z][a-zA-Z]+)\b", query)
    if camel_case:
        return camel_case[0]

    # Try to find snake_case identifiers
    snake_case = re.findall(r"\b([a-z][a-z_]+[a-z])\b", query)
    # Filter out common stop words
    stop_words = {"where", "find", "what", "how", "does", "this", "that",
                  "used", "called", "from", "with", "all", "the", "and"}
    meaningful = [w for w in snake_case if w not in stop_words and len(w) > 3]
    if meaningful:
        return meaningful[0]

    return ""


def _search_file(
    abs_path: Path,
    rel_path: str,
    language: str,
    repository_id: str,
    search_term: str,
) -> List[Dict[str, Any]]:
    """
    Searches a single file for the search term and returns
    matching chunks with surrounding context.
    """
    code = read_file_safely(abs_path)
    if not code:
        return []

    lines = code.split("\n")
    results = []
    found_lines = []

    # Find all lines containing the search term (case-sensitive first)
    for i, line in enumerate(lines):
        if search_term in line:
            found_lines.append(i)  # 0-indexed

    if not found_lines:
        return []

    # For each matching line, extract surrounding context
    for line_idx in found_lines[:5]:  # max 5 matches per file
        start = max(0, line_idx - CONTEXT_LINES)
        end = min(len(lines), line_idx + CONTEXT_LINES + 1)

        chunk_code = "\n".join(lines[start:end])

        results.append({
            "repository_id": repository_id,
            "file_path": rel_path,
            "language": language,
            "start_line": start + 1,   # 1-indexed
            "end_line": end,           # 1-indexed
            "code": chunk_code,
            "symbol_name": search_term,
            "symbol_type": "reference",
            "similarity_score": 1.0,  # exact match = highest score
        })

    return results
