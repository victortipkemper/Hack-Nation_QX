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
