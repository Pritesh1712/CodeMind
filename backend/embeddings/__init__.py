# embeddings/__init__.py
from .embedder import embed_texts, embed_query, get_model
from .chroma_store import store_chunks, query_chunks, delete_collection, collection_exists
