"""
Learning engine — mines patterns from uploaded Gutachten (training corpus).
Updates verification/remediation hints from real pass/fail evidence.
Verdict logic stays in checklist engine; learning only enriches guidance.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data.exemplar_patterns import EXEMPLAR_PATTERNS

CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "training_corpus"
MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "learned_model.json"

# check_id → exemplar_key (filled at import from registry)
_CHECK_TO_EXEMPLAR: dict[str, str] = {}

_ANCHOR_PATTERNS = [
    r"Zu\s*15\.1/2",
    r"Achslast\s*HA",
    r"Abrollumfang",
    r"§\s*\d+[a-z]?",
    r"Verwendungsbereich",
    r"Teilegutachten",
    r"Prüfbericht",
    r"Anlagen zu Gutachten",
    r"3/4\s+Ansicht",
    r"Fabrikschild",
    r"Geschwindigkeitsindex|SR\s",
    r"Tragfähigkeitsindex|LI\s",
    r"Radtraglast",
    r"GA-Nr",
    r"FIN",
]


def _ensure_check_mapping() -> None:
    if _CHECK_TO_EXEMPLAR:
        return
    from engine.checklist_registry import CHECKLIST

    for check in CHECKLIST:
        _CHECK_TO_EXEMPLAR[check.check_id] = check.exemplar_key


def _empty_model() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": None,
        "exemplar_count": 0,
        "checks": {},
    }


def _load_model() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return _empty_model()
    try:
        return json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_model()


def _save_model(model: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model["updated_at"] = datetime.now(timezone.utc).isoformat()
    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")


def _check_block(model: dict[str, Any], exemplar_key: str) -> dict[str, Any]:
    checks = model.setdefault("checks", {})
    if exemplar_key not in checks:
        checks[exemplar_key] = {
            "pass_count": 0,
            "fail_count": 0,
            "anchor_phrases": [],
            "pass_evidence_samples": [],
            "fail_evidence_samples": [],
            "paragraph_snippets": [],
        }
    return checks[exemplar_key]


def _extract_anchors(text: str) -> list[str]:
    found: list[str] = []
    for pat in _ANCHOR_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            found.append(m.group().strip()[:60])
    return list(dict.fromkeys(found))[:8]


def _trim_sample(text: str, max_len: int = 220) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _top_anchors(counter: Counter[str], limit: int = 5) -> list[str]:
    return [phrase for phrase, _ in counter.most_common(limit)]


def learn_from_exemplar(exemplar: dict[str, Any]) -> None:
    """Incrementally update model from one saved training exemplar."""
    _ensure_check_mapping()
    model = _load_model()
    model["exemplar_count"] = model.get("exemplar_count", 0) + 1

    steps = exemplar.get("checklist_steps") or []
    paragraphs = exemplar.get("paragraphs") or []
    full_text = " ".join(p.get("text", "") for p in paragraphs[:30])

    per_key_anchors: dict[str, Counter[str]] = {}
    # Several checks can share one exemplar_key (e.g. L1-ROUTE-001 and
    # L1-DOC-001 → tga_documentation), so count pass/fail once per document.
    per_key_passed: set[str] = set()
    per_key_failed: set[str] = set()

    for step in steps:
        if not step.get("executed"):
            continue
        exemplar_key = _CHECK_TO_EXEMPLAR.get(step.get("check_id", ""))
        if not exemplar_key:
            continue

        block = _check_block(model, exemplar_key)
        evidence = step.get("evidence") or step.get("reason") or ""
        passed = step.get("passed") is True and not step.get("flagged")

        key_anchors = per_key_anchors.setdefault(exemplar_key, Counter())
        for a in _extract_anchors(evidence + " " + full_text):
            key_anchors[a] += 1

        if passed:
            per_key_passed.add(exemplar_key)
            samples: list[str] = block["pass_evidence_samples"]
            sample = _trim_sample(evidence)
            if sample and sample not in samples:
                samples.append(sample)
                block["pass_evidence_samples"] = samples[-12:]
        elif step.get("flagged") or step.get("passed") is False:
            per_key_failed.add(exemplar_key)
            samples = block["fail_evidence_samples"]
            sample = _trim_sample(evidence)
            if sample and sample not in samples:
                samples.append(sample)
                block["fail_evidence_samples"] = samples[-12:]

    for exemplar_key in per_key_passed | per_key_failed:
        block = _check_block(model, exemplar_key)
        if exemplar_key in per_key_failed:
            block["fail_count"] += 1
        else:
            block["pass_count"] += 1

    # Paragraph snippets linked to flagged rules
    for mapping in exemplar.get("training_labels", {}).get("paragraph_rule_mapping", []):
        rule_id = mapping.get("rule_id", "")
        exemplar_key = _CHECK_TO_EXEMPLAR.get(rule_id)
        if not exemplar_key:
            continue
        block = _check_block(model, exemplar_key)
        snippets: list[str] = block["paragraph_snippets"]
        ref = mapping.get("paragraph_ref") or ""
        if ref and ref not in snippets:
            snippets.append(ref[:120])
            block["paragraph_snippets"] = snippets[-10:]

    for exemplar_key, counter in per_key_anchors.items():
        block = _check_block(model, exemplar_key)
        existing = Counter(dict.fromkeys(block.get("anchor_phrases", []), 1))
        existing.update(counter)
        block["anchor_phrases"] = _top_anchors(existing)

    _save_model(model)


def rebuild_model_from_corpus() -> dict[str, Any]:
    """Full rebuild from all JSON files in training_corpus/."""
    _ensure_check_mapping()
    model = _empty_model()
    MODEL_PATH.unlink(missing_ok=True)

    if not CORPUS_DIR.exists():
        _save_model(model)
        return model_status()

    files = sorted(CORPUS_DIR.glob("*.json"))
    for path in files:
        try:
            exemplar = json.loads(path.read_text(encoding="utf-8"))
            learn_from_exemplar(exemplar)
        except (json.JSONDecodeError, OSError):
            continue

    return model_status()


def bootstrap_from_hackathon() -> dict[str, Any]:
    """Seed learning model by processing hackathon PDFs (no upload dirs)."""
    from data.golden_corpus import list_corpus_pdfs
    from engine.checklist_engine import execute_checklist
    from services.feature_extractor import extract_features
    from services.pdf_parser import extract_text_from_pdf
    from services.pdf_blocks import extract_page_paragraphs

    _ensure_check_mapping()
    learned = 0
    errors: list[str] = []

    for pdf in list_corpus_pdfs():
        try:
            text, pages = extract_text_from_pdf(str(pdf))
            features = extract_features(text, pdf.name, len(pages))
            execution = execute_checklist(features, gutachten_id=pdf.stem)
            paragraphs = extract_page_paragraphs(str(pdf))
            exemplar = {
                "filename": pdf.name,
                "verdict": execution.final_verdict.status.value,
                "checklist_steps": [s.model_dump() for s in execution.steps],
                "paragraphs": [
                    {"page": b.page, "text": b.text[:500]} for b in paragraphs[:40]
                ],
                "training_labels": {"paragraph_rule_mapping": []},
            }
            learn_from_exemplar(exemplar)
            learned += 1
        except Exception as exc:
            errors.append(f"{pdf.name}: {exc}")

    status = model_status()
    status["bootstrap_learned"] = learned
    status["bootstrap_errors"] = errors[:5]
    return status


def get_learned_hints(
    exemplar_key: str,
    current_evidence: str = "",
) -> tuple[str, str, dict[str, Any]]:
    """
    Returns (remediation, verification, meta).
    meta: {learned: bool, pass_count, fail_count, source}
    """
    seed = EXEMPLAR_PATTERNS.get(exemplar_key, {})
    seed_ver = seed.get("verification", "")
    seed_rem = seed.get("remediation", "")

    model = _load_model()
    block = model.get("checks", {}).get(exemplar_key, {})
    pass_n = block.get("pass_count", 0)
    fail_n = block.get("fail_count", 0)

    meta = {
        "learned": pass_n + fail_n > 0,
        "pass_count": pass_n,
        "fail_count": fail_n,
        "source": "seed",
    }

    verification_parts: list[str] = []
    remediation_parts: list[str] = []

    if pass_n >= 1:
        meta["source"] = "corpus+seed" if pass_n >= 3 else "corpus+seed"
        verification_parts.append(
            f"Aus {pass_n} bestandenen Gutachten im Lernkorpus:"
        )
        anchors = block.get("anchor_phrases", [])
        if anchors:
            verification_parts.append(
                "Typische Nachweisstellen: " + ", ".join(anchors[:5]) + "."
            )
        for sample in block.get("pass_evidence_samples", [])[-2:]:
            verification_parts.append(f"Erfolgreicher Nachweis: „{sample}“")

    if fail_n >= 1:
        meta["source"] = "corpus+seed"
        for sample in block.get("fail_evidence_samples", [])[-2:]:
            remediation_parts.append(
                f"Bei {fail_n} ähnlichen Beanstandungen: „{sample}“"
            )

    if current_evidence and pass_n == 0 and fail_n == 0:
        verification_parts.append(f"Aktueller Befund: {_trim_sample(current_evidence, 180)}")

    verification = " ".join(verification_parts)
    if seed_ver:
        verification = (verification + " " + seed_ver).strip() if verification else seed_ver

    remediation = " ".join(remediation_parts)
    if seed_rem:
        remediation = (remediation + " " + seed_rem).strip() if remediation else seed_rem

    if pass_n + fail_n >= 3:
        meta["source"] = "corpus-primary"

    return remediation, verification, meta


def model_status() -> dict[str, Any]:
    model = _load_model()
    checks = model.get("checks", {})
    return {
        "model_path": str(MODEL_PATH),
        "updated_at": model.get("updated_at"),
        "exemplar_count": model.get("exemplar_count", 0),
        "corpus_files": len(list(CORPUS_DIR.glob("*.json"))) if CORPUS_DIR.exists() else 0,
        "learned_checks": len(checks),
        "checks_summary": {
            k: {
                "pass": v.get("pass_count", 0),
                "fail": v.get("fail_count", 0),
            }
            for k, v in sorted(checks.items())
        },
    }
