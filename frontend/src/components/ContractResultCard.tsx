"use client";

import React, { useState, useCallback } from "react";
import {
  AlertTriangle, CheckCircle, ChevronDown, ChevronUp,
  Copy, Download, ExternalLink, FileText, Scale,
  Shield, Clock, Flag, ClipboardList, Check, Info
} from "lucide-react";

const LEGAL_DISCLAIMER =
  "Disclaimer: ContractIQ is an AI-powered contract analysis tool and does not provide legal advice. Results are for informational purposes only. Consult a licensed attorney for official legal counsel.";

interface RedFlag {
  clause_title: string;
  clause_text: string;
  severity: string;
  explanation: string;
  recommendation: string;
}

interface KeyDate {
  event: string;
  timeline: string;
}

interface AnalysisResult {
  analysis_id: string;
  share_token: string;
  share_url: string;
  filename: string;
  page_count: number;
  is_ocr: boolean;
  is_chunked: boolean;
  contract_type: string;
  favors_party: string;
  risk_score: number;
  risk_level: string;
  executive_summary: string;
  plain_english_summary: string;
  red_flags: RedFlag[];
  obligations: string[];
  key_dates: KeyDate[];
  pdf_report_url: string;
  disclaimer: string;
}

interface ContractResultCardProps {
  result: AnalysisResult;
  apiBaseUrl: string;
  onAnalyzeAnother: () => void;
}

// ── Risk Configuration ──────────────────────────────────────────────────────
const RISK_CONFIG: Record<string, { label: string; color: string; bg: string; gaugeBg: string; textClass: string }> = {
  CRITICAL: { label: "CRITICAL RISK", color: "#dc2626", bg: "rgba(220,38,38,0.12)", gaugeBg: "rgba(220,38,38,0.15)", textClass: "risk-critical" },
  HIGH:     { label: "HIGH RISK",     color: "#ea580c", bg: "rgba(234,88,12,0.12)",  gaugeBg: "rgba(234,88,12,0.15)",  textClass: "risk-high" },
  MODERATE: { label: "MODERATE RISK", color: "#d97706", bg: "rgba(217,119,6,0.12)", gaugeBg: "rgba(217,119,6,0.15)", textClass: "risk-moderate" },
  LOW:      { label: "LOW RISK",      color: "#16a34a", bg: "rgba(22,163,74,0.12)",  gaugeBg: "rgba(22,163,74,0.15)",  textClass: "risk-low" },
};

const SEVERITY_CLASSES: Record<string, string> = {
  CRITICAL: "severity-critical",
  HIGH:     "severity-high",
  MEDIUM:   "severity-medium",
  LOW:      "severity-low",
};

// ── SVG Risk Gauge ──────────────────────────────────────────────────────────
const RiskGauge: React.FC<{ score: number; color: string }> = ({ score, color }) => {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <svg width="140" height="140" className="drop-shadow-2xl">
      {/* Track */}
      <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="10" />
      {/* Progress — animated */}
      <circle
        cx="70" cy="70" r={radius}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{
          transform: "rotate(-90deg)",
          transformOrigin: "center",
          transition: "stroke-dashoffset 1.5s cubic-bezier(0.34, 1.56, 0.64, 1)",
          filter: `drop-shadow(0 0 8px ${color}88)`,
        }}
      />
      {/* Score text */}
      <text x="70" y="64" textAnchor="middle" fill="white" fontSize="26" fontWeight="800" fontFamily="Inter, sans-serif">
        {Math.round(score)}
      </text>
      <text x="70" y="82" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="10" fontFamily="Inter, sans-serif">
        / 100
      </text>
    </svg>
  );
};

