from typing import List, Optional

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
