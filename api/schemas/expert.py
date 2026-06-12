from typing import Literal, Optional

from pydantic import BaseModel


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
