from datetime import date

from schemas.gutachten import (
    CaseSummary,
    Gutachten,
    LoweringSpec,
    ModificationData,
    SpacerSpec,
    VehicleData,
    WheelTireSpec,
)

# Shared BMW 320i E90 base vehicle
_BMW_320I_E90 = VehicleData(
    make="BMW",
    model="320i",
    variant="Limousine",
    chassis_code="E90",
    vin="WBAVB13506PT12345",
    first_registration=date(2008, 3, 15),
    fuel_type="petrol",
    power_kw=110,
    original_tire_size_front="225/45 R17",
    original_tire_size_rear="225/45 R17",
    original_rim_size_front="7.5Jx17 ET37",
    original_rim_size_rear="7.5Jx17 ET37",
    original_offset_et_front=37,
    original_offset_et_rear=37,
    has_esp=True,
    has_abs=True,
    gross_vehicle_weight_kg=1840,
)

_BMW_I4_EV = VehicleData(
    make="BMW",
    model="i4",
    variant="eDrive40",
    chassis_code="G26",
    vin="WBA21CF0007A12345",
    first_registration=date(2023, 6, 1),
    fuel_type="electric",
    power_kw=250,
    original_tire_size_front="245/45 R18",
    original_tire_size_rear="245/45 R18",
    original_rim_size_front="8.0Jx18 ET40",
    original_rim_size_rear="8.0Jx18 ET40",
    original_offset_et_front=40,
    original_offset_et_rear=40,
    has_esp=True,
    has_abs=True,
    gross_vehicle_weight_kg=2125,
)

_WHEEL_19_BMW = WheelTireSpec(
    manufacturer="BBS",
    model="CH-R",
    size="245/40 R19",
    rim_width_inch=8.5,
    rim_diameter_inch=19,
    offset_et=35,
    load_index=97,
    speed_index="W",
    abe_number="B 123456",
)

_WHEEL_19_NO_ABE = WheelTireSpec(
    manufacturer="Replica",
    model="Unknown",
    size="245/40 R19",
    rim_width_inch=8.5,
    rim_diameter_inch=19,
    offset_et=20,
    load_index=85,
    speed_index="H",
    abe_number=None,
    teilegutachten_number=None,
)

_BMW_M4_F82 = VehicleData(
    make="BMW",
    model="M4",
    variant="Coupé",
    chassis_code="F82",
    vin="WBS3C910X0M0001146",
    first_registration=date(2017, 4, 18),
    fuel_type="petrol",
    power_kw=317,
    original_tire_size_front="235/30 R20",
    original_tire_size_rear="265/30 R20",
    original_rim_size_front="9.0Jx20 ET26",
    original_rim_size_rear="10.5Jx20 ET31",
    original_offset_et_front=26,
    original_offset_et_rear=31,
    has_esp=True,
    has_abs=True,
    gross_vehicle_weight_kg=1840,
    max_rear_axle_load_kg=1250,
)

