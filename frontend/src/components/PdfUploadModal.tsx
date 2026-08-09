"use client";

import React, { useState } from 'react';
import { UploadCloud, FileText, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

interface PdfUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPdfUploaded: (docId: string, filename: string) => void;
  apiBaseUrl?: string;
}

export const PdfUploadModal: React.FC<PdfUploadModalProps> = ({
  isOpen,
  onClose,
  onPdfUploaded,
  apiBaseUrl = 'http://localhost:8000',
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setStatusMsg({ type: 'error', text: 'Please select a valid .pdf file.' });
        return;
      }
      setFile(selected);
      setStatusMsg(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setStatusMsg(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiBaseUrl}/upload-pdf`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload PDF document');
      }

      const data = await response.json();
      const doc = data.document;
      setStatusMsg({
        type: 'success',
        text: `Ingested '${doc.filename}' into ChromaDB! ID: ${doc.id.slice(0, 8)}...`,
      });

      onPdfUploaded(doc.id, doc.filename);
      setTimeout(() => {
        setFile(null);
        onClose();
      }, 1500);
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Error uploading file to server.' });
    } finally {
      setIsUploading(false);
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

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-teal-500/20 text-teal-300 border border-teal-500/30">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-100">Upload PDF to RAG Store</h3>
            <p className="text-xs text-slate-400">Ingest document into ChromaDB vector knowledge base</p>
          </div>
        </div>

        {/* Upload Zone */}
        <div className="mt-4 border-2 border-dashed border-teal-500/30 hover:border-teal-400 rounded-xl p-6 text-center bg-teal-950/20 transition-all cursor-pointer relative">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
          <UploadCloud className="w-10 h-10 mx-auto text-teal-400 mb-2 animate-bounce" />
          {file ? (
            <div>
              <p className="text-xs font-semibold text-teal-200">{file.name}</p>
              <p className="text-[10px] text-slate-400 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div>
              <p className="text-xs font-medium text-slate-200">Click or drag PDF file here</p>
              <p className="text-[10px] text-slate-400 mt-1">Supports enterprise policies, manuals & reports</p>
            </div>
          )}
        </div>

        {/* Status Alert */}
        {statusMsg && (
          <div
            className={`mt-4 p-3 rounded-lg text-xs flex items-center gap-2 border ${
              statusMsg.type === 'success'
                ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
            }`}
          >
            {statusMsg.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            )}
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Actions */}
        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className={`px-4 py-2 rounded-lg text-xs font-semibold text-white shadow-lg flex items-center gap-2 ${
              !file || isUploading
                ? 'bg-teal-900/50 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 shadow-teal-500/20'
            }`}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Ingesting to ChromaDB...
              </>
            ) : (
              'Ingest PDF Document'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
