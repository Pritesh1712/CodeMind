"""
models/schemas.py — API Request/Response Schemas

These Pydantic models define the shape of data going in and out of our API.
They are separate from the database models to give us flexibility.

Student note:
  - Request schemas validate incoming data
  - Response schemas define what we send back to the frontend
  - Pydantic automatically converts types and validates constraints
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator
import re


# ── Repository Schemas ────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body for POST /api/repositories/analyze"""
    url: str  # GitHub repository URL

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        """Make sure the URL looks like a GitHub repo URL."""
        v = v.strip().rstrip("/")
        # Basic pattern: github.com/owner/repo with optional .git
        pattern = r"^https?://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?$"
        if not re.match(pattern, v, re.IGNORECASE):
            raise ValueError(
                "URL must be a valid GitHub repository URL like: "
                "https://github.com/owner/repository"
            )
        # Normalize: remove .git suffix if present
        if v.endswith(".git"):
            v = v[:-4]
        return v


class RepositoryResponse(BaseModel):
    """Returned whenever we describe a repository."""
    id: str
    url: str
    name: str
    status: str
    progress_message: str
    chunks_count: int
    created_at: datetime
    indexed_at: Optional[datetime]
    error_message: Optional[str]


class RepositoryStatusResponse(BaseModel):
    """Lightweight status-only response (used for polling during indexing)."""
    id: str
    status: str
    progress_message: str
    chunks_count: int
    error_message: Optional[str]


# ── Citation Schema ───────────────────────────────────────────────────────────

class Citation(BaseModel):
    """
    A reference to a specific piece of code in the repository.
    Shows up in AI responses as clickable badges.
    """
    file_path: str        # e.g., "src/auth/login.py"
    start_line: int       # first line of the relevant code
    end_line: int         # last line of the relevant code
    code: str             # the actual code snippet
    language: str = ""    # programming language (for syntax highlighting)
    symbol_name: str = "" # function/class name if applicable


# ── Chat Schemas ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for POST /api/chat"""
    repository_id: str
    question: str
    chat_id: Optional[str] = None  # None = start a new chat


class MessageResponse(BaseModel):
    """A single message for the frontend."""
    id: str
    role: str                        # "user" or "assistant"
    content: str
    citations: List[Citation] = []   # only assistant messages have citations
    follow_up_questions: List[str] = []  # interactive suggested next questions
    created_at: datetime


class ChatResponse(BaseModel):
    """The AI's answer + associated metadata."""
    chat_id: str
    answer: str
    citations: List[Citation]
    confidence_score: float          # 0.0–1.0
    query_type: str                  # "conceptual" or "exact_reference"
    follow_up_questions: List[str] = []  # 2-3 logical next questions to explore


class ChatListItem(BaseModel):
    """Summary of a chat (for the sidebar list)."""
    id: str
    repository_id: str
    title: str
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime
    message_count: int


class UpdateChatRequest(BaseModel):
    """Request body for PATCH /api/chats/{id}"""
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


class ChatDetailResponse(BaseModel):
    """Full chat with all messages (for loading a conversation)."""
    id: str
    repository_id: str
    title: str
    is_pinned: bool = False
    created_at: datetime
    messages: List[MessageResponse]


# ── Search Schema ─────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """Request body for POST /api/search (debug/direct search)."""
    repository_id: str
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    """One retrieved code chunk."""
    file_path: str
    start_line: int
    end_line: int
    code: str
    language: str
    symbol_name: str
    similarity_score: float
