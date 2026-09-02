"""
chunking/fallback_chunker.py — Sliding Window Line Chunker

For languages we can't parse with AST (JS, Go, Java, etc.),
we use a simple sliding-window approach: cut the file into
overlapping chunks of N lines.

Why overlapping?
  If a function spans lines 45–75, and our chunks are 0-49 and 50-99,
  the function is split in two! Overlapping ensures the function
  appears completely in at least one chunk.

Student note:
  This is the "dumb but reliable" fallback. It works for any language
  and guarantees we don't miss code, even if chunks aren't perfectly
  aligned to function boundaries.
"""

import logging
from typing import List
from chunking.chunk_models import CodeChunk

logger = logging.getLogger(__name__)

# Chunk size in lines — 60 lines is roughly a screen height of code
CHUNK_SIZE = 60

# Overlap in lines — ensures functions aren't split across chunks
OVERLAP = 15


def chunk_by_lines(
    file_path: str,
    code: str,
    repository_id: str,
    language: str,
) -> List[CodeChunk]:
    """
    Splits a file into overlapping line-based chunks.

    Args:
        file_path: Relative path (for metadata)
        code: Full source code
        repository_id: Parent repository ID
        language: Programming language name

    Returns:
        List of CodeChunk objects
    """
    lines = code.split("\n")
    total_lines = len(lines)

    if total_lines == 0:
        return []

    chunks = []
    start = 0  # 0-indexed

    while start < total_lines:
        end = min(start + CHUNK_SIZE, total_lines)  # exclusive end

        # Extract this window of lines
        chunk_lines = lines[start:end]
        chunk_code = "\n".join(chunk_lines)

        # Skip empty chunks
        if chunk_code.strip():
            chunks.append(CodeChunk(
                repository_id=repository_id,
                file_path=file_path,
                language=language,
                code=chunk_code,
                start_line=start + 1,    # convert to 1-indexed
                end_line=end,            # end is already 1-indexed (exclusive → inclusive)
                symbol_name="",          # unknown for line-based chunks
                symbol_type="chunk",
            ))

        # Move forward by (CHUNK_SIZE - OVERLAP) to create overlap
        step = CHUNK_SIZE - OVERLAP
        start += step

        # Safety check: avoid infinite loops
        if step <= 0:
            break

    logger.debug(f"Fallback chunker: {file_path} → {len(chunks)} chunks")
    return chunks
