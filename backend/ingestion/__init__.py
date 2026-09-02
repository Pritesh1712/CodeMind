# ingestion/__init__.py
# Note: cloner imports gitpython — only import when needed (after pip install)
from .filters import should_index_file, get_language
