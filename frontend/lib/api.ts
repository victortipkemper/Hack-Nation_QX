import type {
  ChecklistExecution,
  ExpertKnowledgeEntry,
  ExpertReviewRequest,
  ExpertReviewResponse,
  UploadResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function fetchHealth(): Promise<{
  status: string;
  version: string;
  checklist_engine?: boolean;
  checklist_version?: string;
  llm_available?: boolean;
}> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("API nicht erreichbar");
  return res.json();
}

export async function fetchUploadChecklist(
  uploadId: string
): Promise<ChecklistExecution> {
  const res = await fetch(`${API_BASE}/api/uploads/${uploadId}/checklist`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Checkliste konnte nicht geladen werden");
  return res.json();
}

export async function submitExpertReview(
  review: ExpertReviewRequest
): Promise<ExpertReviewResponse> {
  const res = await fetch(`${API_BASE}/api/expert-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });
  if (!res.ok) {
    throw new Error("Experten-Bewertung konnte nicht gespeichert werden");
  }
  return res.json();
}

export async function fetchExpertKnowledge(): Promise<ExpertKnowledgeEntry[]> {
  const res = await fetch(`${API_BASE}/api/expert-knowledge`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Wissensdatenbank konnte nicht geladen werden");
  return res.json();
}

export async function uploadGutachtenPdf(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(
      typeof err.detail === "string" ? err.detail : "Upload failed"
    );
  }

  return res.json();
}

export interface ProcedureStepOut {
  order: number;
  title: string;
  instruction: string;
  acceptance_criteria: string;
  tools: string[];
}

export interface ExpertGuidanceItem {
  check_id: string;
  check_name: string;
  citation: string;
  finding: string;
  severity: string;
  merkblatt_sections: string[];
  merkblatt_excerpt: string;
  standard_procedure: ProcedureStepOut[];
  nachpruefung_steps: ProcedureStepOut[];
  documentation_checklist: string[];
  practice_notes: string[];
  learned_verification: string;
  learned_remediation: string;
  llm_guide: string;
  citations: string[];
}

export interface ExpertNachpruefungResponse {
  upload_id: string;
  filename: string;
  flagged_count: number;
  llm_used: boolean;
  llm_model?: string | null;
  merkblatt_available: boolean;
  items: ExpertGuidanceItem[];
}

export async function fetchExpertNachpruefung(
  uploadId: string,
  checkId?: string,
  useLlm = true
): Promise<ExpertNachpruefungResponse> {
  const params = new URLSearchParams();
  if (checkId) params.set("check_id", checkId);
  params.set("use_llm", String(useLlm));
  const res = await fetch(
    `${API_BASE}/api/expert/nachpruefung/${uploadId}?${params}`,
    { method: "POST" }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Fehler" }));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : "Expertenwissen nicht verfügbar"
    );
  }
  return res.json();
}
