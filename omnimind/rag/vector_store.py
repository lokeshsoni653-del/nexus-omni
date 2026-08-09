import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from omnimind.rag.chunking import DocumentChunk
from omnimind.rag.embeddings import BaseEmbeddingProvider, cosine_similarity

logger = logging.getLogger("omnimind.rag.vector_store")


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float


class BaseVectorStore(ABC):
    """Abstract interface for Vector Databases."""

    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Store document chunks and their embedding vectors."""
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform vector similarity search."""
        pass

    @abstractmethod
    async def delete_document(self, doc_id: str) -> int:
        """Delete all chunks for given doc_id."""
        pass


class InMemoryVectorStore(BaseVectorStore):
    """High performance in-memory vector store with metadata filtering."""

    def __init__(self):
        self._chunks: Dict[str, DocumentChunk] = {}
        self._vectors: Dict[str, List[float]] = {}

    async def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must equal number of embeddings.")

        for chunk, emb in zip(chunks, embeddings):
            self._chunks[chunk.chunk_id] = chunk
            self._vectors[chunk.chunk_id] = emb
        
        logger.info(f"Added {len(chunks)} chunks to InMemoryVectorStore.")

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        results: List[SearchResult] = []

        for chunk_id, chunk in self._chunks.items():
            # Apply metadata filtering if specified
            if metadata_filter:
                match = all(
                    chunk.metadata.get(k) == v for k, v in metadata_filter.items()
                )
                if not match:
                    continue

            emb = self._vectors[chunk_id]
            score = cosine_similarity(query_vector, emb)
            results.append(SearchResult(chunk=chunk, score=round(score, 4)))

        # Sort by similarity score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def delete_document(self, doc_id: str) -> int:
        to_delete = [
            chunk_id for chunk_id, chunk in self._chunks.items()
            if chunk.doc_id == doc_id
        ]

        for chunk_id in to_delete:
            del self._chunks[chunk_id]
            del self._vectors[chunk_id]

        logger.info(f"Deleted {len(to_delete)} chunks for doc_id='{doc_id}'")
        return len(to_delete)
