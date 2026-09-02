"""
models/repository.py — Repository Database Model

Tracks every GitHub repository that has been submitted for analysis.

Fields:
  - id: unique ID (UUID string)
  - url: original GitHub URL
  - name: e.g., "tiangolo/fastapi"
  - status: current indexing state (see RepositoryStatus enum)
  - created_at: when it was first submitted
  - indexed_at: when indexing finished (None if not done)
  - error_message: any error that occurred during indexing
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class RepositoryStatus:
    """
    Simple string constants for repository indexing states.
    Using a plain class instead of Enum keeps things simple and readable.
    """
    PENDING = "pending"          # just submitted, not started
    CLONING = "cloning"          # downloading the repo
    SCANNING = "scanning"        # walking the file tree
    CHUNKING = "chunking"        # splitting code into pieces
    EMBEDDING = "embedding"      # generating vector embeddings
    INDEXING = "indexing"        # storing into ChromaDB
    READY = "ready"              # fully indexed, ready to chat
    FAILED = "failed"            # something went wrong


class Repository(SQLModel, table=True):
    """SQLModel table for storing repository metadata."""

    # Primary key — we generate a random UUID for each repo
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    # The GitHub URL the user submitted
    url: str = Field(index=True, unique=True)

    # Human-readable name like "owner/repo"
    name: str = Field(default="")

    # Current status of indexing
    status: str = Field(default=RepositoryStatus.PENDING)

    # Progress message for the UI (e.g., "Parsing 42 files...")
    progress_message: str = Field(default="")

    # Number of code chunks indexed (shown in UI)
    chunks_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = Field(default=None)

    # Error message if status == FAILED
    error_message: Optional[str] = Field(default=None)
