"""
OmniMind AI — SQLAlchemy ORM Models

Tables:
  - users       : platform users (API key + Password auth)
  - documents   : uploaded PDF documents
  - workflows   : multi-agent workflow definitions
  - tasks       : individual Celery task records
  - agent_logs  : streamed agent thought log events
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from omnimind.db.base import Base
import enum


# ── Enumerations ──────────────────────────────────────────────────────────────

class WorkflowStatus(str, enum.Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCESS   = "success"
    FAILED    = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    SUCCESS  = "success"
    FAILED   = "failed"


class AgentType(str, enum.Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER       = "worker"
    RAG          = "rag"
    REVIEWER     = "reviewer"


# ── User Model ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email           = Column(String(255), unique=True, nullable=False, index=True)
    name            = Column(String(255), nullable=False)
    api_key         = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflows       = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    documents       = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ── Document Model ─────────────────────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id         = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    filename        = Column(String(255), nullable=False)
    file_path       = Column(Text, nullable=False)
    s3_key          = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, default=0)
    chunks_indexed  = Column(Integer, default=0)
    collection_name = Column(String(255), default="omnimind_pdf_knowledge")
    status          = Column(String(50), default="indexed")
    meta_data       = Column(JSON, default=dict)
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user            = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document id={self.id} filename={self.filename}>"


# ── Workflow Model ─────────────────────────────────────────────────────────────

class Workflow(Base):
    __tablename__ = "workflows"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id         = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name            = Column(String(255), nullable=False)
    description     = Column(Text, default="")
    goal            = Column(Text, nullable=False)
    execution_mode  = Column(String(20), default="dag")
    status          = Column(SAEnum(WorkflowStatus), default=WorkflowStatus.PENDING, index=True)
    celery_task_id  = Column(String(255), nullable=True, index=True)
    pdf_report_path = Column(Text, nullable=True)
    pdf_report_url  = Column(Text, nullable=True)
    result          = Column(JSON, default=None)
    error_message   = Column(Text, default=None)
    started_at      = Column(DateTime, default=None)
    completed_at    = Column(DateTime, default=None)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user            = relationship("User", back_populates="workflows")
    tasks           = relationship("Task", back_populates="workflow", cascade="all, delete-orphan", order_by="Task.created_at")

    def __repr__(self):
        return f"<Workflow id={self.id} status={self.status}>"


# ── Task Model ─────────────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id             = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id    = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    task_key       = Column(String(100), nullable=False)   # e.g. "plan", "rag_search"
    agent_type     = Column(SAEnum(AgentType), default=AgentType.WORKER)
    description    = Column(Text, default="")
    status         = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    result         = Column(JSON, default=None)
    error_message  = Column(Text, default=None)
    execution_ms   = Column(Float, default=None)
    created_at     = Column(DateTime, default=datetime.utcnow)
    completed_at   = Column(DateTime, default=None)

    # Relationships
    workflow       = relationship("Workflow", back_populates="tasks")
    logs           = relationship("AgentLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task id={self.id} key={self.task_key} status={self.status}>"


# ── AgentLog Model ─────────────────────────────────────────────────────────────

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    task_id     = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    agent_name  = Column(String(100), nullable=False)
    log_type    = Column(String(50), default="thought")  # thought | action | result | error
    content     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task        = relationship("Task", back_populates="logs")

    def __repr__(self):
        return f"<AgentLog id={self.id} agent={self.agent_name} type={self.log_type}>"


# ── ContractAnalysis Model ─────────────────────────────────────────────────────

class RiskLevel(str, enum.Enum):
    LOW      = "LOW"
    MODERATE = "MODERATE"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class ContractAnalysis(Base):
    """Stores every contract analysis run — supports free-tier tracking and shareable links."""
    __tablename__ = "contract_analyses"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    share_token     = Column(String(36), unique=True, nullable=False, index=True,
                             default=lambda: str(uuid.uuid4()))
    # File info
    filename        = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    page_count      = Column(Integer, default=0)
    is_ocr          = Column(Boolean, default=False)   # True if scanned PDF OCR was used
    is_chunked      = Column(Boolean, default=False)   # True if long-doc chunking was used
    chunk_count     = Column(Integer, default=1)

    # Analysis results
    risk_score      = Column(Float, default=0.0)       # 0–100
    risk_level      = Column(SAEnum(RiskLevel), default=RiskLevel.LOW)
    contract_type   = Column(String(100), nullable=True)
    favors_party    = Column(String(100), nullable=True)
    analysis_json   = Column(JSON, default=dict)       # Full structured analysis

    # PDF Report
    pdf_report_path = Column(Text, nullable=True)
    pdf_report_url  = Column(Text, nullable=True)

    # Rate limiting / abuse prevention
    client_ip       = Column(String(64), nullable=True, index=True)
    user_id         = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    is_pro_analysis = Column(Boolean, default=False)

    created_at      = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at    = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ContractAnalysis id={self.id} risk={self.risk_level} score={self.risk_score}>"
