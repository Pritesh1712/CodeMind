"""
database.py — Database Setup

We use SQLite (a simple file-based database) via SQLModel.
SQLModel = SQLAlchemy + Pydantic, so our DB models are also our API schemas.

Student note:
  - SQLite stores everything in a single .db file — great for learning!
  - create_db_and_tables() is called once when the app starts
"""

import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from config import settings

def _get_engine():
    """Initializes the database engine and ensures parent directories exist."""
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        file_path_str = db_url.replace("sqlite:///", "")
        # Remove any sqlite relative path prefixes
        db_path = Path(file_path_str)
        if not db_path.is_absolute():
            # If relative, ensure parent dir exists relative to current working dir
            db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            db_path.parent.mkdir(parents=True, exist_ok=True)

    return create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )

# SQLite engine — creates the .db file if it doesn't exist
engine = _get_engine()


def create_db_and_tables():
    """Creates all database tables defined in our models and migrates columns."""
    from sqlalchemy import text
    SQLModel.metadata.create_all(engine)
    
    # Auto-migrate newly added columns if table already existed
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE chat ADD COLUMN is_pinned BOOLEAN DEFAULT 0"))
            conn.commit()
        except Exception:
            pass  # Column already exists


def get_session():
    """
    Dependency for FastAPI routes.
    Each request gets its own database session, which is closed afterward.
    Usage in a route:  session: Session = Depends(get_session)
    """
    with Session(engine) as session:
        yield session
