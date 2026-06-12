from pathlib import Path

from services.env_loader import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from data.mock_cases import MOCK_CASES, get_case_summaries
from engine.rules import execute_test_plan
from schemas.gutachten import CaseSummary, Gutachten
from schemas.upload import UploadResponse
from schemas.verdict import TestPlanResult
from schemas.upload import UploadedDocument
from schemas.expert import (
    ExpertKnowledgeEntry,
    ExpertNachpruefungResponse,
    ExpertProcedureResponse,
    ExpertReviewRequest,
    ExpertReviewResponse,
)
from schemas.whitebox import ChecklistExecution
from data.golden_corpus import find_corpus_pdf, list_corpus_pdfs, extract_case_id, GOLDEN_VERDICTS
from engine.checklist_engine import checklist_to_test_plan, execute_checklist
from engine.checklist_registry import CHECKLIST_VERSION
from services.calibration import run_calibration
from services.corpus_evaluator import evaluate_full_corpus, evaluate_single_pdf
from services.feature_extractor import extract_features
from services.pdf_parser import extract_text_from_pdf
from services.reference_documents import REFERENCE_RENDER_DIR, get_reference_document
from services.expert_decisions import delete_entry, list_entries, record_decision
from services.upload_service import UPLOADS_DIR, process_upload

app = FastAPI(
    title="Autocomply API",
    description=(
        "RegTech platform for vehicle homologation (Einzelabnahme). "
        "One Gutachten in, one auditable verdict out."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8010",
        "http://localhost:8010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_RENDER_DIR.mkdir(parents=True, exist_ok=True)

CHECKLIST_ENGINE_VERSION = "0.3.1-learning"


@app.on_event("startup")
def bootstrap_learning_if_empty() -> None:
    """Seed learned hints from hackathon corpus when no uploads exist yet."""
    try:
        from services.learning_engine import bootstrap_from_hackathon, model_status

        status = model_status()
        if status["exemplar_count"] == 0 and status["corpus_files"] == 0:
            bootstrap_from_hackathon()
    except Exception:
        pass


@app.get("/api/health")
def health_check():
    from services.llm_guidance import llm_available

    return {
        "status": "ok",
        "service": "autocomply-api",
        "version": CHECKLIST_ENGINE_VERSION,
        "checklist_engine": True,
        "checklist_version": CHECKLIST_VERSION,
        "llm_available": llm_available(),
    }


@app.get("/api/uploads/{upload_id}/checklist", response_model=ChecklistExecution)
def get_upload_checklist(upload_id: str):
    """Re-run checklist on a previously uploaded PDF (fallback / refresh)."""
    pdf_path = UPLOADS_DIR / upload_id / "original.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"Upload '{upload_id}' not found.")
    full_text, pages = extract_text_from_pdf(str(pdf_path))
    features = extract_features(
        full_text,
        filename=pdf_path.name,
        page_count=len(pages),
    )
    return execute_checklist(features, gutachten_id=upload_id)


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases():
    """Return archetypal reference cases for frontend selection."""
    return get_case_summaries()


@app.get("/api/cases/{case_id}", response_model=Gutachten)
def get_case(case_id: str):
    """Return full Gutachten JSON for a specific mock case."""
    if case_id not in MOCK_CASES:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return MOCK_CASES[case_id]


@app.get("/api/cases/{case_id}/document", response_model=UploadedDocument)
def get_case_document(case_id: str):
    """Return rendered PDF pages + paragraph annotations for a reference case."""
    doc = get_reference_document(case_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No PDF document available for case '{case_id}'.",
        )
    return doc


@app.post("/api/analyze", response_model=TestPlanResult)
def analyze_gutachten(gutachten: Gutachten):
    """
    Accept structured Gutachten JSON and return deterministic test plan result.
    No generative inference — rules engine only.
    """
    return execute_test_plan(gutachten)


@app.post("/api/checklist/analyze", response_model=ChecklistExecution)
def analyze_with_checklist(gutachten: Gutachten):
    """
    Run fixed checklist against structured Gutachten (re-extracts from notes if present).
    Deterministic white-box execution — no file-ID hardcoding.
    """
    text = gutachten.notes or ""
    features = extract_features(text, filename=gutachten.title)
    return execute_checklist(features, gutachten_id=gutachten.gutachten_id)


@app.get("/api/corpus")
def list_hackathon_corpus():
    """List available hackathon test PDFs with golden verdicts."""
    pdfs = list_corpus_pdfs()
    items = []
    for pdf in pdfs:
        case_id = extract_case_id(pdf.name) or pdf.stem
        golden = GOLDEN_VERDICTS.get(case_id, {})
        items.append({
            "case_id": case_id,
            "filename": pdf.name,
            "path": str(pdf),
            "expected_verdict": golden.get("verdict", "UNKNOWN"),
            "expected_gap": golden.get("gap"),
        })
    return {"total": len(items), "cases": items}


@app.post("/api/corpus/{case_id}/analyze", response_model=ChecklistExecution)
def analyze_corpus_case(case_id: str):
    """Analyze a specific hackathon corpus PDF by case ID (e.g. 1146)."""
    pdf_path = find_corpus_pdf(case_id)
    if pdf_path is None:
        raise HTTPException(status_code=404, detail=f"Corpus case '{case_id}' not found.")
    full_text, pages = extract_text_from_pdf(str(pdf_path))
    features = extract_features(full_text, filename=pdf_path.name, page_count=len(pages))
    return execute_checklist(features, gutachten_id=case_id)


@app.post("/api/corpus/{case_id}/analyze-full", response_model=UploadResponse)
def analyze_corpus_case_full(case_id: str):
    """Full pipeline for hackathon corpus PDF: extract → checklist → annotations."""
    pdf_path = find_corpus_pdf(case_id)
    if pdf_path is None:
        raise HTTPException(status_code=404, detail=f"Corpus case '{case_id}' not found.")
    return process_upload(pdf_path.read_bytes(), pdf_path.name)


@app.post("/api/evaluate-corpus")
def evaluate_corpus():
    """Score checklist engine against all 50 golden corpus PDFs."""
    return evaluate_full_corpus()


@app.post("/api/calibrate")
def calibrate_against_solution_key():
    """
    Validate engine against Lösungsschlüssel:
    GREEN → keine error-Flags; YELLOW → primärer Gap-Check muss feuern.
    """
    return run_calibration()


@app.get("/api/learn/status")
def learning_status():
    """How many Gutachten the hint engine has learned from."""
    from services.learning_engine import model_status

    return model_status()


@app.post("/api/learn/rebuild")
def rebuild_learning_model():
    """Re-scan training_corpus/ and rebuild learned_model.json."""
    from services.learning_engine import rebuild_model_from_corpus

    return rebuild_model_from_corpus()


@app.post("/api/learn/bootstrap")
def bootstrap_learning_from_hackathon():
    """Process all hackathon PDFs into the learning model (no new uploads)."""
    from services.learning_engine import bootstrap_from_hackathon

    return bootstrap_from_hackathon()


@app.get("/api/reference/regulatory/mbl751.pdf")
def get_merkblatt_751_pdf():
    """Serve VdTÜV Merkblatt 751 PDF from hackathon bundle or reference_docs."""
    from services.merkblatt_extractor import resolve_merkblatt_pdf

    pdf = resolve_merkblatt_pdf()
    if pdf is None or not pdf.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "Merkblatt 751 PDF nicht gefunden. "
                "Lege die Datei unter hackathon-data/Hackathon/Merkblatt - Procedural Instructions - Level 2/ ab."
            ),
        )
    return FileResponse(
        pdf,
        media_type="application/pdf",
        filename="VdTUEV_Merkblatt_751.pdf",
    )


