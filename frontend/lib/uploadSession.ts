import type { ChecklistExecution, Gutachten, TestPlanResult } from "@/types";
import type { GutachtenDocument } from "@/lib/documentAnnotations";

export type SessionStatus = "loading" | "ready" | "error";

export interface GutachtenSession {
  id: string;
  uploadId: string;
  filename: string;
  status: SessionStatus;
  error?: string;
  gutachten: Gutachten | null;
  result: TestPlanResult | null;
  checklistExecution: ChecklistExecution | null;
  document: GutachtenDocument | null;
}

export function createLoadingSession(file: File): GutachtenSession {
  const tempId = `pending-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  return {
    id: tempId,
    uploadId: tempId,
    filename: file.name,
    status: "loading",
    gutachten: null,
    result: null,
    checklistExecution: null,
    document: null,
  };
}

export function sessionLabel(session: GutachtenSession): string {
  const base = session.filename.replace(/\.pdf$/i, "");
  return base.length > 28 ? `${base.slice(0, 25)}…` : base;
}
