from typing import List, Literal, Optional

from pydantic import BaseModel


class ProcedureStepOut(BaseModel):
    order: int
    title: str
    instruction: str
    acceptance_criteria: str = ""
    tools: List[str] = []


class ExpertGuidanceItem(BaseModel):
    check_id: str
    check_name: str
    citation: str
    finding: str
    severity: str
    merkblatt_sections: List[str] = []
    merkblatt_excerpt: str = ""
    standard_procedure: List[ProcedureStepOut]
    nachpruefung_steps: List[ProcedureStepOut]
    documentation_checklist: List[str]
    practice_notes: List[str]
    learned_verification: str = ""
    learned_remediation: str = ""
    llm_guide: str = ""
    citations: List[str] = []


class ExpertNachpruefungResponse(BaseModel):
    upload_id: str
    filename: str
    flagged_count: int
    llm_used: bool
    llm_model: Optional[str] = None
    merkblatt_available: bool
    items: List[ExpertGuidanceItem]


class ExpertProcedureResponse(BaseModel):
    check_id: str
    procedure_available: bool
    merkblatt_sections: List[str] = []
    merkblatt_excerpt: str = ""
    standard_procedure: List[ProcedureStepOut] = []
    nachpruefung_steps: List[ProcedureStepOut] = []
    documentation_checklist: List[str] = []
    practice_notes: List[str] = []


class ExpertReviewRequest(BaseModel):
    check_id: str
    check_name: str = ""
    evidence: str
    decision: Literal["approve", "reject"]
    note: str = ""
    gutachten_id: str = ""
    expert: str = ""


class ExpertKnowledgeEntry(BaseModel):
    entry_id: str
    fingerprint: str
    decision: Literal["approve", "reject"] = "approve"
    check_id: str
    check_name: str = ""
    evidence: str
    note: str = ""
    gutachten_id: str = ""
    expert: str = ""
    created_at: str


class ExpertReviewResponse(BaseModel):
    decision: str
    stored: bool
    entry: Optional[ExpertKnowledgeEntry] = None
