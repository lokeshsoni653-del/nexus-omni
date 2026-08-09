import { Node, Edge } from '@xyflow/react';
import { CustomNodeData, StartWorkflowApiPayload } from '../types/workflow';

/**
 * Converts React Flow visual node/edge graph into a JSON payload ready
 * for submission to the FastAPI /start-workflow backend engine.
 */
export function convertGraphToWorkflowPayload(
  nodes: Node<CustomNodeData>[],
  edges: Edge[],
  workflowGoal: string,
  executionMode: 'dag' | 'sequential' = 'dag',
  documentIds: string[] = []
): StartWorkflowApiPayload {
  // Map connected tool nodes to their respective agent target nodes
  const agentToolsMap: Record<string, string[]> = {};

  // Build dependency map between agent nodes from directed edges
  const dependenciesMap: Record<string, string[]> = {};

  nodes.forEach((node) => {
    if (node.type === 'agentNode') {
      dependenciesMap[node.id] = [];
      agentToolsMap[node.id] = [];
    }
  });

  edges.forEach((edge) => {
    const sourceNode = nodes.find((n) => n.id === edge.source);
    const targetNode = nodes.find((n) => n.id === edge.target);

    if (!sourceNode || !targetNode) return;

    // Edge from ToolNode -> AgentNode (Attaching tool to agent)
    if (sourceNode.type === 'toolNode' && targetNode.type === 'agentNode') {
      const toolKind = sourceNode.data.toolKind;
      if (toolKind && !agentToolsMap[targetNode.id].includes(toolKind)) {
        agentToolsMap[targetNode.id].push(toolKind);
      }
    }

    // Edge from AgentNode -> AgentNode (DAG dependency: target depends on source)
    if (sourceNode.type === 'agentNode' && targetNode.type === 'agentNode') {
      if (!dependenciesMap[targetNode.id].includes(sourceNode.id)) {
        dependenciesMap[targetNode.id].push(sourceNode.id);
      }
    }
  });

  // Construct node descriptions and metadata
  const mappedNodes = nodes
    .filter((node) => node.type === 'agentNode')
    .map((node) => {
      const data = node.data;
      const role = data.role || 'worker';
      const assignedTools = agentToolsMap[node.id] || [];

      return {
        id: node.id,
        label: data.label,
        role: role,
        description: data.description,
        dependencies: dependenciesMap[node.id] || [],
        tools: assignedTools,
      };
    });

  return {
    name: `Visual Workflow (${mappedNodes.length} Agents)`,
    goal: workflowGoal || 'Execute autonomous multi-agent analysis and report generation.',
    execution_mode: executionMode,
    document_ids: documentIds,
    extra_context: {
      graph_structure: mappedNodes,
      total_nodes: nodes.length,
      total_edges: edges.length,
    },
  };
}
