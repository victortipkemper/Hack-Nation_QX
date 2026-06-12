"use client";

import { Database, FileSearch, LayoutPanelLeft, ListChecks } from "lucide-react";
import { ComplianceDashboard } from "./ComplianceDashboard";
import { DocumentViewer } from "./DocumentViewer";
import { GutachtenViewer } from "./GutachtenViewer";
import { WhiteBoxChecklist, type ExpertDecision } from "./WhiteBoxChecklist";
import type { GutachtenDocument } from "@/lib/documentAnnotations";
import type {
  ChecklistExecution,
  Gutachten,
  RuleResult,
  TestPlanResult,
  WhiteBoxStep,
} from "@/types";

type WorkspaceTab = "data" | "document" | "checklist";

interface InspectorWorkspaceProps {
  gutachten: Gutachten | null;
  result: TestPlanResult | null;
  checklistExecution: ChecklistExecution | null;
  document: GutachtenDocument | null;
  loading: boolean;
  inspectedRule: RuleResult | null;
  activeAnnotation: ReturnType<
    typeof import("@/lib/documentAnnotations").getAnnotationForRule
  >;
  onInspectRule: (rule: RuleResult) => void;
  onCloseDocument: () => void;
  workspaceTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
  onExpertReview?: (
    step: WhiteBoxStep,
    decision: ExpertDecision
  ) => Promise<void>;
}

export function InspectorWorkspace({
  gutachten,
  result,
  checklistExecution,
  document,
  loading,
  inspectedRule,
  activeAnnotation,
  onInspectRule,
  onCloseDocument,
  workspaceTab,
  onTabChange,
  onExpertReview,
}: InspectorWorkspaceProps) {
  const hasAnalysis = Boolean(checklistExecution || result);
  const showDocument =
    workspaceTab === "document" &&
    inspectedRule &&
    activeAnnotation &&
    document &&
    document.pageImages &&
    document.pageImages.length > 0;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="shrink-0 flex items-center gap-1 px-4 py-2 bg-white border-b border-slate-200">
        <button
          type="button"
          onClick={() => onTabChange("checklist")}
          disabled={!checklistExecution}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            workspaceTab === "checklist"
              ? "bg-violet-50 text-violet-800 border border-violet-200"
              : "text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          }`}
        >
          <ListChecks className="w-4 h-4" />
          White-Box
        </button>
        <button
          type="button"
          onClick={() => onTabChange("data")}
          disabled={!gutachten}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            workspaceTab === "data"
              ? "bg-brand-50 text-brand-700 border border-brand-200"
              : "text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          }`}
        >
          <Database className="w-4 h-4" />
          Gutachten-Daten
        </button>
        <button
          type="button"
          onClick={() => onTabChange("document")}
          disabled={!document?.pageImages?.length}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            workspaceTab === "document"
              ? "bg-amber-50 text-amber-800 border border-amber-200"
              : "text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          }`}
        >
          <FileSearch className="w-4 h-4" />
          PDF-Dokument
          {document?.pageImages?.length ? (
            <span className="text-xs bg-slate-100 px-1.5 rounded">
              {document.pageImages.length} S.
            </span>
          ) : null}
        </button>
        {inspectedRule && (
          <span className="ml-auto text-xs text-amber-700 bg-amber-50 border border-amber-100 px-2 py-1 rounded-full">
            Prüfung: {inspectedRule.rule_id}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-hidden grid grid-cols-1 xl:grid-cols-2 divide-x divide-slate-200">
        <div className="overflow-y-auto p-5 scrollbar-thin bg-slate-50/40 min-h-0">
          <div className="flex items-center gap-2 mb-4">
            <LayoutPanelLeft className="w-4 h-4 text-slate-400" />
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              {showDocument ? "Dokument — Fehlerstelle markiert" : "Übersicht"}
            </p>
          </div>

          {showDocument ? (
            <DocumentViewer
              document={document!}
              rule={inspectedRule!}
              annotation={activeAnnotation!}
              onClose={onCloseDocument}
            />
          ) : workspaceTab === "document" && document?.pageImages?.length ? (
            <DocumentViewer
              document={document}
              rule={
                inspectedRule ?? {
                  rule_id: "—",
                  rule_name: "Vollansicht",
                  passed: true,
                  flagged: false,
                  citation: "",
                  reason: "",
                }
              }
              annotation={{
                rule_id: "—",
                highlight_section_id: "page_1",
                highlight_text: document.filename,
                ai_explanation:
                  "Wählen Sie eine beanstandete Prüfung in der White-Box-Checkliste, um die Fehlerstelle im PDF zu markieren.",
                regulatory_links: [],
              }}
              onClose={() => onTabChange("checklist")}
            />
          ) : gutachten && workspaceTab === "data" ? (
            <GutachtenViewer gutachten={gutachten} />
          ) : hasAnalysis && workspaceTab === "checklist" ? (
            <ComplianceDashboard
              result={result!}
              loading={loading}
              selectedRuleId={inspectedRule?.rule_id}
              onInspectRule={onInspectRule}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-sm text-slate-400 gap-3">
              <ListChecks className="w-10 h-10 text-slate-300" />
              <p>PDF-Gutachten in der Sidebar hochladen</p>
              <p className="text-xs text-slate-400">
                Die White-Box-Checkliste erscheint nach der Analyse
              </p>
            </div>
          )}
        </div>

        <div className="overflow-y-auto p-5 scrollbar-thin min-h-0">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
            White-Box Checkliste
          </p>
          <WhiteBoxChecklist
            execution={checklistExecution}
            loading={loading}
            selectedCheckId={inspectedRule?.rule_id}
            onInspectCheck={onInspectRule}
            onExpertReview={onExpertReview}
          />
        </div>
      </div>
    </div>
  );
}
