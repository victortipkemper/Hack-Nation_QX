"""
Golden corpus ground truth — evaluation only, NOT used in checking logic.
Maps hackathon PDF IDs to expected verdicts from solution keys.
"""

from pathlib import Path
from typing import Optional

HACKATHON_BASE = (
    Path(__file__).resolve().parent.parent.parent
    / "hackathon-data"
    / "Hackathon"
    / "Gutachten - Reports"
    / "50 Structured Gutachten (Reports)"
)

CORPUS1_DIR = HACKATHON_BASE / "Gutachten Part 1"
CORPUS2_DIR = (
    HACKATHON_BASE
    / "Gutachten Part 2 (25,21,19)"
    / "AutoComply_Testkorpus_25_Gutachten"
)

# Expected verdicts from 00_Loesungsschluessel_INTERN*.pdf
GOLDEN_VERDICTS: dict[str, dict] = {
    # Corpus 2 (1101-1125)
    "1101": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1102": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1103": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1104": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1105": {"verdict": "GREEN", "route": "21", "gap": None},
    "1106": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1107": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1108": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1109": {"verdict": "GREEN", "route": "19-3", "gap": None},
    "1110": {"verdict": "GREEN", "route": "21", "gap": None},
    "1111": {"verdict": "GREEN+AUFL", "route": "19-3", "gap": None},
    "1112": {"verdict": "GREEN+AUFL", "route": "19-3", "gap": None},
    "1113": {"verdict": "GREEN+AUFL", "route": "19-3", "gap": None},
    "1114": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1115": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1116": {"verdict": "GREEN+EV", "route": "19-3", "gap": None},
    "1117": {"verdict": "GREEN+EV", "route": "19-3", "gap": None},
    "1118": {"verdict": "GREEN+EV", "route": "19-3", "gap": None},
    "1119": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1120": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1121": {"verdict": "YELLOW", "route": "21", "gap": "r39_circumference"},
    "1122": {"verdict": "YELLOW", "route": "19-3", "gap": "tga_scope"},
    "1123": {"verdict": "YELLOW", "route": "21", "gap": "wheel_load_doc"},
    "1124": {"verdict": "YELLOW", "route": "19-3", "gap": "min_rim_tga"},
    "1125": {"verdict": "YELLOW", "route": "19-3", "gap": "tga_auflage"},
    # Corpus 1 (1126-1150)
    "1126": {"verdict": "GREEN", "route": "21", "gap": None},
    "1127": {"verdict": "GREEN", "route": "21", "gap": None},
    "1128": {"verdict": "GREEN", "route": "21", "gap": None},
    "1129": {"verdict": "GREEN", "route": "21", "gap": None},
    "1130": {"verdict": "GREEN", "route": "21", "gap": None},
    "1131": {"verdict": "GREEN", "route": "21", "gap": None},
    "1132": {"verdict": "GREEN", "route": "21", "gap": None},
    "1133": {"verdict": "GREEN", "route": "21", "gap": None},
    "1134": {"verdict": "GREEN", "route": "21", "gap": None},
    "1135": {"verdict": "GREEN", "route": "21", "gap": None},
    "1136": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1137": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1138": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1139": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1140": {"verdict": "GREEN+AUFL", "route": "21", "gap": None},
    "1141": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1142": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1143": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1144": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1145": {"verdict": "GREEN+EV", "route": "21", "gap": None},
    "1146": {"verdict": "YELLOW", "route": "21", "gap": "load_index"},
    "1147": {"verdict": "YELLOW", "route": "21", "gap": "speed_rating"},
    "1148": {"verdict": "YELLOW", "route": "21", "gap": "r39_circumference"},
    "1149": {"verdict": "YELLOW", "route": "21", "gap": "brake_section_41"},
    "1150": {"verdict": "YELLOW", "route": "21", "gap": "wheel_cover_30c_36a"},
}

PASS_VERDICTS = {"GREEN", "GREEN+AUFL", "GREEN+EV"}


def extract_case_id(filename: str) -> Optional[str]:
    """Extract 4-digit case ID from hackathon filename."""
    import re
    m = re.match(r"^(\d{4})_", filename)
    return m.group(1) if m else None


def find_corpus_pdf(case_id: str) -> Optional[Path]:
    """Locate PDF for a case ID in either corpus directory."""
    for directory in (CORPUS1_DIR, CORPUS2_DIR):
        if not directory.exists():
            continue
        for pdf in directory.glob(f"{case_id}_*.pdf"):
            return pdf
    return None


def list_corpus_pdfs() -> list[Path]:
    """Return all hackathon test PDFs (excluding solution keys)."""
    pdfs: list[Path] = []
    for directory in (CORPUS1_DIR, CORPUS2_DIR):
        if directory.exists():
            pdfs.extend(
                p for p in directory.glob("*.pdf")
                if not p.name.startswith("00_")
            )
    return sorted(pdfs, key=lambda p: p.name)
