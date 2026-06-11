import type { ChecklistExecution, TestPlanResult } from "@/types";

const NEW_ENGINE_CHECK_IDS = new Set([
  "L1-ROUTE-001",
  "L2-751-I.5.1.6",
  "L3-AUFSTELLUNG-001",
]);

/** True when the API returned the golden-calibrated checklist (not legacy rules engine). */
export function isCalibratedChecklist(
  execution: ChecklistExecution | null | undefined
): boolean {
  if (!execution?.steps?.length) return false;

  const version = execution.checklist_version ?? "";
  if (version.includes("fallback")) return false;

  if (version.includes("golden") || version.includes("1.1")) {
    return true;
  }

  // Signature of the new fixed checklist (not old L1-19-002 rules engine)
  const ids = new Set(execution.steps.map((s) => s.check_id));
  return [...NEW_ENGINE_CHECK_IDS].every((id) => ids.has(id));
}

export function testPlanFromChecklist(
  execution: ChecklistExecution
): TestPlanResult {
  return {
    gutachten_id: execution.gutachten_id,
    levels: execution.levels,
    final_verdict: execution.final_verdict,
    executed_at: execution.executed_at,
  };
}
