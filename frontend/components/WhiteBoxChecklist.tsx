"use client";

import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleSlash,
  AlertTriangle,
  XCircle,
  ListChecks,
  Info,
  Loader2,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { useState } from "react";
import type { ChecklistExecution, RuleResult, WhiteBoxStep } from "@/types";

export type ExpertDecision = "approve" | "reject";

interface WhiteBoxChecklistProps {
  execution: ChecklistExecution | null;
  loading?: boolean;
  selectedCheckId?: string | null;
  onInspectCheck?: (rule: RuleResult) => void;
  onExpertReview?: (
    step: WhiteBoxStep,
    decision: ExpertDecision
  ) => Promise<void>;
}

function isErrorFinding(step: WhiteBoxStep): boolean {
  return (
    (step.severity ?? "error") === "error" &&
    step.executed &&
    (step.flagged || step.passed === false)
  );
}

function isAdvisoryNote(step: WhiteBoxStep): boolean {
  return step.severity === "advisory" && step.executed;
}

function stepToRule(step: WhiteBoxStep): RuleResult {
  return {
    rule_id: step.check_id,
    rule_name: step.check_name,
    passed: step.passed ?? true,
    flagged: step.flagged,
    citation: step.citation,
    reason: step.reason || step.evidence,
  };
}

function StepIcon({ step }: { step: WhiteBoxStep }) {
  if (!step.applicable) {
    return <CircleSlash className="w-4 h-4 text-slate-300 shrink-0" />;
  }
  if (!step.executed) {
    return <CircleSlash className="w-4 h-4 text-slate-400 shrink-0" />;
  }
  if (isErrorFinding(step)) {
    return <XCircle className="w-4 h-4 text-red-500 shrink-0" />;
  }
  if (isAdvisoryNote(step)) {
    return <Info className="w-4 h-4 text-blue-500 shrink-0" />;
  }
  return <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />;
}

