"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CaseSelector } from "@/components/CaseSelector";
import { InspectorWorkspace } from "@/components/InspectorWorkspace";
import {
  fetchHealth,
  fetchUploadChecklist,
  submitExpertReview,
  uploadGutachtenPdf,
} from "@/lib/api";
import { resolveChecklistExecution } from "@/lib/checklistFallback";
import {
  isCalibratedChecklist,
  testPlanFromChecklist,
} from "@/lib/checklistView";
import {
  getAnnotationForRule,
  type GutachtenDocument,
} from "@/lib/documentAnnotations";
import { uploadedDocumentToGutachtenDocument } from "@/lib/uploadDocument";
import {
  createLoadingSession,
  type GutachtenSession,
} from "@/lib/uploadSession";
import type { RuleResult, WhiteBoxStep } from "@/types";
import type { ExpertDecision } from "@/components/WhiteBoxChecklist";

type WorkspaceTab = "data" | "document" | "checklist";

export default function HomePage() {
  const [sessions, setSessions] = useState<GutachtenSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [uploadingCount, setUploadingCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [inspectedRule, setInspectedRule] = useState<RuleResult | null>(null);
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>("checklist");
  const [apiOutdated, setApiOutdated] = useState(false);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) ?? null,
    [sessions, activeSessionId]
  );

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        const calibrated =
          h.checklist_engine &&
          h.version.includes("checklist") &&
          (h.checklist_version?.includes("golden") ||
            h.checklist_version?.includes("1.1"));
        setApiOutdated(!calibrated);
      })
      .catch(() => setApiOutdated(true));
  }, []);

  const activeAnnotation = useMemo(() => {
    if (!activeSession?.document || !inspectedRule) return null;
    return getAnnotationForRule(activeSession.document, inspectedRule);
  }, [activeSession?.document, inspectedRule]);

  const processOneFile = useCallback(async (file: File, pendingId: string) => {
    try {
      const response = await uploadGutachtenPdf(file);

      let checklist = response.checklist_execution ?? null;
      if (!isCalibratedChecklist(checklist)) {
        try {
          checklist = await fetchUploadChecklist(response.upload_id);
        } catch {
          /* handled below */
        }
      }
      if (isCalibratedChecklist(checklist)) {
        setApiOutdated(false);
      } else {
        setApiOutdated(true);
      }

      const checklistExecution = resolveChecklistExecution(checklist);

      if (!checklistExecution) {
        let detail = "Unbekannte API-Version.";
        try {
          const h = await fetchHealth();
          detail = `API meldet Version „${h.version}“${
            h.checklist_version ? ` (Checkliste ${h.checklist_version})` : ""
          } — erwartet wird 0.3.0-checklist.`;
        } catch {
          detail = "API auf Port 8010 nicht erreichbar.";
        }
        throw new Error(
          `Kalibrierte Checkliste nicht verfügbar. ${detail} Bitte start.bat ausführen und beide PowerShell-Fenster offen lassen.`
        );
      }

      const document = uploadedDocumentToGutachtenDocument(
        response.document,
        response.gutachten.gutachten_id
      );

      const readySession: GutachtenSession = {
        id: `upload:${response.upload_id}`,
        uploadId: response.upload_id,
        filename: file.name,
        status: "ready",
        gutachten: response.gutachten,
        result: testPlanFromChecklist(checklistExecution),
        checklistExecution,
        document,
      };

      setSessions((prev) =>
        prev.map((s) => (s.id === pendingId ? readySession : s))
      );
      setActiveSessionId(readySession.id);
      setWorkspaceTab("checklist");
      setInspectedRule(null);
      setError(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload fehlgeschlagen.";
      setSessions((prev) =>
        prev.map((s) =>
          s.id === pendingId
            ? { ...s, status: "error" as const, error: message }
            : s
        )
      );
      setError(message);
    }
  }, []);

  const handleUploadFiles = useCallback(
    async (files: File[]) => {
      setError(null);

      const pendingSessions = files.map((file) => createLoadingSession(file));
      setSessions((prev) => [...prev, ...pendingSessions]);
      setUploadingCount((c) => c + files.length);

      if (pendingSessions[0]) {
        setActiveSessionId(pendingSessions[0].id);
      }

      await Promise.all(
        files.map((file, i) =>
          processOneFile(file, pendingSessions[i]!.id)
        )
      );

      setUploadingCount((c) => Math.max(0, c - files.length));
    },
    [processOneFile]
  );

  const handleSelectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    setInspectedRule(null);
    setWorkspaceTab("checklist");
  }, []);

  const handleRemoveSession = useCallback(
    (sessionId: string) => {
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== sessionId);
        if (activeSessionId === sessionId) {
          const fallback = next.find((s) => s.status === "ready") ?? next[0];
          setActiveSessionId(fallback?.id ?? null);
          setInspectedRule(null);
        }
        return next;
      });
    },
    [activeSessionId]
  );

  const handleExpertReview = useCallback(
    async (step: WhiteBoxStep, decision: ExpertDecision) => {
      const session = sessions.find((s) => s.id === activeSessionId);
      if (!session) return;

      await submitExpertReview({
        check_id: step.check_id,
        check_name: step.check_name,
        evidence: step.reason || step.evidence,
        decision,
        gutachten_id: session.checklistExecution?.gutachten_id ?? "",
      });

      // Approval changes the verdict — re-run the checklist with the new knowledge
      if (
        decision === "approve" &&
        session.uploadId &&
        !session.uploadId.startsWith("pending-")
      ) {
        const checklist = await fetchUploadChecklist(session.uploadId);
        const checklistExecution = resolveChecklistExecution(checklist);
        if (checklistExecution) {
          setSessions((prev) =>
            prev.map((s) =>
              s.id === session.id
                ? {
                    ...s,
                    checklistExecution,
                    result: testPlanFromChecklist(checklistExecution),
                  }
                : s
            )
          );
        }
      }
    },
    [sessions, activeSessionId]
  );

  const handleInspectRule = useCallback((rule: RuleResult) => {
    setInspectedRule(rule);
    setWorkspaceTab("document");
  }, []);

  const handleCloseDocument = useCallback(() => {
    setInspectedRule(null);
    setWorkspaceTab("checklist");
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      <CaseSelector
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onRemoveSession={handleRemoveSession}
        onUploadFiles={handleUploadFiles}
        uploadingCount={uploadingCount}
      />

      <main className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="shrink-0 px-6 py-4 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                TÜV Inspector Workspace
              </h2>
              <p className="text-sm text-slate-500">
                {activeSession
                  ? activeSession.filename
                  : "Gutachten hochladen → Checkliste → Beanstandungen im PDF"}
              </p>
            </div>
            {activeSession?.gutachten && (
              <div className="text-right hidden sm:block shrink-0">
                <p className="text-xs text-slate-400">Aktives Gutachten</p>
                <p className="text-sm font-mono text-slate-600 truncate max-w-[220px]">
                  {activeSession.gutachten.gutachten_id}
                </p>
              </div>
            )}
          </div>
        </header>

        {apiOutdated && (
          <div className="mx-4 mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
            Falsche oder alte API (Port 8010 erwartet).{" "}
            <code className="text-xs bg-amber-100 px-1 rounded">
              start.bat
            </code>{" "}
            ausführen — beide PowerShell-Fenster offen lassen.
          </div>
        )}

        {error && (
          <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        <InspectorWorkspace
          gutachten={activeSession?.gutachten ?? null}
          result={activeSession?.result ?? null}
          checklistExecution={activeSession?.checklistExecution ?? null}
          document={activeSession?.document ?? null}
          loading={activeSession?.status === "loading"}
          inspectedRule={inspectedRule}
          activeAnnotation={activeAnnotation}
          onInspectRule={handleInspectRule}
          onCloseDocument={handleCloseDocument}
          workspaceTab={workspaceTab}
          onTabChange={setWorkspaceTab}
          onExpertReview={handleExpertReview}
        />
      </main>
    </div>
  );
}
