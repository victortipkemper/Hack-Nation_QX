"""Detect photo / scan evidence in Foto-Anlagen PDFs (image-heavy unstructured docs)."""

import re
from dataclasses import dataclass, field

# Labels on dedicated photo-annex pages (not §59 Fabrikschilder in Aufstellung!)
PHOTO_LABEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("3/4_vorn", re.compile(r"3/4\s+Ansicht\s+vorn", re.I)),
    ("3/4_hinten", re.compile(r"3/4\s+Ansicht\s+hinten", re.I)),
    ("fin", re.compile(r"(?:^|\n)\s*FIN\s*(?:\n|$)", re.I | re.M)),
    ("fabrikschild", re.compile(r"(?:^|\n)\s*Fabrikschild\s*(?:\n|$)", re.I | re.M)),
    ("zbi", re.compile(r"(?:^|\n)\s*ZBI\s*(?:\n|$)", re.I | re.M)),
]

# Only these count for pass/fail — no false flags from §-text or TGA mentions
CANONICAL_PHOTO_LABELS = frozenset({"3/4_vorn", "3/4_hinten", "fin", "fabrikschild", "zbi"})

# Pages that are NOT photo annex (TGA tables, Aufstellung, Prüfplan text, …)
_NON_PHOTO_PAGE_MARKERS = re.compile(
    r"g-zl\.:|reifenvergleich|verwendungsbereich|aufstellung der technischen|"
    r"§\s*\d|paragraph\s*\(§\)|prüfbericht zu ga-nr|tüv austria",
    re.I,
)


@dataclass
class PhotoEvidenceItem:
    label: str
    page: int
    source_file: str
    has_image: bool
    image_count: int
    confidence: float = 0.0
    note: str = ""


@dataclass
class PhotoEvidenceAnalysis:
    items: list[PhotoEvidenceItem] = field(default_factory=list)
    required_labels_found: list[str] = field(default_factory=list)
    missing_image_labels: list[str] = field(default_factory=list)
    complete: bool = True
    summary: str = ""


def is_photo_annex_page(text: str) -> bool:
    """True only for dedicated Foto-Anlagen pages, not TGA/Aufstellung sheets."""
    if not text.strip():
        return False
    lower = text.lower()
    if _NON_PHOTO_PAGE_MARKERS.search(text):
        # Exception: first pages of Anl.pdf have header + photos
        if "anlagen zu gutachten" in lower and (
            "3/4 ansicht" in lower or "fabrikschild" in lower or re.search(r"(?:^|\n)\s*fin\s", lower, re.M)
        ):
            return True
        return False
    if "anlagen zu gutachten" in lower:
        return True
    if re.search(r"3/4\s+ansicht", lower):
        return True
    return False


def _page_has_substantial_image(pdf_path: str, page_index: int) -> tuple[bool, int, float]:
    try:
        import fitz
    except ImportError:
        return False, 0, 0.0

    doc = fitz.open(pdf_path)
    page = doc[page_index]
    images = page.get_images(full=True)
    img_count = len(images)

    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
    samples = pix.samples
    if not samples:
        doc.close()
        return img_count > 0, img_count, 0.85 if img_count else 0.0

    non_white = sum(
        1
        for i in range(0, len(samples), pix.n)
        if any(samples[i + c] < 235 for c in range(min(3, pix.n)))
    )
    total_px = max(len(samples) // max(pix.n, 1), 1)
    ratio = non_white / total_px
    doc.close()

    # Embedded image OR substantial non-blank render (scanned photo page)
    has_visual = img_count > 0 or ratio > 0.06
    confidence = 0.95 if img_count > 0 else min(0.88, ratio * 4)
    return has_visual, img_count, confidence


def _labels_on_page(text: str) -> list[str]:
    if not is_photo_annex_page(text):
        return []
    found: list[str] = []
    for label_id, pattern in PHOTO_LABEL_PATTERNS:
        if pattern.search(text):
            found.append(label_id)
    return found


def analyze_photo_evidence(
    pdf_path: str,
    page_texts: list[str],
    source_file: str,
) -> PhotoEvidenceAnalysis:
    """Analyze only Foto-Anlagen pages — ignores §59 Fabrikschilder etc. in other PDFs."""
    analysis = PhotoEvidenceAnalysis()
    seen_labels: dict[str, PhotoEvidenceItem] = {}

    for page_idx, text in enumerate(page_texts):
        if not is_photo_annex_page(text):
            continue
        labels = _labels_on_page(text)
        if not labels:
            continue
        has_img, img_count, conf = _page_has_substantial_image(pdf_path, page_idx)
        for label in labels:
            if label not in CANONICAL_PHOTO_LABELS:
                continue
            item = PhotoEvidenceItem(
                label=label,
                page=page_idx + 1,
                source_file=source_file,
                has_image=has_img,
                image_count=img_count,
                confidence=conf,
                note="Bild/Scan erkannt" if has_img else "Label ohne Bildinhalt",
            )
            prev = seen_labels.get(label)
            # Keep best evidence per label (image wins over text-only mention)
            if prev is None or (item.has_image and not prev.has_image):
                seen_labels[label] = item

    analysis.items = list(seen_labels.values())
    for item in analysis.items:
        analysis.required_labels_found.append(item.label)
        if not item.has_image:
            analysis.missing_image_labels.append(item.label)
            analysis.complete = False

    if analysis.items:
        ok = sum(1 for i in analysis.items if i.has_image)
        analysis.summary = (
            f"{ok}/{len(analysis.items)} Fotonachweise mit Bildinhalt "
            f"({', '.join(analysis.required_labels_found)})."
        )
    else:
        analysis.summary = "Keine Foto-Anlagen-Seiten erkannt."
        analysis.complete = True  # no photo annex → no false failure

    return analysis
