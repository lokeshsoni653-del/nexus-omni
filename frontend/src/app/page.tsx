"use client";

import React, { useState, useCallback, useEffect } from "react";
import { ContractHeader } from "../components/ContractHeader";
import { ContractUploadZone } from "../components/ContractUploadZone";
import { ContractResultCard } from "../components/ContractResultCard";
import { AnalysisHistory } from "../components/AnalysisHistory";
import { PricingSection } from "../components/PricingSection";
import { PaywallModal } from "../components/PaywallModal";
import { AuthModal } from "../components/AuthModal";
import { GlobalDragDropOverlay } from "../components/GlobalDragDropOverlay";
import { DocumentChatPanel } from "../components/DocumentChatPanel";

// ── Advanced Canvas Tab (lazy-loaded) ─────────────────────────────────────────
import { Header } from "../components/Header";
import { Sidebar } from "../components/Sidebar";
import { VisualCanvas } from "../components/VisualCanvas";
import { PdfUploadModal } from "../components/PdfUploadModal";
import { TerminalConsole } from "../components/TerminalConsole";
import { convertGraphToWorkflowPayload } from "../utils/graphToJson";
import { CustomNodeData, AgentRoleType, ToolKindType } from "../types/workflow";
import {
  Node, Edge, applyNodeChanges, applyEdgeChanges,
  addEdge, Connection, NodeChange, EdgeChange,
} from "@xyflow/react";

type Tab = "analyzer" | "history" | "pricing" | "advanced";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://omnimind-backend-u94t.onrender.com";
const WS_BASE  = process.env.NEXT_PUBLIC_WS_URL  || "wss://omnimind-backend-u94t.onrender.com";
const FREE_LIMIT = 3;

// ── Initial Canvas Nodes ──────────────────────────────────────────────────────
const initialNodes: Node<CustomNodeData>[] = [
  { id: "pdf_tool_1", type: "toolNode", position: { x: 50, y: 180 },
    data: { label: "Chroma PDF Knowledge Base", toolKind: "pdf_reader", description: "Ingested enterprise PDF vector store." } },
  { id: "agent_orchestrator", type: "agentNode", position: { x: 340, y: 50 },
    data: { label: "Orchestrator Agent", role: "orchestrator", description: "Goal decomposition & task planning.", assignedTools: [] } },
  { id: "agent_rag", type: "agentNode", position: { x: 340, y: 240 },
    data: { label: "RAG Specialist", role: "rag", description: "ChromaDB vector search & retrieval.", assignedTools: ["Chroma PDF Reader"] } },
  { id: "agent_worker", type: "agentNode", position: { x: 700, y: 150 },
    data: { label: "Worker Agent", role: "worker", description: "Core analysis & research execution.", assignedTools: ["Web Search Engine"] } },
  { id: "agent_reviewer", type: "agentNode", position: { x: 1040, y: 150 },
    data: { label: "Reviewer Agent", role: "reviewer", description: "Quality validation & final output.", assignedTools: [] } },
];
const initialEdges: Edge[] = [
  { id: "e1", source: "pdf_tool_1",        target: "agent_rag",      animated: true, style: { stroke: "#10b981", strokeWidth: 2 } },
  { id: "e2", source: "agent_orchestrator", target: "agent_rag",      animated: true, style: { stroke: "#a855f7", strokeWidth: 2.5 } },
  { id: "e3", source: "agent_rag",          target: "agent_worker",   animated: true, style: { stroke: "#3b82f6", strokeWidth: 2.5 } },
  { id: "e4", source: "agent_worker",       target: "agent_reviewer", animated: true, style: { stroke: "#f59e0b", strokeWidth: 2.5 } },
];

