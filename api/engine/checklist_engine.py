"""
White-box checklist execution engine.
Runs the fixed checklist sequentially — deterministic, fully traceable.
Calibrated against Hackathon Lösungsschlüssel (50 PDFs).
"""

import hashlib
from datetime import datetime, timezone

from data.gap_check_mapping import AUFSTELLUNG_DEDUPE_IF_FLAGGED
from engine.checklist_registry import CHECKLIST, CHECKLIST_VERSION, _remediation
from schemas.features import DocumentFeatures
from schemas.verdict import (
    FinalVerdict,
    LevelResult,
    RuleResult,
    TestPlanResult,
    VerdictStatus,
)
from schemas.whitebox import ChecklistExecution, WhiteBoxStep
from services.expert_decisions import find_decision, make_fingerprint

LEVEL_NAMES = {
    1: "Level 1 — StVZO (formales Recht)",
    2: "Level 2 — VdTÜV Merkblatt 751",
    3: "Level 3 — TÜV-Praxis",
    4: "Level 4 — Konsens technische Dienste",
}


def execute_checklist(
    features: DocumentFeatures,
    gutachten_id: str = "unknown",
) -> ChecklistExecution:
    """Execute fixed checklist; dedupe L3 flags covered by L2; verdict = error-level only."""
    steps: list[WhiteBoxStep] = []
    step_num = 0
    applicable_count = 0
    executed_count = 0
    level_rules: dict[int, list[RuleResult]] = {1: [], 2: [], 3: [], 4: []}

    for check in CHECKLIST:
        step_num += 1
        is_applicable, applicability_reason = check.applicable(features)

        if not is_applicable:
            remediation, verification, hint_source = _remediation(check.exemplar_key)
            steps.append(
                WhiteBoxStep(
                    step=step_num,
                    check_id=check.check_id,
                    level=check.level,
                    check_name=check.check_name,
                    citation=check.citation,
                    severity=check.severity,
                    applicable=False,
                    applicability_reason=applicability_reason,
                    executed=False,
                    skipped_reason="Nicht anwendbar für dieses Gutachten.",
                    remediation_hint=remediation,
                    verification_hint=verification,
                    exemplar_reference=verification,
                    hint_source=hint_source,
                )
            )
            continue

        applicable_count += 1
        passed, flagged, reason, _evidence_key = check.evaluate(features)
        executed_count += 1
        remediation, verification, hint_source = _remediation(
            check.exemplar_key, reason
        )
        fingerprint = make_fingerprint(check.check_id, reason)

        # Saved expert decision for this exact finding:
        # approve → finding is acceptable, step passes;
        # reject → genuine defect, stays flagged but marked confirmed.
        entry = None
        if check.severity == "error" and (flagged or passed is False):
            entry = find_decision(check.check_id, reason)
        decision = entry.get("decision", "approve") if entry else ""
        if decision == "approve":
            passed = True
            flagged = False
            reason = (
                f"Durch Expertenwissen freigegeben "
                f"({entry['entry_id']}): {reason}"
            )
        elif decision == "reject":
            reason = (
                f"Beanstandung durch Experten bestätigt "
                f"({entry['entry_id']}): {reason}"
            )

        steps.append(
            WhiteBoxStep(
                step=step_num,
                check_id=check.check_id,
                level=check.level,
                check_name=check.check_name,
                citation=check.citation,
                severity=check.severity,
                applicable=True,
                applicability_reason=applicability_reason,
                executed=True,
                passed=passed,
                flagged=flagged,
                evidence=reason,
                reason=reason,
                remediation_hint=remediation if (not passed or flagged) else "",
                verification_hint=verification,
                exemplar_reference=verification,
                hint_source=hint_source,
                review_fingerprint=fingerprint,
                expert_override=decision == "approve",
                expert_override_id=entry["entry_id"] if decision == "approve" else "",
                expert_confirmed=decision == "reject",
                expert_confirmed_id=entry["entry_id"] if decision == "reject" else "",
            )
        )

    _dedupe_aufstellung(steps)
    _sync_level_rules(steps, level_rules)

    levels = _build_levels(level_rules)
    final_verdict = _compute_verdict(steps, gutachten_id)

    return ChecklistExecution(
        gutachten_id=gutachten_id,
        checklist_version=CHECKLIST_VERSION,
        total_checks=len(CHECKLIST),
        applicable_checks=applicable_count,
        executed_checks=executed_count,
        steps=steps,
        levels=levels,
        final_verdict=final_verdict,
        executed_at=datetime.now(timezone.utc).isoformat(),
    )


