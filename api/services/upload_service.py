import uuid
from pathlib import Path

from engine.checklist_engine import checklist_to_test_plan, execute_checklist
from schemas.upload import UploadResponse
from services.document_annotator import build_uploaded_document
from services.feature_extractor import extract_features
from services.training_store import save_training_exemplar
from services.pdf_parser import extract_text_from_pdf, parse_gutachten_from_pdf
from services.pdf_renderer import render_pdf_pages

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def process_upload(file_bytes: bytes, filename: str) -> UploadResponse:
    """Route PDF or ZIP bundle to the appropriate pipeline."""
    lower = filename.lower()
    if lower.endswith(".zip"):
        from services.bundle_processor import process_bundle_upload

        return process_bundle_upload(file_bytes, filename)
    if lower.endswith(".pdf"):
        return process_pdf_upload(file_bytes, filename)
    raise ValueError("Nur PDF oder ZIP werden unterstützt.")


def process_pdf_upload(file_bytes: bytes, filename: str) -> UploadResponse:
    """
    Full upload pipeline:
    1. Store PDF
    2. Extract text → Gutachten JSON
    3. Checklist engine → TestPlanResult (golden-calibrated)
    4. Render pages + build annotations
    """
    upload_id = str(uuid.uuid4())
    upload_dir = UPLOADS_DIR / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = upload_dir / "original.pdf"
    pdf_path.write_bytes(file_bytes)

    full_text, page_texts = extract_text_from_pdf(str(pdf_path))
    gutachten = parse_gutachten_from_pdf(full_text, filename, upload_id)

    features = extract_features(
        full_text, filename=filename, page_count=len(page_texts)
    )
    checklist_execution = execute_checklist(
        features, gutachten_id=gutachten.gutachten_id
    )
    test_plan = checklist_to_test_plan(checklist_execution)

    pages_dir = upload_dir / "pages"
    rendered = render_pdf_pages(str(pdf_path), str(pages_dir))
    page_count = max(len(rendered), len(page_texts), 1)

    document = build_uploaded_document(
        upload_id=upload_id,
        filename=filename,
        pdf_path=str(pdf_path),
        page_count=page_count,
        page_texts=page_texts,
        test_plan=test_plan,
        checklist_execution=checklist_execution,
    )

    response = UploadResponse(
        upload_id=upload_id,
        gutachten=gutachten,
        test_plan=test_plan,
        checklist_execution=checklist_execution,
        document=document,
    )

    # Accumulate training exemplar for future document-based learning
    save_training_exemplar(response, str(pdf_path))

    return response
