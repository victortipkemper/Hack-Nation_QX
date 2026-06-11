"""Build document annotations from rules engine + paragraph knowledge base."""

from schemas.upload import DocumentSection, RuleAnnotation, UploadedDocument
from schemas.verdict import TestPlanResult
from schemas.whitebox import ChecklistExecution
from services.explanation_service import build_rule_annotation


def _sections_from_pages(page_texts: list[str]) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    for i, text in enumerate(page_texts):
        if text.strip():
            sections.append(
                DocumentSection(
                    id=f"page_{i + 1}",
                    label=f"Seite {i + 1}",
                    content=text.strip()[:2000],
                    page=i + 1,
                )
            )
    return sections


def build_uploaded_document(
    upload_id: str,
    filename: str,
    pdf_path: str,
    page_count: int,
    page_texts: list[str],
    test_plan: TestPlanResult,
    checklist_execution: ChecklistExecution | None = None,
) -> UploadedDocument:
    """Generate paragraph-precise annotations for all flagged/failed rules."""
    annotations: list[RuleAnnotation] = []

    for level in test_plan.levels:
        for rule in level.rules:
            if rule.passed and not rule.flagged:
                continue
            annotations.append(
                build_rule_annotation(rule, pdf_path, checklist_execution)
            )

    page_urls = [
        f"/api/uploads/{upload_id}/pages/{i + 1}.png"
        for i in range(page_count)
    ]

    return UploadedDocument(
        upload_id=upload_id,
        filename=filename,
        pdf_url=f"/api/uploads/{upload_id}/original.pdf",
        page_count=page_count,
        page_urls=page_urls,
        sections=_sections_from_pages(page_texts),
        annotations=annotations,
    )
