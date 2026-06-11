"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { CitationPopover } from "./CitationPopover";
import type { LevelResult, RuleResult } from "@/types";

function RuleIcon({ rule }: { rule: RuleResult }) {
  if (!rule.passed && !rule.flagged) {
    return <XCircle className="w-5 h-5 text-red-500" />;
  }
  if (rule.flagged || !rule.passed) {
    return <AlertTriangle className="w-5 h-5 text-amber-500" />;
  }
  return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
}

function ruleStatusLabel(rule: RuleResult): string {
  if (!rule.passed && !rule.flagged) return "Failed";
  if (rule.flagged) return "Flagged";
  return "Passed";
}

const levelColors: Record<number, string> = {
  1: "border-l-blue-500",
  2: "border-l-indigo-500",
  3: "border-l-violet-500",
  4: "border-l-purple-500",
};

interface LevelChecklistProps {
  levels: LevelResult[];
}

export function LevelChecklist({ levels }: LevelChecklistProps) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: true,
    4: true,
  });

  return (
    <div className="space-y-4">
      {levels.map((level) => (
        <div
          key={level.level}
          className={`bg-white rounded-xl border border-slate-200 border-l-4 ${levelColors[level.level]} overflow-hidden`}
        >
          <button
            type="button"
            onClick={() =>
              setExpanded((e) => ({ ...e, [level.level]: !e[level.level] }))
            }
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-slate-100 text-xs font-bold text-slate-600">
                L{level.level}
              </span>
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-900">
                  Level {level.level}: {level.level_name}
                </p>
                <p className="text-xs text-slate-500">
                  {level.rules.length} rule
                  {level.rules.length !== 1 ? "s" : ""} evaluated
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {level.all_passed && !level.any_flagged ? (
                <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  All passed
                </span>
              ) : level.any_flagged ? (
                <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                  Review needed
                </span>
              ) : (
                <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                  Failed
                </span>
              )}
              <ChevronDown
                className={`w-4 h-4 text-slate-400 transition-transform ${
                  expanded[level.level] ? "rotate-180" : ""
                }`}
              />
            </div>
          </button>

          {expanded[level.level] && (
            <div className="border-t border-slate-100 divide-y divide-slate-50">
              {level.rules.map((rule) => (
                <div
                  key={rule.rule_id}
                  className="flex items-start gap-3 px-4 py-3 hover:bg-slate-50/50"
                >
                  <CitationPopover rule={rule}>
                    <RuleIcon rule={rule} />
                  </CitationPopover>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-slate-800">
                        {rule.rule_name}
                      </p>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                          !rule.passed && !rule.flagged
                            ? "bg-red-50 text-red-600"
                            : rule.flagged
                              ? "bg-amber-50 text-amber-600"
                              : "bg-emerald-50 text-emerald-600"
                        }`}
                      >
                        {ruleStatusLabel(rule)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 font-mono">
                      {rule.rule_id}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
