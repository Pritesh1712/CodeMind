"""
generation/answer_parser.py — Citation Extractor

After the LLM generates an answer, we parse it to extract
file:line citations mentioned in the response.

LLMs (when instructed) tend to write things like:
  "The authentication is handled in `src/auth.py:42-67`"

We extract those and return structured Citation objects.

Student note:
  We also inject citations based on which chunks we retrieved.
  Even if the LLM doesn't explicitly cite a file, if it used that
  chunk as evidence, we include it as a citation.
"""

import re
import logging
from typing import List, Tuple, Dict, Any
from models.schemas import Citation

logger = logging.getLogger(__name__)

# Regex to find citation patterns like:
#   src/auth.py:42-67
#   backend/api/routes.py:10-25
#   auth.ts:100-150
CITATION_PATTERN = re.compile(
    r"`?([^\s`]+\.[a-zA-Z]+):(\d+)-(\d+)`?"
)


def extract_citations_from_text(text: str) -> List[Tuple[str, int, int]]:
    """
    Finds citation patterns in LLM response text.

    Returns:
        List of (file_path, start_line, end_line) tuples
    """
    citations = []
    for match in CITATION_PATTERN.finditer(text):
        file_path = match.group(1)
        start_line = int(match.group(2))
        end_line = int(match.group(3))
        citations.append((file_path, start_line, end_line))
    return citations


def build_citations_from_chunks(chunks: List[Dict[str, Any]]) -> List[Citation]:
    """
    Creates Citation objects from retrieved chunks.
    These are the "ground truth" citations — based on what we actually retrieved.

    We prefer this over parsing from LLM text because:
      1. LLMs sometimes format citations slightly differently
      2. We have the exact code snippets from retrieval
      3. This ensures citations are always accurate
    """
    citations = []
    seen = set()

    for chunk in chunks:
        file_path = chunk.get("file_path", "")
        start_line = chunk.get("start_line", 0)
        end_line = chunk.get("end_line", 0)
        code = chunk.get("code", "")
        language = chunk.get("language", "")
        symbol_name = chunk.get("symbol_name", "")

        # Deduplicate
        key = f"{file_path}:{start_line}"
        if key in seen:
            continue
        seen.add(key)

        citations.append(Citation(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            code=code,
            language=language,
            symbol_name=symbol_name,
        ))

    return citations


def extract_follow_up_questions(text: str) -> Tuple[str, List[str]]:
    """
    Extracts 2-3 suggested follow-up questions from the LLM answer.
    Returns (cleaned_text_without_raw_section, list_of_questions).
    """
    questions = []
    # Match section "### 💡 Next Questions to Explore:" or similar
    section_pattern = r"(?:###\s*(?:💡\s*)?(?:Next|Related|Follow-up|Follow up)\s*Questions(?:\s*to\s*Explore)?:?\s*)([\s\S]*?)$"
    match = re.search(section_pattern, text, re.IGNORECASE)

    cleaned_text = text
    if match:
        questions_block = match.group(1)
        for line in questions_block.strip().split("\n"):
            line = line.strip()
            # Match '- question' or '1. question' or '- **question**'
            q_match = re.match(r"^(?:[-*•]|\d+\.)\s*(?:\*\*)?(.*?)(?:\*\*)?\??$", line)
            if q_match:
                q_text = q_match.group(1).strip()
                q_text = q_text.strip("*_` ").rstrip("?")
                # Make sure it's a real question
                if len(q_text) > 8 and not q_text.startswith("[Specific"):
                    questions.append(f"{q_text}?")

        # Clean the raw section from the main text body so we render it as interactive pills
        cleaned_text = text[:match.start()].rstrip()

    # Fallback smart resume/learning questions if none explicitly found
    if not questions and len(text) > 120 and "not enough evidence" not in text.lower():
        questions = [
            "How does data and state flow between components?",
            "What are the best resume talking points for this project?",
            "Explain how the routing and main pages are structured",
        ]

    return cleaned_text, questions[:3]
