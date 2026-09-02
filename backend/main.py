"""
main.py — CodeMind Backend Entry Point

This is where the FastAPI application is created and configured.

To run:
  uvicorn main:app --reload --port 8000

Then visit:
  http://localhost:8000/docs    ← Interactive API documentation (Swagger UI)
  http://localhost:8000/redoc   ← Alternative API docs

Student note:
  FastAPI automatically generates API documentation from your code!
  Open /docs to see all endpoints, try them out, and understand the schemas.
"""

import sys
import logging
from contextlib import asynccontextmanager

# Configure UTF-8 encoding on Windows to prevent charmap UnicodeEncodeErrors with emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file first
from dotenv import load_dotenv
load_dotenv()

from database import create_db_and_tables
from api import repositories_router, chat_router, search_router
from config import settings

# ── Logging Configuration ─────────────────────────────────────────────────────
# Set up logging so we can see what's happening in the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Application Lifecycle ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs startup/shutdown logic.
    Called once when the server starts and once when it stops.
    """
    # Startup
    logger.info("🚀 CodeMind backend starting...")
    create_db_and_tables()  # Create SQLite tables if they don't exist
    logger.info("✅ Database ready")
    logger.info(f"📂 Repos directory: {settings.get_repos_path()}")
    logger.info(f"🗄️  ChromaDB directory: {settings.get_chroma_path()}")

    yield  # Application runs here

    # Shutdown (cleanup if needed)
    logger.info("👋 CodeMind backend shutting down")


# ── Create FastAPI App ────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeMind API",
    description="AI-powered codebase chat portal — ask questions about any GitHub repository",
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) allows the React frontend (port 5173)
# to make requests to this backend (port 8000).
# Without CORS, browsers block cross-origin requests by default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Create React App dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # Allow GET, POST, DELETE, etc.
    allow_headers=["*"],   # Allow all headers
)


# ── Register Routers ──────────────────────────────────────────────────────────
# Each router handles a group of related endpoints
app.include_router(repositories_router)
app.include_router(chat_router)
app.include_router(search_router)


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
def health_check():
    """Simple health check endpoint — returns 200 if the server is running."""
    return {"status": "ok", "service": "CodeMind API"}


@app.get("/", tags=["meta"])
def root():
    """Root endpoint — shows basic info."""
    return {
        "message": "Welcome to CodeMind API",
        "docs": "/docs",
        "health": "/health",
    }
