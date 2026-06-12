"""
Process unstructured document bundles (ZIP with Protokoll + Anlagen + Aufstellung).
Merges text/image evidence for checklist — deterministic, no per-file-ID logic.
"""

import json
import re
import uuid
import zipfile
from pathlib import Path

from engine.checklist_engine import checklist_to_test_plan, execute_checklist
from schemas.features import BundleEvidence, DocumentFeatures, PhotoEvidenceItem, ProtocolSectionResult
from schemas.upload import UploadResponse
from services.bundle_classifier import BundleRole, is_photo_annex_file, resolve_role
from services.document_annotator import build_uploaded_document
from services.feature_extractor import extract_features
from services.image_evidence import analyze_photo_evidence
from services.pdf_parser import extract_text_from_pdf, parse_gutachten_from_pdf
from services.pdf_renderer import render_pdf_pages
from services.protocol_parser import parse_protocol
from services.training_store import save_training_exemplar
from services.upload_service import UPLOADS_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
PDF_EXTENSIONS = {".pdf"}


def process_bundle_upload(file_bytes: bytes, filename: str) -> UploadResponse:
    upload_id = str(uuid.uuid4())
    upload_dir = UPLOADS_DIR / upload_id
    bundle_dir = upload_dir / "bundle"
    pages_dir = upload_dir / "pages"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    _extract_archive(file_bytes, filename, bundle_dir)

    members = sorted(
        p
        for p in bundle_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in PDF_EXTENSIONS | IMAGE_EXTENSIONS
    )
    if not members:
        raise ValueError("ZIP enthält keine PDF- oder Bilddateien.")

    file_records: list[dict] = []
    combined_text_parts: list[str] = []
    combined_page_texts: list[str] = []
    page_sources: list[dict] = []
    global_page = 0

    roles_map: dict[str, str] = {}
    protocol_text = ""
    photo_items: list[PhotoEvidenceItem] = []
    protocol_sections: list[ProtocolSectionResult] = []
    protocol_all_passed = True
    vins: list[str] = []
    gutachten_nr = ""

    composite_path = upload_dir / "composite.pdf"
    _init_composite_pdf(composite_path)

    for member in members:
        rel = str(member.relative_to(bundle_dir))
        start_global_page = global_page + 1

        if member.suffix.lower() in IMAGE_EXTENSIONS:
            role = BundleRole.ANLAGEN.value
            text = f"[Bild-Anlage: {member.name}]"
            page_texts = [text]
            _image_to_page_png(member, pages_dir, start_global_page)
            _append_image_to_composite(composite_path, member)
        else:
            text, page_texts = extract_text_from_pdf(str(member))
            role = resolve_role(member.name, text).value
            tmp_render = render_pdf_pages(str(member), str(pages_dir / f"_tmp_{member.stem}"))
            _append_pdf_to_composite(composite_path, member)
            for i, png_path in enumerate(tmp_render):
                dst = pages_dir / f"{start_global_page + i}.png"
                src = Path(png_path)
                if src.exists():
                    dst.write_bytes(src.read_bytes())

        roles_map[rel] = role
        combined_text_parts.append(f"\n--- {member.name} ({role}) ---\n{text}")

        for i, pt in enumerate(page_texts):
            global_page += 1
            combined_page_texts.append(pt)
            page_sources.append(
                {"page": global_page, "source": rel, "role": role, "source_page": i + 1}
            )

        if role == BundleRole.PROTOKOLL.value:
            protocol_text += "\n" + text
            pa = parse_protocol(text)
            if pa.gutachten_nr:
                gutachten_nr = pa.gutachten_nr
            if pa.vin:
                vins.append(pa.vin)
            protocol_all_passed = protocol_all_passed and pa.all_passed
            for sec in pa.sections:
                protocol_sections.append(
                    ProtocolSectionResult(
                        section_id=sec.section_id,
                        title=sec.title,
                        final_passed=sec.final_passed,
                        fulfilled_markers=sec.fulfilled_markers,
                        open_markers=sec.open_markers,
                        reason=sec.final_reason,
                    )
                )

        role_enum = BundleRole(role) if role in [r.value for r in BundleRole] else BundleRole.OTHER
        first_page = page_texts[0] if page_texts else ""
        if (
            member.suffix.lower() == ".pdf"
            and is_photo_annex_file(role_enum, member.name, first_page)
        ):
            pe = analyze_photo_evidence(str(member), page_texts, rel)
            for item in pe.items:
                photo_items.append(
                    PhotoEvidenceItem(
                        label=item.label,
                        page=start_global_page + item.page - 1,
                        source_file=item.source_file,
                        has_image=item.has_image,
                        image_count=item.image_count,
                        confidence=item.confidence,
                        note=item.note,
                    )
                )

        vin_matches = re.findall(r"\b[A-HJ-NPR-Z0-9]{17}\b", text)
        vins.extend(vin_matches)

        file_records.append({"file": rel, "role": role, "pages": len(page_texts)})

    combined_text = "\n".join(combined_text_parts)
    unique_vins = list(dict.fromkeys(vins))
    vin_consistent = len(unique_vins) <= 1

    if not gutachten_nr:
        ga = re.search(r"\b([A-Z0-9]{6,}-?\d*)\b", combined_text)
        gutachten_nr = ga.group(1) if ga else upload_id[:8]

    features = extract_features(
        combined_text,
        filename=filename,
        page_count=len(combined_page_texts),
    )
    features = _apply_bundle_evidence(
        features,
        BundleEvidence(
            is_bundle=True,
            source_zip=filename,
            gutachten_nr=gutachten_nr,
            files=[r["file"] for r in file_records],
            roles=roles_map,
            vin=unique_vins[0] if unique_vins else features.vin,
            vin_consistent=vin_consistent,
            vins_found=unique_vins,
            has_protokoll=any(r["role"] == BundleRole.PROTOKOLL.value for r in file_records),
            has_anlagen=any(
                r["role"] in (BundleRole.PHOTO_ANLAGEN.value, BundleRole.ANLAGEN.value)
                for r in file_records
            ),
            has_photo_anlagen=any(
                r["role"] == BundleRole.PHOTO_ANLAGEN.value for r in file_records
            ),
            has_gutachten=any(r["role"] == BundleRole.GUTACHTEN.value for r in file_records),
            has_aufstellung=any(r["role"] == BundleRole.AUFSTELLUNG.value for r in file_records),
            has_national_aufstellung=any(
                r["role"] == BundleRole.AUFSTELLUNG.value for r in file_records
            ),
            protocol_sections=protocol_sections,
            protocol_all_passed=protocol_all_passed,
            protocol_summary=parse_protocol(protocol_text).summary if protocol_text else "",
            photo_evidence=photo_items,
            photos_complete=all(p.has_image for p in photo_items) if photo_items else False,
            combined_page_count=len(combined_page_texts),
        ),
    )

    gutachten = parse_gutachten_from_pdf(combined_text, filename, upload_id)
    if unique_vins:
        gutachten.vehicle.vin = unique_vins[0]
    gutachten.title = f"Bundle {gutachten_nr}"
    gutachten.gutachten_id = gutachten_nr or upload_id
    gutachten.notes = (
        f"Unstrukturiertes Dokumentenpaket: {len(file_records)} Dateien, "
        f"{len(combined_page_texts)} Seiten."
    )

    checklist_execution = execute_checklist(features, gutachten_id=gutachten.gutachten_id)
    test_plan = checklist_to_test_plan(checklist_execution)

    manifest = {
        "upload_id": upload_id,
        "bundle_files": file_records,
        "page_sources": page_sources,
        "gutachten_nr": gutachten_nr,
        "vins": unique_vins,
    }
    (upload_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pdf_for_annot = str(composite_path if composite_path.exists() else members[0])
    document = build_uploaded_document(
        upload_id=upload_id,
        filename=filename,
        pdf_path=pdf_for_annot,
        page_count=len(combined_page_texts),
        page_texts=combined_page_texts,
        test_plan=test_plan,
        checklist_execution=checklist_execution,
    )

    response = UploadResponse(
        upload_id=upload_id,
        gutachten=gutachten,
        test_plan=test_plan,
        checklist_execution=checklist_execution,
        document=document,
        bundle_manifest=manifest,
    )
    save_training_exemplar(response, pdf_for_annot)
    return response


def _extract_archive(file_bytes: bytes, filename: str, dest: Path) -> None:
    if filename.lower().endswith(".zip"):
        import io

        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            zf.extractall(dest)
        return
    dest.joinpath(filename).write_bytes(file_bytes)


def _init_composite_pdf(path: Path) -> None:
    try:
        import fitz

        doc = fitz.open()
        doc.save(str(path))
        doc.close()
    except Exception:
        pass


def _append_pdf_to_composite(composite: Path, pdf_path: Path) -> None:
    try:
        import fitz

        if not composite.exists():
            return
        doc = fitz.open(str(composite))
        src = fitz.open(str(pdf_path))
        doc.insert_pdf(src)
        doc.save(str(composite))
        doc.close()
        src.close()
    except Exception:
        pass


def _append_image_to_composite(composite: Path, image_path: Path) -> None:
    try:
        import fitz

        if not composite.exists():
            return
        doc = fitz.open(str(composite))
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, filename=str(image_path))
        doc.save(str(composite))
        doc.close()
    except Exception:
        pass


def _image_to_page_png(image_path: Path, pages_dir: Path, page_num: int) -> list[str]:
    pages_dir.mkdir(parents=True, exist_ok=True)
    try:
        import fitz

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, filename=str(image_path))
        out = pages_dir / f"{page_num}.png"
        page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(str(out))
        doc.close()
        return [str(out)]
    except Exception:
        return []


def _apply_bundle_evidence(features: DocumentFeatures, bundle: BundleEvidence) -> DocumentFeatures:
    data = features.model_dump()
    data["bundle"] = bundle.model_dump()
    if bundle.vin:
        data["vin"] = bundle.vin
    if bundle.is_bundle and features.route == "unknown":
        data["route"] = "21"
    return DocumentFeatures(**data)
