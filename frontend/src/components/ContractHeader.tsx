"use client";
import React from "react";
import { Scale, Sparkles, Key, History, DollarSign, Settings2 } from "lucide-react";

type Tab = "analyzer" | "history" | "pricing" | "advanced";

interface ContractHeaderProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  onOpenAuthModal: () => void;
  apiKey: string;
  serverStatus: "online" | "offline" | "checking";
  usageCount: number;
  freeLimit: number;
}

export const ContractHeader: React.FC<ContractHeaderProps> = ({
  activeTab,
  onTabChange,
  onOpenAuthModal,
  apiKey,
  serverStatus,
  usageCount,
  freeLimit,
}) => {
  const statusColors = {
    online:   "bg-emerald-500",
    offline:  "bg-red-500",
    checking: "bg-amber-500 animate-pulse",
  };

  const remaining = Math.max(0, freeLimit - usageCount);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "analyzer",  label: "Analyzer",       icon: <Scale className="w-3.5 h-3.5" /> },
    { id: "history",   label: "History",        icon: <History className="w-3.5 h-3.5" /> },
    { id: "pricing",   label: "Pricing",        icon: <DollarSign className="w-3.5 h-3.5" /> },
    { id: "advanced",  label: "Advanced Canvas",icon: <Settings2 className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="h-14 glass-panel border-b border-white/10 px-5 flex items-center justify-between gap-4 z-20 shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-2.5 min-w-[180px]">
        <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-700 to-indigo-800 shadow-lg shadow-blue-900/40">
          <Scale className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-sm tracking-tight text-white">ContractIQ</h1>
            <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold">
              AI
            </span>
          </div>
          <p className="text-[10px] text-slate-500 leading-none mt-0.5">Legal Contract Analyzer</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-slate-900/60 border border-white/10 rounded-xl p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === tab.id
                ? "bg-blue-600 text-white shadow-md shadow-blue-900/40"
                : "text-slate-400 hover:text-white hover:bg-white/8"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Free Tier Usage */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-white/10 text-[11px]">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-300">
            <span className={`font-bold ${remaining === 0 ? "text-red-400" : "text-amber-300"}`}>
              {remaining}
            </span>
            /{freeLimit} free left
          </span>
        </div>

        {/* Server Status */}
        <div className="flex items-center gap-1.5 text-[11px]">
          <span className={`w-2 h-2 rounded-full ${statusColors[serverStatus]}`} />
          <span className="text-slate-400 hidden sm:inline capitalize">{serverStatus}</span>
        </div>

        {/* API Key Button */}
        <button
          onClick={onOpenAuthModal}
          className="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-800/80 border border-white/10 hover:border-blue-400/50 text-[11px] text-slate-300 hover:text-white transition-all"
        >
          <Key className="w-3 h-3 text-blue-400" />
          <span>{apiKey ? `${apiKey.slice(0, 8)}…` : "AI Key"}</span>
        </button>
      </div>
    </header>
  );
};
