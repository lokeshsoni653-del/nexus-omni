import pytest
from omnimind.core import (
    WorkflowEngine, WorkflowTaskNode,
    OrchestratorAgent, WorkerAgent, ReviewerAgent
)


@pytest.mark.asyncio
async def test_sequential_workflow():
    engine = WorkflowEngine()
    engine.register_agent(OrchestratorAgent(name="Orchestrator"))
    engine.register_agent(ReviewerAgent(name="Reviewer"))

    tasks = [
        WorkflowTaskNode(id="t1", description="Plan task", assigned_agent="Orchestrator"),
        WorkflowTaskNode(id="t2", description="Review plan", assigned_agent="Reviewer")
    ]

    result = await engine.run_sequential(tasks)
    assert result.success is True
    assert "t1" in result.step_results
    assert "t2" in result.step_results


@pytest.mark.asyncio
async def test_dag_workflow():
    engine = WorkflowEngine()
    engine.register_agent(OrchestratorAgent(name="Orchestrator"))
    engine.register_agent(WorkerAgent(name="Worker"))
    engine.register_agent(ReviewerAgent(name="Reviewer"))

    tasks = [
        WorkflowTaskNode(id="plan", description="Plan project", assigned_agent="Orchestrator"),
        WorkflowTaskNode(id="work1", description="Execute component 1", assigned_agent="Worker", dependencies=["plan"]),
        WorkflowTaskNode(id="work2", description="Execute component 2", assigned_agent="Worker", dependencies=["plan"]),
        WorkflowTaskNode(id="review", description="Review all", assigned_agent="Reviewer", dependencies=["work1", "work2"])
    ]

    result = await engine.run_dag(tasks)
    assert result.success is True
    assert len(result.step_results) == 4
    assert result.step_results["review"].action_taken == "validated_and_approved"
