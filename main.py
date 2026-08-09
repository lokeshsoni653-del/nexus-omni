import os
import sys
import asyncio
import logging

from omnimind.core import (
    OrchestratorAgent, WorkerAgent, RAGAgent, ReviewerAgent,
    WorkflowEngine, WorkflowTaskNode, AgentMemory
)
from omnimind.rag import HybridRetriever, ChromaDBManager, PDFIngestionPipeline
from omnimind.tools import (
    ToolRegistry, WebSearchTool, DocumentRetrievalTool, PythonCodeExecutorTool, HTTPClientTool,
    ChromaPDFQueryTool
)
from generate_sample_pdf import create_sample_pdf

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("omnimind.cli")


async def main():
    print("\n" + "=" * 80)
    print("OmniMind AI -- Autonomous Multi-Agent SaaS & Enterprise RAG Platform")
    print("Phase 1: Multi-Agent DAG Core Engine | Phase 2: ChromaDB PDF Document Intelligence")
    print("=" * 80 + "\n")

    # 1. Generate & Ingest Private PDF into ChromaDB
    print("[1/4] Phase 2: Ingesting Private PDF Document into ChromaDB Vector Store...")
    pdf_path = "sample_enterprise_policy.pdf"
    if not os.path.exists(pdf_path):
        create_sample_pdf(pdf_path)

    chroma_mgr = ChromaDBManager(
        collection_name="omnimind_pdf_knowledge",
        persist_directory="./chroma_db"
    )

    ingestion_pipeline = PDFIngestionPipeline(
        chroma_manager=chroma_mgr,
        chunk_size=400,
        chunk_overlap=40
    )

    ingest_result = ingestion_pipeline.ingest_pdf(pdf_path)
    print(f"[OK] Ingested '{pdf_path}': {ingest_result['chunks_ingested']} chunks stored in ChromaDB!")
    print(f"[OK] Total Collection Count: {chroma_mgr.count()}\n")

    # 2. Setup Tool Registry & Equip Agents with ChromaPDFQueryTool
    print("[2/4] Registering Agent Tools including ChromaPDFQueryTool...")
    tools = ToolRegistry()
    tools.register(WebSearchTool())
    tools.register(DocumentRetrievalTool())
    tools.register(PythonCodeExecutorTool())
    tools.register(HTTPClientTool())

    # Register custom ChromaDB PDF Query Tool for agents
    chroma_tool = ChromaPDFQueryTool(chroma_manager=chroma_mgr)
    tools.register(chroma_tool)
    print(f"[OK] Registered Tools: {tools.list_tools()}\n")

    # 3. Setup Agents & Workflow Engine
    print("[3/4] Initializing Multi-Agent System equipped with Private PDF RAG...")
    memory = AgentMemory()

    orchestrator = OrchestratorAgent(tool_registry=tools, memory=memory)
    worker = WorkerAgent(tool_registry=tools, memory=memory)
    rag_agent = RAGAgent(tool_registry=tools, memory=memory)
    reviewer = ReviewerAgent(tool_registry=tools, memory=memory)

    # Equip worker and RAG agent with ChromaPDFQueryTool explicitly
    worker.register_tool(chroma_tool)
    rag_agent.register_tool(chroma_tool)

    engine = WorkflowEngine(memory=memory)
    engine.register_agent(orchestrator)
    engine.register_agent(worker)
    engine.register_agent(rag_agent)
    engine.register_agent(reviewer)
    print("[OK] Agents Registered & Equipped: Orchestrator, Worker, RAGSpecialist, Reviewer\n")

    # 4. Run Concurrent DAG Multi-Agent Workflow Querying Private PDF
    print("[4/4] Executing Multi-Agent DAG Workflow Querying Private PDF Knowledge...")
    dag_tasks = [
        WorkflowTaskNode(
            id="plan",
            description="Decompose goal: 'Retrieve SLA latency metrics and security policy from private PDF'",
            assigned_agent="Orchestrator",
            dependencies=[]
        ),
        WorkflowTaskNode(
            id="chroma_pdf_search",
            description="Query ChromaDB PDF knowledge for SLA latency target and security policy",
            assigned_agent="RAGSpecialist",
            dependencies=["plan"]
        ),
        WorkflowTaskNode(
            id="verify_and_report",
            description="Verify retrieved ChromaDB PDF insights and validate policy compliance",
            assigned_agent="Reviewer",
            dependencies=["chroma_pdf_search"]
        )
    ]

    result = await engine.run_dag(dag_tasks, workflow_id="chroma_pdf_rag_dag")

    print("\n" + "=" * 80)
    print(f"Workflow Execution Complete! Success: {result.success} | Time: {result.total_execution_time_ms} ms")
    print("=" * 80)

    for task_id, step in result.step_results.items():
        print(f"\n- Task ID: [{task_id}] | Agent: {step.agent_name}")
        print(f"  Action Taken: {step.action_taken}")
        print(f"  Output: {step.output}")

    print("\n" + "=" * 80)
    print("OmniMind AI Phase 2: Document Intelligence & ChromaDB RAG execution successful!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
