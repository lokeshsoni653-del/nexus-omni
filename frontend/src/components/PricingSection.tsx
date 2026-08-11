"use client";

import React, { useState } from "react";
import { Check, Zap, Building2, User, Scale, ArrowRight } from "lucide-react";

const FREE_FEATURES = [
  "3 contract analyses per month",
  "Risk Score & Red Flag detection",
  "Plain English summary",
  "Key dates & obligations",
  "Shareable report links",
];

const PRO_FEATURES = [
  "Unlimited contract analyses",
  "Priority AI processing",
  "Full PDF download reports",
  "Advanced clause comparison",
  "Email report delivery",
  "API access",
  "All Free tier features",
];

const BUSINESS_FEATURES = [
  "Everything in Pro",
  "Team workspace (up to 20 users)",
  "White-label PDF reports",
  "Custom clause library",
  "Bulk contract analysis",
  "Dedicated support & SLA",
  "CRM / Zapier integrations",
];

interface PricingCard {
  id: string;
  name: string;
  price: string;
  period: string;
  annualNote?: string;
  description: string;
  features: string[];
  icon: React.ReactNode;
  ctaLabel: string;
  ctaAction: () => void;
  popular?: boolean;
  freeNote?: string;
}

interface PricingSectionProps {
  onGetStarted: () => void;
}

export const PricingSection: React.FC<PricingSectionProps> = ({ onGetStarted }) => {
  const [isAnnual, setIsAnnual] = useState(false);

  const cards: PricingCard[] = [
    {
      id:          "free",
      name:        "Free",
      price:       "$0",
      period:      "forever",
      description: "Perfect for freelancers reviewing occasional contracts.",
      features:    FREE_FEATURES,
      icon:        <User className="w-5 h-5" />,
      ctaLabel:    "Start Free — No Credit Card",
      ctaAction:   onGetStarted,
      freeNote:    "3 analyses / month",
    },
    {
      id:          "pro",
      name:        "Pro",
      price:       isAnnual ? "$15" : "$19",
      period:      "/ month",
      annualNote:  isAnnual ? "Billed $180/year · Save 21%" : undefined,
      description: "For consultants, startups, and teams reviewing contracts weekly.",
      features:    PRO_FEATURES,
      icon:        <Zap className="w-5 h-5" />,
      ctaLabel:    "Upgrade to Pro",
      ctaAction:   () => alert("Stripe checkout coming soon! Add STRIPE_KEY to Render to activate."),
      popular:     true,
    },
    {
      id:          "business",
      name:        "Business",
      price:       isAnnual ? "$39" : "$49",
      period:      "/ month",
      annualNote:  isAnnual ? "Billed $468/year · Save 20%" : undefined,
      description: "For law firms and procurement teams with high-volume needs.",
      features:    BUSINESS_FEATURES,
      icon:        <Building2 className="w-5 h-5" />,
      ctaLabel:    "Contact Sales",
      ctaAction:   () => alert("Contact us at hello@contractiq.ai"),
    },
  ];

  return (
    <div className="max-w-5xl mx-auto w-full space-y-8 py-4">
      {/* Heading */}
      <div className="text-center space-y-3">
        <div className="flex items-center justify-center gap-2 text-blue-400 text-sm font-semibold">
          <Scale className="w-4 h-4" />
          <span>Simple, Transparent Pricing</span>
        </div>
        <h2 className="text-3xl font-black text-white leading-tight">
          Start Free. <span className="gradient-text">Scale As You Grow.</span>
        </h2>
        <p className="text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
          Every plan includes AI-powered risk detection. Missing one bad clause can cost thousands — ContractIQ pays for itself with the first analysis.
        </p>

        {/* Annual / Monthly Toggle */}
        <div className="flex items-center justify-center gap-3 pt-2">
          <span className={`text-sm font-medium ${!isAnnual ? "text-white" : "text-slate-500"}`}>Monthly</span>
          <button
            onClick={() => setIsAnnual(!isAnnual)}
            className={`relative w-12 h-6 rounded-full transition-colors ${isAnnual ? "bg-blue-600" : "bg-slate-700"}`}
          >
            <span
              className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${isAnnual ? "translate-x-6" : "translate-x-0"}`}
            />
          </button>
          <span className={`text-sm font-medium ${isAnnual ? "text-white" : "text-slate-500"}`}>
            Annual <span className="text-emerald-400 text-xs font-bold">Save 20%</span>
          </span>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {cards.map((card) => (
          <div
            key={card.id}
            className={`relative flex flex-col rounded-2xl p-6 transition-all ${
              card.popular
                ? "pricing-card-popular scale-[1.02]"
                : "glass-card hover:border-white/15"
            }`}
          >
            {card.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[11px] font-bold shadow-lg shadow-blue-900/40">
                ★ Most Popular
              </div>
            )}

            {/* Header */}
            <div className="space-y-3 mb-6">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                card.popular ? "bg-blue-600/30 text-blue-300" : "bg-slate-800 text-slate-400"
              }`}>
                {card.icon}
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">{card.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{card.description}</p>
              </div>
              <div>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-black text-white">{card.price}</span>
                  <span className="text-sm text-slate-400">{card.period}</span>
                </div>
                {card.annualNote && (
                  <p className="text-[11px] text-emerald-400 mt-0.5">{card.annualNote}</p>
                )}
                {card.freeNote && (
                  <p className="text-[11px] text-slate-500 mt-0.5">{card.freeNote}</p>
                )}
              </div>
            </div>

            {/* Features */}
            <ul className="space-y-2.5 flex-1 mb-6">
              {card.features.map((f, i) => (
                <li key={i} className="flex items-center gap-2.5 text-xs text-slate-300">
                  <Check className={`w-4 h-4 shrink-0 ${card.popular ? "text-blue-400" : "text-emerald-500"}`} />
                  {f}
                </li>
              ))}
            </ul>

            {/* CTA */}
            <button
              onClick={card.ctaAction}
              className={`w-full py-3 rounded-xl text-sm font-bold transition-all active:scale-95 flex items-center justify-center gap-2 ${
                card.popular
                  ? "bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white shadow-lg shadow-blue-900/40"
                  : card.id === "free"
                  ? "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10"
              }`}
            >
              {card.ctaLabel}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Bottom Trust Strip */}
      <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs text-slate-500">
        <span>✓ No credit card for free tier</span>
        <span>✓ Cancel anytime</span>
        <span>✓ Data never sold or shared</span>
        <span>✓ SOC 2 compliant infrastructure</span>
      </div>

      {/* Legal Disclaimer */}
      <p className="text-[10px] text-slate-700 text-center leading-relaxed">
        Disclaimer: ContractIQ is an AI-powered contract analysis tool and does not provide legal advice.
        Results are for informational purposes only. Consult a licensed attorney for official legal counsel.
      </p>
    </div>
  );
};
