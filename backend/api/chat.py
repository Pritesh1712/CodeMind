"""
api/chat.py — Chat API Routes

Endpoints:
  POST /api/chat               - Ask a question (main endpoint!)
  GET  /api/chats              - List all chats
  GET  /api/chats/{id}         - Get chat with full message history
  DELETE /api/chats/{id}       - Delete a chat
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from database import get_session
from models.repository import Repository, RepositoryStatus
from models.schemas import (
    ChatRequest, ChatResponse, ChatListItem, ChatDetailResponse, UpdateChatRequest
)
from services.chat_service import (
    create_chat, add_message, get_chat_list, get_chat_detail, delete_chat
)
from services.query_service import answer_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    session: Session = Depends(get_session),
):
    """
    Main chat endpoint — ask a question about a repository.

    Flow:
      1. Validate repository is indexed
      2. Get or create a chat
      3. Save user message
      4. Run the question-answering pipeline
      5. Save assistant message
      6. Return the answer
    """
    # ── Validate repository ───────────────────────────────────────────────────
    repo = session.get(Repository, request.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.status != RepositoryStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Repository is not ready yet. Current status: {repo.status}",
        )

    # ── Get or create chat ────────────────────────────────────────────────────
    if request.chat_id:
        # Continue an existing chat
        from models.chat import Chat
        chat = session.get(Chat, request.chat_id)
        if not chat or chat.repository_id != request.repository_id:
            raise HTTPException(status_code=404, detail="Chat not found")
    else:
        # Start a new chat
        chat = create_chat(session, request.repository_id)

    # ── Save user message ─────────────────────────────────────────────────────
    add_message(session, chat.id, "user", request.question)

    # ── Run the Q&A pipeline ──────────────────────────────────────────────────
    try:
        result = answer_question(
            repository_id=request.repository_id,
            question=request.question,
            chat_id=chat.id,
            session=session,
        )
    except Exception as e:
        logger.error(f"Query service error: {e}")
        error_msg = str(e)
        # Save error as assistant message
        add_message(session, chat.id, "assistant",
                    f"An error occurred: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

    # ── Save assistant response ───────────────────────────────────────────────
    add_message(session, chat.id, "assistant", result.answer, result.citations)

    return result


@router.get("/chats", response_model=List[ChatListItem])
def list_chats(
    repository_id: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Lists all chats, optionally filtered by repository."""
    return get_chat_list(session, repository_id)


@router.get("/chats/{chat_id}", response_model=ChatDetailResponse)
def get_chat(chat_id: str, session: Session = Depends(get_session)):
    """Returns a specific chat with all its messages."""
    chat = get_chat_detail(session, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/chats/{chat_id}", response_model=ChatListItem)
def update_chat_item(
    chat_id: str,
    request: UpdateChatRequest,
    session: Session = Depends(get_session),
):
    """Updates a chat's title or pinned status."""
    from services.chat_service import update_chat
    chat = update_chat(
        session=session,
        chat_id=chat_id,
        title=request.title,
        is_pinned=request.is_pinned,
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Return updated list item
    from models.chat import Message
    from sqlmodel import select
    msg_count = len(session.exec(select(Message).where(Message.chat_id == chat.id)).all())
    return ChatListItem(
        id=chat.id,
        repository_id=chat.repository_id,
        title=chat.title,
        is_pinned=chat.is_pinned,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=msg_count,
    )


@router.delete("/chats/{chat_id}")
def remove_chat(chat_id: str, session: Session = Depends(get_session)):
    """Deletes a chat and all its messages."""
    success = delete_chat(session, chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}
