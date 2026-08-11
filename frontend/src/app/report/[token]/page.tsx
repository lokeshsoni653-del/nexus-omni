"use client";

import React, { useEffect, useState } from "react";
import { ContractResultCard } from "../../../components/ContractResultCard";
import { Scale, Loader2, AlertTriangle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://omnimind-backend-u94t.onrender.com";

interface PageProps {
  params: Promise<{ token: string }>;
}

export default function SharedReportPage({ params }: PageProps) {
  const { token } = use(params);
  const [result, setResult]   = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string>("");

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const res = await fetch(`${API_BASE}/contract/report/${token}`);
        if (res.status === 404) {
          setError("Report not found. This link may have expired or been deleted.");
          return;
        }
        if (!res.ok) throw new Error(`Failed to load report (${res.status})`);
        const data = await res.json();
        setResult({
          ...data,
          analysis_id:   data.analysis_id  || token,
          share_token:   data.share_token  || token,
          share_url:     typeof window !== "undefined" ? window.location.href : "",
          pdf_report_url: data.pdf_report_url || "",
        });
      } catch (err: any) {
        setError(err.message || "Failed to load report.");
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [token]);

  return (
    <div className="min-h-screen bg-[#060b14] text-slate-100">
      {/* Top Bar */}
      <header className="h-14 border-b border-white/8 px-5 flex items-center justify-between bg-[#060b14]/80 backdrop-blur-lg sticky top-0 z-20">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-700 to-indigo-800">
            <Scale className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-sm text-white">ContractIQ</span>
          <span className="text-[10px] px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold">AI</span>
        </div>
        <Link href="/" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
          Analyze Your Contract
        </Link>
      </header>

      {/* Report Header */}
      <div className="px-6 pt-8 pb-4 max-w-4xl mx-auto">
        <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
          <Scale className="w-3.5 h-3.5 text-blue-400" />
          <span>Shared Contract Analysis Report</span>
          <span>·</span>
          <span className="font-mono">{token.slice(0, 12)}...</span>
        </div>
        <h1 className="text-2xl font-black text-white">
          {result?.filename || "Contract Analysis"}
        </h1>
        {result?.created_at && (
          <p className="text-xs text-slate-500 mt-1">
            Analyzed on {new Date(result.created_at).toLocaleDateString("en-US", {
              year: "numeric", month: "long", day: "numeric",
            })}
          </p>
        )}
      </div>

      {/* Content */}
      <div className="px-6 pb-12 max-w-4xl mx-auto">
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
            <p className="text-slate-400 text-sm">Loading contract analysis…</p>
          </div>
        )}
        {error && (
          <div className="flex items-start gap-3 p-5 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 max-w-md mx-auto mt-8">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-red-400" />
            <div>
              <p className="font-semibold text-sm mb-1">Report Not Found</p>
              <p className="text-xs leading-relaxed">{error}</p>
              <Link href="/" className="inline-block mt-3 text-xs text-blue-400 hover:text-blue-300 underline">
                ← Analyze a new contract
              </Link>
            </div>
          </div>
        )}
        {result && !loading && (
          <ContractResultCard
            result={result}
            apiBaseUrl={API_BASE}
            onAnalyzeAnother={() => { window.location.href = "/"; }}
          />
        )}
      </div>

      {/* Footer */}
      <footer className="text-center py-6 border-t border-white/6 text-[11px] text-slate-600 space-y-1">
        <p>Powered by <span className="text-blue-400 font-semibold">ContractIQ</span> — AI-Powered Contract Analysis</p>
        <p>Disclaimer: ContractIQ does not provide legal advice. Consult a licensed attorney for official legal counsel.</p>
      </footer>
    </div>
  );
}
