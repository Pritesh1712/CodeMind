"""
models/chat.py — Chat & Message Database Models

A Chat is like a "conversation thread" — it belongs to a repository
and contains many Messages back and forth.

Structure:
  Chat (1) ──► Messages (many)
"""

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
import uuid


class Message(SQLModel, table=True):
    """
    A single message in a chat conversation.
    role is either "user" or "assistant".
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    # Foreign key linking this message to its chat
    chat_id: str = Field(foreign_key="chat.id", index=True)

    # Who sent this message
    role: str = Field(default="user")  # "user" or "assistant"

    # The text content of the message
    content: str = Field(default="")

    # For assistant messages: JSON string of citations
    # Example: '[{"file": "src/auth.py", "start": 10, "end": 25, "code": "..."}]'
    citations_json: Optional[str] = Field(default=None)

    # When the message was created
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship back to the parent chat
    chat: Optional["Chat"] = Relationship(back_populates="messages")


class Chat(SQLModel, table=True):
    """
    A conversation thread associated with a specific repository.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    # Which repository this chat is about
    repository_id: str = Field(foreign_key="repository.id", index=True)

    # Auto-generated title (we use the first user message)
    title: str = Field(default="New Chat")

    # Whether the user pinned this chat to top
    is_pinned: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # All messages in this chat (loaded via SQLModel relationship)
    messages: List[Message] = Relationship(back_populates="chat")
