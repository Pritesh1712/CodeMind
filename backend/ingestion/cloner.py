"""
ingestion/cloner.py — GitHub Repository Cloner

Handles cloning a GitHub repository to local disk using GitPython.

Steps:
  1. Validate the URL
  2. Check if already cloned (avoid re-cloning)
  3. Clone via git
  4. Return the local path

Student note:
  GitPython is a Python wrapper around the git command-line tool.
  It gives us a clean API instead of calling subprocess manually.
"""

import re
import shutil
import logging
from pathlib import Path
from git import Repo, GitCommandError, InvalidGitRepositoryError
from config import settings

logger = logging.getLogger(__name__)


def extract_repo_name(url: str) -> str:
    """
    Extracts "owner/repo" from a GitHub URL.
    Example: "https://github.com/tiangolo/fastapi" → "tiangolo/fastapi"
    """
    # Match: github.com/owner/repo (with optional .git suffix)
    match = re.match(r"https?://github\.com/([\w\-\.]+/[\w\-\.]+?)(?:\.git)?/?$", url)
    if match:
        return match.group(1)
    return "unknown/repo"


def get_clone_path(repo_id: str) -> Path:
    """Returns the local directory where a repo should be cloned."""
    return settings.get_repos_path() / repo_id


def clone_repository(url: str, repo_id: str) -> Path:
    """
    Clones a GitHub repository to local disk.

    Args:
        url: The GitHub repository URL
        repo_id: Unique ID for this repository (used as directory name)

    Returns:
        Path to the cloned repository on disk

    Raises:
        ValueError: if the URL is invalid or repo doesn't exist
        RuntimeError: if cloning fails
    """
    clone_path = get_clone_path(repo_id)

    # If already cloned, unpack any zips and return
    if clone_path.exists() and (clone_path / ".git").exists():
        logger.info(f"Repository already cloned at {clone_path}")
        _unpack_zip_archives(clone_path)
        return clone_path

    # Clean up any partial clone
    if clone_path.exists():
        delete_clone(repo_id)

    logger.info(f"Cloning {url} → {clone_path}")

    try:
        # Clone with a depth limit to speed things up for large repos
        Repo.clone_from(
            url,
            str(clone_path),
            depth=1,
            no_single_branch=False,
        )
        logger.info(f"Clone complete: {clone_path}")
        _unpack_zip_archives(clone_path)
        return clone_path

    except GitCommandError as e:
        error_msg = str(e)
        # Provide helpful error messages for common failures
        if "not found" in error_msg.lower() or "repository" in error_msg.lower():
            raise ValueError(
                f"Repository not found or is private: {url}. "
                "Make sure the repository exists and is public."
            )
        elif "timeout" in error_msg.lower():
            raise RuntimeError("Clone timed out. The repository might be too large.")
        else:
            raise RuntimeError(f"Failed to clone repository: {error_msg}")


def _remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree on Windows to clear read-only git files."""
    import os
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _unpack_zip_archives(clone_path: Path):
    """Recursively unzips any .zip archives in the repository."""
    import zipfile
    for zip_file in list(clone_path.glob("*.zip")) + list(clone_path.glob("*/*.zip")):
        try:
            extract_target = zip_file.parent / zip_file.stem
            if not extract_target.exists():
                logger.info(f"Unpacking archive {zip_file.name} to {extract_target}")
                with zipfile.ZipFile(zip_file, 'r') as z:
                    z.extractall(extract_target)
        except Exception as ze:
            logger.warning(f"Could not extract zip archive {zip_file}: {ze}")


def delete_clone(repo_id: str):
    """Removes the local clone of a repository (handles Windows read-only git files)."""
    clone_path = get_clone_path(repo_id)
    if clone_path.exists():
        try:
            shutil.rmtree(clone_path, onerror=_remove_readonly)
            logger.info(f"Deleted clone: {clone_path}")
        except Exception as e:
            logger.warning(f"Could not remove entire clone directory {clone_path}: {e}")
