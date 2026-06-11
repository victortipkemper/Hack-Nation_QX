import type { CaseSummary, Gutachten, TestPlanResult } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function fetchCases(): Promise<CaseSummary[]> {
  const res = await fetch(`${API_BASE}/api/cases`);
  if (!res.ok) throw new Error("Failed to fetch cases");
  return res.json();
}

export async function fetchCase(caseId: string): Promise<Gutachten> {
  const res = await fetch(`${API_BASE}/api/cases/${caseId}`);
  if (!res.ok) throw new Error(`Failed to fetch case ${caseId}`);
  return res.json();
}

export async function analyzeGutachten(
  gutachten: Gutachten
): Promise<TestPlanResult> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(gutachten),
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
}