MOCK_CASES: dict[str, Gutachten] = {
    # Case 0: Real PDF — BMW M4 F82 §21 Gutachten with internal Widerspruch
    "case-06-bmw-m4-widerspruch": Gutachten(
        gutachten_id="case-06-bmw-m4-widerspruch",
        gutachten_type="widerspruch",
        title="§21 Gutachten — BMW M4 F82 (MU-AC 1146) — Widerspruch",
        issuing_authority="Technische Prüfstelle für den Kraftfahrzeugverkehr – MUSTER",
        issue_date=date(2026, 5, 25),
        vehicle=_BMW_M4_F82,
        modification=ModificationData(
            modification_type="wheels_tires",
            wheels_front=WheelTireSpec(
                manufacturer="VuH genehm.",
                model="VA 20″",
                size="235/30 R20",
                rim_width_inch=9.0,
                rim_diameter_inch=20,
                offset_et=26,
                load_index=88,
                speed_index="Y",
                abe_number=None,
                teilegutachten_number=None,
            ),
            wheels_rear=WheelTireSpec(
                manufacturer="VuH genehm.",
                model="HA 20″",
                size="265/30 R20",
                rim_width_inch=10.5,
                rim_diameter_inch=20,
                offset_et=31,
                load_index=89,
                speed_index="Y",
                abe_number=None,
                teilegutachten_number=None,
            ),
            spacers_front_mm=0,
            spacers_rear_mm=0,
            total_track_width_increase_mm=0,
        ),
        notes=(
            "Real document: 1146_E_21_BMW_M4_LI_Widerspruch.pdf — "
            "§21 positive confirmation contradicts 'BE erloschen — kein TGA'."
        ),
    ),
    # Case 1: Standard-ABE — BMW 320i with 19" wheels + 12mm spacers (should PASS)
    "case-01-standard-abe": Gutachten(
        gutachten_id="case-01-standard-abe",
        gutachten_type="standard_abe",
        title="Standard-ABE — BMW 320i E90 19″ Räder + 12 mm Spacer",
        issuing_authority="TÜV Süd",
        issue_date=date(2024, 1, 15),
        vehicle=_BMW_320I_E90,
        modification=ModificationData(
            modification_type="wheels_tires",
            wheels_front=_WHEEL_19_BMW,
            wheels_rear=_WHEEL_19_BMW,
            spacers_front_mm=12,
            spacers_rear_mm=12,
            spacer_spec=SpacerSpec(
                thickness_mm=12,
                hubcentric=True,
                material="aluminium",
            ),
            total_track_width_increase_mm=24,
        ),
        notes="Archetypal PASS case: ABE-documented wheels with hub-centric spacers within limits.",
    ),
    # Case 2: Teilegutachten — parts certificate instead of ABE
    "case-02-teilegutachten": Gutachten(
        gutachten_id="case-02-teilegutachten",
        gutachten_type="teilegutachten",
        title="Teilegutachten — BMW 320i E90 19″ Räder (ohne ABE)",
        issuing_authority="DEKRA Automobil",
        issue_date=date(2024, 3, 22),
        vehicle=_BMW_320I_E90,
        modification=ModificationData(
            modification_type="wheels_tires",
            wheels_front=WheelTireSpec(
                manufacturer="OZ Racing",
                model="Superturismo",
                size="245/40 R19",
                rim_width_inch=8.5,
                rim_diameter_inch=19,
                offset_et=35,
                load_index=97,
                speed_index="W",
                teilegutachten_number="TG-BMW-E90-2024-0042",
            ),
            wheels_rear=WheelTireSpec(
                manufacturer="OZ Racing",
                model="Superturismo",
                size="245/40 R19",
                rim_width_inch=8.5,
                rim_diameter_inch=19,
                offset_et=35,
                load_index=97,
                speed_index="W",
                teilegutachten_number="TG-BMW-E90-2024-0042",
            ),
            spacers_front_mm=0,
            spacers_rear_mm=0,
            total_track_width_increase_mm=0,
        ),
        notes="Teilegutachten case: vehicle-specific parts certificate, no general ABE.",
    ),
    # Case 3: Lowering with conditions — 45mm drop exceeds ESP threshold
    "case-03-lowering-conditional": Gutachten(
        gutachten_id="case-03-lowering-conditional",
        gutachten_type="lowering",
        title="Tieferlegung — BMW 320i E90 (−45 mm, ESP-Bedingung)",
        issuing_authority="TÜV Nord",
        issue_date=date(2024, 5, 10),
        vehicle=_BMW_320I_E90,
        modification=ModificationData(
            modification_type="lowering",
            lowering=LoweringSpec(
                spring_set="H&R Sportfedern",
                drop_front_mm=45,
                drop_rear_mm=40,
                teilegutachten_number="TG-HR-E90-2023-0188",
            ),
            total_track_width_increase_mm=0,
        ),
        notes="Conditional case: lowering exceeds 40mm ESP tacit threshold — AUDIT FLAGGED expected.",
    ),
    # Case 4: EV edge case — BMW i4 with wheel modification
    "case-04-ev-edge": Gutachten(
        gutachten_id="case-04-ev-edge",
        gutachten_type="ev_edge",
        title="EV Edge Case — BMW i4 eDrive40 20″ Räder",
        issuing_authority="TÜV Rheinland",
        issue_date=date(2024, 7, 8),
        vehicle=_BMW_I4_EV,
        modification=ModificationData(
            modification_type="wheels_tires",
            wheels_front=WheelTireSpec(
                manufacturer="BMW",
                model="Individual 20″",
                size="255/40 R20",
                rim_width_inch=8.5,
                rim_diameter_inch=20,
                offset_et=38,
                load_index=99,
                speed_index="Y",
                abe_number="B 789012",
            ),
            wheels_rear=WheelTireSpec(
                manufacturer="BMW",
                model="Individual 20″",
                size="255/40 R20",
                rim_width_inch=8.5,
                rim_diameter_inch=20,
                offset_et=38,
                load_index=99,
                speed_index="Y",
                abe_number="B 789012",
            ),
            spacers_front_mm=0,
            spacers_rear_mm=0,
            total_track_width_increase_mm=0,
        ),
        notes="EV edge case: R10/R100 institutional consensus flags expected.",
    ),
    # Case 5: Flawed case — no documentation, bad offset, non-hub-centric spacers
    "case-05-flawed": Gutachten(
        gutachten_id="case-05-flawed",
        gutachten_type="flawed",
        title="Mangelhaft — BMW 320i E90 (keine ABE, ET20, Spacer 15 mm)",
        issuing_authority="Unbekannt",
        issue_date=date(2024, 9, 1),
        vehicle=_BMW_320I_E90,
        modification=ModificationData(
            modification_type="wheels_tires",
            wheels_front=_WHEEL_19_NO_ABE,
            wheels_rear=_WHEEL_19_NO_ABE,
            spacers_front_mm=15,
            spacers_rear_mm=15,
            spacer_spec=SpacerSpec(
                thickness_mm=15,
                hubcentric=False,
                material="steel",
            ),
            total_track_width_increase_mm=30,
        ),
        notes="Flawed case: missing ABE/TG, excessive offset deviation, non-hub-centric spacers — FAIL expected.",
    ),
}


