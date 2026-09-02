"""
chunking/python_ast_chunker.py — AST-Based Python Code Chunker

Uses Python's built-in `ast` module to parse Python source code
and split it into meaningful chunks at function/class boundaries.

Why AST chunking?
  Fixed-size line chunking might cut a function in half:
    Lines 1–50: top of a function
    Lines 51–100: bottom of the function + start of next
  AST-aware chunking keeps each function whole and labeled.

Student note:
  Abstract Syntax Tree (AST) = a tree representation of code structure.
  Python can parse its own code into an AST, giving us function/class
  locations without having to write complex regex patterns.
"""

import ast
import logging
from pathlib import Path
from typing import List
from chunking.chunk_models import CodeChunk

logger = logging.getLogger(__name__)


def chunk_python_file(
    file_path: str,
    code: str,
    repository_id: str,
    language: str = "python"
) -> List[CodeChunk]:
    """
    Splits a Python file into chunks using AST parsing.

    Strategy:
      1. Parse the entire file into an AST.
      2. Find all top-level functions, classes, and methods.
      3. Each becomes one chunk with precise line numbers.
      4. Everything else (module-level code) becomes a "module" chunk.

    Args:
        file_path: Relative file path (for metadata)
        code: The full source code text
        repository_id: ID of the parent repository
        language: Should be "python"

    Returns:
        List of CodeChunk objects
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # If the file has a syntax error, we can't parse it
        logger.warning(f"Syntax error in {file_path}: {e}")
        return []

    lines = code.split("\n")
    chunks = []
    covered_lines = set()  # track which lines are inside a named symbol

    # ── Walk the top-level nodes in the file ─────────────────────────────────
    for node in ast.iter_child_nodes(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Top-level function
            chunk = _extract_function_chunk(
                node, lines, file_path, repository_id, language, parent=""
            )
            if chunk:
                chunks.append(chunk)
                covered_lines.update(range(chunk.start_line, chunk.end_line + 1))

        elif isinstance(node, ast.ClassDef):
            # Class — we chunk the class itself AND each of its methods
            class_chunks = _extract_class_chunks(
                node, lines, file_path, repository_id, language
            )
            for c in class_chunks:
                chunks.append(c)
                covered_lines.update(range(c.start_line, c.end_line + 1))

    # ── Capture any module-level code not inside a function/class ────────────
    module_lines = [
        (i + 1, line) for i, line in enumerate(lines)
        if (i + 1) not in covered_lines and line.strip()
    ]

    if module_lines:
        # Group consecutive module-level lines into one chunk
        module_code = "\n".join(line for _, line in module_lines)
        first_line = module_lines[0][0]
        last_line = module_lines[-1][0]

        if module_code.strip():
            chunks.append(CodeChunk(
                repository_id=repository_id,
                file_path=file_path,
                language=language,
                code=module_code,
                start_line=first_line,
                end_line=last_line,
                symbol_name="",
                symbol_type="module",
            ))

    return chunks


def _extract_function_chunk(
    node: ast.FunctionDef,
    lines: List[str],
    file_path: str,
    repository_id: str,
    language: str,
    parent: str,
) -> CodeChunk:
    """Extracts a function or async function as a CodeChunk."""
    start = node.lineno       # 1-indexed
    end = node.end_lineno     # 1-indexed

    # Get the actual code lines (AST line numbers are 1-indexed)
    code_lines = lines[start - 1 : end]
    code = "\n".join(code_lines)

    # Build the full symbol name, e.g., "MyClass.my_method"
    full_name = f"{parent}.{node.name}" if parent else node.name

    symbol_type = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"

    return CodeChunk(
        repository_id=repository_id,
        file_path=file_path,
        language=language,
        code=code,
        start_line=start,
        end_line=end,
        symbol_name=full_name,
        symbol_type=symbol_type,
    )


def _extract_class_chunks(
    node: ast.ClassDef,
    lines: List[str],
    file_path: str,
    repository_id: str,
    language: str,
) -> List[CodeChunk]:
    """
    Extracts a class and all its methods as separate chunks.
    Returns: [class_chunk, method1_chunk, method2_chunk, ...]
    """
    result = []
    class_name = node.name

    # The class itself (including its docstring/class body)
    start = node.lineno
    end = node.end_lineno
    class_code = "\n".join(lines[start - 1 : end])

    result.append(CodeChunk(
        repository_id=repository_id,
        file_path=file_path,
        language=language,
        code=class_code,
        start_line=start,
        end_line=end,
        symbol_name=class_name,
        symbol_type="class",
    ))

    # Each method inside the class
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_chunk = _extract_function_chunk(
                child, lines, file_path, repository_id, language, parent=class_name
            )
            if method_chunk:
                result.append(method_chunk)

    return result
