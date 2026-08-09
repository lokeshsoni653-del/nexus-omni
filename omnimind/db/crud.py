"""
OmniMind AI — CRUD Operations

Full create/read/update/delete operations for all ORM models.
"""
import secrets
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from omnimind.db.models import User, Document, Workflow, Task, AgentLog, WorkflowStatus, TaskStatus

logger = logging.getLogger("omnimind.db.crud")


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(db: Session, email: str, name: str) -> User:
    api_key = secrets.token_urlsafe(32)
    user = User(email=email, name=name, api_key=api_key)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user: {email}")
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
    return db.query(User).filter(User.api_key == api_key).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


# ── Document CRUD ─────────────────────────────────────────────────────────────

def create_document(
    db: Session,
    user_id: str,
    filename: str,
    file_path: str,
    file_size_bytes: int = 0,
    chunks_indexed: int = 0,
    collection_name: str = "omnimind_pdf_knowledge",
    meta_data: dict = None,
) -> Document:
    doc = Document(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        chunks_indexed=chunks_indexed,
        collection_name=collection_name,
        meta_data=meta_data or {},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, doc_id: str) -> Optional[Document]:
    return db.query(Document).filter(Document.id == doc_id).first()


def list_user_documents(db: Session, user_id: str) -> List[Document]:
    return db.query(Document).filter(Document.user_id == user_id).all()


def update_document_chunks(db: Session, doc_id: str, chunks_indexed: int) -> Optional[Document]:
    doc = get_document(db, doc_id)
    if doc:
        doc.chunks_indexed = chunks_indexed
        db.commit()
        db.refresh(doc)
    return doc


# ── Workflow CRUD ─────────────────────────────────────────────────────────────

def create_workflow(
    db: Session,
    user_id: str,
    name: str,
    goal: str,
    description: str = "",
    execution_mode: str = "dag",
) -> Workflow:
    workflow = Workflow(
        user_id=user_id,
        name=name,
        goal=goal,
        description=description,
        execution_mode=execution_mode,
        status=WorkflowStatus.PENDING,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    logger.info(f"Created workflow: {workflow.id}")
    return workflow


def get_workflow(db: Session, workflow_id: str) -> Optional[Workflow]:
    return db.query(Workflow).filter(Workflow.id == workflow_id).first()


def list_user_workflows(
    db: Session, user_id: str, skip: int = 0, limit: int = 50
) -> List[Workflow]:
    return (
        db.query(Workflow)
        .filter(Workflow.user_id == user_id)
        .order_by(Workflow.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_workflow_status(
    db: Session,
    workflow_id: str,
    status: WorkflowStatus,
    celery_task_id: str = None,
    result: dict = None,
    error_message: str = None,
) -> Optional[Workflow]:
    workflow = get_workflow(db, workflow_id)
    if not workflow:
        return None
    workflow.status = status
    workflow.updated_at = datetime.utcnow()
    if celery_task_id:
        workflow.celery_task_id = celery_task_id
    if status == WorkflowStatus.RUNNING and not workflow.started_at:
        workflow.started_at = datetime.utcnow()
    if status in (WorkflowStatus.SUCCESS, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
        workflow.completed_at = datetime.utcnow()
    if result is not None:
        workflow.result = result
    if error_message is not None:
        workflow.error_message = error_message
    db.commit()
    db.refresh(workflow)
    return workflow


# ── Task CRUD ─────────────────────────────────────────────────────────────────

def create_task(
    db: Session,
    workflow_id: str,
    task_key: str,
    description: str,
    agent_type: str = "worker",
) -> Task:
    from omnimind.db.models import AgentType
    task = Task(
        workflow_id=workflow_id,
        task_key=task_key,
        description=description,
        agent_type=AgentType(agent_type),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: str) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def list_workflow_tasks(db: Session, workflow_id: str) -> List[Task]:
    return db.query(Task).filter(Task.workflow_id == workflow_id).all()


def update_task_status(
    db: Session,
    task_id: str,
    status: TaskStatus,
    result: dict = None,
    error_message: str = None,
    execution_ms: float = None,
) -> Optional[Task]:
    task = get_task(db, task_id)
    if not task:
        return None
    task.status = status
    if result is not None:
        task.result = result
    if error_message is not None:
        task.error_message = error_message
    if execution_ms is not None:
        task.execution_ms = execution_ms
    if status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
        task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


# ── AgentLog CRUD ─────────────────────────────────────────────────────────────

def create_agent_log(
    db: Session,
    task_id: str,
    workflow_id: str,
    agent_name: str,
    content: str,
    log_type: str = "thought",
) -> AgentLog:
    log = AgentLog(
        task_id=task_id,
        workflow_id=workflow_id,
        agent_name=agent_name,
        log_type=log_type,
        content=content,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_workflow_logs(
    db: Session,
    workflow_id: str,
    limit: int = 500
) -> List[AgentLog]:
    return (
        db.query(AgentLog)
        .filter(AgentLog.workflow_id == workflow_id)
        .order_by(AgentLog.created_at.asc())
        .limit(limit)
        .all()
    )
