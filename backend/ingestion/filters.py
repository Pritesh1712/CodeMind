"""
ingestion/filters.py — File Filtering Rules

Decides which files in a repository should be indexed.
We want source code, not binary files, build artifacts, or huge files.

Student note:
  This is one of the most important quality filters in the pipeline.
  Garbage in = garbage out. If we embed irrelevant files, our search
  results will be polluted with noise.
"""

import os
from pathlib import Path
from config import settings

# ── Directories to completely skip ───────────────────────────────────────────
# We won't even look inside these directories.
IGNORED_DIRS = {
    ".git", ".github", ".gitlab",
    "node_modules", "bower_components",
    "venv", ".venv", "env", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "build", "dist", "out", "target", "bin", "obj",
    ".next", ".nuxt", ".svelte-kit",
    "vendor", "third_party",
    "coverage", ".coverage",
    "migrations",  # DB migrations are often auto-generated
    ".idea", ".vscode",
}

# ── File extensions we WANT to index ─────────────────────────────────────────
# Map extension → language name (used for syntax highlighting later)
SUPPORTED_EXTENSIONS = {
    # Python
    ".py": "python",
    # JavaScript / TypeScript
    ".js": "javascript", ".jsx": "jsx",
    ".ts": "typescript", ".tsx": "tsx",
    # Web
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "scss",
    # Java / Kotlin
    ".java": "java", ".kt": "kotlin",
    # C / C++
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # Ruby
    ".rb": "ruby",
    # PHP
    ".php": "php",
    # Swift
    ".swift": "swift",
    # Shell
    ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    # Config / Data
    ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini",
    # Documentation (useful for understanding context)
    ".md": "markdown", ".rst": "rst",
    # SQL
    ".sql": "sql",
    # GraphQL
    ".graphql": "graphql", ".gql": "graphql",
    # Dockerfile
    ".dockerfile": "dockerfile",
}

# ── Specific filenames to skip regardless of extension ───────────────────────
IGNORED_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "Cargo.lock",
    ".DS_Store", "Thumbs.db",
    ".gitignore", ".gitattributes", ".npmignore",
    "LICENSE", "LICENCE",
}


def should_index_file(file_path: Path) -> bool:
    """
    Returns True if this file should be indexed.

    Checks (in order):
      1. No part of the path is an ignored directory
      2. Filename is not in the skip list
      3. Extension is in our supported list
      4. File size is within limits
    """
    # Check if any parent directory is ignored
    for part in file_path.parts:
        if part.lower() in IGNORED_DIRS:
            return False

    # Skip files with ignored names
    if file_path.name in IGNORED_FILENAMES:
        return False

    # Skip files without a supported extension
    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False

    # Skip files that are too large
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            return False
    except OSError:
        return False  # can't stat → skip

    return True


def get_language(file_path: Path) -> str:
    """Returns the programming language name for a file."""
    ext = file_path.suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext, "text")
