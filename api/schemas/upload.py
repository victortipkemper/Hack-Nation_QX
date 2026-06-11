from typing import List, Optional

from pydantic import BaseModel

from schemas.gutachten import Gutachten
from schemas.verdict import TestPlanResult
from schemas.whitebox import ChecklistExecution


class HighlightRegion(BaseModel):
    page: int
    top: float
    left: float
    width: float
    height: float
    label: Optional[str] = None


class RegulatoryLink(BaseModel):
    label: str
    url: str


class RuleAnnotation(BaseModel):
    rule_id: str
    paragraph_ref: str = ""
    highlight_section_id: str
    highlight_text: str
    ai_explanation: str
    regulatory_references: List[str] = []
    regulatory_links: List[RegulatoryLink] = []
    remediation_hint: str = ""
    regions: List[HighlightRegion] = []


class DocumentSection(BaseModel):
    id: str
    label: str
    content: str
    page: Optional[int] = None


class UploadedDocument(BaseModel):
    upload_id: str
    filename: str
    pdf_url: str
    page_count: int
    page_urls: List[str]
    sections: List[DocumentSection]
    annotations: List[RuleAnnotation]


class UploadResponse(BaseModel):
    upload_id: str
    gutachten: Gutachten
    test_plan: TestPlanResult
    checklist_execution: ChecklistExecution
    document: UploadedDocument
