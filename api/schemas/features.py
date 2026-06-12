"""Extracted document features — drives checklist applicability (not file IDs)."""

from typing import Optional

from pydantic import BaseModel, Field


class PhotoEvidenceItem(BaseModel):
    label: str
    page: int = 0
    source_file: str = ""
    has_image: bool = False
    image_count: int = 0
    confidence: float = 0.0
    note: str = ""


class ProtocolSectionResult(BaseModel):
    section_id: str
    title: str = ""
    final_passed: Optional[bool] = None
    fulfilled_markers: int = 0
    open_markers: int = 0
    reason: str = ""


class BundleEvidence(BaseModel):
    is_bundle: bool = False
    source_zip: str = ""
    gutachten_nr: str = ""
    files: list[str] = Field(default_factory=list)
    roles: dict[str, str] = Field(default_factory=dict)
    vin: str = ""
    vin_consistent: bool = True
    vins_found: list[str] = Field(default_factory=list)
    has_protokoll: bool = False
    has_anlagen: bool = False
    has_photo_anlagen: bool = False
    has_gutachten: bool = False
    has_aufstellung: bool = False
    has_national_aufstellung: bool = False
    protocol_sections: list[ProtocolSectionResult] = Field(default_factory=list)
    protocol_all_passed: bool = True
    protocol_summary: str = ""
    photo_evidence: list[PhotoEvidenceItem] = Field(default_factory=list)
    photos_complete: bool = True
    combined_page_count: int = 0


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
    bundle: BundleEvidence = Field(default_factory=BundleEvidence)
