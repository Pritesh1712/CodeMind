"""
chunking/chunk_models.py — Data Model for a Code Chunk

A CodeChunk represents one meaningful piece of code extracted from a file.
Every chunk carries rich metadata so we can cite it precisely.

Student note:
  Think of a chunk as a "unit of knowledge" that we embed and search.
  The smaller and more focused the chunk, the better the search results.
"""

from dataclasses import dataclass, field


@dataclass
class CodeChunk:
    """
    One piece of code with all its metadata.

    This is what gets stored in ChromaDB and returned during retrieval.
    """

    # ── What repository / file this came from ────────────────────────────────
    repository_id: str       # unique ID of the parent repository
    file_path: str           # relative path, e.g., "src/auth/login.py"
    language: str            # e.g., "python", "javascript"

    # ── The actual code ──────────────────────────────────────────────────────
    code: str                # the code text of this chunk

    # ── Line numbers (for citations) ─────────────────────────────────────────
    start_line: int          # 1-indexed, inclusive
    end_line: int            # 1-indexed, inclusive

    # ── Semantic metadata ────────────────────────────────────────────────────
    symbol_name: str = ""    # function/class name (empty for fallback chunks)
    symbol_type: str = ""    # "function", "class", "method", "module", etc.

    # ── Unique ID (auto-generated) ───────────────────────────────────────────
    chunk_id: str = field(default="")

    def __post_init__(self):
        """Generate a stable chunk ID from its location."""
        if not self.chunk_id:
            # ID = repo_id + file + start line — guaranteed unique per repo
            self.chunk_id = (
                f"{self.repository_id}::{self.file_path}::{self.start_line}"
            )

    def to_document_text(self) -> str:
        """
        Creates the text string that gets embedded.
        Including the file path and symbol name improves search quality
        because the embedding captures "where" the code lives.
        """
        parts = [f"File: {self.file_path}"]
        if self.symbol_name:
            parts.append(f"Symbol: {self.symbol_name} ({self.symbol_type})")
        parts.append(f"Language: {self.language}")
        parts.append("")  # blank line
        parts.append(self.code)
        return "\n".join(parts)

    def to_metadata(self) -> dict:
        """
        Returns a flat dict for ChromaDB metadata storage.
        ChromaDB only supports string/int/float values in metadata.
        """
        return {
            "repository_id": self.repository_id,
            "file_path": self.file_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "code": self.code,  # store code in metadata for retrieval
        }
