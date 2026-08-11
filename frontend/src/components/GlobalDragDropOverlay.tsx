"use client";

import React, { useState, useEffect, useCallback } from "react";
import { UploadCloud, FileText, Sparkles } from "lucide-react";

interface GlobalDragDropOverlayProps {
  onFileDropped: (file: File) => void;
}

export const GlobalDragDropOverlay: React.FC<GlobalDragDropOverlayProps> = ({ onFileDropped }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer && e.dataTransfer.types.includes("Files")) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only turn off if leaving window bounds
    if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.toLowerCase().endsWith(".pdf")) {
        onFileDropped(droppedFile);
      }
    }
  }, [onFileDropped]);

  useEffect(() => {
    window.addEventListener("dragover", handleDragOver);
    window.addEventListener("dragleave", handleDragLeave);
    window.addEventListener("drop", handleDrop);

    return () => {
      window.removeEventListener("dragover", handleDragOver);
      window.removeEventListener("dragleave", handleDragLeave);
      window.removeEventListener("drop", handleDrop);
    };
  }, [handleDragOver, handleDragLeave, handleDrop]);

  if (!isDragging) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-slate-950/85 backdrop-blur-lg flex flex-col items-center justify-center p-6 border-4 border-dashed border-teal-400 animate-fade-in pointer-events-none">
      <div className="p-5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-400/40 mb-4 animate-bounce">
        <UploadCloud className="w-16 h-16 text-teal-300" />
      </div>

      <div className="flex items-center gap-2 text-teal-300 font-bold text-2xl mb-2">
        <Sparkles className="w-6 h-6 animate-pulse" />
        <span>Drop PDF Document Anywhere to Auto-Ingest</span>
      </div>

      <p className="text-slate-300 text-sm max-w-md text-center">
        Release your file anywhere on Chrome to automatically ingest into your enterprise ChromaDB vector store.
      </p>

      <div className="mt-6 flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-semibold">
        <FileText className="w-4 h-4" />
        <span>Supports PDF policies, financial reports & contracts</span>
      </div>
    </div>
  );
};