def _is_error_flag(step: WhiteBoxStep) -> bool:
    return (
        step.severity == "error"
        and step.executed
        and (step.flagged or step.passed is False)
    )


def _dedupe_aufstellung(steps: list[WhiteBoxStep]) -> None:
    """Suppress L3-AUFSTELLUNG when L2 already flagged the same root cause."""
    error_flagged = {s.check_id for s in steps if _is_error_flag(s)}
    if "L3-AUFSTELLUNG-001" not in error_flagged:
        return
    if not any(cid in error_flagged for cid in AUFSTELLUNG_DEDUPE_IF_FLAGGED):
        return
    for step in steps:
        if step.check_id == "L3-AUFSTELLUNG-001" and _is_error_flag(step):
            step.passed = True
            step.flagged = False
            step.reason = "Bereits durch spezifische L2-Prüfung abgedeckt (keine Doppel-Beanstandung)."
            step.evidence = step.reason
            step.remediation_hint = ""


def _sync_level_rules(
    steps: list[WhiteBoxStep],
    level_rules: dict[int, list[RuleResult]],
) -> None:
    """Only error-severity checks appear in compliance levels / annotations."""
    for step in steps:
        if not step.executed or step.severity != "error":
            continue
        level_rules[step.level].append(
            RuleResult(
                rule_id=step.check_id,
                rule_name=step.check_name,
                passed=step.passed if step.passed is not None else True,
                flagged=step.flagged,
                citation=step.citation,
                reason=step.reason,
            )
        )


def checklist_to_test_plan(execution: ChecklistExecution) -> TestPlanResult:
    return TestPlanResult(
        gutachten_id=execution.gutachten_id,
        levels=execution.levels,
        final_verdict=execution.final_verdict,
        executed_at=execution.executed_at,
    )


def _build_levels(level_rules: dict[int, list[RuleResult]]) -> list[LevelResult]:
    levels: list[LevelResult] = []
    for level_num in sorted(level_rules.keys()):
        rules = level_rules[level_num]
        if not rules:
            continue
        levels.append(
            LevelResult(
                level=level_num,
                level_name=LEVEL_NAMES[level_num],
                rules=rules,
                all_passed=all(r.passed for r in rules),
                any_flagged=any(r.flagged for r in rules),
            )
        )
    return levels


def _compute_verdict(steps: list[WhiteBoxStep], gutachten_id: str) -> FinalVerdict:
    error_flags = [s for s in steps if _is_error_flag(s)]
    confirmed = [s for s in error_flags if s.expert_confirmed]

    if error_flags and len(confirmed) == len(error_flags):
        status = VerdictStatus.FAIL
        ids = ", ".join(s.check_id for s in error_flags)
        summary = (
            f"Beanstandung durch Experten bestätigt "
            f"({len(error_flags)}): {ids}"
        )
    elif error_flags:
        status = VerdictStatus.AUDIT_FLAGGED
        ids = ", ".join(s.check_id for s in error_flags)
        summary = f"Beanstandung ({len(error_flags)}): {ids}"
        if confirmed:
            summary += f" — davon {len(confirmed)} bestätigt"
    else:
        status = VerdictStatus.PASS
        summary = "Alle Pflichtprüfungen bestanden — keine Beanstandung."

    trail_seed = f"{gutachten_id}:{CHECKLIST_VERSION}:{datetime.now(timezone.utc).isoformat()}"
    audit_id = hashlib.sha256(trail_seed.encode()).hexdigest()[:16]

    return FinalVerdict(
        status=status,
        summary=summary,
        deterministic=True,
        audit_trail_id=audit_id,
    )
