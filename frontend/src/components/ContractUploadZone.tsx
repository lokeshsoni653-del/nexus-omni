"use client";

import React, { useState, useCallback, useRef } from "react";
import { UploadCloud, FileText, X, Loader2, Sparkles, AlertTriangle, Scale } from "lucide-react";

const LEGAL_DISCLAIMER =
  "Disclaimer: ContractIQ is an AI-powered contract analysis tool and does not provide legal advice. Results are for informational purposes only. Consult a licensed attorney for official legal counsel.";

interface ContractUploadZoneProps {
  onAnalysisComplete: (result: any) => void;
  onAnalysisStart: () => void;
  apiBaseUrl: string;
  apiKey?: string;
  usageCount: number;
  freeLimit: number;
  onUpgradeCta: () => void;
}

export const ContractUploadZone: React.FC<ContractUploadZoneProps> = ({
  onAnalysisComplete,
  onAnalysisStart,
  apiBaseUrl,
  apiKey,
  usageCount,
  freeLimit,
  onUpgradeCta,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState<string>("");
  const [error, setError] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const remaining = freeLimit - usageCount;
  const isLimitReached = usageCount >= freeLimit;

  const handleFile = useCallback((file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setError("File must be under 25MB.");
      return;
    }
    setError("");
    setSelectedFile(file);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleAnalyze = async () => {
    if (!selectedFile || isAnalyzing || isLimitReached) return;

    setIsAnalyzing(true);
    setError("");
    onAnalysisStart();

    const progressSteps = [
      "Extracting contract text…",
      "Identifying parties & contract type…",
      "Scanning for red flag clauses…",
      "Calculating risk score…",
      "Generating plain-English summary…",
      "Building obligations list…",
      "Generating your PDF report…",
    ];

    let step = 0;
    setProgress(progressSteps[0]);
    const progressInterval = setInterval(() => {
      step = (step + 1) % progressSteps.length;
      setProgress(progressSteps[step]);
    }, 3500);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (apiKey) formData.append("api_key", apiKey);

      const headers: Record<string, string> = {};
      if (apiKey) headers["X-API-Key"] = apiKey;

      const res = await fetch(`${apiBaseUrl}/contract/analyze`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (res.status === 429) {
        const data = await res.json();
        const msg = data?.detail?.message || "Free tier limit reached. Upgrade to Pro.";
        setError(msg);
        onUpgradeCta();
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `Analysis failed (${res.status})`);
      }

      const result = await res.json();
      onAnalysisComplete(result);

      // Save to localStorage history
      try {
        const historyKey = "contractiq_history";
        const existing = JSON.parse(localStorage.getItem(historyKey) || "[]");
        existing.unshift({
          id:          result.analysis_id,
          share_token: result.share_token,
          filename:    result.filename,
          risk_score:  result.risk_score,
          risk_level:  result.risk_level,
          contract_type: result.contract_type,
          analyzed_at: new Date().toISOString(),
        });
        localStorage.setItem(historyKey, JSON.stringify(existing.slice(0, 50)));

        // Update usage count
        const usageKey = "contractiq_usage_count";
        const prev = parseInt(localStorage.getItem(usageKey) || "0", 10);
        localStorage.setItem(usageKey, String(prev + 1));
      } catch (_) {}

      setSelectedFile(null);
    } catch (err: any) {
      setError(err.message || "Analysis failed. Please try again.");
    } finally {
      clearInterval(progressInterval);
      setIsAnalyzing(false);
      setProgress("");
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-5">
      {/* Drop Zone */}
      <div
        className={`upload-drop-zone rounded-2xl p-10 text-center cursor-pointer transition-all ${
          isDragging ? "dragging" : ""
        } ${selectedFile ? "border-blue-500/60 bg-blue-950/10" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isAnalyzing && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        {isAnalyzing ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="relative">
                <div className="w-16 h-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
                <Scale className="absolute inset-0 m-auto w-7 h-7 text-blue-400" />
              </div>
            </div>
            <p className="text-blue-300 font-semibold text-sm">{progress}</p>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden max-w-xs mx-auto">
              <div className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full shimmer" style={{width: "100%"}} />
            </div>
            <p className="text-slate-500 text-xs">This may take 15–60 seconds for large contracts</p>
          </div>
        ) : selectedFile ? (
          <div className="space-y-3">
            <div className="flex items-center justify-center gap-3 p-4 rounded-xl bg-blue-950/30 border border-blue-500/30 max-w-sm mx-auto">
              <FileText className="w-8 h-8 text-blue-400 shrink-0" />
              <div className="text-left min-w-0">
                <p className="text-sm font-semibold text-blue-200 truncate">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB · PDF</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                className="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors shrink-0"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-slate-400 text-xs">Click to choose a different file</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 animate-float">
                <UploadCloud className="w-12 h-12 text-blue-400" />
              </div>
            </div>
            <div>
              <p className="text-lg font-bold text-white mb-1">
                Drop your contract PDF here
              </p>
              <p className="text-slate-400 text-sm">
                or <span className="text-blue-400 font-semibold cursor-pointer hover:text-blue-300">click to browse</span> · Max 25MB
              </p>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-slate-500">
              <span>✓ Service Agreements</span>
              <span>✓ NDAs</span>
              <span>✓ Leases</span>
              <span>✓ Employment Contracts</span>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-950/40 border border-red-500/30 text-sm text-red-300 animate-slide-up">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Analyze Button */}
      <div className="space-y-3">
        {isLimitReached ? (
          <button
            onClick={onUpgradeCta}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-bold text-base shadow-lg shadow-amber-900/30 transition-all active:scale-95"
          >
            🔒 Upgrade to Pro — Unlimited Analyses · $19/month
          </button>
        ) : (
          <button
            onClick={handleAnalyze}
            disabled={!selectedFile || isAnalyzing}
            className={`w-full py-4 rounded-xl font-bold text-base text-white shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2 ${
              !selectedFile || isAnalyzing
                ? "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 shadow-blue-900/40"
            }`}
          >
            {isAnalyzing ? (
              <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing…</>
            ) : (
              <><Scale className="w-5 h-5" /> Analyze Contract — Get Risk Score & Red Flags</>
            )}
          </button>
        )}

        {/* Free Tier Badge */}
        {!isLimitReached && (
          <div className="flex items-center justify-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs text-slate-400">
              <span className="text-amber-300 font-semibold">{remaining}</span> free {remaining === 1 ? "analysis" : "analyses"} remaining · No credit card required
            </span>
          </div>
        )}
      </div>

      {/* Legal Disclaimer (Guardrail 1) */}
      <p className="text-[10px] text-slate-600 text-center leading-relaxed px-4">
        {LEGAL_DISCLAIMER}
      </p>
    </div>
  );
};
