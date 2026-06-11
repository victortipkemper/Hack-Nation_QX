"use client";

import { FileText, Loader2, Plus, X } from "lucide-react";
import { DocumentUpload } from "./DocumentUpload";
import { VerdictBadge } from "./VerdictBadge";
import type { GutachtenSession } from "@/lib/uploadSession";
import { sessionLabel } from "@/lib/uploadSession";
import type { VerdictStatus } from "@/types";

interface CaseSelectorProps {
  sessions: GutachtenSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onRemoveSession: (sessionId: string) => void;
  onUploadFiles: (files: File[]) => Promise<void>;
  uploadingCount: number;
}

export function CaseSelector({
  sessions,
  activeSessionId,
  onSelectSession,
  onRemoveSession,
  onUploadFiles,
  uploadingCount,
}: CaseSelectorProps) {
  return (
    <aside className="w-72 shrink-0 bg-white border-r border-slate-200 flex flex-col h-full">
      <div className="p-4 border-b border-slate-200 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AC</span>
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900">Autocomply</h1>
            <p className="text-xs text-slate-500">Gutachten-Prüfung</p>
          </div>
        </div>
      </div>

      <DocumentUpload
        onUploadFiles={onUploadFiles}
        loading={uploadingCount > 0}
        loadingCount={uploadingCount}
      />

      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="px-3 pt-3 pb-1 flex items-center justify-between shrink-0">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Gutachten ({sessions.length})
          </p>
          {sessions.length > 0 && (
            <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
              <Plus className="w-3 h-3" />
              weitere hinzufügen
            </span>
          )}
        </div>

        {sessions.length === 0 ? (
          <div className="mx-3 p-4 rounded-lg bg-slate-50 border border-dashed border-slate-200 text-center">
            <p className="text-xs text-slate-500 leading-relaxed">
              Noch keine Gutachten. PDF(s) oben hochladen — jedes erscheint als
              eigener Tab.
            </p>
          </div>
        ) : (
          <nav className="flex-1 overflow-y-auto scrollbar-thin px-2 pb-2 space-y-1">
            {sessions.map((session) => {
              const isActive = activeSessionId === session.id;
              const verdict = session.result?.final_verdict.status;

              return (
                <div
                  key={session.id}
                  className={`group flex items-stretch rounded-lg border transition-all ${
                    isActive
                      ? "border-brand-300 bg-brand-50 shadow-sm"
                      : "border-transparent hover:bg-slate-50 hover:border-slate-200"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelectSession(session.id)}
                    disabled={session.status === "loading"}
                    className="flex-1 text-left px-3 py-2.5 min-w-0 disabled:opacity-70"
                  >
                    <div className="flex items-start gap-2">
                      {session.status === "loading" ? (
                        <Loader2 className="w-4 h-4 text-brand-500 animate-spin shrink-0 mt-0.5" />
                      ) : (
                        <FileText
                          className={`w-4 h-4 shrink-0 mt-0.5 ${
                            isActive ? "text-brand-600" : "text-slate-400"
                          }`}
                        />
                      )}
                      <div className="min-w-0 flex-1">
                        <p
                          className={`text-sm font-medium truncate ${
                            isActive ? "text-brand-900" : "text-slate-800"
                          }`}
                        >
                          {sessionLabel(session)}
                        </p>
                        {session.status === "error" ? (
                          <p className="text-[10px] text-red-600 mt-0.5 truncate">
                            {session.error ?? "Fehler"}
                          </p>
                        ) : session.status === "loading" ? (
                          <p className="text-[10px] text-slate-500 mt-0.5">
                            Analysiere…
                          </p>
                        ) : verdict ? (
                          <div className="mt-1.5">
                            <VerdictBadge
                              status={verdict as VerdictStatus}
                              size="sm"
                            />
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </button>
                  {session.status !== "loading" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveSession(session.id);
                      }}
                      className="shrink-0 px-2 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Entfernen"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </nav>
        )}
      </div>

      <div className="p-4 border-t border-slate-200 bg-slate-50 shrink-0">
        <p className="text-xs text-slate-500 leading-relaxed">
          Mehrere PDFs · je Tab eine White-Box-Checkliste
        </p>
      </div>
    </aside>
  );
}
