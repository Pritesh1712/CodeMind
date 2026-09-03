"""
services/query_service.py — Question Answering Pipeline

This is the "answer pipeline" that runs every time a user asks a question:

  1. Classify the query (conceptual vs exact reference)
  2. Retrieve relevant code chunks
  3. Assess confidence
  4. Generate answer (or return "insufficient evidence")
  5. Extract citations
  6. Return everything to the API

Student note:
  This file shows how all the pieces fit together end-to-end.
  It's a great file to read if you want to understand the full
  RAG (Retrieval-Augmented Generation) pipeline.
"""

import logging
from typing import List
from sqlmodel import Session, select
from models.repository import Repository
from models.schemas import ChatResponse, Citation
from routing.query_router import classify_query
from retrieval.retriever import retrieve_chunks
from confidence.scorer import calculate_confidence
from generation.prompt_builder import build_prompt
from generation.groq_client import generate_answer
from generation.answer_parser import build_citations_from_chunks
from config import settings

logger = logging.getLogger(__name__)


def answer_question(
    repository_id: str,
    question: str,
    chat_id: str,
    session: Session,
) -> ChatResponse:
    """
    Full question-answering pipeline.

    Args:
        repository_id: Which repository to search
        question: The user's question
        chat_id: ID of the current chat (for response)
        session: Database session

    Returns:
        ChatResponse with answer, citations, and confidence score
    """
    # Get repo info (for context in the prompt)
    repo = session.get(Repository, repository_id)
    repo_name = repo.name if repo else ""

    logger.info(f"Processing question: '{question[:80]}...' for repo {repo_name}")

    # ── Step 1: Classify query ────────────────────────────────────────────────
    router_result = classify_query(question)
    query_type = router_result.query_type
    logger.info(f"Query type: {query_type} (confidence: {router_result.confidence:.2f})")

    # ── Step 2: Retrieve relevant chunks ──────────────────────────────────────
    chunks = retrieve_chunks(
        repository_id=repository_id,
        query=question,
        query_type=query_type,
        top_k=settings.top_k,
    )

    # ── Step 3: Check confidence ──────────────────────────────────────────────
    confidence = calculate_confidence(chunks)
    logger.info(f"Confidence: {confidence.score:.2f} (sufficient={confidence.is_sufficient})")

    # ── Step 4: Generate answer ───────────────────────────────────────────────
    follow_up_questions = []
    if chunks:
        # We have code/file evidence — generate an LLM answer
        messages = build_prompt(question, chunks, repo_name)
        raw_answer = generate_answer(messages)
        citations = build_citations_from_chunks(chunks)
        # Extract 2-3 logical follow-up questions
        from generation.answer_parser import extract_follow_up_questions
        answer, follow_up_questions = extract_follow_up_questions(raw_answer)
    else:
        # No chunks found in vector index
        answer = (
            f"I couldn't find any code files indexed in **{repo_name}** to answer this question.\n\n"
            "This may occur if the repository is empty, contains only non-code binary assets, or is still being indexed."
        )
        citations = []
        follow_up_questions = [
            f"What is the intended tech stack for {repo_name}?",
            "What files or folders are present in this repository?",
        ]

    # ── Step 5: Return result ─────────────────────────────────────────────────
    return ChatResponse(
        chat_id=chat_id,
        answer=answer,
        citations=citations,
        confidence_score=confidence.score,
        query_type=query_type,
        follow_up_questions=follow_up_questions,
    )


def _build_insufficient_evidence_response(chunks: List[dict]) -> str:
    """
    Creates a helpful response when confidence is too low.
    Mentions the closest files found (if any) to help the user refine their query.
    """
    if not chunks:
        return (
            "I couldn't find any relevant code in this repository to answer your question.\n\n"
            "This might mean:\n"
            "- The feature or concept you're asking about doesn't exist in this repository\n"
            "- The repository might use different terminology\n"
            "- Try rephrasing your question with specific function or class names"
        )

    # There are some chunks but not enough confidence
    closest_files = list({c.get("file_path", "") for c in chunks[:3] if c.get("file_path")})
    files_str = "\n".join(f"- `{f}`" for f in closest_files)

    return (
        "I couldn't find enough relevant evidence in this repository to answer that confidently.\n\n"
        f"The closest matches I found were in:\n{files_str}\n\n"
        "Try:\n"
        "- Being more specific (e.g., mention the function/class name)\n"
        "- Asking about a different aspect of the same topic\n"
        "- Using 'where is X used?' for exact symbol searches"
    )
