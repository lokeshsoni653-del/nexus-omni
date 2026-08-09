"use client";

import React, { useState } from 'react';
import { Key, User, Lock, Mail, X, CheckCircle2, ShieldCheck, LogIn, UserPlus } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  apiBaseUrl?: string;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  apiKey,
  onApiKeyChange,
  apiBaseUrl = 'http://localhost:8000',
}) => {
  const [tab, setTab] = useState<'apikey' | 'login' | 'signup'>('apikey');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    try {
      const res = await fetch(`${apiBaseUrl}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Signup failed');
      onApiKeyChange(data.api_key);
      setStatusMsg(`Account created! API Key configured: ${data.api_key.slice(0, 10)}...`);
      setTimeout(onClose, 1500);
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    try {
      const res = await fetch(`${apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      onApiKeyChange(data.api_key);
      setStatusMsg(`Welcome back, ${data.name}! API Key set.`);
      setTimeout(onClose, 1500);
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-md glass-panel rounded-2xl border border-white/10 p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-white/10 pb-3 mb-4">
          <button
            onClick={() => setTab('apikey')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              tab === 'apikey'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-3.5 h-3.5" /> API Key Auth
          </button>
          <button
            onClick={() => setTab('login')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              tab === 'login'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LogIn className="w-3.5 h-3.5" /> Login
          </button>
          <button
            onClick={() => setTab('signup')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              tab === 'signup'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" /> Register SaaS
          </button>
        </div>

        {/* API Key View */}
        {tab === 'apikey' && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-base text-slate-100">Multi-Tenant API Key Authentication</h3>
                <p className="text-xs text-slate-400">Isolate workflows, RAG documents, and PDF exports</p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Active X-API-Key</label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => onApiKeyChange(e.target.value)}
                placeholder="Enter custom X-API-Key or leave empty for dev mode..."
                className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-purple-200 font-mono focus:border-purple-500 outline-none"
              />
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              When using Dev Mode (empty key), requests automatically authenticate as <code className="text-purple-300">dev@omnimind.local</code>.
            </p>

            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs shadow-lg shadow-purple-900/30 transition-all"
            >
              Save & Continue
            </button>
          </div>
        )}

        {/* Login View */}
        {tab === 'login' && (
          <form onSubmit={handleLogin} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@enterprise.com"
                className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-100 outline-none focus:border-sky-500"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-lg shadow-sky-900/30 transition-all"
            >
              Sign In to SaaS Platform
            </button>
          </form>
        )}

        {/* Signup View */}
        {tab === 'signup' && (
          <form onSubmit={handleSignup} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Alice Executive"
                className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-100 outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alice@enterprise.com"
                className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-100 outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-100 outline-none focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-lg shadow-emerald-900/30 transition-all"
            >
              Register & Generate API Key
            </button>
          </form>
        )}

        {statusMsg && (
          <div className="mt-3 p-2.5 rounded bg-slate-900 border border-white/10 text-xs text-purple-300 font-mono text-center">
            {statusMsg}
          </div>
        )}
      </div>
    </div>
  );
};
