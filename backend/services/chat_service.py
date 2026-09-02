"""
services/chat_service.py — Chat History Manager

Handles creating, reading, and updating chat conversations in the database.

Student note:
  This service sits between the API routes and the database.
  It keeps route handlers thin (they just call services)
  and business logic centralized here.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from models.chat import Chat, Message
from models.schemas import (
    ChatListItem, ChatDetailResponse, MessageResponse, Citation
)

logger = logging.getLogger(__name__)


def create_chat(session: Session, repository_id: str, title: str = "New Chat") -> Chat:
    """Creates a new chat and saves it to the database."""
    chat = Chat(repository_id=repository_id, title=title)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    logger.info(f"Created chat {chat.id} for repo {repository_id}")
    return chat


def add_message(
    session: Session,
    chat_id: str,
    role: str,
    content: str,
    citations: Optional[List[Citation]] = None,
) -> Message:
    """Adds a message to a chat."""
    citations_json = None
    if citations:
        citations_json = json.dumps([c.model_dump() for c in citations])

    message = Message(
        chat_id=chat_id,
        role=role,
        content=content,
        citations_json=citations_json,
    )
    session.add(message)

    # Update chat's updated_at timestamp
    chat = session.get(Chat, chat_id)
    if chat:
        chat.updated_at = datetime.utcnow()
        # Use the first user message as the chat title (max 50 chars)
        if role == "user" and chat.title == "New Chat":
            chat.title = content[:50] + ("..." if len(content) > 50 else "")
        session.add(chat)

    session.commit()
    session.refresh(message)
    return message


def get_chat_list(session: Session, repository_id: Optional[str] = None) -> List[ChatListItem]:
    """Returns all chats, pinned first then newest updated first."""
    query = select(Chat).order_by(Chat.is_pinned.desc(), Chat.updated_at.desc())
    if repository_id:
        query = query.where(Chat.repository_id == repository_id)

    chats = session.exec(query).all()

    result = []
    for chat in chats:
        # Count messages for this chat
        messages_query = select(Message).where(Message.chat_id == chat.id)
        messages = session.exec(messages_query).all()

        result.append(ChatListItem(
            id=chat.id,
            repository_id=chat.repository_id,
            title=chat.title,
            is_pinned=getattr(chat, "is_pinned", False) or False,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(messages),
        ))

    return result


def update_chat(
    session: Session,
    chat_id: str,
    title: Optional[str] = None,
    is_pinned: Optional[bool] = None,
) -> Optional[Chat]:
    """Updates a chat's title or pinned status."""
    chat = session.get(Chat, chat_id)
    if not chat:
        return None

    if title is not None:
        chat.title = title.strip()
    if is_pinned is not None:
        chat.is_pinned = is_pinned

    chat.updated_at = datetime.utcnow()
    session.add(chat)
    session.commit()
    session.refresh(chat)
    logger.info(f"Updated chat {chat_id}: title='{chat.title}', pinned={chat.is_pinned}")
    return chat


def get_chat_detail(session: Session, chat_id: str) -> Optional[ChatDetailResponse]:
    """Returns a full chat with all its messages."""
    chat = session.get(Chat, chat_id)
    if not chat:
        return None

    messages_query = select(Message).where(
        Message.chat_id == chat_id
    ).order_by(Message.created_at)
    messages = session.exec(messages_query).all()

    message_responses = []
    for msg in messages:
        # Parse citations JSON back into Citation objects
        citations = []
        if msg.citations_json:
            try:
                raw_citations = json.loads(msg.citations_json)
                citations = [Citation(**c) for c in raw_citations]
            except Exception:
                pass  # ignore malformed citations

        message_responses.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=citations,
            created_at=msg.created_at,
        ))

    return ChatDetailResponse(
        id=chat.id,
        repository_id=chat.repository_id,
        title=chat.title,
        is_pinned=getattr(chat, "is_pinned", False) or False,
        created_at=chat.created_at,
        messages=message_responses,
    )


def delete_chat(session: Session, chat_id: str) -> bool:
    """Deletes a chat and all its messages."""
    chat = session.get(Chat, chat_id)
    if not chat:
        return False

    # Delete messages first (foreign key constraint)
    messages_query = select(Message).where(Message.chat_id == chat_id)
    messages = session.exec(messages_query).all()
    for message in messages:
        session.delete(message)

    session.delete(chat)
    session.commit()
    logger.info(f"Deleted chat {chat_id}")
    return True
