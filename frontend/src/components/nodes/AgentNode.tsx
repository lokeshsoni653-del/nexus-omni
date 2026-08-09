"use client";

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Bot, Cpu, Database, ShieldCheck, Search, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { CustomNodeData } from '../../types/workflow';

const roleConfig = {
  orchestrator: {
    bg: 'from-purple-900/60 to-slate-900/90',
    border: 'border-purple-500/40 hover:border-purple-400',
    badgeBg: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    glow: 'shadow-[0_0_20px_rgba(168,85,247,0.15)]',
    icon: Cpu,
    title: 'Orchestrator Agent',
  },
  worker: {
    bg: 'from-blue-900/60 to-slate-900/90',
    border: 'border-blue-500/40 hover:border-blue-400',
    badgeBg: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.15)]',
    icon: Bot,
    title: 'Worker Agent',
  },
  rag: {
    bg: 'from-emerald-900/60 to-slate-900/90',
    border: 'border-emerald-500/40 hover:border-emerald-400',
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.15)]',
    icon: Database,
    title: 'RAG Specialist',
  },
  reviewer: {
    bg: 'from-amber-900/60 to-slate-900/90',
    border: 'border-amber-500/40 hover:border-amber-400',
    badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.15)]',
    icon: ShieldCheck,
    title: 'Reviewer Agent',
  },
};

export const AgentNode = memo(({ data, selected }: NodeProps & { data: CustomNodeData }) => {
  const roleKey = data.role || 'worker';
  const cfg = roleConfig[roleKey] || roleConfig.worker;
  const IconComponent = cfg.icon;

  const status = data.status || 'idle';

  return (
    <div
      className={`relative w-72 rounded-xl bg-gradient-to-br ${cfg.bg} backdrop-blur-xl border ${
        selected ? 'border-sky-400 ring-2 ring-sky-400/50 scale-[1.02]' : cfg.border
      } p-4 transition-all duration-300 ${cfg.glow}`}
    >
      {/* Incoming Connection Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-slate-400 !border-2 !border-slate-900 hover:!bg-sky-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left-target"
        className="!w-3 !h-3 !bg-slate-400 !border-2 !border-slate-900 hover:!bg-sky-400"
      />

      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-slate-800/80 border border-white/10 text-white shadow-inner">
            <IconComponent className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-slate-100 leading-snug">{data.label}</h3>
            <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-medium border ${cfg.badgeBg}`}>
              {cfg.title}
            </span>
          </div>
        </div>

        {/* Status Indicator */}
        <div>
          {status === 'running' && (
            <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium animate-pulse">
              <Clock className="w-3.5 h-3.5" /> Working
            </span>
          )}
          {status === 'success' && (
            <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" /> Done
            </span>
          )}
          {status === 'failed' && (
            <span className="flex items-center gap-1 text-[11px] text-rose-400 font-medium">
              <AlertCircle className="w-3.5 h-3.5" /> Failed
            </span>
          )}
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-300/90 leading-relaxed mb-3 line-clamp-2">
        {data.description || 'Autonomous agent configured for workflow task execution.'}
      </p>

      {/* Assigned Tools Badges */}
      {data.assignedTools && data.assignedTools.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-2 border-t border-white/10">
          {data.assignedTools.map((tool, idx) => (
            <span key={idx} className="px-1.5 py-0.5 rounded bg-slate-800/90 text-[10px] text-slate-300 border border-white/5">
              🛠️ {tool}
            </span>
          ))}
        </div>
      )}

      {/* Outgoing Connection Handles */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-sky-400 !border-2 !border-slate-900 hover:!scale-125"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right-source"
        className="!w-3 !h-3 !bg-sky-400 !border-2 !border-slate-900 hover:!scale-125"
      />
    </div>
  );
});

AgentNode.displayName = 'AgentNode';
