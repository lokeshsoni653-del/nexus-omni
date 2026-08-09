"use client";

import React, { useState, useCallback, useEffect } from 'react';
import {
  Node,
  Edge,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Connection,
  NodeChange,
  EdgeChange,
} from '@xyflow/react';

import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { VisualCanvas } from '../components/VisualCanvas';
import { PdfUploadModal } from '../components/PdfUploadModal';
import { TerminalConsole } from '../components/TerminalConsole';
import { AuthModal } from '../components/AuthModal';
import { CustomNodeData, AgentRoleType, ToolKindType } from '../types/workflow';
import { convertGraphToWorkflowPayload } from '../utils/graphToJson';

// Initial Preset Nodes
const initialNodes: Node<CustomNodeData>[] = [
  {
    id: 'pdf_tool_1',
    type: 'toolNode',
    position: { x: 50, y: 180 },
    data: {
      label: 'Chroma PDF Knowledge Base',
      toolKind: 'pdf_reader',
      description: 'Ingested enterprise policy PDF document vector store.',
    },
  },
  {
    id: 'agent_orchestrator',
    type: 'agentNode',
    position: { x: 340, y: 50 },
    data: {
      label: 'Orchestrator Agent',
      role: 'orchestrator',
      description: 'Decomposes high-level goals into parallel agent task nodes.',
      assignedTools: [],
    },
  },
  {
    id: 'agent_rag',
    type: 'agentNode',
    position: { x: 340, y: 240 },
    data: {
      label: 'RAG Specialist',
      role: 'rag',
      description: 'Queries ChromaDB vector collection for PDF enterprise policies & SLAs.',
      assignedTools: ['Chroma PDF Reader'],
    },
  },
  {
    id: 'agent_worker',
    type: 'agentNode',
    position: { x: 700, y: 150 },
    data: {
      label: 'Worker Agent',
      role: 'worker',
      description: 'Executes core analysis based on retrieved policy knowledge.',
      assignedTools: ['Web Search Engine'],
    },
  },
  {
    id: 'agent_reviewer',
    type: 'agentNode',
    position: { x: 1040, y: 150 },
    data: {
      label: 'Reviewer Agent',
      role: 'reviewer',
      description: 'Validates outputs, checks safety policy, and formats final report.',
      assignedTools: [],
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: 'e_pdf_rag',
    source: 'pdf_tool_1',
    target: 'agent_rag',
    animated: true,
    style: { stroke: '#10b981', strokeWidth: 2 },
  },
  {
    id: 'e_orch_rag',
    source: 'agent_orchestrator',
    target: 'agent_rag',
    animated: true,
    style: { stroke: '#a855f7', strokeWidth: 2.5 },
  },
  {
    id: 'e_rag_worker',
    source: 'agent_rag',
    target: 'agent_worker',
    animated: true,
    style: { stroke: '#3b82f6', strokeWidth: 2.5 },
  },
  {
    id: 'e_worker_reviewer',
    source: 'agent_worker',
    target: 'agent_reviewer',
    animated: true,
    style: { stroke: '#f59e0b', strokeWidth: 2.5 },
  },
];

export default function App() {
  const [nodes, setNodes] = useState<Node<CustomNodeData>[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [goal, setGoal] = useState<string>(
    'Ingest enterprise policy PDF, query latency SLA targets, and summarize security compliance requirements.'
  );
  const [executionMode, setExecutionMode] = useState<'dag' | 'sequential'>('dag');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [isTerminalOpen, setIsTerminalOpen] = useState<boolean>(true);
  const [isPdfModalOpen, setIsPdfModalOpen] = useState<boolean>(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [apiKey, setApiKey] = useState<string>('');
  const [pdfReportUrl, setPdfReportUrl] = useState<string | null>(null);
  const [uploadedDocIds, setUploadedDocIds] = useState<string[]>([]);
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  const API_BASE = 'http://localhost:8000';

  // Check Backend Server Status
  useEffect(() => {
    const checkServer = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) setServerStatus('online');
        else setServerStatus('offline');
      } catch (err) {
        setServerStatus('offline');
      }
    };
    checkServer();
    const interval = setInterval(checkServer, 10000);
    return () => clearInterval(interval);
  }, []);

  // React Flow Handlers
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds) as Node<CustomNodeData>[]),
    []
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge({ ...connection, animated: true }, eds)),
    []
  );

  // Palette Handlers
  const handleAddAgentNode = (role: AgentRoleType) => {
    const id = `agent_${role}_${Date.now()}`;
    const roleTitles: Record<AgentRoleType, string> = {
      orchestrator: 'Orchestrator Agent',
      worker: 'Worker Agent',
      rag: 'RAG Specialist',
      reviewer: 'Reviewer Agent',
    };

    const newNode: Node<CustomNodeData> = {
      id,
      type: 'agentNode',
      position: { x: 400 + Math.random() * 100, y: 150 + Math.random() * 100 },
      data: {
        label: roleTitles[role],
        role: role,
        description: `Custom ${roleTitles[role]} for visual workflow execution.`,
        assignedTools: [],
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const handleAddToolNode = (kind: ToolKindType) => {
    const id = `tool_${kind}_${Date.now()}`;
    const toolTitles: Record<ToolKindType, string> = {
      pdf_reader: 'Chroma PDF Reader',
      web_search: 'Web Search Engine',
      code_executor: 'Python Sandbox',
    };

    const newNode: Node<CustomNodeData> = {
      id,
      type: 'toolNode',
      position: { x: 150 + Math.random() * 100, y: 300 + Math.random() * 100 },
      data: {
        label: toolTitles[kind],
        toolKind: kind,
        description: `Attached tool plugin: ${toolTitles[kind]}.`,
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const handleLoadTemplate = (templateName: string) => {
    if (templateName === 'enterprise_rag') {
      setNodes(initialNodes);
      setEdges(initialEdges);
      setGoal('Ingest enterprise policy PDF, query latency SLA targets, and summarize security compliance requirements.');
    } else if (templateName === 'web_researcher') {
      const webNodes: Node<CustomNodeData>[] = [
        {
          id: 'tool_web',
          type: 'toolNode',
          position: { x: 100, y: 180 },
          data: { label: 'Web Search Engine', toolKind: 'web_search', description: 'Live web search plugin' },
        },
        {
          id: 'agent_worker_web',
          type: 'agentNode',
          position: { x: 400, y: 180 },
          data: { label: 'Market Research Agent', role: 'worker', description: 'Gathers competitive intelligence', assignedTools: ['Web Search'] },
        },
        {
          id: 'agent_reviewer_web',
          type: 'agentNode',
          position: { x: 750, y: 180 },
          data: { label: 'Executive Analyst', role: 'reviewer', description: 'Synthesizes market insights into briefing', assignedTools: [] },
        },
      ];
      const webEdges: Edge[] = [
        { id: 'e_w1', source: 'tool_web', target: 'agent_worker_web', animated: true },
        { id: 'e_w2', source: 'agent_worker_web', target: 'agent_reviewer_web', animated: true },
      ];
      setNodes(webNodes);
      setEdges(webEdges);
      setGoal('Research recent multi-agent SaaS architecture trends and synthesize competitive market analysis.');
    }
  };

  const handlePdfUploaded = (docId: string, filename: string) => {
    setUploadedDocIds((prev) => [...prev, docId]);
  };

  // Trigger Multi-Agent Workflow
  const handleRunWorkflow = async () => {
    if (!goal.trim()) return;

    setIsRunning(true);
    setIsTerminalOpen(true);
    setPdfReportUrl(null);

    const payload = convertGraphToWorkflowPayload(
      nodes,
      edges,
      goal,
      executionMode,
      uploadedDocIds
    );

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['X-API-Key'] = apiKey;

    try {
      const response = await fetch(`${API_BASE}/start-workflow`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setActiveWorkflowId(data.workflow_id);

      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: { ...n.data, status: 'running' },
        }))
      );

      // Poll Status until completion
      const pollStatus = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_BASE}/status/${data.workflow_id}`, { headers });
          if (statusRes.ok) {
            const statusData = await statusRes.json();
            if (statusData.status === 'success' || statusData.status === 'failed') {
              clearInterval(pollStatus);
              setIsRunning(false);
              if (statusData.pdf_report_url) {
                setPdfReportUrl(statusData.pdf_report_url);
              }
              setNodes((nds) =>
                nds.map((n) => ({
                  ...n,
                  data: { ...n.data, status: statusData.status === 'success' ? 'success' : 'failed' },
                }))
              );
            }
          }
        } catch (e) {
          console.error('Status poll error:', e);
        }
      }, 2000);
    } catch (err) {
      console.error('Failed to run workflow:', err);
      setIsRunning(false);
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: { ...n.data, status: 'failed' },
        }))
      );
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#090d16] text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        goal={goal}
        onGoalChange={setGoal}
        executionMode={executionMode}
        onExecutionModeChange={setExecutionMode}
        onRunWorkflow={handleRunWorkflow}
        isRunning={isRunning}
        onToggleTerminal={() => setIsTerminalOpen(!isTerminalOpen)}
        isTerminalOpen={isTerminalOpen}
        serverStatus={serverStatus}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        apiKey={apiKey}
        pdfReportUrl={pdfReportUrl}
      />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Palette Sidebar */}
        <Sidebar
          onAddAgentNode={handleAddAgentNode}
          onAddToolNode={handleAddToolNode}
          onLoadTemplate={handleLoadTemplate}
          onOpenPdfModal={() => setIsPdfModalOpen(true)}
        />

        {/* Visual React Flow Canvas Area */}
        <main className="flex-1 flex flex-col relative h-full">
          <div className="flex-1 w-full h-full relative">
            <VisualCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
            />
          </div>

          {/* Bottom Sliding Terminal Console */}
          <TerminalConsole
            isOpen={isTerminalOpen}
            onClose={() => setIsTerminalOpen(false)}
            workflowId={activeWorkflowId}
            wsBaseUrl="ws://localhost:8000"
          />
        </main>
      </div>

      {/* PDF Upload Modal */}
      <PdfUploadModal
        isOpen={isPdfModalOpen}
        onClose={() => setIsPdfModalOpen(false)}
        onPdfUploaded={handlePdfUploaded}
        apiBaseUrl={API_BASE}
      />

      {/* User Auth & API Key Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        apiKey={apiKey}
        onApiKeyChange={setApiKey}
        apiBaseUrl={API_BASE}
      />
    </div>
  );
}
