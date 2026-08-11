"use client";

import React, { useEffect, useState } from "react";
import { History, FileText, ExternalLink, Trash2, Scale } from "lucide-react";

interface HistoryItem {
  id: string;
  share_token: string;
  filename: string;
  risk_score: number;
  risk_level: string;
  contract_type: string;
  analyzed_at: string;
}

const RISK_COLORS: Record<string, string> = {
  CRITICAL: "text-red-400 bg-red-950/40 border-red-500/30",
  HIGH:     "text-orange-400 bg-orange-950/40 border-orange-500/30",
  MODERATE: "text-amber-400 bg-amber-950/40 border-amber-500/30",
  LOW:      "text-emerald-400 bg-emerald-950/40 border-emerald-500/30",
};

interface AnalysisHistoryProps {
  onViewReport: (shareToken: string) => void;
}

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({ onViewReport }) => {
  const [items, setItems] = useState<HistoryItem[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("contractiq_history");
      setItems(raw ? JSON.parse(raw) : []);
    } catch { setItems([]); }
  }, []);

  const handleDelete = (id: string) => {
    const updated = items.filter((i) => i.id !== id);
    setItems(updated);
    localStorage.setItem("contractiq_history", JSON.stringify(updated));
  };

  const handleClearAll = () => {
    setItems([]);
    localStorage.removeItem("contractiq_history");
    localStorage.removeItem("contractiq_usage_count");
  };

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/8">
          <History className="w-10 h-10 text-slate-600" />
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-300">No analyses yet</p>
          <p className="text-sm text-slate-500 mt-1">
            Upload a contract on the Analyzer tab to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto w-full space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-bold text-white">
          <History className="w-5 h-5 text-blue-400" />
          Analysis History
          <span className="text-sm font-normal text-slate-400">({items.length} contracts)</span>
        </h2>
        <button
          onClick={handleClearAll}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" /> Clear all
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map((item) => {
          const riskClass = RISK_COLORS[item.risk_level] || RISK_COLORS.MODERATE;
          const date = new Date(item.analyzed_at).toLocaleDateString("en-US", {
            month: "short", day: "numeric", year: "numeric",
          });

          return (
            <div
              key={item.id}
              className="glass-card p-4 flex items-center gap-4 hover:border-blue-500/30 transition-all group"
            >
              {/* Score Circle */}
              <div className={`w-14 h-14 rounded-xl flex flex-col items-center justify-center border shrink-0 ${riskClass}`}>
                <span className="text-lg font-black leading-none">{Math.round(item.risk_score)}</span>
                <span className="text-[9px] font-semibold opacity-80">RISK</span>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <FileText className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <p className="text-sm font-semibold text-slate-100 truncate">{item.filename}</p>
                </div>
                <p className="text-xs text-slate-400">
                  {item.contract_type} · <span className={`font-semibold ${riskClass.split(" ")[0]}`}>{item.risk_level}</span>
                </p>
                <p className="text-[11px] text-slate-600 mt-0.5">{date}</p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                <button
                  onClick={() => onViewReport(item.share_token)}
                  className="p-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 transition-all"
                  title="View Report"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="p-2 rounded-lg bg-red-900/20 hover:bg-red-900/40 text-red-400 transition-all"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex items-center gap-2 pt-2">
        <Scale className="w-3.5 h-3.5 text-blue-400" />
        <p className="text-xs text-slate-500">
          History is stored locally in your browser. Shareable links work for anyone with the URL.
        </p>
      </div>
    </div>
  );
};
