"""Extracted document features — drives checklist applicability (not file IDs)."""

from typing import Optional

from pydantic import BaseModel, Field


class AufstellungFlags(BaseModel):
    """Which StVZO paragraphs are marked N/A vs compliant in Aufstellung."""

    section_30c_na: bool = False
    section_36_na: bool = False
    section_36a_na: bool = False
    section_41_na: bool = False
    section_57_na: bool = False
    section_36_compliant: bool = False


class PruefberichtFlags(BaseModel):
    nachweis_vorhanden: Optional[bool] = None
    eigenpruefung: Optional[bool] = None
    ergebnisse_erreicht: Optional[bool] = None
    radtraglast_ausreichend_claimed: bool = False
    positive_schlussbescheinigung: bool = False


class DocumentFeatures(BaseModel):
    """Structured features extracted from Gutachten PDF text."""

    raw_text: str = ""
    filename: str = ""
    page_count: int = 0

    # Routing
    route: str = "unknown"  # "19-3", "21", "abe"
    archetype_hint: str = ""  # from filename only — NOT used for verdict logic

    # Vehicle
    vin: str = ""
    make: str = ""
    model: str = ""
    fuel_type: str = "petrol"
    is_ev: bool = False
    vmax_kmh: Optional[int] = None

    # Modifications detected
    has_wheel_change: bool = False
    has_brake_change: bool = False
    has_lowering: bool = False
    has_lift: bool = False
    has_spacers: bool = False
    has_track_wideners: bool = False

    # Wheel/tire data
    load_index_front: Optional[int] = None
    load_index_rear: Optional[int] = None
    speed_index: Optional[str] = None
    max_rear_axle_load_kg: Optional[int] = None
    rolling_circumference_delta_pct: Optional[float] = None
    min_rim_inch_from_tga: Optional[int] = None
    documented_rim_inch: Optional[int] = None

    # Documentation
    has_abe: bool = False
    has_tga: bool = False
    has_tga_kein: bool = False
    tga_wrong_vehicle: bool = False
    tga_auflage_missing: bool = False

    # Contradictions
    be_erloschen_claimed: bool = False
    internal_contradiction: bool = False

    aufstellung: AufstellungFlags = Field(default_factory=AufstellungFlags)
    pruefbericht: PruefberichtFlags = Field(default_factory=PruefberichtFlags)
