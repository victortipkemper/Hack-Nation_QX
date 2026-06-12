"""Classify files inside an unstructured document bundle (ZIP)."""

import re
from enum import Enum


class BundleRole(str, Enum):
    PROTOKOLL = "protokoll"
    PHOTO_ANLAGEN = "photo_anlagen"  # Foto-Anhang (3/4-Ansicht, FIN, …)
    ANLAGEN = "anlagen"  # legacy alias
    AUFSTELLUNG = "aufstellung"
    GUTACHTEN = "gutachten"
    OTHER = "other"


_ROLE_PATTERNS: list[tuple[BundleRole, re.Pattern[str]]] = [
    (BundleRole.PROTOKOLL, re.compile(r"protokoll|prüfbericht|pruefbericht|c\d+_", re.I)),
    (
        BundleRole.PHOTO_ANLAGEN,
        re.compile(r"\banl\b(?![a-z])|foto[-_]?anl|photo[-_]?appendix|inspectors\s+justification", re.I),
    ),
    (BundleRole.AUFSTELLUNG, re.compile(r"nw_nat|_nw\b|aufstellung|national", re.I)),
    (BundleRole.GUTACHTEN, re.compile(r"\bgak\b|report|gutachten", re.I)),
]


def classify_by_filename(filename: str) -> BundleRole:
    name = filename.lower()
    for role, pattern in _ROLE_PATTERNS:
        if pattern.search(name):
            return role
    return BundleRole.OTHER


def classify_by_text(text: str) -> BundleRole:
    lower = text.lower()
    if re.search(r"c\d+\s+prüfbericht|prüfbericht zu ga-nr", lower):
        return BundleRole.PROTOKOLL
    if re.search(r"anlagen zu gutachten", lower):
        return BundleRole.PHOTO_ANLAGEN
    if re.search(r"aufstellung der technischen vorschriften", lower):
        return BundleRole.AUFSTELLUNG
    if re.search(r"aufstellung der nationalen|anlage 2 zum gutachten", lower):
        return BundleRole.AUFSTELLUNG
    if re.search(
        r"gutachten zur erlangung|gutachten nach §\s*21|untersuchungsbericht|änderungsabnahme",
        lower,
    ):
        return BundleRole.GUTACHTEN
    return BundleRole.OTHER


def resolve_role(filename: str, text: str) -> BundleRole:
    """Text structure beats filename — avoids §59 'Fabrikschilder' / Prüfplan mislabels."""
    by_text = classify_by_text(text)
    if by_text != BundleRole.OTHER:
        return by_text
    by_name = classify_by_filename(filename)
    if by_name != BundleRole.OTHER:
        return by_name
    return BundleRole.OTHER


def is_photo_annex_file(role: BundleRole, filename: str, first_page_text: str) -> bool:
    if role == BundleRole.PHOTO_ANLAGEN:
        return True
    lower = first_page_text.lower()
    return "anlagen zu gutachten" in lower or bool(
        re.search(r"3/4\s+ansicht", lower)
    )
