import pytest
from omnimind.rag import (
    TextChunker, InMemoryVectorStore, MockEmbeddingProvider, HybridRetriever
)


@pytest.mark.asyncio
async def test_text_chunker():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = "OmniMind AI is a powerful autonomous multi-agent platform designed for enterprise search and RAG workloads."
    chunks = chunker.split_text(text, doc_id="doc_test")
    assert len(chunks) > 1
    assert chunks[0].doc_id == "doc_test"


@pytest.mark.asyncio
async def test_vector_store():
    store = InMemoryVectorStore()
    provider = MockEmbeddingProvider(dim=64)
    chunks = TextChunker(chunk_size=100, chunk_overlap=10).split_text("Sample document text for indexing", "doc1")
    embeddings = await provider.embed_documents([c.content for c in chunks])

    await store.add_chunks(chunks, embeddings)
    query_vec = await provider.embed_query("Sample document")
    results = await store.search(query_vec, top_k=2)

    assert len(results) > 0
    assert results[0].score > 0.0


@pytest.mark.asyncio
async def test_hybrid_retriever():
    retriever = HybridRetriever()
    await retriever.ingest_document("d1", "OmniMind AI high performance DAG multi agent system.")

    results = await retriever.retrieve("DAG multi agent", top_k=2)
    assert len(results) == 1
    assert results[0]["doc_id"] == "d1"