// ── Red Flag Card ───────────────────────────────────────────────────────────
const RedFlagCard: React.FC<{ flag: RedFlag; index: number }> = ({ flag, index }) => {
  const [expanded, setExpanded] = useState(index < 2);
  const sevClass = SEVERITY_CLASSES[flag.severity?.toUpperCase()] || "severity-medium";

  return (
    <div className="rounded-xl border border-white/8 bg-slate-900/50 overflow-hidden transition-all">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 text-left gap-3 hover:bg-white/4 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className={`shrink-0 text-[10px] font-bold px-2 py-1 rounded-lg ${sevClass}`}>
            {flag.severity}
          </span>
          <span className="text-sm font-semibold text-slate-100 truncate">{flag.clause_title}</span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-slate-500 shrink-0" /> : <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/6">
          {flag.clause_text && (
            <div className="mt-3 p-3 rounded-lg bg-slate-800/60 border border-white/6">
              <p className="text-[11px] text-slate-400 italic leading-relaxed">"{flag.clause_text}"</p>
            </div>
          )}
          <div className="flex gap-2 items-start">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-300 leading-relaxed">{flag.explanation}</p>
          </div>
          <div className="flex gap-2 items-start p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/20">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
            <p className="text-xs text-emerald-300 leading-relaxed"><span className="font-semibold">Action: </span>{flag.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
};

// ── Main Result Card ─────────────────────────────────────────────────────────
export const ContractResultCard: React.FC<ContractResultCardProps> = ({
  result,
  apiBaseUrl,
  onAnalyzeAnother,
}) => {
  const [copied, setCopied] = useState(false);
  const riskCfg = RISK_CONFIG[result.risk_level] || RISK_CONFIG.MODERATE;
  const pdfUrl  = result.pdf_report_url
    ? (result.pdf_report_url.startsWith("/") ? `${apiBaseUrl}${result.pdf_report_url}` : result.pdf_report_url)
    : null;

  const handleCopyLink = useCallback(async () => {
    const url = result.share_url || `${window.location.origin}/report/${result.share_token}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }, [result]);

  return (
    <div className="animate-slide-up w-full max-w-4xl mx-auto space-y-6">
      {/* ── Top Summary Bar ── */}
      <div
        className="rounded-2xl p-6 border"
        style={{ background: riskCfg.gaugeBg, borderColor: `${riskCfg.color}30` }}
      >
        <div className="flex flex-col sm:flex-row items-center gap-6">
          {/* Gauge */}
          <div className="shrink-0">
            <RiskGauge score={result.risk_score} color={riskCfg.color} />
          </div>

          {/* Info */}
          <div className="flex-1 space-y-3 text-center sm:text-left">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <span
                  className="px-3 py-1 rounded-full text-xs font-bold border"
                  style={{ color: riskCfg.color, borderColor: riskCfg.color, background: riskCfg.bg }}
                >
                  ● {riskCfg.label}
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs bg-slate-800 border border-white/10 text-slate-300 font-medium">
                  {result.contract_type}
                </span>
                {result.is_ocr && (
                  <span className="px-2 py-1 rounded-full text-[10px] bg-amber-950/40 border border-amber-500/30 text-amber-300">
                    ⚠️ Scanned PDF · OCR used
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold text-white">{result.filename}</h2>
              <p className="text-xs text-slate-400">
                {result.page_count > 0 && `${result.page_count} pages · `}
                Favors: <span className="font-semibold text-slate-300">{result.favors_party}</span>
                {result.is_chunked && ` · Analyzed in ${result.is_chunked ? "sections" : "single pass"}`}
              </p>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">{result.executive_summary}</p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2 shrink-0 min-w-[160px]">
            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white text-xs font-bold shadow-lg shadow-blue-900/30 transition-all"
              >
                <Download className="w-3.5 h-3.5" /> Download PDF
              </a>
            )}
            <button
              onClick={handleCopyLink}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-white/10 text-slate-200 text-xs font-medium transition-all"
            >
              {copied ? <><Check className="w-3.5 h-3.5 text-emerald-400" /> Copied!</> : <><Copy className="w-3.5 h-3.5" /> Share Report</>}
            </button>
            <button
              onClick={onAnalyzeAnother}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/8 text-slate-400 text-xs font-medium transition-all"
            >
              <Scale className="w-3.5 h-3.5" /> New Analysis
            </button>
          </div>
        </div>
      </div>

      {/* ── Two-Column Detail Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Plain English Summary */}
        <div className="glass-card p-5 space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-bold text-white">
            <Info className="w-4 h-4 text-blue-400" />
            What You're Agreeing To (Plain English)
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">{result.plain_english_summary}</p>
        </div>

        {/* Key Dates */}
        <div className="glass-card p-5 space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-bold text-white">
            <Clock className="w-4 h-4 text-teal-400" />
            Key Dates & Deadlines
          </h3>
          {result.key_dates?.length > 0 ? (
            <div className="space-y-2">
              {result.key_dates.map((kd, i) => (
                <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-800/50">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0 mt-1.5" />
                  <div>
                    <p className="text-xs font-semibold text-slate-200">{kd.event}</p>
                    <p className="text-xs text-teal-300">{kd.timeline}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No specific dates identified.</p>
          )}
        </div>
      </div>

      {/* ── Red Flags Section ── */}
      {result.red_flags?.length > 0 && (
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-bold text-white">
              <Flag className="w-4 h-4 text-red-400" />
              Red Flag Clauses
              <span className="px-2 py-0.5 rounded-full bg-red-950/50 border border-red-500/30 text-red-300 text-[10px] font-bold">
                {result.red_flags.length} found
              </span>
            </h3>
            <div className="flex items-center gap-2 text-[10px] text-slate-500">
              {["CRITICAL","HIGH","MEDIUM","LOW"].map(s => {
                const cnt = result.red_flags.filter(f => f.severity?.toUpperCase() === s).length;
                return cnt > 0 ? (
                  <span key={s} className={`px-1.5 py-0.5 rounded ${SEVERITY_CLASSES[s]}`}>
                    {cnt} {s}
                  </span>
                ) : null;
              })}
            </div>
          </div>
          <div className="space-y-2">
            {result.red_flags.map((flag, i) => (
              <RedFlagCard key={i} flag={flag} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* ── Obligations Section ── */}
      {result.obligations?.length > 0 && (
        <div className="glass-card p-5 space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-bold text-white">
            <ClipboardList className="w-4 h-4 text-indigo-400" />
            Your Obligations Under This Contract
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {result.obligations.map((obl, i) => (
              <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-800/50">
                <span className="w-5 h-5 rounded-full bg-indigo-950/60 border border-indigo-500/30 text-[10px] font-bold text-indigo-300 flex items-center justify-center shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">{obl}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Legal Disclaimer (Guardrail 1) ── */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-slate-900/60 border border-white/6">
        <Shield className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
        <p className="text-[10px] text-slate-600 leading-relaxed">{LEGAL_DISCLAIMER}</p>
      </div>
    </div>
  );
};
