"""
ingestion/file_walker.py — Repository File Walker

Walks through all files in a cloned repository and returns
only the ones that should be indexed (using our filters).

Returns a list of (absolute_path, relative_path, language) tuples.

Student note:
  os.walk() is a generator that yields (dirpath, dirnames, filenames)
  for every directory in the tree. We use it to recursively find all files.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple
from ingestion.filters import should_index_file, get_language

logger = logging.getLogger(__name__)


def walk_repository(repo_path: Path) -> List[Tuple[Path, str, str]]:
    """
    Walks a repository directory and finds all indexable files.

    Args:
        repo_path: Root directory of the cloned repository

    Returns:
        List of tuples: (absolute_path, relative_path, language)
        - absolute_path: full path on disk
        - relative_path: path relative to repo root (used in citations)
        - language: programming language name
    """
    results = []
    skipped_count = 0

    for dirpath, dirnames, filenames in os.walk(repo_path):
        dir_path = Path(dirpath)

        # ── Prune ignored directories in-place ──────────────────────────────
        # Modifying dirnames in-place tells os.walk to skip those directories.
        # This is more efficient than checking paths after the fact.
        dirnames[:] = [
            d for d in dirnames
            if d not in {".git", "node_modules", "venv", ".venv",
                         "__pycache__", "build", "dist", "target",
                         ".next", ".nuxt", "vendor"}
        ]

        for filename in filenames:
            abs_path = dir_path / filename

            if should_index_file(abs_path):
                # Relative path from repo root (for citations like "src/auth.py")
                rel_path = str(abs_path.relative_to(repo_path))
                # Normalize path separators to forward slashes
                rel_path = rel_path.replace("\\", "/")
                language = get_language(abs_path)
                results.append((abs_path, rel_path, language))
            else:
                skipped_count += 1

    logger.info(
        f"File walk complete: {len(results)} files to index, "
        f"{skipped_count} files skipped"
    )
    return results
