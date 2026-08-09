"""
Phase 3 Backend Engine Tests — FastAPI, Celery, SQLAlchemy DB, and WebSockets
"""
import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from omnimind.db.base import Base, get_db, create_all_tables, get_session_factory
from omnimind.db.models import User, Workflow, Task, Document, WorkflowStatus, TaskStatus
from omnimind.db.crud import create_user, create_workflow, get_workflow
from omnimind.backend.api.main import app

# Ensure main database tables are created for worker tasks
create_all_tables()

SessionLocal = get_session_factory()


@pytest.fixture(autouse=True)
def setup_test_db():
    create_all_tables()
    db = SessionLocal()
    if not db.query(User).filter(User.email == "dev@omnimind.local").first():
        create_user(db, email="dev@omnimind.local", name="Dev User")
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Database & ORM Tests ───────────────────────────────────────────────────

def test_database_models():
    """Verify ORM models can be created and queried in database."""
    db = SessionLocal()
    user = create_user(db, f"test_{os.urandom(4).hex()}@omnimind.ai", "Test User")
    assert user.id is not None
    assert user.api_key is not None

    wf = create_workflow(db, user.id, "Test Workflow", "Analyze enterprise policies")
    assert wf.id is not None
    assert wf.status == WorkflowStatus.PENDING

    fetched = get_workflow(db, wf.id)
    assert fetched.name == "Test Workflow"
    db.close()


# ── 2. Health Endpoint Test ───────────────────────────────────────────────────

def test_health_check_endpoint(client):
    """Test GET /health returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ── 3. Upload PDF Endpoint Test ───────────────────────────────────────────────

def test_upload_pdf_endpoint(client, tmp_path):
    """Test POST /upload-pdf uploads and indexes a PDF file."""
    pdf_content = b"%PDF-1.4 dummy pdf content for testing ingestion pipeline"
    files = {"file": ("test_policy.pdf", pdf_content, "application/pdf")}

    response = client.post("/upload-pdf", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "document" in data
    assert data["document"]["filename"] == "test_policy.pdf"
    assert "id" in data["document"]


def test_upload_pdf_rejects_non_pdf(client):
    """Test POST /upload-pdf rejects non-PDF files."""
    files = {"file": ("script.py", b"print('hello')", "text/plain")}
    response = client.post("/upload-pdf", files=files)
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]


# ── 4. Workflow Lifecycle Endpoints Test ──────────────────────────────────────

def test_start_workflow_endpoint(client):
    """Test POST /start-workflow creates workflow and returns task_id immediately."""
    payload = {
        "name": "Integration Test Workflow",
        "goal": "Verify multi-agent workflow execution engine via API",
        "execution_mode": "dag",
    }
    response = client.post("/start-workflow", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "workflow_id" in data
    assert "task_id" in data
    assert "websocket_stream_url" in data

    workflow_id = data["workflow_id"]
    task_id = data["task_id"]

    # Query /status/{workflow_id}
    status_response = client.get(f"/status/{workflow_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["workflow_id"] == workflow_id


def test_status_by_celery_task_id(client):
    """Test GET /status/task/{celery_task_id} retrieves workflow by task ID."""
    payload = {
        "name": "Task ID Lookup Test",
        "goal": "Test task ID query capability",
    }
    start_resp = client.post("/start-workflow", json=payload)
    assert start_resp.status_code == 202
    task_id = start_resp.json()["task_id"]

    status_resp = client.get(f"/status/task/{task_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["celery_task_id"] == task_id


def test_list_workflows_endpoint(client):
    """Test GET /workflows returns list of user workflows."""
    response = client.get("/workflows")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── 5. WebSocket Stream Test ──────────────────────────────────────────────────

def test_websocket_stream(client):
    """Test WebSocket connection to /ws/stream/{workflow_id}."""
    start_resp = client.post(
        "/start-workflow",
        json={"name": "WS Test Workflow", "goal": "Test WebSocket agent stream"},
    )
    workflow_id = start_resp.json()["workflow_id"]

    with client.websocket_connect(f"/ws/stream/{workflow_id}") as websocket:
        data = websocket.receive_json()
        assert "log_type" in data
        assert "agent_name" in data
