"""
tests/test_file_filters.py — Tests for file filtering logic

Run with: pytest tests/test_file_filters.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from ingestion.filters import should_index_file, get_language, SUPPORTED_EXTENSIONS


def make_fake_path(path_str: str, size_bytes: int = 1000) -> Path:
    """Creates a mock Path object with a fake stat."""
    p = Path(path_str)
    mock_stat = MagicMock()
    mock_stat.st_size = size_bytes
    with patch.object(Path, 'stat', return_value=mock_stat):
        return p


class TestGetLanguage:
    def test_python(self):
        assert get_language(Path("src/auth.py")) == "python"

    def test_javascript(self):
        assert get_language(Path("app.js")) == "javascript"

    def test_typescript(self):
        assert get_language(Path("utils.ts")) == "typescript"

    def test_unknown_extension(self):
        assert get_language(Path("file.xyz")) == "text"


class TestShouldIndexFile:
    def test_ignores_node_modules(self):
        p = Path("project/node_modules/lodash/index.js")
        assert not should_index_file(p)

    def test_ignores_git_dir(self):
        p = Path("project/.git/config")
        assert not should_index_file(p)

    def test_ignores_pycache(self):
        p = Path("project/__pycache__/module.pyc")
        assert not should_index_file(p)

    def test_ignores_venv(self):
        p = Path("project/venv/lib/site-packages/requests/__init__.py")
        assert not should_index_file(p)

    def test_ignores_lock_files(self):
        p = Path("package-lock.json")
        assert not should_index_file(p)

    def test_ignores_unsupported_extension(self):
        p = Path("image.png")
        assert not should_index_file(p)

    def test_ignores_binary(self):
        p = Path("program.exe")
        assert not should_index_file(p)

    def test_all_supported_extensions(self):
        """Every extension in SUPPORTED_EXTENSIONS should pass the filter
        (when file has reasonable size and is not in ignored dir)."""
        for ext in SUPPORTED_EXTENSIONS:
            p = Path(f"src/file{ext}")
            # Mock stat to return small file size
            with patch.object(Path, 'stat', return_value=MagicMock(st_size=100)):
                result = should_index_file(p)
                assert result, f"Extension {ext} should be indexed"
