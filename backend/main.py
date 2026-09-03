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
    logger.info("📂 Repos directory: {settings.get_repos_path()}")
    logger.info(f"🗄️  ChromaDB directory: {settings.get_chroma_path()}")

    yield  # Application runs here and opens port immediately

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
# Allow requests from frontend in development and production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# ── Serve Built Frontend (Single-Port Production Deployment) ──────────────────
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", tags=["frontend"])
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/", tags=["meta"])
    def root():
        """Root endpoint when frontend is hosted separately."""
        return {
            "message": "Welcome to CodeMind API",
            "docs": "/docs",
            "health": "/health",
        }

