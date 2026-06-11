"""
Extract structured Gutachten data from PDF text.
Heuristic parser — deterministic, no LLM in the decision path.
"""

import re
import uuid
from datetime import date, datetime

from schemas.gutachten import (
    Gutachten,
    ModificationData,
    VehicleData,
    WheelTireSpec,
)

TIRE_PATTERN = re.compile(r"(\d{3}/\d{2})\s*R(\d{2})")
LI_SI_PATTERN = re.compile(r"(\d{2})([YWHVZ])")
ET_PATTERN = re.compile(r"ET\s*(\d+)")
RIM_PATTERN = re.compile(r"(\d+[,.]?\d*)\s*J\s*[x×]\s*(\d+)", re.I)
VIN_PATTERN = re.compile(r"\b(WBA[A-Z0-9]{13,17}|WBS[A-Z0-9]{13,17})\b")
DATE_PATTERN = re.compile(r"\b(\d{2})\.(\d{2})\.(\d{4})\b")
ACHSLAST_PATTERN = re.compile(
    r"(?:zul\.?\s*)?Achslast\s*HA\s*(\d{1,4}(?:\.\d{3})*|\d+)\s*kg", re.I
)


def _parse_german_kg(value: str) -> int:
    """Parse '1.250' → 1250 or '1250' → 1250."""
    value = value.strip().replace(" ", "")
    if "." in value and len(value.split(".")[-1]) == 3:
        return int(value.replace(".", ""))
    return int(float(value.replace(",", ".")))
GA_NR_PATTERN = re.compile(r"(?:GA[- ]?Nr\.?|mit Nr\.?)\s*:?\s*([A-Z0-9-]+)", re.I)


