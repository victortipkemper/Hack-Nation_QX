"""
PDF text-block extraction with precise bounding boxes for paragraph-level highlighting.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from schemas.upload import HighlightRegion


@dataclass
class TextBlock:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float
    page_height: float

    def to_region(self, label: str = "", padding_pct: float = 0.3) -> HighlightRegion:
        pw, ph = self.page_width, self.page_height
        pad_x = pw * padding_pct / 100
        pad_y = ph * padding_pct / 100
        x0 = max(0, self.x0 - pad_x)
        y0 = max(0, self.y0 - pad_y)
        x1 = min(pw, self.x1 + pad_x)
        y1 = min(ph, self.y1 + pad_y)
        return HighlightRegion(
            page=self.page,
            top=round(y0 / ph * 100, 2),
            left=round(x0 / pw * 100, 2),
            width=round((x1 - x0) / pw * 100, 2),
            height=round((y1 - y0) / ph * 100, 2),
            label=label or self.text[:40],
        )


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower().strip()


def _merge_rects(rects: list, page_width: float, page_height: float) -> tuple[float, float, float, float] | None:
    if not rects:
        return None
    x0 = min(r.x0 for r in rects)
    y0 = min(r.y0 for r in rects)
    x1 = max(r.x1 for r in rects)
    y1 = max(r.y1 for r in rects)
    return x0, y0, x1, y1


def _find_in_text_blocks(page, phrases: list[str], pw: float, ph: float) -> tuple[float, float, float, float] | None:
    """Fallback: match phrases against text blocks with bounding boxes."""
    data = page.get_text("dict")
    normalized_phrases = [_normalize(p) for p in phrases if len(p) >= 3]

    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines_text: list[str] = []
        x0, y0, x1, y1 = float("inf"), float("inf"), 0.0, 0.0
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span.get("text", "")
                lines_text.append(t)
                bbox = span.get("bbox", [0, 0, 0, 0])
                x0 = min(x0, bbox[0])
                y0 = min(y0, bbox[1])
                x1 = max(x1, bbox[2])
                y1 = max(y1, bbox[3])
        block_text = _normalize(" ".join(lines_text))
        if x0 >= float("inf"):
            continue
        for phrase in normalized_phrases:
            if phrase in block_text or phrase[:12] in block_text:
                return x0, y0, x1, y1
    return None


def _search_phrase(page, phrase: str) -> list:
    """Search with fallbacks for encoding variants."""
    variants = [
        phrase,
        phrase.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss"),
        phrase.replace("§", "SS"),
    ]
    for v in variants:
        rects = page.search_for(v)
        if rects:
            return rects
    # partial: first 20 chars
    if len(phrase) > 15:
        rects = page.search_for(phrase[:20])
        if rects:
            return rects
    return []


def find_regions_from_evidence(
    pdf_path: str,
    phrases: list[str],
    label: str = "",
) -> list[HighlightRegion]:
    """Search PDF for phrases extracted from checklist evidence."""
    regions: list[HighlightRegion] = []
    for phrase in phrases:
        if len(phrase) < 3:
            continue
        found = find_anchor_regions(pdf_path, [phrase], label=label)
        regions.extend(found)
        if regions:
            break
    return regions[:3]


def find_anchor_regions(
    pdf_path: str,
    search_phrases: list[str],
    page_hint: int | None = None,
    merge_phrases: list[str] | None = None,
    label: str = "",
) -> list[HighlightRegion]:
    """
    Find precise highlight regions for a paragraph anchor.
    Merges multiple phrase matches into one bounding box per page.
    """
    try:
        import fitz
    except ImportError:
        return []

    regions: list[HighlightRegion] = []
    doc = fitz.open(pdf_path)

    pages_to_search = (
        [page_hint - 1] if page_hint and 1 <= page_hint <= len(doc) else range(len(doc))
    )

    for page_idx in pages_to_search:
        page = doc[page_idx]
        pw, ph = page.rect.width, page.rect.height
        page_num = page_idx + 1
        all_rects = []

        for phrase in search_phrases + (merge_phrases or []):
            all_rects.extend(_search_phrase(page, phrase))

        merged = _merge_rects(all_rects, pw, ph)
        if not merged:
            merged = _find_in_text_blocks(page, search_phrases + (merge_phrases or []), pw, ph)
        if not merged:
            continue

        x0, y0, x1, y1 = merged

        # Expand narrow matches to minimum readable width (paragraph lines)
        min_width_pct = 25
        current_w = (x1 - x0) / pw * 100
        if current_w < min_width_pct:
            expand = (min_width_pct / 100 * pw - (x1 - x0)) / 2
            x0 = max(0, x0 - expand)
            x1 = min(pw, x1 + expand)

        block = TextBlock(page_num, label, x0, y0, x1, y1, pw, ph)
        regions.append(block.to_region(label=label, padding_pct=0.15))

        if page_hint:
            break

    doc.close()
    return regions


def extract_page_paragraphs(pdf_path: str) -> list[TextBlock]:
    """Extract all text blocks with bboxes — used for training corpus."""
    try:
        import fitz
    except ImportError:
        return []

    blocks: list[TextBlock] = []
    doc = fitz.open(pdf_path)
    for page_idx, page in enumerate(doc):
        pw, ph = page.rect.width, page.rect.height
        data = page.get_text("dict")
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            lines_text = []
            x0, y0, x1, y1 = float("inf"), float("inf"), 0, 0
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    t = span.get("text", "").strip()
                    if t:
                        lines_text.append(t)
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    x0 = min(x0, bbox[0])
                    y0 = min(y0, bbox[1])
                    x1 = max(x1, bbox[2])
                    y1 = max(y1, bbox[3])
            text = " ".join(lines_text).strip()
            if text and x0 < float("inf"):
                blocks.append(
                    TextBlock(page_idx + 1, text, x0, y0, x1, y1, pw, ph)
                )
    doc.close()
    return blocks


def find_paragraph_by_stvzo_ref(
    pdf_path: str, paragraph_ref: str
) -> list[HighlightRegion]:
    """Match §-references like '§36', '§ 19', 'Zu 15.1/2' in document."""
    ref_clean = paragraph_ref.replace(" ", "")
    patterns = [paragraph_ref, ref_clean]
    if "§" in paragraph_ref:
        num = re.search(r"§\s*(\d+)", paragraph_ref)
        if num:
            patterns.append(f"§{num.group(1)}")
            patterns.append(f"SS{num.group(1)}")
    return find_anchor_regions(pdf_path, patterns, label=paragraph_ref)
