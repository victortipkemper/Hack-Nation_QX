"""
Extract structured DocumentFeatures from Gutachten PDF text.
Drives checklist applicability — never uses file ID for verdict logic.
"""

import re
from typing import Optional

from schemas.features import AufstellungFlags, DocumentFeatures, PruefberichtFlags

# EU tire load index → kg per tire (subset used in corpus)
LI_TO_KG: dict[int, int] = {
    80: 450, 81: 462, 82: 475, 83: 487, 84: 500, 85: 515, 86: 530,
    87: 545, 88: 560, 89: 580, 90: 600, 91: 615, 92: 630, 93: 650,
    94: 670, 95: 690, 96: 710, 97: 730, 98: 750, 99: 775, 100: 800,
    101: 825, 102: 850, 103: 875, 104: 900, 105: 925, 106: 950,
    107: 975, 108: 1000, 109: 1030, 110: 1060,
}

# Speed index → max km/h
SR_TO_KMH: dict[str, int] = {
    "H": 210, "V": 240, "W": 270, "Y": 300, "Z": 300,
}

TIRE_PATTERN = re.compile(r"(\d{3}/\d{2})\s*R(\d{2})")
LI_SI_PATTERN = re.compile(r"(\d{2})([YWHVZ])")
ACHSLAST_PATTERN = re.compile(
    r"(?:zul\.?\s*)?Achslast\s*HA\s*(\d{1,4}(?:\.\d{3})*|\d+)\s*kg", re.I
)
CIRC_DELTA_PATTERN = re.compile(
    r"(?:Abrollumfang|Abrollumfangabweichung|Δ|Delta)[^\d]*([+-]?\d+[,.]?\d*)\s*%",
    re.I,
)
VMAX_PATTERN = re.compile(r"(?:Vmax|Höchstgeschwindigkeit|T)\s*[:\s]*(\d{2,3})\s*km/h", re.I)
RIM_INCH_PATTERN = re.compile(r"(\d{1,2})[,.]?\d*\s*(?:J|Zoll|″|\"|inch)", re.I)
MIN_RIM_TGA_PATTERN = re.compile(
    r"(?:mindest|Mindest)[- ]?(?:Felgengröße|Felgendurchmesser|Felge)[^\d]*(\d{1,2})\s*(?:Zoll|″|\")",
    re.I,
)
TGA_SCOPE_PATTERN = re.compile(
    r"Verwendungsbereich:\s*([^\n]+)", re.I
)
SECTION3_BLOCK = re.compile(
    r"3\s+Begutachtete[^\n]*\n(.*?)(?=4\s+Durchgef)", re.S | re.I
)
AUFLAGEN_BLOCK = re.compile(
    r"5\s+Auflagen\s*\n(.*?)(?=6\s+Hinweise)", re.S | re.I
)
TGA_VEHICLE_PATTERN = re.compile(
    r"(?:Teilegutachten|TGA)\s+(?:gilt\s+für|für\s+(?:Fahrzeug|BMW|Audi|VW|MB|Typ))\s*([^\n;]{5,80})",
    re.I,
)
AUFLAGE_A3_PATTERN = re.compile(r"A3[^\n]*(?:50\s*km|Nachziehen)", re.I)


def _parse_german_kg(value: str) -> int:
    value = value.strip().replace(" ", "")
    if "." in value and len(value.split(".")[-1]) == 3:
        return int(value.replace(".", ""))
    return int(float(value.replace(",", ".")))


def _parse_float_de(value: str) -> float:
    return float(value.replace(",", ".").replace("+", ""))


def _bewertung_after_paragraph(lines: list[str], start_idx: int) -> Optional[str]:
    """Read Aufstellung Bewertung (N/A* or Vorschriftsmäßig) after a §-Zeile."""
    for j in range(start_idx + 1, min(start_idx + 6, len(lines))):
        line = lines[j].strip()
        if re.match(r"N/?A\*?", line, re.I):
            return "N/A"
        if re.search(r"vorschriftsm", line, re.I):
            return "Vorschriftsmäßig"
    return None


def _extract_aufstellung_block(text: str) -> str:
    """Limit parsing to the Aufstellung table — avoids false § hits elsewhere."""
    m = re.search(
        r"Aufstellung\s+der\s+technischen\s+Vorschriften.*",
        text,
        re.I | re.S,
    )
    return m.group(0) if m else text


