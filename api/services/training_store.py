"""
Training corpus store — accumulates uploaded documents for future model training.
Each entry: extracted paragraphs, rules results, annotations, remediation patterns.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from schemas.upload import UploadResponse
from services.pdf_blocks import extract_page_paragraphs

CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "training_corpus"


def save_training_exemplar(response: UploadResponse, pdf_path: str) -> None:
    """
    Persist upload as training exemplar (JSON).
    TODO: Feed into fine-tuning pipeline for paragraph detection + explanation generation.
    """
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    paragraphs = extract_page_paragraphs(pdf_path)
    exemplar = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "upload_id": response.upload_id,
        "filename": response.document.filename,
        "gutachten_type": response.gutachten.gutachten_type,
        "verdict": response.test_plan.final_verdict.status.value,
        "gutachten": response.gutachten.model_dump(mode="json"),
        "test_plan": response.test_plan.model_dump(mode="json"),
        "checklist_steps": [
            s.model_dump() for s in response.checklist_execution.steps
        ],
        "bundle_manifest": response.bundle_manifest,
        "annotations": [a.model_dump() for a in response.document.annotations],
        "paragraphs": [
            {
                "page": b.page,
                "text": b.text,
                "bbox_pct": {
                    "top": round(b.y0 / b.page_height * 100, 2),
                    "left": round(b.x0 / b.page_width * 100, 2),
                    "width": round((b.x1 - b.x0) / b.page_width * 100, 2),
                    "height": round((b.y1 - b.y0) / b.page_height * 100, 2),
                },
            }
            for b in paragraphs
        ],
        "training_labels": {
            "paragraph_rule_mapping": [
                {
                    "rule_id": a.rule_id,
                    "paragraph_ref": a.paragraph_ref,
                    "regions": [r.model_dump() for r in a.regions],
                    "remediation": a.remediation_hint,
                }
                for a in response.document.annotations
            ],
            # TODO: Human auditor corrections override for supervised learning
            "auditor_corrections": [],
        },
    }

    out_path = CORPUS_DIR / f"{response.upload_id}.json"
    out_path.write_text(json.dumps(exemplar, ensure_ascii=False, indent=2), encoding="utf-8")

    from services.learning_engine import learn_from_exemplar

    learn_from_exemplar(exemplar)
