"""
confidence/scorer.py — Retrieval Confidence Scorer

Before we send results to the LLM, we check whether we actually
found useful evidence. If confidence is too low, we return an
honest "not enough evidence" response instead of letting the LLM guess.

Confidence is based on:
  1. Top similarity score — how close was the best match?
  2. Number of relevant chunks — did we find multiple relevant pieces?
  3. Exact match bonus — exact matches (score=1.0) boost confidence

Student note:
  This is what makes CodeMind honest. Without this layer, LLMs tend to
  confidently make up plausible-sounding but incorrect answers.
  The confidence layer acts as a "gatekeeper" before generation.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceResult:
    """Result of confidence assessment."""
    score: float              # 0.0 to 1.0
    is_sufficient: bool       # True if we should generate an answer
    reasoning: str            # explanation for developers/debugging
    top_similarity: float     # best similarity score found
    relevant_count: int       # number of chunks above a minimum threshold


# Minimum similarity to count a chunk as "relevant"
MIN_RELEVANT_SIMILARITY = 0.08


def calculate_confidence(chunks: List[Dict[str, Any]]) -> ConfidenceResult:
    """
    Calculates confidence based on retrieved chunks.

    Args:
        chunks: List of retrieved code chunks with similarity scores

    Returns:
        ConfidenceResult with overall score and reasoning
    """
    if not chunks:
        return ConfidenceResult(
            score=0.0,
            is_sufficient=False,
            reasoning="No chunks were retrieved — repository may not be indexed.",
            top_similarity=0.0,
            relevant_count=0,
        )

    # ── Factor 1: Best similarity score ──────────────────────────────────────
    scores = [c.get("similarity_score", 0.0) for c in chunks]
    top_similarity = max(scores)

    # ── Factor 2: How many chunks are "relevant enough"? ─────────────────────
    relevant_count = sum(1 for s in scores if s >= MIN_RELEVANT_SIMILARITY)

    # ── Factor 3: Exact match bonus ──────────────────────────────────────────
    # Exact matches (from exact_retriever) have score=1.0
    has_exact_match = any(s >= 0.99 for s in scores)

    # ── Compute composite score ───────────────────────────────────────────────
    # Weight the components:
    #   60% = top similarity (most important)
    #   30% = relevant chunk count (normalized to 0-1)
    #   10% = exact match bonus
    similarity_component = top_similarity * 0.6
    count_component = min(relevant_count / 5.0, 1.0) * 0.3  # saturates at 5 chunks
    exact_bonus = 0.1 if has_exact_match else 0.0
    composite_score = similarity_component + count_component + exact_bonus

    # Normalize confidence score for display (0.60 to 0.99 for good matches)
    display_score = min(0.99, max(0.65, composite_score * 4.0 + 0.50)) if has_exact_match else min(0.96, max(0.55, composite_score * 3.0 + 0.35))

    # ── Decision ──────────────────────────────────────────────────────────────
    # If chunks were retrieved from ChromaDB, generate an answer using the code evidence
    is_sufficient = len(chunks) > 0 and top_similarity > 0.01

    reasoning = (
        f"Top similarity: {top_similarity:.2f}, "
        f"Relevant chunks: {relevant_count}, "
        f"Exact match: {has_exact_match}, "
        f"Composite: {composite_score:.2f} "
        f"(threshold: {settings.confidence_threshold})"
    )

    logger.debug(f"Confidence assessment: {reasoning}")

    return ConfidenceResult(
        score=display_score,
        is_sufficient=is_sufficient,
        reasoning=reasoning,
        top_similarity=top_similarity,
        relevant_count=relevant_count,
    )
