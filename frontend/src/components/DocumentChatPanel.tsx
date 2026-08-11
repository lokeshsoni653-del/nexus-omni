"use client";

import React, { useState } from "react";
import { MessageSquare, Send, X, Bot, User, Sparkles, FileText, Loader2, BookOpen } from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  sources?: Array<{ id: string; snippet: string }>;
  timestamp: string;
}

interface DocumentChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl?: string;
  apiKey?: string;
}

export const DocumentChatPanel: React.FC<DocumentChatPanelProps> = ({
  isOpen,
  onClose,
  apiBaseUrl = "https://omnimind-backend-u94t.onrender.com",
  apiKey = "",
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "ai",
      text: "Hello! I am your OmniMind PDF Document Intelligence Assistant. Ask me any question about your ingested enterprise PDFs, policies, or SLAs!",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isSending, setIsSending] = useState(false);

  if (!isOpen) return null;

  const handleSendMessage = async () => {
    if (!inputQuery.trim() || isSending) return;

    const userText = inputQuery.trim();
    setInputQuery("");

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsSending(true);

    const targetUrl = apiBaseUrl || "https://omnimind-backend-u94t.onrender.com";

    try {
      const response = await fetch(`${targetUrl}/chat/document-qa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userText, api_key: apiKey || undefined }),
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();

      const aiMessage: Message = {
        id: `ai_${Date.now()}`,
        sender: "ai",
        text: data.answer,
        sources: data.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: `err_${Date.now()}`,
        sender: "ai",
        text: `Error querying document store: ${err.message || "Failed to reach backend server"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md glass-panel bg-[#0d1322]/95 border-l border-white/10 shadow-2xl flex flex-col transition-all">
      {/* Drawer Header */}
      <div className="h-16 px-5 border-b border-white/10 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-teal-500/20 text-teal-300 border border-teal-500/30">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
              <span>Document Q&A Chat</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30 font-medium">
                Live RAG
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">Ask questions directly about uploaded PDFs</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.sender === "ai" && (
              <div className="w-8 h-8 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-300 shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[82%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                msg.sender === "user"
                  ? "bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-br-none"
                  : "bg-slate-900/90 border border-white/10 text-slate-200 rounded-bl-none shadow-lg"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {/* Source Excerpts if available */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-white/10 space-y-1.5">
                  <div className="flex items-center gap-1 text-[10px] font-semibold text-teal-400">
                    <BookOpen className="w-3 h-3" />
                    <span>Retrieved Knowledge Citations:</span>
                  </div>
                  {msg.sources.map((s, i) => (
                    <div key={i} className="text-[10px] p-2 rounded-lg bg-teal-950/40 border border-teal-500/20 text-slate-300">
                      <span className="font-semibold text-teal-300">[{s.id}]:</span> "{s.snippet}"
                    </div>
                  ))}
                </div>
              )}

              <span className="block text-[9px] text-slate-400 text-right mt-1.5 opacity-70">
                {msg.timestamp}
              </span>
            </div>

            {msg.sender === "user" && (
              <div className="w-8 h-8 rounded-xl bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-300 shrink-0 mt-0.5">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isSending && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-300 shrink-0 animate-pulse">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="bg-slate-900/90 border border-white/10 p-3.5 rounded-2xl text-xs text-teal-300 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Searching ChromaDB & synthesizing AI response...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Form Footer */}
      <div className="p-4 border-t border-white/10 bg-slate-900/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a question about your PDF documents..."
            className="flex-1 h-10 px-3.5 rounded-xl bg-slate-950/80 border border-white/10 focus:border-teal-400 focus:ring-1 focus:ring-teal-400 text-xs text-slate-100 placeholder-slate-500 outline-none transition-all"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isSending}
            className={`h-10 px-4 rounded-xl font-semibold text-xs text-white shadow-lg flex items-center justify-center gap-1.5 transition-all ${
              !inputQuery.trim() || isSending
                ? "bg-teal-900/40 text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 shadow-teal-500/20"
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