def extract_text_from_pdf(pdf_path: str) -> tuple[str, list[str]]:
    """Return full text and per-page text."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages), pages

    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages), pages


def _parse_date(text: str) -> date:
    match = DATE_PATTERN.search(text)
    if match:
        d, m, y = match.groups()
        return date(int(y), int(m), int(d))
    return date.today()


def _parse_first_registration(text: str) -> date:
    match = re.search(r"Erstzulassung[:\s]*(\d{2}\.\d{2}\.\d{4})", text, re.I)
    if match:
        d, m, y = match.group(1).split(".")
        return date(int(y), int(m), int(d))
    return _parse_date(text)


def _detect_gutachten_type(text: str) -> str:
    lower = text.lower()
    if "betriebserlaubnis" in lower and "erloschen" in lower:
        if "geltenden vorschriften entspricht" in lower:
            return "widerspruch"
        return "flawed"
    if "kein tga" in lower or "kein teilegutachten" in lower:
        return "flawed"
    if "teilegutachten" in lower and "abe" not in lower:
        return "teilegutachten"
    if "tieferlegung" in lower or "sportfedern" in lower:
        return "lowering"
    if "electric" in lower or "edrive" in lower or "hochvolt" in lower:
        return "ev_edge"
    return "standard_abe"


def _parse_vehicle(text: str) -> VehicleData:
    fin_match = re.search(
        r"Fahrzeug-Ident\.?-Nr\.?\s*:?\s*([A-Z0-9]{17})",
        text,
        re.I,
    )
    vin_match = VIN_PATTERN.search(text)
    vin = (
        fin_match.group(1)
        if fin_match
        else (vin_match.group(1) if vin_match else "UNKNOWN")
    )

    make, model, chassis = "BMW", "Unknown", "—"
    vehicle_match = re.search(
        r"Fahrzeughersteller\s*/\s*Typ[:\s]*([A-Za-z]+)\s*/\s*([^\n(]+)(?:\(([^)]+)\))?",
        text,
        re.I,
    )
    if vehicle_match:
        make = vehicle_match.group(1).strip()
        model_raw = vehicle_match.group(2).strip()
        chassis = (vehicle_match.group(3) or "—").strip()
        if "M4" in model_raw or "M4" in chassis:
            model = "M4"
        elif "320" in model_raw:
            model = "320i"
        elif "i4" in model_raw:
            model = "i4"
        else:
            model = model_raw.split()[0] if model_raw else "Unknown"

    tires = TIRE_PATTERN.findall(text)
    front_tire = f"{tires[0][0]} R{tires[0][1]}" if tires else "225/45 R17"
    rear_tire = (
        f"{tires[1][0]} R{tires[1][1]}" if len(tires) > 1 else front_tire
    )

    et_matches = ET_PATTERN.findall(text)
    et_front = int(et_matches[0]) if et_matches else 37
    et_rear = int(et_matches[1]) if len(et_matches) > 1 else et_front

    rim_matches = RIM_PATTERN.findall(text)
    rim_front = (
        f"{rim_matches[0][0].replace(',', '.')}Jx{rim_matches[0][1]} ET{et_front}"
        if rim_matches
        else f"7.5Jx17 ET{et_front}"
    )
    rim_rear = (
        f"{rim_matches[1][0].replace(',', '.')}Jx{rim_matches[1][1]} ET{et_rear}"
        if len(rim_matches) > 1
        else rim_front
    )

    achslast_match = ACHSLAST_PATTERN.search(text)
    max_rear_axle = (
        _parse_german_kg(achslast_match.group(1)) if achslast_match else None
    )

    return VehicleData(
        make=make,
        model=model,
        variant="Coupé" if "M4" in model else "Limousine",
        chassis_code=chassis,
        vin=vin,
        first_registration=_parse_first_registration(text),
        fuel_type="petrol",
        power_kw=250 if "M4" in model else 110,
        original_tire_size_front=front_tire,
        original_tire_size_rear=rear_tire,
        original_rim_size_front=rim_front,
        original_rim_size_rear=rim_rear,
        original_offset_et_front=et_front,
        original_offset_et_rear=et_rear,
        has_esp=True,
        has_abs=True,
        gross_vehicle_weight_kg=1840,
        max_rear_axle_load_kg=max_rear_axle,
    )


def _parse_wheels(text: str) -> tuple[WheelTireSpec | None, WheelTireSpec | None]:
    """Parse VA/HA wheel specs from Zu 15.1/2 block or modification line."""
    block_match = re.search(
        r"Zu\s*15\.1/2[:\s]*(.*?)(?:Zusätzliche|Vorausgegangene|Bestätigung|Es wurde)",
        text,
        re.S | re.I,
    )
    mod_match = re.search(
        r"Mischbereifung.*?:\s*VA\s*(.*?)\s*/\s*HA\s*([^\n]+)",
        text,
        re.I,
    )

    source = block_match.group(1) if block_match else text
    if mod_match:
        source = f"VA {mod_match.group(1)} HA {mod_match.group(2)}"

    tires = TIRE_PATTERN.findall(source)
    if not tires:
        return None, None

    li_si = LI_SI_PATTERN.findall(source)
    et_vals = [int(e) for e in ET_PATTERN.findall(source)]
    rims = RIM_PATTERN.findall(source)

    def _wheel(idx: int) -> WheelTireSpec:
        w, d = tires[idx] if idx < len(tires) else tires[0]
        li, si = li_si[idx] if idx < len(li_si) else ("91", "W")
        et = et_vals[idx] if idx < len(et_vals) else 37
        rim_w = float(rims[idx][0].replace(",", ".")) if idx < len(rims) else 8.0
        rim_d = float(rims[idx][1]) if idx < len(rims) else float(d)
        has_tga = "teilegutachten" in text.lower() and "kein tga" not in text.lower()
        tg_match = re.search(r"Teilegutachten[- ]?Nr\.?\s*:?\s*([A-Z0-9-]+)", text, re.I)
        abe_match = re.search(r"ABE[- ]?(?:Nr\.?)?\s*:?\s*([A-Z]\s*\d+)", text, re.I)

        return WheelTireSpec(
            manufacturer="VuH genehm." if "VuH" in source else "Unknown",
            model=f"{'VA' if idx == 0 else 'HA'} {d}″",
            size=f"{w} R{d}",
            rim_width_inch=rim_w,
            rim_diameter_inch=rim_d,
            offset_et=et,
            load_index=int(li),
            speed_index=si,
            abe_number=abe_match.group(1).replace(" ", "") if abe_match else None,
            teilegutachten_number=tg_match.group(1) if has_tga and tg_match else None,
        )

    return _wheel(0), _wheel(1) if len(tires) > 1 else _wheel(0)


def parse_gutachten_from_pdf(
    text: str, filename: str, upload_id: str
) -> Gutachten:
    """Build Gutachten schema from extracted PDF text."""
    vehicle = _parse_vehicle(text)
    wheels_front, wheels_rear = _parse_wheels(text)
    gutachten_type = _detect_gutachten_type(text)

    ga_match = GA_NR_PATTERN.search(text)
    gutachten_id = ga_match.group(1) if ga_match else upload_id

    issue_match = re.search(r"vom\s+(\d{2}\.\d{2}\.\d{4})", text, re.I)
    issue_date = (
        datetime.strptime(issue_match.group(1), "%d.%m.%Y").date()
        if issue_match
        else date.today()
    )

    authority_match = re.search(
        r"(Technische Prüfstelle[^\n]+|TÜV[^\n]+|DEKRA[^\n]+)", text, re.I
    )
    authority = authority_match.group(1).strip() if authority_match else "Unbekannt"

    return Gutachten(
        gutachten_id=f"upload-{upload_id[:8]}",
        gutachten_type=gutachten_type,
        title=f"Upload — {filename}",
        issuing_authority=authority,
        issue_date=issue_date,
        vehicle=vehicle,
        modification=ModificationData(
            modification_type="wheels_tires",
            wheels_front=wheels_front,
            wheels_rear=wheels_rear,
            total_track_width_increase_mm=0,
        ),
        notes=f"Automatisch aus PDF extrahiert: {filename}",
    )
