"""
tests/test_python_ast_chunker.py — Tests for Python AST chunker

Run with: pytest tests/test_python_ast_chunker.py -v
"""

import pytest
from chunking.python_ast_chunker import chunk_python_file


SAMPLE_CODE = '''
import os

CONSTANT = 42

def simple_function(x, y):
    """Simple addition."""
    return x + y

async def async_handler(request):
    """Async function."""
    data = await request.json()
    return data

class MyClass:
    """A sample class."""

    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"

    @staticmethod
    def static_method():
        return "static"

x = simple_function(1, 2)
'''


def test_chunks_are_created():
    """At least some chunks should be returned."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    assert len(chunks) > 0


def test_function_is_chunked():
    """simple_function should appear as its own chunk."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    symbol_names = [c.symbol_name for c in chunks]
    assert "simple_function" in symbol_names


def test_async_function_is_chunked():
    """Async functions should also be captured."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    symbol_names = [c.symbol_name for c in chunks]
    assert "async_handler" in symbol_names


def test_class_is_chunked():
    """The class itself should be a chunk."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    symbol_names = [c.symbol_name for c in chunks]
    assert "MyClass" in symbol_names


def test_method_is_chunked():
    """Class methods should be their own chunks with parent.method notation."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    symbol_names = [c.symbol_name for c in chunks]
    assert "MyClass.greet" in symbol_names


def test_line_numbers_are_correct():
    """start_line and end_line should be 1-indexed and valid."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    for chunk in chunks:
        assert chunk.start_line >= 1
        assert chunk.end_line >= chunk.start_line


def test_code_matches_lines():
    """Code content should match the actual source lines."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    for chunk in chunks:
        if chunk.symbol_name == "simple_function":
            assert "def simple_function" in chunk.code
            assert "return x + y" in chunk.code


def test_metadata_fields():
    """All metadata fields should be populated."""
    chunks = chunk_python_file("test.py", SAMPLE_CODE, "repo-123")
    for chunk in chunks:
        assert chunk.repository_id == "repo-123"
        assert chunk.file_path == "test.py"
        assert chunk.language == "python"
        assert chunk.chunk_id != ""


def test_syntax_error_returns_empty():
    """Syntax-broken code should return empty list (no crash)."""
    bad_code = "def foo(\n  this is not valid python!!!"
    chunks = chunk_python_file("bad.py", bad_code, "repo-123")
    assert chunks == []


def test_empty_file_returns_empty():
    chunks = chunk_python_file("empty.py", "", "repo-123")
    assert chunks == []
