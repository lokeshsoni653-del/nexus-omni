import logging
from typing import List, Dict, Any, Optional
from omnimind.rag.chunking import TextChunker, DocumentChunk
from omnimind.rag.embeddings import BaseEmbeddingProvider, MockEmbeddingProvider
from omnimind.rag.vector_store import BaseVectorStore, InMemoryVectorStore, SearchResult

logger = logging.getLogger("omnimind.rag.retriever")


class HybridRetriever:
    """Enterprise RAG Retriever supporting document ingestion, dense vector search, and keyword boosting."""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        chunker: Optional[TextChunker] = None,
    ):
        self.vector_store = vector_store or InMemoryVectorStore()
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.chunker = chunker or TextChunker(chunk_size=400, chunk_overlap=40)

    async def ingest_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """Chunk text document, generate embeddings, and store in vector store."""
        chunks = self.chunker.split_text(text, doc_id=doc_id, metadata=metadata)
        if not chunks:
            logger.warning(f"No chunks generated for doc_id='{doc_id}'")
            return []

        chunk_texts = [c.content for c in chunks]
        embeddings = await self.embedding_provider.embed_documents(chunk_texts)
        await self.vector_store.add_chunks(chunks, embeddings)

        logger.info(f"Ingested doc_id='{doc_id}' with {len(chunks)} chunks.")
        return chunks

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve top relevant chunks using dense vector search and keyword match reranking."""
        query_vector = await self.embedding_provider.embed_query(query)
        search_results: List[SearchResult] = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k * 2,  # Fetch candidate pool for reranking
            metadata_filter=metadata_filter
        )

        query_terms = set(query.lower().split())

        formatted_results: List[Dict[str, Any]] = []
        for res in search_results:
            chunk_terms = set(res.chunk.content.lower().split())
            overlap = len(query_terms.intersection(chunk_terms))
            
            # Hybrid score boosting based on keyword term overlap
            boosted_score = res.score + (overlap * 0.05)

            if boosted_score >= min_score:
                formatted_results.append({
                    "chunk_id": res.chunk.chunk_id,
                    "doc_id": res.chunk.doc_id,
                    "content": res.chunk.content,
                    "score": round(boosted_score, 4),
                    "metadata": res.chunk.metadata
                })

        # Sort again by boosted score
        formatted_results.sort(key=lambda item: item["score"], reverse=True)
        return formatted_results[:top_k]