def get_case_summaries() -> list[CaseSummary]:
    descriptions = {
        "case-06-bmw-m4-widerspruch": (
            "Real §21 Gutachten BMW M4 F82 (MU-AC 1146): 20″ Mischbereifung, kein TGA, "
            "interner Widerspruch BE erloschen vs. positive Bestätigung. Expected: AUDIT FLAGGED."
        ),
        "case-01-standard-abe": (
            "BMW 320i E90 with ABE-certified 19″ BBS CH-R wheels and 12 mm hub-centric spacers. "
            "Expected: PASS."
        ),
        "case-02-teilegutachten": (
            "BMW 320i E90 with OZ Racing wheels via Teilegutachten (no general ABE). "
            "Expected: PASS with documentation verified."
        ),
        "case-03-lowering-conditional": (
            "BMW 320i E90 with H&R lowering springs (−45 mm front). "
            "Expected: AUDIT FLAGGED (ESP 40 mm rule)."
        ),
        "case-04-ev-edge": (
            "BMW i4 eDrive40 with 20″ wheels. EV institutional consensus flags for R10/R100. "
            "Expected: AUDIT FLAGGED."
        ),
        "case-05-flawed": (
            "BMW 320i E90 with undocumented replica wheels, ET20, non-hub-centric 15 mm spacers. "
            "Expected: FAIL."
        ),
    }
    expected = {
        "case-06-bmw-m4-widerspruch": "AUDIT_FLAGGED",  # kein TGA, Widerspruch, HA-LI
        "case-01-standard-abe": "PASS",
        "case-02-teilegutachten": "PASS",
        "case-03-lowering-conditional": "AUDIT_FLAGGED",
        "case-04-ev-edge": "AUDIT_FLAGGED",
        "case-05-flawed": "FAIL",
    }
    return [
        CaseSummary(
            id=case_id,
            gutachten_type=g.gutachten_type,
            title=g.title,
            description=descriptions[case_id],
            expected_verdict=expected[case_id],
            vehicle_summary=f"{g.vehicle.make} {g.vehicle.model} ({g.vehicle.chassis_code})",
        )
        for case_id, g in MOCK_CASES.items()
    ]
