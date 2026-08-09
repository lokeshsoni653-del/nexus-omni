from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    agent_type: str = Field(default="orchestrator", description="Agent type: orchestrator, worker, rag, reviewer")
    task: str = Field(description="Task description or question for agent")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    agent_name: str
    action_taken: str
    output: Any
    success: bool
    execution_time_ms: float = 0.0


class RAGIngestRequest(BaseModel):
    doc_id: str = Field(description="Unique document ID")
    text: str = Field(description="Document text content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RAGIngestResponse(BaseModel):
    doc_id: str
    chunks_created: int
    success: bool


class RAGQueryRequest(BaseModel):
    query: str = Field(description="Search query string")
    top_k: int = Field(default=3, description="Number of results to retrieve")
    min_score: float = Field(default=0.0, description="Minimum similarity score cutoff")


class RAGQueryResponse(BaseModel):
    query: str
    documents: List[Dict[str, Any]]


class DAGTaskItem(BaseModel):
    id: str
    description: str
    assigned_agent: str
    dependencies: List[str] = Field(default_factory=list)


class WorkflowRunRequest(BaseModel):
    workflow_id: str = Field(default="custom_workflow")
    execution_mode: str = Field(default="dag", description="Execution mode: 'dag' or 'sequential'")
    tasks: List[DAGTaskItem]
