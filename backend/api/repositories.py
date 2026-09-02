"""
api/repositories.py — Repository API Routes

Endpoints:
  POST /api/repositories/analyze   - Submit a new GitHub URL for indexing
  GET  /api/repositories           - List all repositories
  GET  /api/repositories/{id}      - Get repository details
  GET  /api/repositories/{id}/status - Poll indexing status (lightweight)

Student note:
  We use FastAPI's BackgroundTasks to run indexing without
  blocking the HTTP response. The client polls /status until done.
"""

import asyncio
import logging
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlmodel import Session, select
from database import get_session
from models.repository import Repository, RepositoryStatus
from models.schemas import (
    AnalyzeRequest, RepositoryResponse, RepositoryStatusResponse
)
from services.indexing_service import index_repository
from embeddings.chroma_store import collection_exists

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


def _repo_to_response(repo: Repository) -> RepositoryResponse:
    """Converts a Repository DB model to its API response schema."""
    return RepositoryResponse(
        id=repo.id,
        url=repo.url,
        name=repo.name,
        status=repo.status,
        progress_message=repo.progress_message,
        chunks_count=repo.chunks_count,
        created_at=repo.created_at,
        indexed_at=repo.indexed_at,
        error_message=repo.error_message,
    )


@router.post("/analyze", response_model=RepositoryResponse)
async def analyze_repository(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """
    Submit a GitHub repository URL for indexing.

    If the URL was already indexed, returns the existing record.
    Otherwise, starts indexing as a background task.
    """
    url = request.url

    # ── Check if already indexed ──────────────────────────────────────────────
    existing = session.exec(
        select(Repository).where(Repository.url == url)
    ).first()

    if existing:
        # If it's ready or currently being indexed, return existing
        if existing.status in (RepositoryStatus.READY, RepositoryStatus.CLONING,
                               RepositoryStatus.SCANNING, RepositoryStatus.CHUNKING,
                               RepositoryStatus.EMBEDDING, RepositoryStatus.INDEXING):
            logger.info(f"Repository already exists: {existing.id}")
            return _repo_to_response(existing)

        # If it previously failed, allow re-indexing by resetting status
        if existing.status == RepositoryStatus.FAILED:
            existing.status = RepositoryStatus.PENDING
            existing.error_message = None
            existing.progress_message = "Re-starting indexing..."
            session.add(existing)
            session.commit()
            session.refresh(existing)

            background_tasks.add_task(
                _run_indexing, existing.id, url
            )
            return _repo_to_response(existing)

    # ── Create new repository record ──────────────────────────────────────────
    repo = Repository(url=url, status=RepositoryStatus.PENDING)
    session.add(repo)
    session.commit()
    session.refresh(repo)

    # Start indexing in the background (non-blocking)
    background_tasks.add_task(_run_indexing, repo.id, url)

    logger.info(f"Started indexing for {url} (id={repo.id})")
    return _repo_to_response(repo)


async def _run_indexing(repository_id: str, url: str):
    """
    Wrapper that creates a fresh DB session for the background task.
    Background tasks can't reuse the request's session.
    """
    from database import engine
    from sqlmodel import Session as SQLSession

    with SQLSession(engine) as session:
        await index_repository(repository_id, url, session)


@router.get("", response_model=List[RepositoryResponse])
def list_repositories(session: Session = Depends(get_session)):
    """Returns all repositories."""
    repos = session.exec(select(Repository).order_by(Repository.created_at.desc())).all()
    return [_repo_to_response(r) for r in repos]


@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(repo_id: str, session: Session = Depends(get_session)):
    """Returns details for one repository."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return _repo_to_response(repo)


@router.get("/{repo_id}/status", response_model=RepositoryStatusResponse)
def get_repository_status(repo_id: str, session: Session = Depends(get_session)):
    """
    Lightweight status endpoint — used by the frontend to poll indexing progress.
    Only returns status fields, not full metadata.
    """
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryStatusResponse(
        id=repo.id,
        status=repo.status,
        progress_message=repo.progress_message,
        chunks_count=repo.chunks_count,
        error_message=repo.error_message,
    )


@router.delete("/{repo_id}")
def delete_repository(repo_id: str, session: Session = Depends(get_session)):
    """
    Completely removes a repository, including its DB records,
    chats, cloned files, and ChromaDB vector embeddings.
    """
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 1. Delete associated chats & messages
    from models.chat import Chat, Message
    chats = session.exec(select(Chat).where(Chat.repository_id == repo_id)).all()
    for chat in chats:
        messages = session.exec(select(Message).where(Message.chat_id == chat.id)).all()
        for msg in messages:
            session.delete(msg)
        session.delete(chat)

    # 2. Delete ChromaDB collection
    from embeddings.chroma_store import delete_collection
    delete_collection(repo_id)

    # 3. Delete cloned files on disk
    from ingestion.cloner import delete_clone
    delete_clone(repo_id)

    # 4. Delete repository record
    session.delete(repo)
    session.commit()

    logger.info(f"Deleted repository {repo_id} ({repo.name})")
    return {"status": "deleted", "id": repo_id}
