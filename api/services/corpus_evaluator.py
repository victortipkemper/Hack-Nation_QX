"""
Evaluate checklist engine against golden hackathon corpus.
Ground truth used for scoring only — never in checking logic.
"""

from schemas.whitebox import ChecklistExecution
from data.golden_corpus import (
    GOLDEN_VERDICTS,
    PASS_VERDICTS,
    extract_case_id,
    list_corpus_pdfs,
)
from engine.checklist_engine import execute_checklist
from services.feature_extractor import extract_features
from services.pdf_parser import extract_text_from_pdf


def _map_engine_verdict(status: str) -> str:
    if status == "PASS":
        return "GREEN"
    return "YELLOW"


def _expected_matches(actual_status: str, expected: str) -> bool:
    actual_mapped = _map_engine_verdict(actual_status)
    if expected in PASS_VERDICTS:
        return actual_mapped == "GREEN"
    return actual_mapped == "YELLOW"


def evaluate_single_pdf(pdf_path: str) -> dict:
    """Run checklist on one PDF and compare to golden verdict."""
    from pathlib import Path
    path = Path(pdf_path)
    filename = path.name
    case_id = extract_case_id(filename) or filename

    full_text, pages = extract_text_from_pdf(pdf_path)
    features = extract_features(full_text, filename=filename, page_count=len(pages))
    execution = execute_checklist(features, gutachten_id=case_id)

    golden = GOLDEN_VERDICTS.get(case_id, {})
    expected = golden.get("verdict", "UNKNOWN")
    actual = execution.final_verdict.status.value
    matches = _expected_matches(actual, expected) if expected != "UNKNOWN" else None

    flagged_checks = [
        s.check_id
        for s in execution.steps
        if s.executed
        and s.severity == "error"
        and (not s.passed or s.flagged)
    ]

    return {
        "case_id": case_id,
        "filename": filename,
        "expected_verdict": expected,
        "actual_verdict": _map_engine_verdict(actual),
        "matches": matches,
        "flagged_checks": flagged_checks,
        "expected_gap": golden.get("gap"),
        "applicable_checks": execution.applicable_checks,
        "executed_checks": execution.executed_checks,
    }


def evaluate_full_corpus() -> dict:
    """Evaluate all 50 hackathon PDFs against golden corpus."""
    pdfs = list_corpus_pdfs()
    results = []
    correct = 0
    total = 0

    for pdf in pdfs:
        result = evaluate_single_pdf(str(pdf))
        results.append(result)
        if result["matches"] is not None:
            total += 1
            if result["matches"]:
                correct += 1

    yellow_cases = [r for r in results if r["expected_verdict"] == "YELLOW"]
    yellow_detected = sum(
        1 for r in yellow_cases if r["actual_verdict"] == "YELLOW"
    )

    return {
        "total_pdfs": len(pdfs),
        "evaluated": total,
        "accuracy": round(correct / total, 3) if total else 0,
        "correct": correct,
        "yellow_recall": round(yellow_detected / len(yellow_cases), 3)
        if yellow_cases
        else 0,
        "yellow_total": len(yellow_cases),
        "yellow_detected": yellow_detected,
        "results": results,
    }
