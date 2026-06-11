import type { ChecklistExecution } from "@/types";
import { isCalibratedChecklist } from "@/lib/checklistView";

/**
 * Use only the API checklist — never replay legacy test_plan rules as flags.
 * The old rules engine produced many false positives (e.g. 1128 §21 erloschen).
 */
export function resolveChecklistExecution(
  checklist?: ChecklistExecution | null
): ChecklistExecution | null {
  if (isCalibratedChecklist(checklist)) {
    return checklist!;
  }
  return null;
}
