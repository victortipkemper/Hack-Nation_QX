"use client";

import { Clock, Fingerprint, Shield, Zap } from "lucide-react";
import { LevelChecklist } from "./LevelChecklist";
import { VerdictBadge } from "./VerdictBadge";
import type { TestPlanResult } from "@/types";

interface ComplianceDashboardProps {
  result: TestPlanResult;
  loading?: boolean;
}

export function ComplianceDashboard({
  result,
  loading,
}: ComplianceDashboardProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-500">Executing deterministic test plan…</p>
      </div>
    );
  }

  const { final_verdict: verdict } = result;

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-brand-600" />
          <h2 className="text-lg font-bold text-slate-900">
            Compliance Audit Dashboard
          </h2>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Final Verdict
            </p>
            <VerdictBadge status={verdict.status} />
          </div>
          <div className="space-y-2 text-sm">
            <p className="text-slate-700 leading-relaxed max-w-lg">
              {verdict.summary}
            </p>
            <div className="flex flex-wrap gap-3 text-xs text-slate-500">
              <span className="inline-flex items-center gap-1">
                <Fingerprint className="w-3.5 h-3.5" />
                {verdict.audit_trail_id}
              </span>
              <span className="inline-flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {new Date(result.executed_at).toLocaleString("de-DE")}
              </span>
              {verdict.deterministic && (
                <span className="inline-flex items-center gap-1 text-brand-600 font-medium">
                  <Zap className="w-3.5 h-3.5" />
                  Deterministic — no LLM inference
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-500" />
          4-Level Regulatory Test Plan
        </h3>
        <LevelChecklist levels={result.levels} />
      </div>
    </div>
  );
}
