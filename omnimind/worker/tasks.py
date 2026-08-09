"""
OmniMind AI — Celery Tasks

All AI workflow execution runs inside these Celery tasks so that
FastAPI routes return immediately with a task_id.

Each task:
  1. Updates the Workflow DB record to RUNNING
  2. Runs the multi-agent DAG workflow
  3. Publishes streaming agent logs to Redis (→ WebSocket clients)
  4. Generates an executive ReportLab PDF report and uploads to S3/Storage
  5. Updates the Workflow DB record to SUCCESS or FAILED
"""
import os
import time
import logging
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
from celery import Task as CeleryBaseTask

from omnimind.worker.celery_app import celery_app

logger = logging.getLogger("omnimind.worker.tasks")


def _run_async(coro):
    """Safely run an async coroutine inside a synchronous Celery task, even if an event loop is running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


# ── Base Task class with DB session lifecycle ─────────────────────────────────

class DatabaseTask(CeleryBaseTask):
    """Celery base task that manages a SQLAlchemy session per task execution."""
    abstract = True
    _db = None

    @property
    def db(self):
        if self._db is None:
            from omnimind.db.base import get_session_factory
            SessionLocal = get_session_factory()
            self._db = SessionLocal()
        return self._db

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._db is not None:
            self._db.close()
            self._db = None


# ── Helper: Publish log and persist to DB ─────────────────────────────────────

def _emit_log(
    workflow_id: str,
    agent_name: str,
    content: str,
    log_type: str = "thought",
    task_id: str = None,
    db=None,
    db_task_id: str = None,
):
    """Publish agent log to Redis event bus AND save to DB."""
    from omnimind.backend.events import publish_agent_event
    publish_agent_event(
        workflow_id=workflow_id,
        agent_name=agent_name,
        log_type=log_type,
        content=content,
        task_id=task_id,
    )
    if db and db_task_id:
        from omnimind.db.crud import create_agent_log
        try:
            create_agent_log(
                db=db,
                task_id=db_task_id,
                workflow_id=workflow_id,
                agent_name=agent_name,
                content=content,
                log_type=log_type,
            )
        except Exception as e:
            logger.warning(f"Failed to persist agent log: {e}")


# ── Main Workflow Celery Task ─────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="omnimind.run_workflow",
    max_retries=1,
    default_retry_delay=5,
)
def run_workflow_task(
    self,
    workflow_id: str,
    goal: str,
    execution_mode: str = "dag",
    document_ids: Optional[List[str]] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main Celery task that runs a full OmniMind multi-agent workflow.

    Returns: dict with success flag, step results, execution time, and PDF report URL.
    """
    from omnimind.db.crud import (
        update_workflow_status, create_task, update_task_status,
        get_workflow,
    )
    from omnimind.db.models import WorkflowStatus, TaskStatus
    from omnimind.backend.events import publish_workflow_complete
    from omnimind.core import (
        OrchestratorAgent, WorkerAgent, RAGAgent, ReviewerAgent,
        WorkflowEngine, WorkflowTaskNode, AgentMemory,
    )
    from omnimind.rag import HybridRetriever, ChromaDBManager
    from omnimind.tools import (
        ToolRegistry, WebSearchTool, DocumentRetrievalTool,
        PythonCodeExecutorTool, ChromaPDFQueryTool,
    )
    from omnimind.services.pdf_generator import WorkflowPdfReportGenerator
    from omnimind.storage import get_storage_provider
    from config import settings

    db = self.db
    start_time = time.time()

    # ── Update workflow to RUNNING ───────────────────────────────────────
    wf_record = get_workflow(db, workflow_id)
    wf_name = wf_record.name if wf_record else "Multi-Agent Workflow"
    user_name = wf_record.user.name if (wf_record and wf_record.user) else "OmniMind User"

    update_workflow_status(db, workflow_id, WorkflowStatus.RUNNING, celery_task_id=self.request.id)
    _emit_log(workflow_id, "System", f"Workflow '{workflow_id}' started.", "system", db=db)

    try:
        # ── Download Cloud Storage Documents if needed ───────────────────
        if document_ids:
            storage = get_storage_provider()
            for doc_id in document_ids:
                from omnimind.db.crud import get_document
                doc_obj = get_document(db, doc_id)
                if doc_obj and doc_obj.s3_key:
                    local_dest = os.path.join(settings.UPLOAD_DIR, f"{doc_obj.id}_{doc_obj.filename}")
                    storage.download_file(doc_obj.s3_key, local_dest)
                    _emit_log(workflow_id, "System", f"Downloaded S3 document '{doc_obj.filename}' for RAG pipeline.", "system", db=db)

        # ── Setup ChromaDB & RAG ─────────────────────────────────────────
        chroma_mgr = ChromaDBManager(
            collection_name=settings.CHROMA_COLLECTION_NAME,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )

        # ── Setup Tools ──────────────────────────────────────────────────
        tools = ToolRegistry()
        tools.register(WebSearchTool())
        tools.register(ChromaPDFQueryTool(chroma_manager=chroma_mgr))
        tools.register(PythonCodeExecutorTool())

        _emit_log(workflow_id, "System", f"Tools registered: {tools.list_tools()}", "system", db=db)

        # ── Create Agent Team ────────────────────────────────────────────
        memory = AgentMemory()
        orchestrator = OrchestratorAgent(tool_registry=tools, memory=memory)
        worker       = WorkerAgent(tool_registry=tools, memory=memory)
        rag_agent    = RAGAgent(tool_registry=tools, memory=memory)
        reviewer     = ReviewerAgent(tool_registry=tools, memory=memory)

        engine = WorkflowEngine(memory=memory)
        engine.register_agent(orchestrator)
        engine.register_agent(worker)
        engine.register_agent(rag_agent)
        engine.register_agent(reviewer)

        _emit_log(workflow_id, "System", "Multi-agent team initialized.", "system", db=db)

        # ── Build DAG Task Nodes ─────────────────────────────────────────
        dag_nodes = [
            WorkflowTaskNode(
                id="plan",
                description=f"Decompose goal: '{goal}'",
                assigned_agent="Orchestrator",
                dependencies=[],
            ),
            WorkflowTaskNode(
                id="knowledge_retrieval",
                description=f"Retrieve relevant knowledge from private documents for: {goal}",
                assigned_agent="RAGSpecialist",
                dependencies=["plan"],
            ),
            WorkflowTaskNode(
                id="execution",
                description=f"Execute the main task based on plan and retrieved knowledge: {goal}",
                assigned_agent="Worker",
                dependencies=["knowledge_retrieval"],
            ),
            WorkflowTaskNode(
                id="review",
                description="Validate all outputs for quality, safety, and completeness.",
                assigned_agent="Reviewer",
                dependencies=["execution"],
            ),
        ]

        # ── Create DB Task Records ───────────────────────────────────────
        db_task_map: Dict[str, str] = {}
        agent_type_map = {
            "plan": "orchestrator",
            "knowledge_retrieval": "rag",
            "execution": "worker",
            "review": "reviewer",
        }
        for node in dag_nodes:
            db_task = create_task(
                db=db,
                workflow_id=workflow_id,
                task_key=node.id,
                description=node.description,
                agent_type=agent_type_map.get(node.id, "worker"),
            )
            db_task_map[node.id] = db_task.id

        # ── Execute Workflow ─────────────────────────────────────────────
        _emit_log(workflow_id, "Orchestrator", f"Starting DAG execution for goal: {goal}", "thought", db=db)

        if execution_mode == "sequential":
            result = _run_async(engine.run_sequential(dag_nodes, workflow_id=workflow_id))
        else:
            result = _run_async(engine.run_dag(dag_nodes, workflow_id=workflow_id))

        # ── Publish step results & update DB Tasks ────────────────────────
        for node_id, step_result in result.step_results.items():
            db_task_id = db_task_map.get(node_id)
            status = TaskStatus.SUCCESS if step_result.success else TaskStatus.FAILED

            _emit_log(
                workflow_id=workflow_id,
                agent_name=step_result.agent_name,
                content=f"Action: {step_result.action_taken} | Output: {str(step_result.output)[:300]}",
                log_type="result",
                db=db,
                db_task_id=db_task_id,
            )

            update_task_status(
                db=db,
                task_id=db_task_id,
                status=status,
                result=step_result.output if isinstance(step_result.output, dict) else {"output": str(step_result.output)},
            )

        # ── Generate ReportLab PDF Executive Report & Upload to Cloud Storage
        pdf_generator = WorkflowPdfReportGenerator(output_dir=settings.UPLOAD_DIR)
        local_pdf_path = pdf_generator.generate_workflow_pdf(
            workflow_id=workflow_id,
            workflow_name=wf_name,
            goal=goal,
            execution_results={
                "step_results": {
                    k: {"agent": v.agent_name, "action": v.action_taken, "output": v.output}
                    for k, v in result.step_results.items()
                }
            },
            user_name=user_name,
        )

        storage = get_storage_provider()
        with open(local_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        pdf_storage_key = storage.upload_file(
            file_bytes=pdf_bytes,
            file_name=os.path.basename(local_pdf_path),
            content_type="application/pdf"
        )
        pdf_download_url = storage.get_public_url(pdf_storage_key)

        _emit_log(workflow_id, "System", f"Executive PDF report generated & uploaded: {pdf_download_url}", "system", db=db)

        # ── Finalize Workflow ────────────────────────────────────────────
        elapsed_ms = (time.time() - start_time) * 1000
        summary = {
            "success": result.success,
            "total_tasks": len(result.step_results),
            "execution_time_ms": round(elapsed_ms, 2),
            "pdf_report_url": pdf_download_url,
            "step_results": {
                k: {
                    "agent": v.agent_name,
                    "action": v.action_taken,
                    "success": v.success,
                }
                for k, v in result.step_results.items()
            },
        }

        final_status = WorkflowStatus.SUCCESS if result.success else WorkflowStatus.FAILED
        wf_updated = update_workflow_status(db, workflow_id, final_status, result=summary)
        if wf_updated:
            wf_updated.pdf_report_path = pdf_storage_key
            wf_updated.pdf_report_url = pdf_download_url
            db.commit()

        publish_workflow_complete(workflow_id, result.success, f"Completed in {elapsed_ms:.0f}ms")

        _emit_log(
            workflow_id,
            "System",
            f"Workflow {'succeeded' if result.success else 'failed'} in {elapsed_ms:.0f}ms. PDF: {pdf_download_url}",
            "workflow_complete",
            db=db,
        )

        return summary

    except Exception as exc:
        elapsed_ms = (time.time() - start_time) * 1000
        error_msg = str(exc)
        logger.error(f"Workflow {workflow_id} failed: {error_msg}", exc_info=True)

        update_workflow_status(
            db, workflow_id, WorkflowStatus.FAILED, error_message=error_msg
        )
        publish_workflow_complete(workflow_id, False, f"Error: {error_msg[:200]}")

        _emit_log(workflow_id, "System", f"Workflow FAILED: {error_msg[:500]}", "error", db=db)
        raise


# ── PDF Ingestion Celery Task ─────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="omnimind.ingest_pdf",
)
def ingest_pdf_task(
    self,
    document_id: str,
    file_path: str,
    collection_name: str = "omnimind_pdf_knowledge",
) -> Dict[str, Any]:
    """Celery task for background PDF ingestion into ChromaDB."""
    from omnimind.rag import ChromaDBManager, PDFIngestionPipeline
    from omnimind.db.crud import update_document_chunks
    from config import settings

    db = self.db
    try:
        chroma_mgr = ChromaDBManager(
            collection_name=collection_name,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
        pipeline = PDFIngestionPipeline(
            chroma_manager=chroma_mgr,
            chunk_size=400,
            chunk_overlap=40,
        )
        result = pipeline.ingest_pdf(file_path)
        update_document_chunks(db, document_id, result.get("chunks_ingested", 0))
        logger.info(f"PDF ingestion complete for doc {document_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"PDF ingestion failed for doc {document_id}: {exc}", exc_info=True)
        raise
