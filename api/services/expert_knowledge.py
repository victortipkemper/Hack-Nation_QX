"""
Aggregate expert knowledge: Merkblatt excerpts, procedures, learned corpus, optional LLM.
"""

from __future__ import annotations

from pathlib import Path

from data.checklist_knowledge import CHECKLIST_KNOWLEDGE
from data.expert_procedures import (
    DEFAULT_NACHPRUEFUNG,
    EXPERT_PROCEDURES,
    ExpertProcedure,
    ProcedureStep,
)
from engine.checklist_engine import execute_checklist
from schemas.expert import (
    ExpertGuidanceItem,
    ExpertNachpruefungResponse,
    ExpertProcedureResponse,
    ProcedureStepOut,
)
from schemas.whitebox import ChecklistExecution, WhiteBoxStep
from services.feature_extractor import extract_features
from services.learning_engine import get_learned_hints
from services.llm_guidance import llm_available, prepare_nachpruefung_guide, template_guide
from services.merkblatt_extractor import excerpt_for_sections, get_merkblatt_sections, resolve_merkblatt_pdf
from services.pdf_parser import extract_text_from_pdf

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def _step_out(s: ProcedureStep) -> ProcedureStepOut:
    return ProcedureStepOut(
        order=s.order,
        title=s.title,
        instruction=s.instruction,
        acceptance_criteria=s.acceptance_criteria,
        tools=s.tools,
    )


def _is_error_step(step: WhiteBoxStep) -> bool:
    return (
        step.severity == "error"
        and step.executed
        and (step.flagged or step.passed is False)
    )


def _procedure_for(check_id: str) -> ExpertProcedure | None:
    return EXPERT_PROCEDURES.get(check_id)


def get_procedure(check_id: str) -> ExpertProcedureResponse:
    proc = _procedure_for(check_id)
    knowledge = CHECKLIST_KNOWLEDGE.get(check_id)
    sections = proc.merkblatt_sections if proc else []
    excerpt = excerpt_for_sections(sections)

    if not proc:
        return ExpertProcedureResponse(
            check_id=check_id,
            procedure_available=False,
            merkblatt_sections=sections,
            merkblatt_excerpt=excerpt,
            practice_notes=[knowledge.explanation_template] if knowledge else [],
        )

    return ExpertProcedureResponse(
        check_id=check_id,
        procedure_available=True,
        merkblatt_sections=sections,
        merkblatt_excerpt=excerpt,
        standard_procedure=[_step_out(s) for s in proc.standard_procedure],
        nachpruefung_steps=[_step_out(s) for s in proc.nachpruefung],
        documentation_checklist=proc.documentation_checklist,
        practice_notes=proc.practice_notes,
    )


def _build_item(
    step: WhiteBoxStep,
    exemplar_key: str,
    use_llm: bool,
) -> ExpertGuidanceItem:
    proc = _procedure_for(step.check_id)
    knowledge = CHECKLIST_KNOWLEDGE.get(step.check_id)

    sections = proc.merkblatt_sections if proc else []
    excerpt = excerpt_for_sections(sections)

    std_steps = proc.standard_procedure if proc else []
    nach_steps = proc.nachpruefung if proc else DEFAULT_NACHPRUEFUNG
    docs = proc.documentation_checklist if proc else []
    notes = list(proc.practice_notes) if proc else []
    if knowledge and knowledge.explanation_template not in notes:
        notes.insert(0, knowledge.explanation_template)

    remediation, verification, _meta = get_learned_hints(exemplar_key, step.evidence)

    citations: list[str] = [step.citation]
    if knowledge:
        citations.extend(knowledge.extra_references)

    context = {
        "check_id": step.check_id,
        "check_name": step.check_name,
        "citation": step.citation,
        "finding": step.evidence or step.reason,
        "merkblatt_excerpt": excerpt[:1500],
        "standard_procedure": [s.__dict__ for s in std_steps],
        "nachpruefung_steps": [s.__dict__ for s in nach_steps],
        "documentation_checklist": docs,
        "practice_notes": notes,
        "learned_verification": verification,
        "learned_remediation": remediation,
    }

    llm_guide = ""
    if use_llm:
        llm_guide, _, _ = prepare_nachpruefung_guide(context)
    else:
        llm_guide = template_guide(context)

    return ExpertGuidanceItem(
        check_id=step.check_id,
        check_name=step.check_name,
        citation=step.citation,
        finding=step.evidence or step.reason,
        severity=step.severity,
        merkblatt_sections=sections,
        merkblatt_excerpt=excerpt[:2000],
        standard_procedure=[_step_out(s) for s in std_steps],
        nachpruefung_steps=[_step_out(s) for s in nach_steps],
        documentation_checklist=docs,
        practice_notes=notes,
        learned_verification=verification,
        learned_remediation=remediation,
        llm_guide=llm_guide,
        citations=list(dict.fromkeys(citations)),
    )


def _load_execution(upload_id: str) -> tuple[ChecklistExecution, str, Path]:
    upload_dir = UPLOADS_DIR / upload_id
    pdf_path = upload_dir / "original.pdf"
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Upload '{upload_id}' nicht gefunden.")

    full_text, pages = extract_text_from_pdf(str(pdf_path))
    features = extract_features(full_text, filename=pdf_path.name, page_count=len(pages))
    execution = execute_checklist(features, gutachten_id=upload_id)
    return execution, pdf_path.name, pdf_path


def _exemplar_key_for(check_id: str) -> str:
    from engine.checklist_registry import CHECKLIST

    for check in CHECKLIST:
        if check.check_id == check_id:
            return check.exemplar_key
    return ""


def build_nachpruefung(
    upload_id: str,
    check_id: str | None = None,
    use_llm: bool = True,
) -> ExpertNachpruefungResponse:
    execution, filename, _pdf = _load_execution(upload_id)

    flagged = [s for s in execution.steps if _is_error_step(s)]
    if check_id:
        flagged = [s for s in flagged if s.check_id == check_id]

    items: list[ExpertGuidanceItem] = []
    llm_used_any = False
    llm_model = None

    for step in flagged:
        key = _exemplar_key_for(step.check_id)
        item = _build_item(step, key, use_llm=use_llm and llm_available())
        if use_llm and llm_available():
            llm_used_any = True
            from services.llm_guidance import _default_model

            llm_model = _default_model()
        items.append(item)

    return ExpertNachpruefungResponse(
        upload_id=upload_id,
        filename=filename,
        flagged_count=len(items),
        llm_used=llm_used_any,
        llm_model=llm_model,
        merkblatt_available=bool(get_merkblatt_sections()) or resolve_merkblatt_pdf() is not None,
        items=items,
    )


def extract_merkblatt_knowledge(force_refresh: bool = False) -> dict:
    """One-shot: extract Merkblatt 751 sections into cache."""
    sections = get_merkblatt_sections(force_refresh=force_refresh)
    pdf = resolve_merkblatt_pdf()
    return {
        "pdf_found": pdf is not None,
        "pdf_path": str(pdf) if pdf else None,
        "section_count": len(sections),
        "section_ids": sorted(sections.keys()),
    }
