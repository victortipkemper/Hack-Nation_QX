from typing import List, Optional

from pydantic import BaseModel

from schemas.verdict import FinalVerdict, LevelResult


class WhiteBoxStep(BaseModel):
    step: int
    check_id: str
    level: int
    check_name: str
    citation: str
    severity: str = "error"  # error | advisory
    applicable: bool
    applicability_reason: str
    executed: bool
    passed: Optional[bool] = None
    flagged: bool = False
    skipped_reason: Optional[str] = None
    evidence: str = ""
    reason: str = ""
    remediation_hint: str = ""
    exemplar_reference: str = ""
    review_fingerprint: str = ""
    expert_override: bool = False
    expert_override_id: str = ""


class ChecklistExecution(BaseModel):
    gutachten_id: str
    checklist_version: str
    total_checks: int
    applicable_checks: int
    executed_checks: int
    steps: List[WhiteBoxStep]
    levels: List[LevelResult]
    final_verdict: FinalVerdict
    executed_at: str
