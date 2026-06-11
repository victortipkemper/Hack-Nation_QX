"""Render and annotate reference-case PDFs for the frontend document viewer."""

import shutil
from pathlib import Path

from data.mock_cases import MOCK_CASES
from engine.rules import execute_test_plan
from schemas.upload import UploadedDocument
from services.document_annotator import build_uploaded_document
from services.pdf_parser import extract_text_from_pdf
from services.pdf_renderer import render_pdf_pages

API_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_PDF_DIR = API_ROOT / "data" / "reference_docs"
REFERENCE_RENDER_DIR = API_ROOT / "data" / "reference_renders"
FRONTEND_DOCS = API_ROOT.parent / "frontend" / "public" / "documents"

CASE_PDF_MAP: dict[str, str] = {
    "case-06-bmw-m4-widerspruch": "1146_E_21_BMW_M4_LI_Widerspruch.pdf",
}


def _ensure_reference_pdf(case_id: str) -> Path | None:
    pdf_name = CASE_PDF_MAP.get(case_id)
    if not pdf_name:
        return None

    REFERENCE_PDF_DIR.mkdir(parents=True, exist_ok=True)
    dest = REFERENCE_PDF_DIR / pdf_name

    if not dest.exists():
        src = FRONTEND_DOCS / pdf_name
        if src.exists():
            shutil.copy(src, dest)
        else:
            return None

    return dest


def get_reference_document(case_id: str) -> UploadedDocument | None:
    """Build a fully annotated document with rendered page images."""
    if case_id not in MOCK_CASES:
        return None

    pdf_path = _ensure_reference_pdf(case_id)
    if not pdf_path:
        return None

    gutachten = MOCK_CASES[case_id]
    test_plan = execute_test_plan(gutachten)

    render_dir = REFERENCE_RENDER_DIR / case_id
    render_dir.mkdir(parents=True, exist_ok=True)

    # Copy PDF into render dir for static serving
    ref_pdf = render_dir / "original.pdf"
    if not ref_pdf.exists():
        shutil.copy(pdf_path, ref_pdf)

    rendered = render_pdf_pages(str(ref_pdf), str(render_dir / "pages"))
    if not rendered:
        return None

    _, page_texts = extract_text_from_pdf(str(ref_pdf))
    page_count = len(rendered)

    doc = build_uploaded_document(
        upload_id=f"ref-{case_id}",
        filename=ref_pdf.name,
        pdf_path=str(ref_pdf),
        page_count=page_count,
        page_texts=page_texts,
        test_plan=test_plan,
    )

    return doc.model_copy(
        update={
            "upload_id": f"ref-{case_id}",
            "pdf_url": f"/api/reference/{case_id}/original.pdf",
            "page_urls": [
                f"/api/reference/{case_id}/pages/{i + 1}.png"
                for i in range(page_count)
            ],
        }
    )
