"use client";

import React from 'react';
import { Play, Terminal, Sparkles, Key, FileText, RefreshCw } from 'lucide-react';

interface HeaderProps {
  goal: string;
  onGoalChange: (newGoal: string) => void;
  executionMode: 'dag' | 'sequential';
  onExecutionModeChange: (mode: 'dag' | 'sequential') => void;
  onRunWorkflow: () => void;
  isRunning: boolean;
  onToggleTerminal: () => void;
  isTerminalOpen: boolean;
  serverStatus: 'online' | 'offline' | 'checking';
  onOpenAuthModal: () => void;
  apiKey: string;
  pdfReportUrl: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  goal,
  onGoalChange,
  executionMode,
  onExecutionModeChange,
  onRunWorkflow,
  isRunning,
  onToggleTerminal,
  isTerminalOpen,
  serverStatus,
  onOpenAuthModal,
  apiKey,
  pdfReportUrl,
}) => {
  return (
    <header className="h-16 glass-panel border-b border-white/10 px-6 flex items-center justify-between gap-4 z-20">
      {/* Brand & Platform Identity */}
      <div className="flex items-center gap-3 min-w-[240px]">
        <div className="p-2 rounded-xl bg-gradient-to-tr from-purple-600 via-sky-500 to-emerald-400 text-white shadow-lg shadow-sky-500/20">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-base tracking-tight text-white">OmniMind AI</h1>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 font-medium">
              SaaS V0.5
            </span>
          </div>
          <p className="text-[11px] text-slate-400">Autonomous Multi-Agent Enterprise RAG Platform</p>
        </div>
      </div>

      {/* Goal Input & Mode Selector */}
      <div className="flex-1 max-w-2xl flex items-center gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={goal}
            onChange={(e) => onGoalChange(e.target.value)}
            placeholder="Enter workflow goal (e.g. Ingest enterprise policy PDF, extract SLAs, and generate compliance report)..."
            className="w-full h-10 px-4 py-2 rounded-lg bg-slate-900/80 border border-white/10 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-xs text-slate-100 placeholder-slate-500 outline-none transition-all"
          />
        </div>

        {/* Execution Mode Selector */}
        <select
          value={executionMode}
          onChange={(e) => onExecutionModeChange(e.target.value as 'dag' | 'sequential')}
          className="h-10 px-3 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-200 outline-none focus:border-sky-500 cursor-pointer font-medium"
        >
          <option value="dag">🔀 Mode: DAG Parallel</option>
          <option value="sequential">➡️ Mode: Sequential</option>
        </select>
      </div>

      {/* Controls, Auth & PDF Export */}
      <div className="flex items-center gap-3">
        {/* Auth / API Key Button */}
        <button
          onClick={onOpenAuthModal}
          className="h-10 px-3 rounded-lg bg-purple-950/40 border border-purple-500/30 hover:border-purple-400 text-xs text-purple-300 flex items-center gap-1.5 transition-all"
          title="Configure Authentication & API Keys"
        >
          <Key className="w-3.5 h-3.5" />
          <span>{apiKey ? `${apiKey.slice(0, 6)}...` : 'Auth / API Key'}</span>
        </button>

        {/* PDF Download Button if report is generated */}
        {pdfReportUrl && (
          <a
            href={pdfReportUrl.startsWith('/') ? `http://localhost:8000${pdfReportUrl}` : pdfReportUrl}
            target="_blank"
            rel="noreferrer"
            className="h-10 px-3.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-900/30 flex items-center gap-1.5 transition-all animate-pulse"
          >
            <FileText className="w-4 h-4" /> Download PDF Report
          </a>
        )}

        {/* Console Toggle Button */}
        <button
          onClick={onToggleTerminal}
          className={`h-10 px-3.5 rounded-lg border text-xs font-medium flex items-center gap-2 transition-all ${
            isTerminalOpen
              ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 shadow-lg shadow-sky-500/10'
              : 'bg-slate-800/80 text-slate-300 border-white/10 hover:border-white/20'
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>Console</span>
        </button>

        {/* Run Workflow Button */}
        <button
          onClick={onRunWorkflow}
          disabled={isRunning || !goal.trim()}
          className={`h-10 px-5 rounded-lg font-semibold text-xs text-white shadow-lg flex items-center gap-2 transition-all ${
            isRunning
              ? 'bg-amber-600/80 cursor-wait opacity-80'
              : 'bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 hover:from-sky-400 hover:to-purple-500 shadow-sky-500/20 active:scale-95'
          }`}
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Executing Agents...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run Workflow</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};