def _parse_aufstellung_sections(text: str) -> dict[str, str]:
    """
    Parse Aufstellung table: map section id → Bewertung.
    Handles PDF encoding where § may appear as special character.
    """
    lines = _extract_aufstellung_block(text).split("\n")
    sections: dict[str, str] = {}
    section_markers = {
        "30c": re.compile(r"(?:§|\ufffd|.)?30c\b"),
        "36": re.compile(r"(?:§|\ufffd|.)?36\b(?!a)"),
        "36a": re.compile(r"(?:§|\ufffd|.)?36a\b"),
        "41": re.compile(r"(?:§|\ufffd|.)?41\b"),
        "57": re.compile(r"(?:§|\ufffd|.)?57\b"),
    }
    for i, line in enumerate(lines):
        for sec_id, pattern in section_markers.items():
            if pattern.search(line):
                bew = _bewertung_after_paragraph(lines, i)
                if bew:
                    sections[sec_id] = bew
    return sections


def _section_na(text: str, section: str) -> bool:
    parsed = _parse_aufstellung_sections(text)
    return parsed.get(section) == "N/A"


def _section_compliant(text: str, section: str) -> bool:
    parsed = _parse_aufstellung_sections(text)
    return parsed.get(section) == "Vorschriftsmäßig"


def _detect_route(text: str) -> str:
    lower = text.lower()
    if (
        re.search(r"gutachten\s+nach\s+§\s*21", text, re.I)
        or re.search(r"betriebserlaubnis\s+gemäß\s+§\s*21", text, re.I)
        or re.search(r"§\s*21\s*stvzo.*§\s*19\s*\(\s*2\s*\)", text, re.I)
    ):
        return "21"
    if (
        re.search(r"änderungsabnahme\s+nach\s+§\s*19\s+abs\.?\s*3", text, re.I)
        or re.search(r"§\s*19\s+abs\.?\s*3\s*stvzo", text, re.I)
        or re.search(r"§\s*19\s*\(\s*3\s*\)", text, re.I)
        or "komponentengutachten" in lower
    ):
        return "19-3"
    return "unknown"


def _extract_section3(text: str) -> str:
    m = SECTION3_BLOCK.search(text)
    return m.group(1) if m else ""


def _detect_modifications(text: str) -> dict[str, bool]:
    lower = text.lower()
    section3 = _extract_section3(text).lower()
    return {
        "has_wheel_change": bool(
            re.search(r"zu\s*15\.1/2|mischbereifung|räder|reifen|felgen|sonderräder", lower)
            or re.search(r"räder|reifen|felgen|sonderräder", section3)
        ),
        "has_brake_change": bool(
            re.search(r"bremsanlage\s+va|bremsscheib|bremsbelag|bremsanlage:", section3)
            or re.search(r"begutachtete[^\n]*bremsanlage", lower)
            or re.search(r"bremsscheiben\s+va|geänderte\s+bremsscheiben", lower)
            or re.search(r"zu\s*15\.1/2[^\n]*bremsscheib", lower)
        ),
        "has_lowering": bool(
            re.search(r"tieferleg|sportfeder|fahrwerk.*-\d+\s*mm|coilover", lower)
        ),
        "has_lift": bool(re.search(r"lift|höherleg|\+50\s*mm|\+7[,.]4\s*%", lower)),
        "has_spacers": bool(re.search(r"spurplatte|distanzscheib", lower)),
        "has_track_wideners": bool(
            re.search(r"spurverbreiterung|spurverbreiter|track\s*widener", lower)
        ),
    }


def _extract_li_values(text: str) -> tuple[Optional[int], Optional[int]]:
    """Extract VA/HA load indices from Zu 15.1/2 or tire lines."""
    block = re.search(
        r"Zu\s*15\.1/2[:\s]*(.*?)(?:Zusätzliche|Vorausgegangene|Bestätigung|Es wurde)",
        text,
        re.S | re.I,
    )
    source = block.group(1) if block else text
    li_matches = LI_SI_PATTERN.findall(source)
    if not li_matches:
        li_matches = LI_SI_PATTERN.findall(text)
    if not li_matches:
        return None, None
    front = int(li_matches[0][0])
    rear = int(li_matches[1][0]) if len(li_matches) > 1 else front
    return front, rear


def _extract_speed_index(text: str) -> Optional[str]:
    block = re.search(r"Zu\s*15\.1/2[:\s]*(.*?)(?:Zusätzliche|Vorausgegangene)", text, re.S | re.I)
    source = block.group(1) if block else text
    m = LI_SI_PATTERN.search(source)
    if m:
        return m.group(2)
    m = LI_SI_PATTERN.search(text)
    return m.group(2) if m else None


