"use client";

import { useCallback, useEffect, useState } from "react";
import { CaseSelector } from "@/components/CaseSelector";
import { ComplianceDashboard } from "@/components/ComplianceDashboard";
import { GutachtenViewer } from "@/components/GutachtenViewer";
import { analyzeGutachten, fetchCase, fetchCases } from "@/lib/api";
import type { CaseSummary, Gutachten, TestPlanResult } from "@/types";

export default function HomePage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [gutachten, setGutachten] = useState<Gutachten | null>(null);
  const [result, setResult] = useState<TestPlanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectCase = useCallback(async (caseId: string) => {
    setSelectedId(caseId);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const g = await fetchCase(caseId);
      setGutachten(g);
      const analysis = await analyzeGutachten(g);
      setResult(analysis);
    } catch {
      setError("Analysis failed. Ensure the API is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases()
      .then((data) => {
        setCases(data);
        if (data.length > 0) {
          handleSelectCase(data[0].id);
        }
      })
      .catch(() =>
        setError("Failed to load reference cases. Is the API running?")
      );
  }, [handleSelectCase]);

  return (
    <div className="flex h-screen overflow-hidden">
      <CaseSelector
        cases={cases}
        selectedId={selectedId}
        onSelect={handleSelectCase}
        loading={loading}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="shrink-0 px-6 py-4 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                TÜV Inspector Workspace
              </h2>
              <p className="text-sm text-slate-500">
                Vehicle homologation compliance audit — wheels, tires &amp;
                Einzelabnahme
              </p>
            </div>
            {gutachten && (
              <div className="text-right hidden sm:block">
                <p className="text-xs text-slate-400">Gutachten ID</p>
                <p className="text-sm font-mono text-slate-600">
                  {gutachten.gutachten_id}
                </p>
              </div>
            )}
          </div>
        </header>

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden">
          <div className="h-full grid grid-cols-1 lg:grid-cols-2 gap-0 divide-x divide-slate-200">
            <div className="overflow-y-auto p-6 scrollbar-thin bg-slate-50/50">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Left — Ingested Gutachten Data
              </p>
              {gutachten ? (
                <GutachtenViewer gutachten={gutachten} />
              ) : (
                <div className="flex items-center justify-center h-48 text-sm text-slate-400">
                  Select a reference case to load Gutachten data
                </div>
              )}
            </div>

            <div className="overflow-y-auto p-6 scrollbar-thin">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Right — Compliance Audit Dashboard
              </p>
              {result || loading ? (
                <ComplianceDashboard result={result!} loading={loading} />
              ) : (
                <div className="flex items-center justify-center h-48 text-sm text-slate-400">
                  Analysis results will appear here
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
