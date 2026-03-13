"""ChromaDB vector store wrapper.

This module is intentionally thin — it wraps ChromaDB behind a clean
interface so the rest of the codebase never imports chromadb directly.
The ingestion script and the RAG service both use this class.
"""

from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings


class VectorStore:
    """Manages a single ChromaDB collection for aerodynamic literature."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Upsert document chunks into the collection."""
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in ids],
        )

    def delete_by_ids(self, ids: list[str]) -> None:
        """Delete vectors by exact ids."""
        if not ids:
            return
        self._collection.delete(ids=ids)

    def delete_where(self, where: dict) -> None:
        """Delete vectors matching a metadata filter."""
        self._collection.delete(where=where)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> list[dict]:
        """Return the top-k most similar chunks for a query embedding.

        Each result dict contains: ``id``, ``document``, ``metadata``,
        ``distance``.
        """
        k = top_k or settings.RETRIEVAL_TOP_K
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "id": doc_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return chunks

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def count(self) -> int:
        return self._collection.count()

    def collection_name(self) -> str:
        return self._collection.name
    
    def get_collection(self):
        """Return the underlying ChromaDB collection for health checks."""
        return self._collection


# ---------------------------------------------------------------------------
# Module-level singleton — avoids re-opening the persistent client on every
# import.  RAG service and ingestion script both access this.
# ---------------------------------------------------------------------------
vector_store = VectorStore()
