import pytest
from httpx import AsyncClient, ASGITransport
from omnimind.backend.api.main import app
from omnimind.db.base import create_all_tables

create_all_tables()


@pytest.mark.asyncio
async def test_api_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_api_start_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/start-workflow", json={
            "name": "API Test Workflow",
            "goal": "Test API workflow trigger"
        })
    assert response.status_code == 202
    data = response.json()
    assert "workflow_id" in data
    assert "task_id" in data


@pytest.mark.asyncio
async def test_api_upload_pdf():
    pdf_content = b"%PDF-1.4 dummy content"
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/upload-pdf", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "document" in data
