"""
api/search.py — Direct Search Endpoint

POST /api/search — Search a repository directly (for debugging/testing)

This endpoint lets you test retrieval without going through the full
question-answering pipeline. Useful for:
  - Verifying indexing worked correctly
  - Debugging search quality
  - Understanding what gets retrieved for a query

Student note:
  This is the "debug/transparency" endpoint. Real users won't use this
  directly, but it's invaluable for development and understanding the system.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from database import get_session
from models.repository import Repository, RepositoryStatus
from models.schemas import SearchRequest, SearchResult
from retrieval.retriever import retrieve_chunks
from routing.query_router import classify_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=List[SearchResult])
def search_repository(
    request: SearchRequest,
    session: Session = Depends(get_session),
):
    """
    Directly search a repository's indexed code.

    Returns ranked code chunks without LLM generation.
    Useful for testing and debugging retrieval quality.
    """
    repo = session.get(Repository, request.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.status != RepositoryStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Repository not ready. Status: {repo.status}",
        )

    # Classify query to use appropriate retrieval strategy
    router_result = classify_query(request.query)

    chunks = retrieve_chunks(
        repository_id=request.repository_id,
        query=request.query,
        query_type=router_result.query_type,
        top_k=request.top_k,
    )

    return [
        SearchResult(
            file_path=c.get("file_path", ""),
            start_line=c.get("start_line", 0),
            end_line=c.get("end_line", 0),
            code=c.get("code", ""),
            language=c.get("language", ""),
            symbol_name=c.get("symbol_name", ""),
            similarity_score=c.get("similarity_score", 0.0),
        )
        for c in chunks
    ]
