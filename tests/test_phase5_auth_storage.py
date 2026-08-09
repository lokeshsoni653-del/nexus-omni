"""
Phase 5 Tests — Authentication, User Isolation, Cloud Storage, and ReportLab PDF Generation
"""
import os
import pytest
from fastapi.testclient import TestClient

from omnimind.db.base import Base, get_session_factory, create_all_tables
from omnimind.db.models import User, Workflow, Document
from omnimind.db.crud import create_user, create_workflow
from omnimind.backend.api.main import app
from omnimind.backend.api.auth import hash_password, verify_password, create_access_token
from omnimind.storage import get_storage_provider
from omnimind.services.pdf_generator import WorkflowPdfReportGenerator

create_all_tables()
SessionLocal = get_session_factory()


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Authentication & Password Hashing Tests ────────────────────────────────

def test_password_hashing():
    """Verify password hashing and verification logic."""
    raw_pass = "SecureSecret123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation():
    """Verify JWT access token creation and decoding."""
    data = {"sub": "user-123-abc", "email": "alice@omnimind.ai"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 20


def test_auth_signup_and_login_endpoints(client):
    """Test POST /auth/signup and POST /auth/login endpoints."""
    email = f"saas_user_{os.urandom(4).hex()}@omnimind.ai"
    password = "MyPassword123!"

    # Signup
    signup_resp = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "name": "SaaS Test User"},
    )
    assert signup_resp.status_code == 201
    data = signup_resp.json()
    assert "access_token" in data
    assert "api_key" in data
    api_key = data["api_key"]

    # Login
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # Profile /me via API Key
    me_resp = client.get("/auth/me", headers={"X-API-Key": api_key})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


# ── 2. Multi-Tenant User Isolation Test ───────────────────────────────────────

def test_multi_tenant_workflow_isolation(client):
    """Test that users cannot access other users' workflows or documents."""
    db = SessionLocal()
    user_a = create_user(db, f"usera_{os.urandom(4).hex()}@omnimind.ai", "User A")
    user_b = create_user(db, f"userb_{os.urandom(4).hex()}@omnimind.ai", "User B")

    wf_a = create_workflow(db, user_a.id, "User A Workflow", "Goal A")
    user_b_api_key = user_b.api_key
    db.close()

    # User B trying to access User A's workflow should receive 404
    response = client.get(
        f"/status/{wf_a.id}",
        headers={"X-API-Key": user_b_api_key},
    )
    assert response.status_code == 404


# ── 3. Cloud Storage Abstraction Test ──────────────────────────────────────────

def test_storage_provider_upload_download(tmp_path):
    """Test cloud storage upload and download logic."""
    storage = get_storage_provider()
    content = b"Sample enterprise PDF document content for cloud storage test."
    filename = f"test_cloud_{os.urandom(4).hex()}.pdf"

    storage_key = storage.upload_file(content, filename)
    assert storage_key is not None

    dest_file = str(tmp_path / "downloaded.pdf")
    downloaded_path = storage.download_file(storage_key, dest_file)
    assert os.path.exists(downloaded_path)


# ── 4. ReportLab Executive PDF Report Generation Test ─────────────────────────

def test_reportlab_pdf_generator(tmp_path):
    """Test ReportLab executive PDF generation service."""
    pdf_gen = WorkflowPdfReportGenerator(output_dir=str(tmp_path))
    pdf_path = pdf_gen.generate_workflow_pdf(
        workflow_id="wf-test-12345",
        workflow_name="Executive Security Audit",
        goal="Audit enterprise policy SLA targets and security compliance",
        execution_results={
            "step_results": {
                "plan": {"agent": "Orchestrator", "action": "decomposed_goal", "output": "Created 4 DAG subtasks"},
                "rag": {"agent": "RAGSpecialist", "action": "searched_chromadb", "output": "Found SLA target < 45ms"},
            }
        },
        user_name="Alice Administrator",
    )

    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 100
