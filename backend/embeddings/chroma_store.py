"""
embeddings/chroma_store.py — ChromaDB Vector Store

ChromaDB is our vector database. It stores:
  - The code chunk text
  - Its embedding vector
  - Metadata (file path, line numbers, language, etc.)

And lets us query: "find chunks most similar to this query"

Each repository gets its own ChromaDB collection, named by repo ID.
This keeps repositories isolated from each other.

Student note:
  A vector database is like a regular database, but instead of
  searching by exact values (WHERE name = 'foo'), you search by
  similarity (find records "close to" this vector).
"""

import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings
from chunking.chunk_models import CodeChunk
from embeddings.embedder import embed_texts, embed_query

logger = logging.getLogger(__name__)

# Module-level ChromaDB client — one connection shared across all requests
_chroma_client: Optional[Any] = None


def get_chroma_client() -> Any:
    """Returns the ChromaDB client, creating it on first call."""
    global _chroma_client
    if _chroma_client is None:
        chroma_path = str(settings.get_chroma_path())
        logger.info(f"Connecting to ChromaDB at: {chroma_path}")
        _chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection_name(repository_id: str) -> str:
    """
    ChromaDB collection names must be:
    - 3-63 characters
    - Start and end with alphanumeric character
    - Only contain alphanumeric, underscores, hyphens
    We prefix with "repo_" and truncate the UUID.
    """
    # UUIDs have hyphens which are allowed, but we prefix for clarity
    safe_id = repository_id.replace("-", "_")
    return f"repo_{safe_id}"[:63]


def store_chunks(repository_id: str, chunks: List[CodeChunk]) -> int:
    """
    Embeds and stores a list of CodeChunks in ChromaDB.

    Args:
        repository_id: Unique ID of the repository
        chunks: List of code chunks to store

    Returns:
        Number of chunks successfully stored
    """
    if not chunks:
        return 0

    client = get_chroma_client()
    collection_name = get_collection_name(repository_id)

    # Get or create the collection for this repository
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"repository_id": repository_id},
    )

    # Process in batches to avoid memory issues with large repos
    batch_size = 100
    total_stored = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        # Generate embedding text for each chunk
        texts = [chunk.to_document_text() for chunk in batch]

        # Generate embeddings for the batch
        embeddings = embed_texts(texts)

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in batch]
        metadatas = [chunk.to_metadata() for chunk in batch]

        # Upsert = insert or update if ID already exists
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,    # store original text too (for inspection)
            metadatas=metadatas,
        )

        total_stored += len(batch)
        logger.debug(f"Stored batch {i//batch_size + 1}: {len(batch)} chunks")

    logger.info(f"Stored {total_stored} chunks for repo {repository_id}")
    return total_stored


def query_chunks(
    repository_id: str,
    query: str,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    Finds the most similar code chunks for a given query.

    Args:
        repository_id: Which repository to search
        query: The user's question or search term
        top_k: How many results to return

    Returns:
        List of dicts with chunk metadata + similarity score
    """
    client = get_chroma_client()
    collection_name = get_collection_name(repository_id)

    # Check if collection exists
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        logger.warning(f"No collection found for repo {repository_id}")
        return []

    # Embed the query
    query_embedding = embed_query(query)

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),  # can't request more than we have
        include=["metadatas", "distances", "documents"],
    )

    # Format results into a list of dicts
    chunks = []
    if results["metadatas"] and results["metadatas"][0]:
        docs = results.get("documents", [[]])[0] if results.get("documents") else []
        for i, (metadata, distance) in enumerate(
            zip(results["metadatas"][0], results["distances"][0])
        ):
            doc = docs[i] if i < len(docs) else ""
            # ChromaDB default space is squared L2 distance. For unit embeddings,
            # Cosine similarity is 1 - (distance / 2.0)
            similarity = max(0.0, min(1.0, 1.0 - float(distance) / 2.0))

            chunks.append({
                **metadata,
                "code": doc or metadata.get("code", ""),
                "similarity_score": similarity,
            })

    return chunks


def delete_collection(repository_id: str):
    """Deletes all indexed data for a repository."""
    client = get_chroma_client()
    collection_name = get_collection_name(repository_id)
    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted collection for repo {repository_id}")
    except Exception as e:
        logger.warning(f"Could not delete collection: {e}")


def collection_exists(repository_id: str) -> bool:
    """Returns True if a repository has already been indexed."""
    client = get_chroma_client()
    collection_name = get_collection_name(repository_id)
    try:
        col = client.get_collection(collection_name)
        return col.count() > 0
    except Exception:
        return False
