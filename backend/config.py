"""
config.py — Application Configuration

All configuration values come from environment variables (or .env file).
We use pydantic-settings so values are validated and typed automatically.

Student note:
  - Settings class reads from .env automatically
  - Access config anywhere with: from config import settings
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Central config for CodeMind backend.
    Each field maps directly to an environment variable.
    """

    # ── LLM ──────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # ── Embeddings ───────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Storage ──────────────────────────────────────────────
    repos_dir: str = "../data/repos"
    chroma_dir: str = "../data/chroma"
    database_url: str = "sqlite:///./codemind.db"

    # ── Retrieval ────────────────────────────────────────────
    top_k: int = 8               # how many chunks to retrieve per query
    confidence_threshold: float = 0.20  # min score to proceed with generation

    # ── Repository Limits ────────────────────────────────────
    max_repo_size_mb: int = 500
    max_file_size_mb: int = 2

    # ── Server ───────────────────────────────────────────────
    backend_port: int = 8000
    frontend_port: int = 5173

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ignore unknown env vars

    def get_repos_path(self) -> Path:
        """Returns absolute path to the repos storage directory."""
        p = Path(self.repos_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_chroma_path(self) -> Path:
        """Returns absolute path to ChromaDB storage directory."""
        p = Path(self.chroma_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


# Singleton — import this everywhere
settings = Settings()
