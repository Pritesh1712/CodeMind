"""
services/indexing_service.py — Repository Indexing Orchestrator

This is the "brain" of the ingestion pipeline. It coordinates:
  1. Clone the repository
  2. Walk the files
  3. Chunk each file
  4. Generate embeddings
  5. Store in ChromaDB
  6. Update database status

It runs as a background task so the API can return immediately
and the frontend can poll for status updates.

Student note:
  This is an example of the "Facade Pattern" — it wraps multiple
  complex subsystems (cloner, chunker, embedder, store) behind
  one simple interface: index_repository(url, repo_id, db_session)
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from sqlmodel import Session
from models.repository import Repository, RepositoryStatus
from ingestion.cloner import clone_repository, extract_repo_name
from ingestion.file_walker import walk_repository
from chunking.chunker import chunk_file
from embeddings.chroma_store import store_chunks, collection_exists
from config import settings

logger = logging.getLogger(__name__)


def _update_status(
    session: Session,
    repo: Repository,
    status: str,
    message: str = "",
):
    """Helper to update repository status in the database."""
    repo.status = status
    repo.progress_message = message
    session.add(repo)
    session.commit()
    session.refresh(repo)
    logger.info(f"[{repo.name}] {status}: {message}")


async def index_repository(
    repository_id: str,
    url: str,
    session: Session,
):
    """
    Full indexing pipeline for a GitHub repository.

    This function:
      - Updates repository status at each step
      - Handles errors gracefully
      - Is idempotent (safe to call multiple times)

    Args:
        repository_id: Unique ID for this repository
        url: GitHub repository URL
        session: Database session for status updates
    """
    # Get the repository record from the database
    repo = session.get(Repository, repository_id)
    if not repo:
        logger.error(f"Repository {repository_id} not found in database")
        return

    try:
        # ── Step 1: Clone ─────────────────────────────────────────────────────
        _update_status(session, repo, RepositoryStatus.CLONING,
                       "Cloning repository from GitHub...")
        repo_path = clone_repository(url, repository_id)
        repo.name = extract_repo_name(url)
        await asyncio.sleep(0.3)

        # ── Step 2: Walk files ────────────────────────────────────────────────
        _update_status(session, repo, RepositoryStatus.SCANNING,
                       "Scanning and discovering source files...")
        files = walk_repository(repo_path)

        if not files:
            raise ValueError("No indexable source files found in this repository.")

        _update_status(session, repo, RepositoryStatus.SCANNING,
                       f"Found {len(files)} source files to index")
        await asyncio.sleep(0.4)

        # ── Step 3: Chunk all files ───────────────────────────────────────────
        _update_status(session, repo, RepositoryStatus.CHUNKING,
                       f"AST parsing and splitting {len(files)} files...")
        all_chunks = []
        for abs_path, rel_path, language in files:
            chunks = chunk_file(abs_path, rel_path, language, repository_id)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise ValueError("No code chunks could be extracted from this repository.")

        _update_status(session, repo, RepositoryStatus.CHUNKING,
                       f"Created {len(all_chunks)} code chunks with exact line ranges")
        await asyncio.sleep(0.4)

        # ── Step 4 + 5: Embed and store ───────────────────────────────────────
        _update_status(session, repo, RepositoryStatus.EMBEDDING,
                       f"Computing 384-d semantic embeddings for {len(all_chunks)} chunks...")

        stored_count = store_chunks(repository_id, all_chunks)
        await asyncio.sleep(0.4)

        _update_status(session, repo, RepositoryStatus.INDEXING,
                       f"Saving {stored_count} embeddings into ChromaDB vector store...")
        await asyncio.sleep(0.4)

        # ── Done! ─────────────────────────────────────────────────────────────
        repo.status = RepositoryStatus.READY
        repo.progress_message = f"Ready! Indexed {stored_count} code chunks."
        repo.chunks_count = stored_count
        repo.indexed_at = datetime.utcnow()
        session.add(repo)
        session.commit()

        logger.info(f"✅ Indexing complete: {repo.name} ({stored_count} chunks)")

    except Exception as e:
        error_message = str(e)
        logger.error(f"❌ Indexing failed for {repository_id}: {error_message}")

        repo.status = RepositoryStatus.FAILED
        repo.error_message = error_message
        repo.progress_message = f"Indexing failed: {error_message}"
        session.add(repo)
        session.commit()
