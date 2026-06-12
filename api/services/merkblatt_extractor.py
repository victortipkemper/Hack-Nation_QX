"""
Extract Merkblatt 751 sections from hackathon PDF for expert knowledge.
Cached as JSON — not used in verdict logic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "expert" / "merkblatt_751_extract.json"

HACKATHON_PDF = (
    Path(__file__).resolve().parent.parent.parent
    / "hackathon-data"
    / "Hackathon"
    / "Merkblatt - Procedural Instructions - Level 2"
    / "vdtuev_017_0751_2021-04-30 2.pdf"
)

BUNDLED_PDF = (
    Path(__file__).resolve().parent.parent / "data" / "reference_docs" / "Merkblatt_751.pdf"
)

SECTION_PATTERN = re.compile(
    r"I\.5\.1\.\d{1,2}|I\.5\.2\.\d{1,2}",
    re.I,
)


def resolve_merkblatt_pdf() -> Path | None:
    """Find Merkblatt 751 PDF (hackathon bundle or bundled copy)."""
    for path in (BUNDLED_PDF, HACKATHON_PDF):
        if path.is_file():
            return path
    return None


def _normalize_section_id(raw: str) -> str:
    return raw.strip().upper().replace(" ", "")


def extract_sections_from_pdf(pdf_path: Path) -> dict[str, str]:
    import fitz  # pymupdf

    doc = fitz.open(str(pdf_path))
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()

    # Split on section headers like I.5.1.6
    matches = list(SECTION_PATTERN.finditer(full_text))
    sections: dict[str, str] = {}

    for i, match in enumerate(matches):
        sec_id = _normalize_section_id(match.group())
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        chunk = re.sub(r"\s+", " ", full_text[start:end]).strip()
        if len(chunk) > 80:
            sections[sec_id] = chunk[:4000]

    return sections


def get_merkblatt_sections(force_refresh: bool = False) -> dict[str, str]:
    """Return cached Merkblatt section text, extracting from PDF if needed."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_PATH.is_file() and not force_refresh:
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            return data.get("sections", {})
        except (json.JSONDecodeError, OSError):
            pass

    pdf = resolve_merkblatt_pdf()
    if pdf is None:
        return {}

    sections = extract_sections_from_pdf(pdf)
    payload = {
        "source_pdf": str(pdf),
        "section_count": len(sections),
        "sections": sections,
    }
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return sections


def excerpt_for_sections(section_ids: list[str], max_len: int = 1200) -> str:
    """Concatenate Merkblatt excerpts for given section IDs."""
    if not section_ids:
        return ""
    all_sections = get_merkblatt_sections()
    parts: list[str] = []
    for sid in section_ids:
        key = _normalize_section_id(sid)
        text = all_sections.get(key, "")
        if text:
            parts.append(f"[{key}] {text[:max_len]}")
    return "\n\n".join(parts)
