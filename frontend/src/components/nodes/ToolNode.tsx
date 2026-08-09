"use client";

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { FileText, Globe, Terminal, Wrench } from 'lucide-react';
import { CustomNodeData } from '../../types/workflow';

const toolConfig = {
  pdf_reader: {
    bg: 'from-teal-900/60 to-slate-900/90',
    border: 'border-teal-500/40 hover:border-teal-400',
    badgeBg: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
    icon: FileText,
    title: 'PDF Reader (RAG)',
  },
  web_search: {
    bg: 'from-cyan-900/60 to-slate-900/90',
    border: 'border-cyan-500/40 hover:border-cyan-400',
    badgeBg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    icon: Globe,
    title: 'Web Search',
  },
  code_executor: {
    bg: 'from-indigo-900/60 to-slate-900/90',
    border: 'border-indigo-500/40 hover:border-indigo-400',
    badgeBg: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    icon: Terminal,
    title: 'Python Executor',
  },
};

export const ToolNode = memo(({ data, selected }: NodeProps & { data: CustomNodeData }) => {
  const toolKind = data.toolKind || 'web_search';
  const cfg = toolConfig[toolKind] || toolConfig.web_search;
  const IconComponent = cfg.icon;

  return (
    <div
      className={`relative w-56 rounded-xl bg-gradient-to-br ${cfg.bg} backdrop-blur-xl border ${
        selected ? 'border-cyan-400 ring-2 ring-cyan-400/50 scale-[1.02]' : cfg.border
      } p-3.5 transition-all duration-300 shadow-[0_0_15px_rgba(6,182,212,0.1)]`}
    >
      <div className="flex items-center gap-2.5 mb-1.5">
        <div className="p-1.5 rounded-md bg-slate-800/80 border border-white/10 text-cyan-300">
          <IconComponent className="w-4 h-4" />
        </div>
        <div>
          <h4 className="font-semibold text-xs text-slate-100">{data.label}</h4>
          <span className={`inline-block px-1.5 py-0.2 rounded text-[9px] font-medium border ${cfg.badgeBg}`}>
            {cfg.title}
          </span>
        </div>
      </div>

      <p className="text-[11px] text-slate-300/80 leading-tight">
        {data.description || 'Custom tool plugin for agents.'}
      </p>

      {/* Target & Source Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-900"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="tool-source"
        className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-900"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-900"
      />
    </div>
  );
});

ToolNode.displayName = 'ToolNode';