def _extract_circumference_delta(text: str) -> Optional[float]:
    matches = CIRC_DELTA_PATTERN.findall(text)
    if not matches:
        # fallback: percentage near Abrollumfang keyword
        m = re.search(r"Abrollumfang[^\n]*?([+-]?\d+[,.]\d+)\s*%", text, re.I)
        if m:
            return abs(_parse_float_de(m.group(1)))
        return None
    values = [abs(_parse_float_de(v)) for v in matches]
    return max(values) if values else None


def _extract_rim_inch(text: str) -> Optional[int]:
    block = re.search(r"Zu\s*15\.1/2[:\s]*(.*?)(?:Zusätzliche|Vorausgegangene)", text, re.S | re.I)
    section3 = _extract_section3(text)
    source = block.group(1) if block else (section3 or text)
    rims = RIM_INCH_PATTERN.findall(source)
    if rims:
        return max(int(r) for r in rims)
    # Pattern: 7,5Jx17 or 8.5Jx19
    jx = re.findall(r"(\d{1,2})[,.]?\d*\s*J\s*[x×]\s*(\d{2})", source, re.I)
    if jx:
        return max(int(d) for _, d in jx)
    tires = TIRE_PATTERN.findall(source)
    if tires:
        return max(int(d) for _, d in tires)
    return None


def _extract_vehicle_code(text: str) -> str:
    vehicle_match = re.search(
        r"Fahrzeughersteller\s*/\s*Typ[:\s]*[^\n]*\(([^)]+)\)", text, re.I
    )
    return (vehicle_match.group(1) if vehicle_match else "").lower()


def _check_tga_wrong_vehicle(text: str) -> bool:
    """Detect TGA Verwendungsbereich mismatch vs. actual vehicle."""
    vehicle_code = _extract_vehicle_code(text)
    scope_match = TGA_SCOPE_PATTERN.search(text)
    if not scope_match or not vehicle_code:
        return False

    tga_scope = scope_match.group(1).lower()
    claimed_ok = bool(
        re.search(
            r"Zuordnung des Prüfzeugnisses[^\n]*eingehalten|Verwendungsbereich\):\s*eingehalten",
            text,
            re.I,
        )
    )
    if not claimed_ok:
        return False

    # Compare chassis / typ codes between vehicle and TGA scope
    vehicle_tokens = set(re.findall(r"[a-z]?\d{2,3}[a-z]?|e\d{2}", vehicle_code))
    scope_tokens = set(re.findall(r"[a-z]?\d{2,3}[a-z]?|e\d{2}", tga_scope))
    if vehicle_tokens and scope_tokens and not vehicle_tokens & scope_tokens:
        return True
    if ("e46" in vehicle_code or "346l" in vehicle_code) and (
        "e90" in tga_scope or "390l" in tga_scope
    ):
        return True
    return False


def _check_tga_auflage_missing(text: str) -> bool:
    """TGA lists Auflage A3 but Gutachten Auflagen section omits it."""
    tga_has_a3 = bool(
        re.search(r"Auflagen\s+A1[^\n]*A3|Auflagen\s+A1–A3|Auflagen\s+A1-A3", text, re.I)
        or re.search(r"Auflage\s+A3|A3[^\n]*(?:50\s*km|Nachziehen)", text, re.I)
    )
    if not tga_has_a3:
        return False

    auflagen_block = AUFLAGEN_BLOCK.search(text)
    auflagen_text = auflagen_block.group(1) if auflagen_block else ""
    gutachten_has_a3 = bool(
        re.search(r"A3|Nachziehen|50\s*km|nachziehen der radschrauben", auflagen_text, re.I)
    )
    return not gutachten_has_a3


