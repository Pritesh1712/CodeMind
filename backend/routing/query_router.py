"""
routing/query_router.py — Query Type Classifier

Classifies a user's question into one of two types:
  - CONCEPTUAL: "How does authentication work?" → use semantic search
  - EXACT_REFERENCE: "Where is login() called?" → use exact/symbol search

Why does this matter?
  If someone asks "Where is `authenticate` used?", vector similarity
  search might return chunks about authentication concepts, not the
  actual call sites. Exact search is much better for reference queries.

How we classify:
  Simple keyword heuristics — fast, transparent, and easy to debug.
  No LLM needed for this step (saves cost and latency).

Student note:
  This is intentionally kept simple for Month 1. Future improvements:
  - Use an LLM to classify
  - Add more query types (e.g., FILE_SEARCH, COMPARISON, DEBUG)
  - Learn from user feedback
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QueryType:
    """Query type constants."""
    CONCEPTUAL = "conceptual"
    EXACT_REFERENCE = "exact_reference"


@dataclass
class RouterResult:
    """Result of query classification."""
    query_type: str          # "conceptual" or "exact_reference"
    confidence: float        # how confident we are in this classification
    reasoning: str           # human-readable explanation (useful for debugging)


# ── Keyword patterns that signal an exact-reference query ────────────────────
# These phrases suggest the user wants to find *where* something appears,
# not *understand* how it works.
EXACT_REFERENCE_PATTERNS = [
    r"\bwhere (is|are|does)\b",        # "where is X used?"
    r"\bwhere (is|are) .+ (used|called|defined|declared)\b",
    r"\bfind (all|any)?\b",           # "find all references to..."
    r"\bwhich files?\b",              # "which files import...?"
    r"\blist (all|the)\b",            # "list all functions that..."
    r"\bwhat files?\b",               # "what files use...?"
    r"\breferences? to\b",            # "references to PaymentService"
    r"\busages? of\b",                # "usages of authenticate"
    r"\bimports? of\b",               # "imports of React"
    r"\bcalled (from|by|in)\b",       # "called from where?"
    r"\bdefined in\b",                # "defined in which file?"
    r"\bwhich (functions?|methods?|classes?)\b",
    r"\bhow many times?\b",
]


def classify_query(query: str) -> RouterResult:
    """
    Classifies a query as conceptual or exact_reference.

    Args:
        query: The user's question

    Returns:
        RouterResult with the classification and reasoning
    """
    query_lower = query.lower().strip()

    # Check each exact-reference pattern
    for pattern in EXACT_REFERENCE_PATTERNS:
        if re.search(pattern, query_lower):
            logger.debug(f"Query classified as EXACT_REFERENCE (pattern: {pattern})")
            return RouterResult(
                query_type=QueryType.EXACT_REFERENCE,
                confidence=0.85,
                reasoning=f"Query matches reference-search pattern: '{pattern}'",
            )

    # Default to conceptual (most questions are conceptual)
    logger.debug("Query classified as CONCEPTUAL (no reference patterns found)")
    return RouterResult(
        query_type=QueryType.CONCEPTUAL,
        confidence=0.75,
        reasoning="No reference-search keywords found; treating as conceptual query",
    )
