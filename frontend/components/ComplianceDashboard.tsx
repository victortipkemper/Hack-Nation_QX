"use client";

import { Clock, Fingerprint, Shield, Zap } from "lucide-react";
import { LevelChecklist } from "./LevelChecklist";
import { VerdictBadge } from "./VerdictBadge";
import type { RuleResult, TestPlanResult } from "@/types";

interface ComplianceDashboardProps {
  result: TestPlanResult;
  loading?: boolean;
  selectedRuleId?: string | null;
  onInspectRule?: (rule: RuleResult) => void;
}

export function ComplianceDashboard({
  result,
  loading,
  selectedRuleId,
  onInspectRule,
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
  const inspectableRules = result.levels.flatMap((l) =>
    l.rules.filter((r) => r.flagged || !r.passed)
  );
  const hasInspectable = inspectableRules.length > 0;

  const handleSummaryClick = () => {
    if (hasInspectable && onInspectRule) {
      onInspectRule(inspectableRules[0]);
    }
  };

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
            <p
              className={`text-slate-700 leading-relaxed max-w-lg ${
                hasInspectable
                  ? "cursor-pointer hover:text-amber-800 hover:underline decoration-amber-400 decoration-2 underline-offset-2 transition-colors"
                  : ""
              }`}
              onClick={handleSummaryClick}
              onKeyDown={(e) => {
                if (hasInspectable && (e.key === "Enter" || e.key === " ")) {
                  e.preventDefault();
                  handleSummaryClick();
                }
              }}
              role={hasInspectable ? "button" : undefined}
              tabIndex={hasInspectable ? 0 : undefined}
              title={
                hasInspectable
                  ? "Klicken, um erste Fehlerstelle im Gutachten zu öffnen"
                  : undefined
              }
            >
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

        {hasInspectable && (
          <p className="mt-3 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
            Klicke auf eine markierte oder fehlgeschlagene Regel, um die
            betroffene Stelle im Gutachten-Dokument mit AI-Erläuterung zu sehen.
          </p>
        )}
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-500" />
          4-Level Regulatory Test Plan
        </h3>
        <LevelChecklist
          levels={result.levels}
          selectedRuleId={selectedRuleId}
          onInspectRule={onInspectRule}
        />
      </div>
    </div>
  );
}
