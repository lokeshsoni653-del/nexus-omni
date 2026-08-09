"use client";

import React, { useEffect, useRef, useState } from 'react';
import { Terminal, X, Trash2, CheckCircle2, AlertTriangle, Cpu, Bot, Database, ShieldCheck, Wifi, WifiOff } from 'lucide-react';
import { AgentLogEvent } from '../types/workflow';

interface TerminalConsoleProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId: string | null;
  wsBaseUrl?: string;
}

export const TerminalConsole: React.FC<TerminalConsoleProps> = ({
  isOpen,
  onClose,
  workflowId,
  wsBaseUrl = 'ws://localhost:8000',
}) => {
  const [logs, setLogs] = useState<AgentLogEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);

  // Connect to WebSocket when workflowId is set
  useEffect(() => {
    if (!workflowId) return;

    const wsUrl = `${wsBaseUrl}/ws/stream/${workflowId}`;
    console.log(`Connecting WebSocket stream: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setLogs((prev) => [
        ...prev,
        {
          agent_name: 'System',
          log_type: 'system',
          content: `WebSocket connected to workflow stream [${workflowId.slice(0, 8)}]`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    };

    ws.onmessage = (event) => {
      try {
        const data: AgentLogEvent = JSON.parse(event.data);
        if (data.log_type === 'ping') return; // Filter keepalive pings

        data.timestamp = new Date().toLocaleTimeString();
        setLogs((prev) => [...prev, data]);
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setLogs((prev) => [
        ...prev,
        {
          agent_name: 'System',
          log_type: 'system',
          content: 'WebSocket connection closed.',
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    };

    ws.onerror = (error) => {
      setIsConnected(false);
      console.error('WebSocket error:', error);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [workflowId, wsBaseUrl]);

  // Auto-scroll to bottom on new log events
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (!isOpen) return null;

  const clearLogs = () => setLogs([]);

  const getAgentBadge = (name: string) => {
    switch (name) {
      case 'Orchestrator':
        return <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[10px] font-mono flex items-center gap-1"><Cpu className="w-3 h-3"/> Orchestrator</span>;
      case 'Worker':
        return <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 text-[10px] font-mono flex items-center gap-1"><Bot className="w-3 h-3"/> Worker</span>;
      case 'RAGSpecialist':
      case 'RAG':
        return <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-mono flex items-center gap-1"><Database className="w-3 h-3"/> RAG Specialist</span>;
      case 'Reviewer':
        return <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-mono flex items-center gap-1"><ShieldCheck className="w-3 h-3"/> Reviewer</span>;
      default:
        return <span className="px-2 py-0.5 rounded bg-slate-700/50 text-slate-300 text-[10px] font-mono">{name}</span>;
    }
  };

  return (
    <div className="h-80 glass-panel border-t border-white/10 flex flex-col z-30 transition-all shadow-2xl">
      {/* Console Header */}
      <div className="h-10 px-4 bg-slate-950/80 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
            <Terminal className="w-4 h-4 text-sky-400" />
            <span>Agent Thought Console (WebSocket Stream)</span>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-900 border border-white/10 text-[10px]">
            {isConnected ? (
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <Wifi className="w-3 h-3 animate-pulse" /> Live Connected
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-400">
                <WifiOff className="w-3 h-3" /> Offline
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={clearLogs}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Clear Logs"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Logs Viewport */}
      <div ref={scrollRef} className="flex-1 p-4 font-mono text-xs overflow-y-auto space-y-2.5 bg-slate-950/90">
        {logs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">
            Waiting for workflow execution to stream live agent thoughts...
          </div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-3 leading-relaxed border-b border-white/5 pb-2">
              <span className="text-[10px] text-slate-500 shrink-0 pt-0.5">{log.timestamp}</span>

              <div className="shrink-0">{getAgentBadge(log.agent_name)}</div>

              <div className="flex-1 text-slate-200 break-words">
                {log.log_type === 'thought' && (
                  <span className="text-purple-300">💡 {log.content}</span>
                )}
                {log.log_type === 'action' && (
                  <span className="text-cyan-300 font-semibold">⚙️ {log.content}</span>
                )}
                {log.log_type === 'result' && (
                  <span className="text-emerald-300">✅ {log.content}</span>
                )}
                {log.log_type === 'error' && (
                  <span className="text-rose-400 font-semibold">❌ {log.content}</span>
                )}
                {log.log_type === 'workflow_complete' && (
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                    🎉 WORKFLOW COMPLETE: {log.content}
                  </span>
                )}
                {log.log_type === 'workflow_failed' && (
                  <span className="text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
                    💥 WORKFLOW FAILED: {log.content}
                  </span>
                )}
                {log.log_type === 'system' && (
                  <span className="text-slate-400 italic">ℹ️ {log.content}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
