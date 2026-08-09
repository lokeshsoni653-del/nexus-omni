"""
OmniMind AI — Workflow Execution, Status, & PDF Export Endpoints
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from omnimind.db.base import get_db
from omnimind.db.models import User, WorkflowStatus
from omnimind.db.crud import (
    create_workflow, get_workflow, list_user_workflows,
    list_workflow_tasks, list_workflow_logs,
)
from omnimind.backend.api.dependencies import get_current_user
from omnimind.worker.tasks import run_workflow_task

logger = logging.getLogger("omnimind.backend.api.routes.workflow")

router = APIRouter(prefix="", tags=["Workflows"])


# ── Request / Response Schemas ────────────────────────────────────────────────

class StartWorkflowRequest(BaseModel):
    name: str = Field(default="Agentic RAG Workflow", description="Workflow name")
    goal: str = Field(..., description="High-level goal or query for agents")
    description: Optional[str] = Field(default="", description="Optional workflow details")
    execution_mode: Optional[str] = Field(default="dag", description="'dag' or 'sequential'")
    document_ids: Optional[List[str]] = Field(default_factory=list, description="Associated document IDs")
    extra_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context parameters")


class TaskStatusResponse(BaseModel):
    id: str
    task_key: str
    agent_type: str
    description: str
    status: str
    result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_ms: Optional[float] = None


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    celery_task_id: Optional[str] = None
    name: str
    goal: str
    execution_mode: str
    status: str
    pdf_report_url: Optional[str] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    tasks: List[TaskStatusResponse] = []
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ── POST /start-workflow ──────────────────────────────────────────────────────

@router.post(
    "/start-workflow",
    summary="Start an autonomous multi-agent workflow",
    response_description="Returns workflow_id and Celery task_id immediately",
    status_code=202,
)
async def start_workflow(
    request: StartWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Asynchronously start a multi-agent workflow for the authenticated user.
    FastAPI creates a Workflow record, hands off to Celery, and returns task_id.
    """
    wf = create_workflow(
        db=db,
        user_id=current_user.id,
        name=request.name,
        goal=request.goal,
        description=request.description or "",
        execution_mode=request.execution_mode or "dag",
    )

    celery_task = run_workflow_task.delay(
        workflow_id=wf.id,
        goal=request.goal,
        execution_mode=wf.execution_mode,
        document_ids=request.document_ids,
        extra_context=request.extra_context,
    )

    wf.celery_task_id = celery_task.id
    db.commit()

    logger.info(f"Dispatched workflow {wf.id} to Celery task {celery_task.id} for user {current_user.email}")

    return JSONResponse(
        status_code=202,
        content={
            "message": "Workflow started successfully.",
            "workflow_id": wf.id,
            "task_id": celery_task.id,
            "status": wf.status.value,
            "websocket_stream_url": f"/ws/stream/{wf.id}",
            "status_check_url": f"/status/{wf.id}",
        },
    )


# ── GET /status/{workflow_id} ─────────────────────────────────────────────────

@router.get(
    "/status/{workflow_id}",
    summary="Get workflow execution status and results",
    response_model=WorkflowStatusResponse,
)
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query workflow progress, individual agent tasks, and final results with user isolation."""
    wf = get_workflow(db, workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found.",
        )

    tasks = list_workflow_tasks(db, workflow_id)
    task_responses = [
        TaskStatusResponse(
            id=t.id,
            task_key=t.task_key,
            agent_type=t.agent_type.value if hasattr(t.agent_type, "value") else str(t.agent_type),
            description=t.description or "",
            status=t.status.value if hasattr(t.status, "value") else str(t.status),
            result=t.result,
            error_message=t.error_message,
            execution_ms=t.execution_ms,
        )
        for t in tasks
    ]

    return WorkflowStatusResponse(
        workflow_id=wf.id,
        celery_task_id=wf.celery_task_id,
        name=wf.name,
        goal=wf.goal,
        execution_mode=wf.execution_mode,
        status=wf.status.value if hasattr(wf.status, "value") else str(wf.status),
        pdf_report_url=wf.pdf_report_url,
        result=wf.result,
        error_message=wf.error_message,
        tasks=task_responses,
        created_at=wf.created_at.isoformat() if wf.created_at else "",
        started_at=wf.started_at.isoformat() if wf.started_at else None,
        completed_at=wf.completed_at.isoformat() if wf.completed_at else None,
    )


# ── GET /status/task/{celery_task_id} ─────────────────────────────────────────

@router.get(
    "/status/task/{celery_task_id}",
    summary="Get status by Celery Task ID",
)
async def get_status_by_celery_task_id(
    celery_task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query workflow status directly using the returned Celery task_id."""
    from omnimind.db.models import Workflow
    wf = db.query(Workflow).filter(Workflow.celery_task_id == celery_task_id).first()
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workflow found for Celery task_id '{celery_task_id}'.",
        )
    return await get_workflow_status(wf.id, db=db, current_user=current_user)


# ── GET /workflows ───────────────────────────────────────────────────────────

@router.get(
    "/workflows",
    summary="List user workflows",
)
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all workflows belonging to the authenticated user."""
    workflows = list_user_workflows(db, current_user.id, skip=skip, limit=limit)
    return [
        {
            "id": w.id,
            "name": w.name,
            "goal": w.goal,
            "status": w.status.value if hasattr(w.status, "value") else str(w.status),
            "celery_task_id": w.celery_task_id,
            "pdf_report_url": w.pdf_report_url,
            "created_at": w.created_at.isoformat() if w.created_at else "",
        }
        for w in workflows
    ]


# ── GET /workflows/{workflow_id}/export-pdf ─────────────────────────────────

@router.get(
    "/workflows/{workflow_id}/export-pdf",
    summary="Download executive ReportLab PDF report for workflow",
)
async def export_workflow_pdf(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download executive ReportLab PDF report for completed workflow."""
    wf = get_workflow(db, workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    if wf.pdf_report_path and os.path.exists(wf.pdf_report_path):
        return FileResponse(
            path=wf.pdf_report_path,
            filename=f"ReportMind_{wf.id[:8]}.pdf",
            media_type="application/pdf",
        )

    # Generate on demand if not present
    from omnimind.services.pdf_generator import WorkflowPdfReportGenerator
    from config import settings
    pdf_gen = WorkflowPdfReportGenerator(output_dir=settings.UPLOAD_DIR)
    pdf_path = pdf_gen.generate_workflow_pdf(
        workflow_id=wf.id,
        workflow_name=wf.name,
        goal=wf.goal,
        execution_results=wf.result or {},
        user_name=current_user.name,
    )
    return FileResponse(
        path=pdf_path,
        filename=f"ReportMind_{wf.id[:8]}.pdf",
        media_type="application/pdf",
    )