@app.post("/api/expert-review", response_model=ExpertReviewResponse)
def submit_expert_review(review: ExpertReviewRequest):
    """
    Expert verdict on a flagged finding — persisted by fingerprint.
    approve → reusable override, future identical findings pass
    automatically; reject → confirmed defect, the finding stays flagged
    as expert-confirmed and the verdict becomes FAIL once every finding
    on the document is confirmed.
    """
    entry = record_decision(
        check_id=review.check_id,
        check_name=review.check_name,
        evidence=review.evidence,
        decision=review.decision,
        note=review.note,
        gutachten_id=review.gutachten_id,
        expert=review.expert,
    )
    return ExpertReviewResponse(
        decision=review.decision,
        stored=entry is not None,
        entry=ExpertKnowledgeEntry(**entry) if entry else None,
    )


@app.get("/api/expert-knowledge", response_model=list[ExpertKnowledgeEntry])
def get_expert_knowledge():
    """List all saved expert decisions (overrides and confirmations)."""
    return [ExpertKnowledgeEntry(**e) for e in list_entries()]


@app.delete("/api/expert-knowledge/{entry_id}")
def remove_expert_knowledge(entry_id: str):
    """Withdraw a saved expert decision."""
    if not delete_entry(entry_id):
        raise HTTPException(status_code=404, detail=f"Entry '{entry_id}' not found.")
    return {"deleted": entry_id}


@app.get("/api/expert/procedures/{check_id}", response_model=ExpertProcedureResponse)
def get_expert_procedure(check_id: str):
    """Structured expert / Merkblatt procedure for one checklist rule."""
    from services.expert_knowledge import get_procedure

    return get_procedure(check_id)


@app.post(
    "/api/expert/nachpruefung/{upload_id}",
    response_model=ExpertNachpruefungResponse,
)
def expert_nachpruefung(
    upload_id: str,
    check_id: str | None = Query(None, description="Einzelne Beanstandung; leer = alle"),
    use_llm: bool = Query(True, description="LLM-Aufbereitung wenn OPENAI_API_KEY gesetzt"),
):
    """
    Nachprüf-Anleitung aus Expertenwissen + Merkblatt + Lernkorpus.
    Optional LLM-Aufbereitung — Verdict bleibt in der Checklist-Engine.
    """
    from services.expert_knowledge import build_nachpruefung

    try:
        return build_nachpruefung(upload_id, check_id=check_id, use_llm=use_llm)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/expert/merkblatt/extract")
def extract_merkblatt_sections(force: bool = Query(False)):
    """Extract Merkblatt 751 I.5.x sections from PDF into expert cache."""
    from services.expert_knowledge import extract_merkblatt_knowledge

    return extract_merkblatt_knowledge(force_refresh=force)


@app.post("/api/upload", response_model=UploadResponse)
async def upload_gutachten_pdf(file: UploadFile = File(...)):
    """
    Upload Gutachten PDF or unstructured ZIP bundle (Protokoll + Anlagen + Aufstellung).
    Pipeline: extract → checklist → annotations + page images.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dateiname fehlt.")
    lower = file.filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".zip")):
        raise HTTPException(status_code=400, detail="Nur PDF oder ZIP werden akzeptiert.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    max_mb = 50 if lower.endswith(".zip") else 20
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Datei zu groß (max {max_mb} MB).")

    try:
        return process_upload(content, file.filename)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Verarbeitung fehlgeschlagen: {exc}",
        ) from exc


# Static mounts last — otherwise they shadow /api/uploads/{id}/checklist
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/api/reference", StaticFiles(directory=str(REFERENCE_RENDER_DIR)), name="reference")
