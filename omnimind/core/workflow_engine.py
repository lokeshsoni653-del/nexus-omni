import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from omnimind.core.base_agent import BaseAgent, AgentStepResult
from omnimind.core.memory import AgentMemory

logger = logging.getLogger("omnimind.core.workflow_engine")


class WorkflowTaskNode(BaseModel):
    id: str
    description: str
    assigned_agent: str
    dependencies: List[str] = Field(default_factory=list)
    retry_count: int = 1


class WorkflowResult(BaseModel):
    workflow_id: str
    success: bool
    step_results: Dict[str, AgentStepResult]
    shared_state: Dict[str, Any]
    total_execution_time_ms: float = 0.0


class WorkflowEngine:
    """Async Multi-Agent DAG Workflow Execution Engine."""

    def __init__(self, memory: Optional[AgentMemory] = None):
        self.agents: Dict[str, BaseAgent] = {}
        self.memory = memory or AgentMemory()

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the workflow engine."""
        self.agents[agent.name] = agent
        logger.info(f"Registered agent '{agent.name}' in WorkflowEngine.")

    async def run_sequential(self, tasks: List[WorkflowTaskNode], workflow_id: str = "seq_workflow") -> WorkflowResult:
        """Execute tasks sequentially, passing accumulative state forward."""
        start_time = asyncio.get_event_loop().time()
        step_results: Dict[str, AgentStepResult] = {}

        for task in tasks:
            agent = self.agents.get(task.assigned_agent)
            if not agent:
                raise ValueError(f"Agent '{task.assigned_agent}' not registered in engine.")

            context = {
                "previous_results": {k: v.output for k, v in step_results.items()},
                "shared_state": self.memory.working_state
            }

            result = await agent.process_task(task.description, context=context)
            step_results[task.id] = result
            self.memory.update_state(f"task_output_{task.id}", result.output)

            if not result.success:
                logger.error(f"Task '{task.id}' failed. Halting sequential workflow.")
                break

        elapsed = (asyncio.get_event_loop().time() - start_time) * 1000.0
        return WorkflowResult(
            workflow_id=workflow_id,
            success=all(r.success for r in step_results.values()),
            step_results=step_results,
            shared_state=self.memory.working_state,
            total_execution_time_ms=round(elapsed, 2)
        )

    async def run_dag(self, tasks: List[WorkflowTaskNode], workflow_id: str = "dag_workflow") -> WorkflowResult:
        """Execute DAG tasks concurrently as soon as their dependencies are satisfied."""
        start_time = asyncio.get_event_loop().time()
        step_results: Dict[str, AgentStepResult] = {}
        completed_tasks: set = set()
        pending_tasks: Dict[str, WorkflowTaskNode] = {t.id: t for t in tasks}

        while pending_tasks:
            # Identify tasks whose dependencies are satisfied
            ready_tasks = [
                task for task_id, task in pending_tasks.items()
                if all(dep in completed_tasks for dep in task.dependencies)
            ]

            if not ready_tasks:
                raise RuntimeError("Cyclic dependency or unresolvable task DAG detected.")

            # Execute ready tasks in parallel
            async def _exec_task(task_node: WorkflowTaskNode) -> tuple[str, AgentStepResult]:
                agent = self.agents.get(task_node.assigned_agent)
                if not agent:
                    raise ValueError(f"Agent '{task_node.assigned_agent}' is missing.")

                context = {
                    "dep_outputs": {dep: step_results[dep].output for dep in task_node.dependencies},
                    "shared_state": self.memory.working_state
                }
                res = await agent.process_task(task_node.description, context=context)
                return task_node.id, res

            task_futures = [_exec_task(t) for t in ready_tasks]
            batch_results = await asyncio.gather(*task_futures, return_exceptions=False)

            for task_id, res in batch_results:
                step_results[task_id] = res
                completed_tasks.add(task_id)
                del pending_tasks[task_id]
                self.memory.update_state(f"dag_task_{task_id}", res.output)

        elapsed = (asyncio.get_event_loop().time() - start_time) * 1000.0
        return WorkflowResult(
            workflow_id=workflow_id,
            success=all(r.success for r in step_results.values()),
            step_results=step_results,
            shared_state=self.memory.working_state,
            total_execution_time_ms=round(elapsed, 2)
        )