export default function ContractIQApp() {
  const [activeTab, setActiveTab]             = useState<Tab>("analyzer");
  const [analysisResult, setAnalysisResult]   = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing]         = useState(false);
  const [apiKey, setApiKey]                   = useState("");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isPaywallOpen, setIsPaywallOpen]     = useState(false);
  const [isChatPanelOpen, setIsChatPanelOpen] = useState(false);
  const [isPdfDropped, setIsPdfDropped]       = useState(false);
  const [usageCount, setUsageCount]           = useState(0);
  const [serverStatus, setServerStatus]       = useState<"online"|"offline"|"checking">("checking");

  // Advanced canvas state
  const [nodes, setNodes]                         = useState<Node<CustomNodeData>[]>(initialNodes);
  const [edges, setEdges]                         = useState<Edge[]>(initialEdges);
  const [goal, setGoal]                           = useState("Ingest enterprise policy PDF and extract key SLA compliance findings.");
  const [executionMode, setExecutionMode]         = useState<"dag"|"sequential">("dag");
  const [isRunning, setIsRunning]                 = useState(false);
  const [activeWorkflowId, setActiveWorkflowId]   = useState<string|null>(null);
  const [isTerminalOpen, setIsTerminalOpen]       = useState(true);
  const [isPdfModalOpen, setIsPdfModalOpen]       = useState(false);
  const [pdfReportUrl, setPdfReportUrl]           = useState<string|null>(null);
  const [uploadedDocIds, setUploadedDocIds]       = useState<string[]>([]);

  // Sync usage count from localStorage
  useEffect(() => {
    const raw = parseInt(localStorage.getItem("contractiq_usage_count") || "0", 10);
    setUsageCount(raw);
  }, [analysisResult]);

  // Check backend health
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        setServerStatus(res.ok ? "online" : "offline");
      } catch { setServerStatus("offline"); }
    };
    check();
    const iv = setInterval(check, 15000);
    return () => clearInterval(iv);
  }, []);

  // Handle drag-drop onto canvas
  const handleGlobalFileDrop = useCallback((file: File) => {
    setActiveTab("analyzer");
    setIsPdfDropped(true);
    setTimeout(() => setIsPdfDropped(false), 100);
  }, []);

  // Handle view report from history
  const handleViewReport = useCallback((shareToken: string) => {
    window.open(`/report/${shareToken}`, "_blank");
  }, []);

  // Canvas handlers
  const onNodesChange = useCallback((changes: NodeChange[]) =>
    setNodes((nds) => applyNodeChanges(changes, nds) as Node<CustomNodeData>[]), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) =>
    setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect     = useCallback((connection: Connection) =>
    setEdges((eds) => addEdge({ ...connection, animated: true }, eds)), []);

  const handleAddAgentNode = (role: AgentRoleType) => {
    const labels: Record<AgentRoleType, string> = {
      orchestrator: "Orchestrator Agent", worker: "Worker Agent",
      rag: "RAG Specialist", reviewer: "Reviewer Agent",
    };
    setNodes((nds) => [...nds, {
      id: `agent_${role}_${Date.now()}`, type: "agentNode",
      position: { x: 400 + Math.random()*80, y: 150 + Math.random()*80 },
      data: { label: labels[role], role, description: `Custom ${labels[role]}`, assignedTools: [] },
    }]);
  };

  const handleAddToolNode = (kind: ToolKindType) => {
    const labels: Record<ToolKindType, string> = {
      pdf_reader: "Chroma PDF Reader", web_search: "Web Search Engine", code_executor: "Python Sandbox",
    };
    setNodes((nds) => [...nds, {
      id: `tool_${kind}_${Date.now()}`, type: "toolNode",
      position: { x: 150 + Math.random()*80, y: 300 + Math.random()*80 },
      data: { label: labels[kind], toolKind: kind, description: `Tool: ${labels[kind]}` },
    }]);
  };

  const handleLoadTemplate = (name: string) => {
    const goalMap: Record<string, string> = {
      enterprise_rag:          "Ingest enterprise policy PDF and extract key SLA compliance findings.",
      legal_contract:          "Audit vendor contract PDF: extract liability caps, SLA penalties, and termination risks.",
      financial_due_diligence: "Analyze earnings PDF: extract Q3 revenue, EBITDA margins, and cash flow risks.",
      web_researcher:          "Research enterprise AI agent platforms and market trends in 2026.",
    };
    setNodes(initialNodes);
    setEdges(initialEdges);
    setGoal(goalMap[name] || goal);
  };

  const handleRunWorkflow = async () => {
    if (!goal.trim()) return;
    setIsRunning(true); setIsTerminalOpen(true); setPdfReportUrl(null);
    const payload = convertGraphToWorkflowPayload(nodes, edges, goal, executionMode, uploadedDocIds);
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;
    try {
      const res = await fetch(`${API_BASE}/start-workflow`, { method: "POST", headers, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setActiveWorkflowId(data.workflow_id);
      setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "running" } })));
      const poll = setInterval(async () => {
        try {
          const sr = await fetch(`${API_BASE}/status/${data.workflow_id}`, { headers });
          if (sr.ok) {
            const sd = await sr.json();
            if (sd.status === "success" || sd.status === "failed") {
              clearInterval(poll); setIsRunning(false);
              if (sd.pdf_report_url) setPdfReportUrl(sd.pdf_report_url);
              setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: sd.status } })));
            }
          }
        } catch { /* ignore */ }
      }, 2000);
    } catch { setIsRunning(false); setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "failed" } }))); }
  };

  return (
    <div className="flex flex-col h-screen bg-[#060b14] text-slate-100 overflow-hidden">
      {/* Global Drag & Drop Overlay */}
      <GlobalDragDropOverlay onFileDropped={handleGlobalFileDrop} />

      {/* ContractIQ Header */}
      <ContractHeader
        activeTab={activeTab}
        onTabChange={(tab) => { setActiveTab(tab); if (tab !== "analyzer") setAnalysisResult(null); }}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        apiKey={apiKey}
        serverStatus={serverStatus}
        usageCount={usageCount}
        freeLimit={FREE_LIMIT}
      />

      {/* ── Main Content Area ── */}
      <main className="flex-1 overflow-y-auto result-scroll">

        {/* ── ANALYZER TAB ── */}
        {activeTab === "analyzer" && (
          <div className="min-h-full flex flex-col">
            {!analysisResult && !isAnalyzing && (
              <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 space-y-8">
                {/* Hero */}
                <div className="text-center max-w-2xl space-y-4">
                  <div className="flex justify-center">
                    <div className="relative">
                      <div className="absolute inset-0 rounded-full bg-blue-500/20 blur-3xl scale-150" />
                      <div className="relative p-5 rounded-2xl bg-gradient-to-br from-blue-800/60 to-indigo-900/60 border border-blue-500/30 animate-float">
                        <svg viewBox="0 0 24 24" className="w-12 h-12 text-blue-300" fill="none" stroke="currentColor" strokeWidth="1.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1M3 12h1m16 0h1M5.636 5.636l.707.707m11.314 11.314.707.707M5.636 18.364l.707-.707m11.314-11.314.707-.707" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <h1 className="text-4xl font-black text-white leading-tight">
                    Know Every Risk Before You Sign
                  </h1>
                  <p className="text-slate-400 text-lg leading-relaxed">
                    Upload any contract PDF. Get an instant risk score, plain-English summary,
                    and every red flag clause — in under 60 seconds.
                  </p>
                  <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
                    {["⚡ 60-Second Analysis","🔒 Red Flag Detection","📊 Risk Score 0–100","📄 PDF Report"].map((f) => (
                      <span key={f} className="px-3 py-1.5 rounded-lg bg-slate-900/60 border border-white/10 text-slate-300 text-xs font-medium">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Upload Zone */}
                <ContractUploadZone
                  onAnalysisComplete={(result) => { setAnalysisResult(result); setUsageCount((c) => c + 1); }}
                  onAnalysisStart={() => setIsAnalyzing(true)}
                  apiBaseUrl={API_BASE}
                  apiKey={apiKey}
                  usageCount={usageCount}
                  freeLimit={FREE_LIMIT}
                  onUpgradeCta={() => setIsPaywallOpen(true)}
                />
              </div>
            )}

            {isAnalyzing && !analysisResult && (
              <div className="flex-1 flex items-center justify-center px-6 py-12">
                <ContractUploadZone
                  onAnalysisComplete={(result) => { setAnalysisResult(result); setIsAnalyzing(false); setUsageCount((c) => c + 1); }}
                  onAnalysisStart={() => {}}
                  apiBaseUrl={API_BASE}
                  apiKey={apiKey}
                  usageCount={usageCount}
                  freeLimit={FREE_LIMIT}
                  onUpgradeCta={() => setIsPaywallOpen(true)}
                />
              </div>
            )}

            {analysisResult && (
              <div className="px-6 py-8">
                <ContractResultCard
                  result={analysisResult}
                  apiBaseUrl={API_BASE}
                  onAnalyzeAnother={() => { setAnalysisResult(null); setIsAnalyzing(false); }}
                />
              </div>
            )}
          </div>
        )}

        {/* ── HISTORY TAB ── */}
        {activeTab === "history" && (
          <div className="px-6 py-8">
            <AnalysisHistory onViewReport={handleViewReport} />
          </div>
        )}

        {/* ── PRICING TAB ── */}
        {activeTab === "pricing" && (
          <div className="px-6 py-8">
            <PricingSection onGetStarted={() => setActiveTab("analyzer")} />
          </div>
        )}

        {/* ── ADVANCED CANVAS TAB ── */}
        {activeTab === "advanced" && (
          <div className="flex h-full overflow-hidden" style={{ height: "calc(100vh - 56px)" }}>
            <Sidebar
              onAddAgentNode={handleAddAgentNode}
              onAddToolNode={handleAddToolNode}
              onLoadTemplate={handleLoadTemplate}
              onOpenPdfModal={() => setIsPdfModalOpen(true)}
              onOpenChatPanel={() => setIsChatPanelOpen(!isChatPanelOpen)}
            />
            <div className="flex-1 flex flex-col relative">
              {/* Advanced Canvas Header */}
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
                apiBaseUrl={API_BASE}
              />
              <div className="flex-1 w-full h-full">
                <VisualCanvas
                  nodes={nodes} edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onConnect={onConnect}
                />
              </div>
              <TerminalConsole
                isOpen={isTerminalOpen}
                onClose={() => setIsTerminalOpen(false)}
                workflowId={activeWorkflowId}
                wsBaseUrl={WS_BASE}
              />
            </div>
          </div>
        )}
      </main>

      {/* ── Modals & Panels ── */}
      <DocumentChatPanel
        isOpen={isChatPanelOpen}
        onClose={() => setIsChatPanelOpen(false)}
        apiBaseUrl={API_BASE}
        apiKey={apiKey}
      />
      <PdfUploadModal
        isOpen={isPdfModalOpen}
        onClose={() => setIsPdfModalOpen(false)}
        onPdfUploaded={(docId) => setUploadedDocIds((p) => [...p, docId])}
        apiBaseUrl={API_BASE}
      />
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        apiKey={apiKey}
        onApiKeyChange={setApiKey}
        apiBaseUrl={API_BASE}
      />
      <PaywallModal
        isOpen={isPaywallOpen}
        onClose={() => setIsPaywallOpen(false)}
        onSwitchToPricing={() => { setIsPaywallOpen(false); setActiveTab("pricing"); }}
        freeLimit={FREE_LIMIT}
      />
    </div>
  );
}
