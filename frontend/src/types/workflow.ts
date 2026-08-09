export type AgentRoleType = 'orchestrator' | 'worker' | 'rag' | 'reviewer';
export type ToolKindType = 'pdf_reader' | 'web_search' | 'code_executor';

export interface CustomNodeData extends Record<string, unknown> {
  label: string;
  role?: AgentRoleType;
  toolKind?: ToolKindType;
  description: string;
  iconName?: string;
  assignedTools?: string[];
  status?: 'idle' | 'running' | 'success' | 'failed';
  output?: string;
}

export interface WorkflowTaskPayload {
  id: string;
  description: string;
  assigned_agent: string;
  dependencies: string[];
}

export interface StartWorkflowApiPayload {
  name: string;
  goal: string;
  description?: string;
  execution_mode: 'dag' | 'sequential';
  document_ids?: string[];
  extra_context?: Record<string, unknown>;
}

export interface AgentLogEvent {
  workflow_id?: string;
  task_id?: string;
  agent_name: string;
  log_type: 'thought' | 'action' | 'result' | 'error' | 'system' | 'ping' | 'workflow_complete' | 'workflow_failed';
  content: string;
  timestamp?: string;
}

export interface WorkflowStatusResponse {
  workflow_id: string;
  celery_task_id?: string;
  name: string;
  goal: string;
  execution_mode: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  result?: Record<string, unknown>;
  error_message?: string;
  tasks: Array<{
    id: string;
    task_key: string;
    agent_type: string;
    description: string;
    status: string;
    result?: Record<string, unknown>;
    execution_ms?: number;
  }>;
}
