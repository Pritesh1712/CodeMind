"""
chunking/chunker.py — Main Chunking Dispatcher

Routes each file to the best available chunker based on its language.

Priority:
  1. Python → AST chunker (best quality, function-level granularity)
  2. All others → Fallback line chunker (reliable, works for any language)

The dispatcher pattern makes it easy to add more language-specific
chunkers later (e.g., tree-sitter for JS/Go) without changing this file.

Student note:
  This is the "Strategy Pattern" in practice — we pick the right
  algorithm at runtime based on the input type.
"""

import logging
import chardet
from pathlib import Path
from typing import List
from chunking.chunk_models import CodeChunk
from chunking.python_ast_chunker import chunk_python_file
from chunking.fallback_chunker import chunk_by_lines

logger = logging.getLogger(__name__)


def read_file_safely(file_path: Path) -> str:
    """
    Reads a file, automatically detecting its encoding.
    Handles UTF-8, Latin-1, and other encodings gracefully.

    Returns empty string if the file cannot be read.
    """
    try:
        # First try UTF-8 (most common)
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass

    try:
        # Detect encoding using chardet
        raw_bytes = file_path.read_bytes()
        detected = chardet.detect(raw_bytes)
        encoding = detected.get("encoding") or "latin-1"
        return raw_bytes.decode(encoding, errors="replace")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return ""


def chunk_file(
    abs_path: Path,
    rel_path: str,
    language: str,
    repository_id: str,
) -> List[CodeChunk]:
    """
    Main entry point: chunks one file into CodeChunk objects.

    Args:
        abs_path: Absolute path on disk (for reading)
        rel_path: Relative path (for metadata/citations)
        language: Programming language name
        repository_id: Parent repository ID

    Returns:
        List of CodeChunk objects (empty list on any error)
    """
    # Read file content
    code = read_file_safely(abs_path)
    if not code.strip():
        logger.debug(f"Skipping empty file: {rel_path}")
        return []

    try:
        # ── Language-specific chunkers ────────────────────────────────────────
        if language == "python":
            chunks = chunk_python_file(rel_path, code, repository_id, language)

            # If AST parsing returned nothing (e.g., syntax error),
            # fall back to line-based chunking
            if not chunks:
                logger.debug(f"AST gave no chunks for {rel_path}, using fallback")
                chunks = chunk_by_lines(rel_path, code, repository_id, language)

        else:
            # For all other languages, use the line-based chunker
            chunks = chunk_by_lines(rel_path, code, repository_id, language)

        logger.debug(f"Chunked {rel_path}: {len(chunks)} chunks")
        return chunks

    except Exception as e:
        logger.error(f"Error chunking {rel_path}: {e}")
        return []
