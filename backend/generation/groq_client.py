"""
generation/groq_client.py — Groq LLM Client

Sends prompts to the Groq API and gets back completions.
Groq provides extremely fast inference for Llama models.

Student note:
  Groq API is compatible with the OpenAI API format, so the same
  messages=[...] pattern works. The main difference is speed:
  Groq can process ~800 tokens/second vs OpenAI's ~50 tokens/second.

  API Docs: https://console.groq.com/docs
"""

import logging
from typing import List, Dict, Optional
from groq import Groq
from config import settings

logger = logging.getLogger(__name__)

# Module-level client instance (reused across requests)
_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    """Returns the Groq client, creating it on first call."""
    global _groq_client
    if _groq_client is None:
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Please add it to your .env file. "
                "Get a free key at https://console.groq.com"
            )
        _groq_client = Groq(api_key=settings.groq_api_key)
        logger.info("Groq client initialized")
    return _groq_client


FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
]


def generate_answer(
    messages: List[Dict[str, str]],
    max_tokens: int = 2048,
    temperature: float = 0.1,  # low temperature = more deterministic/factual
) -> str:
    """
    Sends messages to the Groq API and returns the response text.

    Args:
        messages: List of {role, content} dicts (system + user)
        max_tokens: Maximum length of the response
        temperature: 0.0 = fully deterministic, 1.0 = creative/random
                     We use 0.1 for factual code questions

    Returns:
        The LLM's response as a plain string

    Raises:
        RuntimeError: if the API call fails
    """
    import re
    client = get_groq_client()

    models_to_try = [settings.groq_model] + [m for m in FALLBACK_MODELS if m != settings.groq_model]
    last_error = ""

    for model in models_to_try:
        try:
            logger.info(f"Calling Groq API (model={model})")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            answer = response.choices[0].message.content or ""
            # Strip any chain-of-thought tags (e.g. from Qwen reasoning models)
            answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
            logger.info(f"Groq response received from {model}: {len(answer)} characters")
            return answer

        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            logger.warning(f"Groq API error on model {model}: {error_msg}")
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise RuntimeError(
                    "Invalid Groq API key. Please check your GROQ_API_KEY in .env"
                )
            # Otherwise try next fallback model
            continue

    if "rate_limit" in last_error.lower():
        raise RuntimeError("Groq API rate limit reached. Please wait a moment and try again.")
    raise RuntimeError(f"LLM generation failed: {last_error}")