function StepRow({
  step,
  selected,
  onInspect,
  onExpertReview,
}: {
  step: WhiteBoxStep;
  selected: boolean;
  onInspect?: (rule: RuleResult) => void;
  onExpertReview?: (
    step: WhiteBoxStep,
    decision: ExpertDecision
  ) => Promise<void>;
}) {
  const errorFinding = isErrorFinding(step);
  const [open, setOpen] = useState(selected || errorFinding);
  const [reviewState, setReviewState] = useState<
    "idle" | "saving" | "rejected"
  >("idle");

  const handleReview = async (decision: ExpertDecision) => {
    if (!onExpertReview || reviewState === "saving") return;
    setReviewState("saving");
    try {
      await onExpertReview(step, decision);
      setReviewState(decision === "reject" ? "rejected" : "idle");
    } catch {
      setReviewState("idle");
    }
  };

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-colors ${
        selected
          ? "border-amber-300 bg-amber-50/50"
          : errorFinding
            ? "border-red-100 bg-red-50/30"
            : isAdvisoryNote(step)
              ? "border-blue-100 bg-blue-50/20"
              : "border-slate-100 bg-white"
      }`}
    >
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          if (errorFinding && onInspect) onInspect(stepToRule(step));
        }}
        className="w-full flex items-start gap-2 px-3 py-2.5 text-left hover:bg-slate-50/80"
      >
        <span className="text-xs font-mono text-slate-400 w-6 shrink-0 pt-0.5">
          {step.step}
        </span>
        <StepIcon step={step} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-slate-500">{step.check_id}</span>
            {!step.applicable && (
              <span className="text-[10px] uppercase tracking-wide text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                n/a
              </span>
            )}
            {step.severity === "advisory" && step.applicable && (
              <span className="text-[10px] uppercase tracking-wide text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                Hinweis
              </span>
            )}
            {step.expert_override && (
              <span className="text-[10px] uppercase tracking-wide text-emerald-700 bg-emerald-50 border border-emerald-100 px-1.5 py-0.5 rounded">
                Expertenwissen
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-slate-800 leading-snug">
            {step.check_name}
          </p>
        </div>
        {open ? (
          <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-3 pb-3 pt-0 ml-12 space-y-2 text-xs border-t border-slate-100/80">
          <div>
            <span className="font-semibold text-slate-500">Anwendbarkeit: </span>
            <span className="text-slate-700">{step.applicability_reason}</span>
          </div>

          {step.skipped_reason && (
            <div className="text-slate-500 italic">{step.skipped_reason}</div>
          )}

          {step.executed && (
            <>
              <div>
                <span className="font-semibold text-slate-500">Nachweis: </span>
                <span className="text-slate-700">{step.evidence}</span>
              </div>
              <div className="text-slate-500 font-mono text-[11px]">
                {step.citation}
              </div>
            </>
          )}

          {step.remediation_hint && errorFinding && (
            <div className="flex gap-2 p-2.5 bg-blue-50 border border-blue-100 rounded-md">
              <AlertTriangle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-blue-800 mb-0.5">
                  Korrekturhinweis
                </p>
                <p className="text-blue-900 leading-relaxed">
                  {step.remediation_hint}
                </p>
                {step.exemplar_reference && (
                  <p className="text-blue-700/70 mt-1">
                    Referenz: {step.exemplar_reference}
                  </p>
                )}
              </div>
            </div>
          )}

          {errorFinding && onExpertReview && reviewState !== "rejected" && (
            <div className="flex items-center gap-2 flex-wrap pt-1">
              <span className="font-semibold text-slate-500">
                Experten-Bewertung:
              </span>
              <button
                type="button"
                disabled={reviewState === "saving"}
                onClick={(e) => {
                  e.stopPropagation();
                  void handleReview("approve");
                }}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-emerald-200 bg-emerald-50 text-emerald-800 font-medium hover:bg-emerald-100 disabled:opacity-50"
              >
                {reviewState === "saving" ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ThumbsUp className="w-3.5 h-3.5" />
                )}
                In Ordnung — als zulässig lernen
              </button>
              <button
                type="button"
                disabled={reviewState === "saving"}
                onClick={(e) => {
                  e.stopPropagation();
                  void handleReview("reject");
                }}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-red-200 bg-red-50 text-red-700 font-medium hover:bg-red-100 disabled:opacity-50"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
                Beanstandung bestätigen
              </button>
            </div>
          )}

          {errorFinding && reviewState === "rejected" && (
            <div className="flex items-center gap-1.5 pt-1 text-red-700">
              <ThumbsDown className="w-3.5 h-3.5 shrink-0" />
              <span>
                Beanstandung bestätigt — nicht in die Wissensdatenbank
                übernommen.
              </span>
            </div>
          )}

          {step.expert_override && (
            <div className="flex items-center gap-1.5 pt-1 text-emerald-700">
              <ThumbsUp className="w-3.5 h-3.5 shrink-0" />
              <span>
                Von einem Experten als zulässig bewertet
                {step.expert_override_id
                  ? ` (Eintrag ${step.expert_override_id})`
                  : ""}
                .
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function WhiteBoxChecklist({
  execution,
  loading,
  selectedCheckId,
  onInspectCheck,
  onExpertReview,
}: WhiteBoxChecklistProps) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-14 bg-slate-100 rounded-lg" />
        ))}
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-sm text-slate-500 gap-3 px-4 text-center">
        <ListChecks className="w-8 h-8 text-slate-300" />
        <p>White-Box-Checkliste nicht geladen.</p>
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
          PDF erneut hochladen. Falls das nicht hilft: API auf Port 8000 neu
          starten — die alte Version liefert keine Checkliste.
        </p>
      </div>
    );
  }

  const levels = [1, 2, 3, 4] as const;
  const levelLabels: Record<number, string> = {
    1: "L1 — StVZO",
    2: "L2 — Merkblatt 751",
    3: "L3 — TÜV-Praxis",
    4: "L4 — Konsens",
  };

  const totalErrors = execution.steps.filter(isErrorFinding).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 text-xs text-slate-500 bg-slate-50 border border-slate-100 rounded-lg px-3 py-2">
        <span>
          Checkliste v{execution.checklist_version} — {execution.executed_checks}/
          {execution.applicable_checks} Prüfungen ausgeführt
          {totalErrors > 0 && (
            <span className="ml-2 text-red-600 font-medium">
              · {totalErrors} Beanstandung{totalErrors > 1 ? "en" : ""}
            </span>
          )}
        </span>
        <span className="font-mono">{execution.total_checks} Schritte gesamt</span>
      </div>

      {levels.map((level) => {
        const steps = execution.steps.filter((s) => s.level === level);
        if (!steps.length) return null;
        const flagged = steps.filter(isErrorFinding).length;

        return (
          <div key={level}>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                {levelLabels[level]}
              </h3>
              {flagged > 0 && (
                <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
                  {flagged} Beanstandung{flagged > 1 ? "en" : ""}
                </span>
              )}
            </div>
            <div className="space-y-1.5">
              {steps.map((step) => (
                <StepRow
                  key={step.check_id}
                  step={step}
                  selected={selectedCheckId === step.check_id}
                  onInspect={onInspectCheck}
                  onExpertReview={onExpertReview}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
