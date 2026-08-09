import os
import pytest
from omnimind.rag import ChromaDBManager, PDFIngestionPipeline
from omnimind.tools import ChromaPDFQueryTool
from omnimind.core import WorkerAgent
from generate_sample_pdf import create_sample_pdf


@pytest.fixture
def temp_pdf_file(tmp_path):
    pdf_path = str(tmp_path / "test_doc.pdf")
    create_sample_pdf(pdf_path)
    return pdf_path


@pytest.mark.asyncio
async def test_chroma_db_manager():
    chroma_mgr = ChromaDBManager(collection_name="test_collection", is_ephemeral=True)
    chroma_mgr.add_documents(
        texts=["Passage 1 content", "Passage 2 content"],
        metadatas=[{"source": "test1.pdf", "page": 1}, {"source": "test2.pdf", "page": 2}],
        ids=["id_1", "id_2"]
    )

    assert chroma_mgr.count() == 2
    results = chroma_mgr.query("Passage 1", n_results=1)
    assert len(results) == 1
    assert "Passage 1" in results[0]["content"]


@pytest.mark.asyncio
async def test_pdf_ingestion_pipeline(temp_pdf_file):
    chroma_mgr = ChromaDBManager(collection_name="test_ingest_collection", is_ephemeral=True)
    pipeline = PDFIngestionPipeline(chroma_manager=chroma_mgr, chunk_size=300, chunk_overlap=30)

    res = pipeline.ingest_pdf(temp_pdf_file)
    assert res["status"] == "success"
    assert res["chunks_ingested"] > 0
    assert chroma_mgr.count() > 0


@pytest.mark.asyncio
async def test_chroma_pdf_query_tool(temp_pdf_file):
    chroma_mgr = ChromaDBManager(collection_name="test_tool_collection", is_ephemeral=True)
    pipeline = PDFIngestionPipeline(chroma_manager=chroma_mgr)
    pipeline.ingest_pdf(temp_pdf_file)

    tool = ChromaPDFQueryTool(chroma_manager=chroma_mgr)
    res = await tool.execute(query="latency target")

    assert res.success is True
    assert res.output["found"] is True
    assert len(res.output["passages"]) > 0