def extract_features(
    text: str,
    filename: str = "",
    page_count: int = 0,
) -> DocumentFeatures:
    """Build DocumentFeatures from raw PDF text."""
    lower = text.lower()
    mods = _detect_modifications(text)

    achslast_match = ACHSLAST_PATTERN.search(text)
    max_rear_axle = (
        _parse_german_kg(achslast_match.group(1)) if achslast_match else None
    )

    li_front, li_rear = _extract_li_values(text)
    vmax_match = VMAX_PATTERN.search(text)
    vmax = int(vmax_match.group(1)) if vmax_match else None

    vin_match = re.search(r"Fahrzeug-Ident\.?-Nr\.?\s*:?\s*([A-Z0-9]{17})", text, re.I)
    make_match = re.search(r"Fahrzeughersteller\s*/\s*Typ[:\s]*([A-Za-z]+)", text, re.I)

    is_ev = bool(
        re.search(r"elektro|bev|hochvolt|edrive|model\s*[3sy]|ioniq|id\.?\s*buzz|polestar|ev6|e-tron|i4", lower)
    )

    has_tga = "teilegutachten" in lower and "kein tga" not in lower
    has_tga_kein = "kein tga" in lower or "(kein tga)" in lower
    has_abe = bool(
        re.search(r"\babe\b|allgemeine\s*betriebserlaubnis|abe[- ]?nr", lower)
    )
    has_tga_ref = bool(
        re.search(r"teilegutachten[- ]?nr|tga[- ]?nr|mit\s+nr\.?\s*must", lower)
    )
    if has_tga_ref and not has_tga_kein:
        has_tga = True

    positive_conclusion = bool(
        re.search(
            r"den\s+geltenden\s+vorschriften\s+entspricht|vorschriftsmäßigkeit\s+bezieht",
            lower,
        )
    )
    negative_conclusion = bool(
        re.search(
            r"nicht\s+den\s+geltenden\s+vorschriften|widerspruch|nicht\s+vorschriftsmäßig",
            lower,
        )
    )
    # Procedural §21 erloschen-Begründung ist Normalfall — kein Widerspruch
    be_erloschen = False
    internal_contradiction = positive_conclusion and negative_conclusion

    pruefbericht = PruefberichtFlags(
        nachweis_vorhanden=_parse_ja_nein(text, r"Nachweis\s*(?:vorhanden|belegt)"),
        eigenpruefung=_parse_ja_nein(text, r"Eigenprüfung"),
        ergebnisse_erreicht=_parse_ja_nein(text, r"Ergebnisse\s*erreicht"),
        radtraglast_ausreichend_claimed=bool(
            re.search(r"radtraglast[^\n]*(?:ausreichend|erreicht|ja)", lower)
        ),
        positive_schlussbescheinigung=positive_conclusion,
    )

    min_rim_tga = None
    min_match = MIN_RIM_TGA_PATTERN.search(text)
    if min_match:
        min_rim_tga = int(min_match.group(1))

    return DocumentFeatures(
        raw_text=text,
        filename=filename,
        page_count=page_count,
        route=_detect_route(text),
        vin=vin_match.group(1) if vin_match else "",
        make=make_match.group(1) if make_match else "",
        fuel_type="electric" if is_ev else "petrol",
        is_ev=is_ev,
        vmax_kmh=vmax,
        has_wheel_change=mods["has_wheel_change"],
        has_brake_change=mods["has_brake_change"],
        has_lowering=mods["has_lowering"],
        has_lift=mods["has_lift"],
        has_spacers=mods["has_spacers"],
        has_track_wideners=mods["has_track_wideners"],
        load_index_front=li_front,
        load_index_rear=li_rear,
        speed_index=_extract_speed_index(text),
        max_rear_axle_load_kg=max_rear_axle,
        rolling_circumference_delta_pct=_extract_circumference_delta(text),
        min_rim_inch_from_tga=min_rim_tga,
        documented_rim_inch=_extract_rim_inch(text),
        has_abe=has_abe,
        has_tga=has_tga,
        has_tga_kein=has_tga_kein,
        tga_wrong_vehicle=_check_tga_wrong_vehicle(text),
        tga_auflage_missing=_check_tga_auflage_missing(text),
        be_erloschen_claimed=be_erloschen,
        internal_contradiction=internal_contradiction,
        aufstellung=AufstellungFlags(
            section_30c_na=_section_na(text, "30c"),
            section_36_na=_section_na(text, "36"),
            section_36a_na=_section_na(text, "36a"),
            section_41_na=_section_na(text, "41"),
            section_57_na=_section_na(text, "57"),
            section_36_compliant=_section_compliant(text, "36"),
        ),
        pruefbericht=pruefbericht,
    )


def _parse_ja_nein(text: str, field_pattern: str) -> Optional[bool]:
    m = re.search(rf"{field_pattern}\s*[:\s]*(ja|nein)", text, re.I)
    if m:
        return m.group(1).lower() == "ja"
    return None


def li_to_kg(load_index: int) -> int:
    return LI_TO_KG.get(load_index, load_index * 6 + 140)


def sr_to_kmh(speed_index: str) -> int:
    return SR_TO_KMH.get(speed_index.upper(), 210)
