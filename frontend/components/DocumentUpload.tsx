"use client";

import { useCallback, useRef, useState } from "react";
import { FileUp, Loader2, Upload } from "lucide-react";

interface DocumentUploadProps {
  onUploadFiles: (files: File[]) => Promise<void>;
  loading?: boolean;
  loadingCount?: number;
}

export function DocumentUpload({
  onUploadFiles,
  loading,
  loadingCount = 0,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const pdfs = Array.from(fileList).filter((f) =>
        f.name.toLowerCase().endsWith(".pdf")
      );
      if (pdfs.length === 0) return;
      await onUploadFiles(pdfs);
    },
    [onUploadFiles]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const isBusy = loading || loadingCount > 0;

  return (
    <div className="p-3 border-b border-slate-200 bg-slate-50 shrink-0">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1 mb-2">
        Gutachten hochladen
      </p>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => !isBusy && inputRef.current?.click()}
        className={`rounded-lg border-2 border-dashed p-4 text-center cursor-pointer transition-all ${
          dragOver
            ? "border-brand-400 bg-brand-50"
            : "border-slate-200 hover:border-brand-300 hover:bg-white"
        } ${isBusy ? "opacity-60 cursor-wait" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) {
              handleFiles(e.target.files);
            }
            e.target.value = "";
          }}
        />
        {isBusy ? (
          <div className="flex flex-col items-center gap-2 py-1">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
            <p className="text-xs text-slate-600">
              {loadingCount > 1
                ? `${loadingCount} PDFs werden analysiert…`
                : "PDF wird analysiert…"}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-1">
            <div className="p-2 bg-brand-100 rounded-full">
              <Upload className="w-5 h-5 text-brand-600" />
            </div>
            <p className="text-sm font-medium text-slate-700">
              PDF(s) hier ablegen
            </p>
            <p className="text-xs text-slate-500 flex items-center gap-1">
              <FileUp className="w-3 h-3" />
              mehrere möglich · max. 20 MB
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
