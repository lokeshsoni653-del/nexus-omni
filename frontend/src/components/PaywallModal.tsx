"use client";

import React from "react";
import { X, Scale, Zap, Check, ArrowRight } from "lucide-react";

interface PaywallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToPricing: () => void;
  freeLimit: number;
}

export const PaywallModal: React.FC<PaywallModalProps> = ({
  isOpen,
  onClose,
  onSwitchToPricing,
  freeLimit,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="relative w-full max-w-md glass-card p-7 rounded-2xl animate-slide-up border border-amber-500/20 shadow-2xl shadow-amber-900/20">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-all"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Icon */}
        <div className="flex justify-center mb-5">
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
            <Scale className="w-10 h-10 text-amber-400" />
          </div>
        </div>

        {/* Text */}
        <div className="text-center space-y-2 mb-6">
          <h2 className="text-xl font-black text-white">
            You've Used Your {freeLimit} Free Analyses
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Upgrade to <span className="text-amber-300 font-bold">ContractIQ Pro</span> for unlimited contract analysis, full PDF reports, and priority AI processing.
          </p>
        </div>

        {/* Pro Features */}
        <div className="space-y-2 mb-6">
          {[
            "Unlimited contract analyses",
            "Priority AI processing (faster results)",
            "Full branded PDF reports with every analysis",
            "Email report delivery to clients",
            "API access for automation",
          ].map((f, i) => (
            <div key={i} className="flex items-center gap-2.5 text-xs text-slate-300">
              <Check className="w-4 h-4 text-amber-400 shrink-0" />
              {f}
            </div>
          ))}
        </div>

        {/* Price */}
        <div className="flex items-baseline justify-center gap-1 mb-5">
          <span className="text-4xl font-black text-white">$19</span>
          <span className="text-slate-400 text-sm">/ month</span>
          <span className="ml-2 text-xs text-emerald-400 font-semibold">or $15/mo annually</span>
        </div>

        {/* CTAs */}
        <div className="space-y-2.5">
          <button
            onClick={onSwitchToPricing}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-bold text-sm shadow-lg shadow-amber-900/30 flex items-center justify-center gap-2 transition-all active:scale-95"
          >
            <Zap className="w-4 h-4" /> Upgrade to Pro — $19/month
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 text-sm transition-all"
          >
            Maybe later
          </button>
        </div>

        <p className="text-[10px] text-slate-600 text-center mt-4">
          Cancel anytime · No contracts · Data never sold
        </p>
      </div>
    </div>
  );
};
