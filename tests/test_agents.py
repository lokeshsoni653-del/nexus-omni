import pytest
from omnimind.core import OrchestratorAgent, WorkerAgent, RAGAgent, ReviewerAgent
from omnimind.tools import ToolRegistry, PythonCodeExecutorTool, WebSearchTool
from omnimind.rag import HybridRetriever


@pytest.mark.asyncio
async def test_orchestrator_agent():
    agent = OrchestratorAgent()
    result = await agent.process_task("Build an automated report")
    assert result.success is True
    assert result.agent_name == "Orchestrator"
    assert "plan" in result.output
    assert len(result.output["plan"]) == 3


@pytest.mark.asyncio
async def test_worker_agent_tool_execution():
    registry = ToolRegistry()
    registry.register(PythonCodeExecutorTool())
    agent = WorkerAgent(tool_registry=registry)

    result = await agent.process_task("Calculate python result")
    assert result.success is True
    assert result.action_taken == "executed_python_tool"
    assert "Computed: 4200" in result.output["stdout"]


@pytest.mark.asyncio
async def test_rag_agent():
    retriever = HybridRetriever()
    await retriever.ingest_document("doc1", "OmniMind AI is an enterprise platform.")
    agent = RAGAgent(retriever=retriever)

    result = await agent.process_task("OmniMind AI")
    assert result.success is True
    assert result.action_taken == "retrieved_rag_context"
    assert len(result.output["documents"]) > 0


@pytest.mark.asyncio
async def test_reviewer_agent():
    agent = ReviewerAgent()
    result = await agent.process_task("Verify system outputs")
    assert result.success is True
    assert result.output["is_approved"] is True
