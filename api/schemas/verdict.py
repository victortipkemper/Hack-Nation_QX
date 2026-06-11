from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class VerdictStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    AUDIT_FLAGGED = "AUDIT_FLAGGED"


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    flagged: bool
    citation: str
    reason: str


class LevelResult(BaseModel):
    level: int
    level_name: str
    rules: List[RuleResult]
    all_passed: bool
    any_flagged: bool


class FinalVerdict(BaseModel):
    status: VerdictStatus
    summary: str
    deterministic: bool = True
    audit_trail_id: str


class TestPlanResult(BaseModel):
    gutachten_id: str
    levels: List[LevelResult]
    final_verdict: FinalVerdict
    executed_at: str
