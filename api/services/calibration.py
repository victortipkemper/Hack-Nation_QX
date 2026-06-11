"""
Golden-corpus calibration against Lösungsschlüssel.
Validates: GREEN → no error-level flags; YELLOW → primary gap check fires.
"""

from data.gap_check_mapping import GAP_PRIMARY_CHECKS
from data.golden_corpus import GOLDEN_VERDICTS, PASS_VERDICTS, extract_case_id, list_corpus_pdfs
from engine.checklist_engine import execute_checklist
from services.feature_extractor import extract_features
from services.pdf_parser import extract_text_from_pdf


def _error_flagged_ids(execution) -> list[str]:
    return [
        s.check_id
        for s in execution.steps
        if s.executed
        and s.severity == "error"
        and (s.flagged or s.passed is False)
    ]


def run_calibration() -> dict:
    results: list[dict] = []
    green_fp = 0
    yellow_miss = 0
    yellow_extra = 0
    correct = 0

    for pdf in list_corpus_pdfs():
        case_id = extract_case_id(pdf.name) or pdf.stem
        golden = GOLDEN_VERDICTS.get(case_id, {})
        expected = golden.get("verdict", "UNKNOWN")
        expected_gap = golden.get("gap")

        full_text, pages = extract_text_from_pdf(str(pdf))
        features = extract_features(full_text, pdf.name, len(pages))
        execution = execute_checklist(features, case_id)
        flagged = _error_flagged_ids(execution)

        entry = {
            "case_id": case_id,
            "expected_verdict": expected,
            "expected_gap": expected_gap,
            "flagged_checks": flagged,
            "ok": True,
            "issues": [],
        }

        if expected in PASS_VERDICTS:
            if flagged:
                entry["ok"] = False
                entry["issues"].append(f"False positive: {flagged}")
                green_fp += 1
        elif expected == "YELLOW":
            primary = GAP_PRIMARY_CHECKS.get(expected_gap or "", [])
            if primary and not any(p in flagged for p in primary):
                entry["ok"] = False
                entry["issues"].append(f"Missed primary check {primary}")
                yellow_miss += 1
            extra = [c for c in flagged if c not in primary]
            if extra:
                entry["issues"].append(f"Extra flags: {extra}")
                yellow_extra += len(extra)
        else:
            entry["issues"].append("Unknown expected verdict")

        if entry["ok"]:
            correct += 1
        results.append(entry)

    total = len(results)
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 3) if total else 0,
        "green_false_positives": green_fp,
        "yellow_missed": yellow_miss,
        "yellow_extra_flags": yellow_extra,
        "results": results,
    }
