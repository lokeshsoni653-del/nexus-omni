"use client";

import React from 'react';
import { Bot, Cpu, Database, ShieldCheck, Globe, FileText, Terminal, Sparkles, Layers, PlusCircle } from 'lucide-react';
import { AgentRoleType, ToolKindType } from '../types/workflow';

interface SidebarProps {
  onAddAgentNode: (role: AgentRoleType) => void;
  onAddToolNode: (kind: ToolKindType) => void;
  onLoadTemplate: (templateName: string) => void;
  onOpenPdfModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onAddAgentNode,
  onAddToolNode,
  onLoadTemplate,
  onOpenPdfModal,
}) => {
  return (
    <aside className="w-72 glass-panel border-r border-white/10 flex flex-col h-full z-10 select-none">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-sky-400" />
          <h2 className="font-semibold text-sm text-slate-100">Node Palette</h2>
        </div>
        <span className="text-[10px] bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2 py-0.5 rounded-full font-mono">
          Canvas V1.0
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Agent Templates */}
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5 text-purple-400" /> Agent Team Nodes
          </h3>
          <div className="space-y-2">
            <button
              onClick={() => onAddAgentNode('orchestrator')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-purple-500/30 hover:border-purple-400 hover:bg-purple-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-purple-500/20 text-purple-300">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">Orchestrator Agent</div>
                  <div className="text-[10px] text-slate-400">Goal decomposition & planning</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>

            <button
              onClick={() => onAddAgentNode('worker')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-blue-500/30 hover:border-blue-400 hover:bg-blue-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-blue-500/20 text-blue-300">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">Worker Agent</div>
                  <div className="text-[10px] text-slate-400">Task execution & web research</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>

            <button
              onClick={() => onAddAgentNode('rag')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-emerald-500/30 hover:border-emerald-400 hover:bg-emerald-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-emerald-500/20 text-emerald-300">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">RAG Specialist</div>
                  <div className="text-[10px] text-slate-400">Vector store document retrieval</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>

            <button
              onClick={() => onAddAgentNode('reviewer')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-amber-500/30 hover:border-amber-400 hover:bg-amber-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-amber-500/20 text-amber-300">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">Reviewer Agent</div>
                  <div className="text-[10px] text-slate-400">Quality control & validation</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          </div>
        </div>

        {/* Tools Palette */}
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Tool Plugins
          </h3>
          <div className="space-y-2">
            <button
              onClick={() => onAddToolNode('pdf_reader')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-teal-500/30 hover:border-teal-400 hover:bg-teal-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-teal-500/20 text-teal-300">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">Chroma PDF Reader</div>
                  <div className="text-[10px] text-slate-400">Vector search local PDFs</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-teal-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>

            <button
              onClick={() => onAddToolNode('web_search')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-cyan-500/30 hover:border-cyan-400 hover:bg-cyan-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-cyan-500/20 text-cyan-300">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">Web Search Engine</div>
                  <div className="text-[10px] text-slate-400">Live internet queries</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>

            <button
              onClick={() => onAddToolNode('code_executor')}
              className="w-full text-left p-2.5 rounded-lg bg-slate-800/60 border border-indigo-500/30 hover:border-indigo-400 hover:bg-indigo-950/30 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded bg-indigo-500/20 text-indigo-300">
                  <Terminal className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">Python Sandbox</div>
                  <div className="text-[10px] text-slate-400">Code generation & execution</div>
                </div>
              </div>
              <PlusCircle className="w-4 h-4 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          </div>
        </div>

        {/* Preset Templates */}
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            ⚡ Preset Workflows
          </h3>
          <div className="space-y-2">
            <button
              onClick={() => onLoadTemplate('enterprise_rag')}
              className="w-full text-left p-2.5 rounded-lg bg-gradient-to-r from-purple-900/40 to-emerald-900/40 border border-purple-500/30 hover:border-purple-400 transition-all"
            >
              <div className="text-xs font-semibold text-purple-200">Enterprise Policy RAG</div>
              <div className="text-[10px] text-slate-300">PDF Reader + Orchestrator + RAG + Reviewer</div>
            </button>

            <button
              onClick={() => onLoadTemplate('web_researcher')}
              className="w-full text-left p-2.5 rounded-lg bg-gradient-to-r from-blue-900/40 to-cyan-900/40 border border-blue-500/30 hover:border-blue-400 transition-all"
            >
              <div className="text-xs font-semibold text-blue-200">Market Intelligence Team</div>
              <div className="text-[10px] text-slate-300">Web Search + Worker + Python Code + Reviewer</div>
            </button>
          </div>
        </div>
      </div>

      {/* Upload PDF Drawer Trigger */}
      <div className="p-4 border-t border-white/10 bg-slate-900/60">
        <button
          onClick={onOpenPdfModal}
          className="w-full py-2.5 px-3 rounded-lg bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white font-medium text-xs shadow-lg shadow-teal-900/30 flex items-center justify-center gap-2 transition-all"
        >
          <FileText className="w-4 h-4" /> Upload PDF Document
        </button>
      </div>
    </aside>
  );
};
