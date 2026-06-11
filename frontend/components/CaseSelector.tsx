"use client";

import { Car, ChevronRight } from "lucide-react";
import { VerdictBadge } from "./VerdictBadge";
import type { CaseSummary, VerdictStatus } from "@/types";

interface CaseSelectorProps {
  cases: CaseSummary[];
  selectedId: string | null;
  onSelect: (caseId: string) => void;
  loading?: boolean;
}

export function CaseSelector({
  cases,
  selectedId,
  onSelect,
  loading,
}: CaseSelectorProps) {
  return (
    <aside className="w-72 shrink-0 bg-white border-r border-slate-200 flex flex-col h-full">
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AC</span>
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900">Autocomply</h1>
            <p className="text-xs text-slate-500">Einzelabnahme Audit</p>
          </div>
        </div>
      </div>

      <div className="p-3 flex-1 overflow-y-auto scrollbar-thin">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2 mb-2">
          Reference Cases
        </p>
        <nav className="space-y-1">
          {cases.map((c) => {
            const isSelected = selectedId === c.id;
            return (
              <button
                key={c.id}
                type="button"
                onClick={() => onSelect(c.id)}
                disabled={loading}
                className={`w-full text-left rounded-lg p-3 transition-all group ${
                  isSelected
                    ? "bg-brand-50 border border-brand-200 shadow-sm"
                    : "hover:bg-slate-50 border border-transparent"
                } ${loading ? "opacity-50 cursor-wait" : ""}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0">
                    <Car
                      className={`w-4 h-4 mt-0.5 shrink-0 ${
                        isSelected ? "text-brand-600" : "text-slate-400"
                      }`}
                    />
                    <div className="min-w-0">
                      <p
                        className={`text-sm font-medium truncate ${
                          isSelected ? "text-brand-900" : "text-slate-800"
                        }`}
                      >
                        {c.title}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">
                        {c.vehicle_summary}
                      </p>
                    </div>
                  </div>
                  <ChevronRight
                    className={`w-4 h-4 shrink-0 mt-0.5 transition-transform ${
                      isSelected
                        ? "text-brand-500 translate-x-0.5"
                        : "text-slate-300 group-hover:text-slate-400"
                    }`}
                  />
                </div>
                <div className="mt-2 ml-6">
                  <VerdictBadge
                    status={c.expected_verdict as VerdictStatus}
                    size="sm"
                  />
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-200 bg-slate-50">
        <p className="text-xs text-slate-500 leading-relaxed">
          One Gutachten in, one auditable verdict out. Rules engine only — zero
          generative inference.
        </p>
      </div>
    </aside>
  );
}
