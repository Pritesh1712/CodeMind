"""
generation/prompt_builder.py — LLM Prompt Constructor

Assembles the final prompt that gets sent to the LLM.
The prompt includes:
  1. System instruction (rules for the LLM to follow)
  2. Retrieved code chunks (the "evidence")
  3. The user's question

Student note:
  Prompt engineering is crucial for RAG (Retrieval-Augmented Generation).
  The system prompt tells the LLM to ONLY use the provided code,
  not its general knowledge about programming. This is what makes
  CodeMind cite actual repository code instead of making things up.
"""

from typing import List, Dict, Any


SYSTEM_PROMPT = """You are CodeMind, an AI mentor specialized in explaining GitHub codebases clearly to students and developers.

STUDENT & RESUME GUIDANCE:
When explaining a project or codebase:
- Provide a clear, structured, step-by-step overview from start to end (1. Project Purpose & High-Level Architecture, 2. Key Modules & Tech Stack, 3. Core Request/Data Flow, 4. Important Implementation Highlights).
- Explain *why* components are structured this way so students can speak confidently about this project in technical interviews and on their resume.

IMPORTANT RULES — follow these strictly:
1. Answer ONLY based on the code evidence provided below. Do not invent details not supported by the evidence.
2. If the evidence does not contain enough information, say clearly: "I couldn't find enough relevant evidence in this repository to answer that confidently."
3. Always cite your sources using the format: `filename:start_line-end_line` (e.g., `src/auth.py:42-67`).
4. Format code cleanly using markdown code blocks with the language specified.
5. Be concise, well-formatted, and educational.
6. At the very end of your response, ALWAYS suggest 2 to 3 logical, high-value follow-up questions formatted under this exact section:

### 💡 Next Questions to Explore:
- [Specific follow-up question 1]?
- [Specific follow-up question 2]?
- [Specific follow-up question 3]?
"""


def build_prompt(
    question: str,
    chunks: List[Dict[str, Any]],
    repo_name: str = "",
) -> List[Dict[str, str]]:
    """
    Builds the messages list for the Groq API call.

    Args:
        question: The user's question
        chunks: Retrieved code chunks with metadata
        repo_name: Repository name (for context)

    Returns:
        List of message dicts in OpenAI-compatible format:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    # Build the context section from retrieved chunks
    context_text = _format_chunks_as_context(chunks, repo_name)

    # Build the user message
    user_message = f"""Repository: {repo_name or "Unknown"}

Retrieved Code Evidence:
{context_text}

Question: {question}

Please answer the question based only on the code evidence above."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def _format_chunks_as_context(
    chunks: List[Dict[str, Any]],
    repo_name: str,
) -> str:
    """
    Formats retrieved chunks into a readable context string for the LLM.
    Each chunk is labeled with its file path and line range.
    """
    if not chunks:
        return "No relevant code found."

    parts = []

    for i, chunk in enumerate(chunks, 1):
        file_path = chunk.get("file_path", "unknown")
        start_line = chunk.get("start_line", 0)
        end_line = chunk.get("end_line", 0)
        language = chunk.get("language", "")
        symbol_name = chunk.get("symbol_name", "")
        code = chunk.get("code", "")

        # Header for this chunk
        header = f"[Evidence {i}] {file_path}:{start_line}-{end_line}"
        if symbol_name:
            header += f" ({symbol_name})"

        parts.append(f"""
{header}
```{language}
{code}
```""")

    return "\n".join(parts)
