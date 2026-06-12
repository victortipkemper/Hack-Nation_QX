"""
Expert decision store — persistent verdicts from human expert review.

When a check flags a finding, an expert decides:
- "approve": the flagged configuration is acceptable → stored as override;
  every future document producing the same finding passes automatically.
- "reject": the finding is a genuine defect → stored as confirmation;
  the finding stays flagged, is marked expert-confirmed, and the document
  verdict becomes FAIL once every finding is confirmed.

A new decision for the same finding replaces the previous one.
Matching is conservative: a decision applies only to the exact
(check_id, evidence) combination, normalized for whitespace and case.
"""

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
KNOWLEDGE_PATH = _DATA_DIR / "expert_knowledge.json"
DECISIONS_LOG_PATH = _DATA_DIR / "expert_decisions.jsonl"

_lock = Lock()


def make_fingerprint(check_id: str, evidence: str) -> str:
    normalized = re.sub(r"\s+", " ", evidence.strip().lower())
    return hashlib.sha256(f"{check_id}|{normalized}".encode()).hexdigest()[:16]


def _load() -> dict:
    if not KNOWLEDGE_PATH.exists():
        return {"version": 1, "entries": []}
    try:
        return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "entries": []}


def _save(db: dict) -> None:
    KNOWLEDGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_PATH.write_text(
        json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def list_entries() -> list[dict]:
    return _load()["entries"]


def find_decision(check_id: str, evidence: str) -> dict | None:
    fp = make_fingerprint(check_id, evidence)
    for entry in _load()["entries"]:
        if entry["fingerprint"] == fp:
            return entry
    return None


def _log_decision(record: dict) -> None:
    DECISIONS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_decision(
    check_id: str,
    check_name: str,
    evidence: str,
    decision: str,
    note: str = "",
    gutachten_id: str = "",
    expert: str = "",
) -> dict:
    """
    Persist the expert decision for this exact finding (idempotent);
    a different decision for the same finding replaces the previous one.
    Every decision is also appended to the audit log.
    """
    fp = make_fingerprint(check_id, evidence)
    now = datetime.now(timezone.utc).isoformat()

    _log_decision(
        {
            "decided_at": now,
            "decision": decision,
            "check_id": check_id,
            "fingerprint": fp,
            "evidence": evidence,
            "note": note,
            "gutachten_id": gutachten_id,
            "expert": expert,
        }
    )

    with _lock:
        db = _load()
        existing = next(
            (e for e in db["entries"] if e["fingerprint"] == fp), None
        )
        if existing and existing.get("decision", "approve") == decision:
            return existing

        db["entries"] = [e for e in db["entries"] if e["fingerprint"] != fp]
        entry = {
            "entry_id": f"ek-{uuid.uuid4().hex[:8]}",
            "fingerprint": fp,
            "decision": decision,
            "check_id": check_id,
            "check_name": check_name,
            "evidence": evidence,
            "note": note,
            "gutachten_id": gutachten_id,
            "expert": expert,
            "created_at": now,
        }
        db["entries"].append(entry)
        _save(db)
        return entry


def delete_entry(entry_id: str) -> bool:
    with _lock:
        db = _load()
        before = len(db["entries"])
        db["entries"] = [e for e in db["entries"] if e["entry_id"] != entry_id]
        if len(db["entries"]) == before:
            return False
        _save(db)
        return True
