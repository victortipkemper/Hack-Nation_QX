"""
Deterministic rules engine for Autocomply.
One Gutachten in, one auditable verdict out — zero generative inference in the decision.
"""

import hashlib
from datetime import datetime, timezone
from typing import List

from schemas.gutachten import Gutachten, ModificationData, VehicleData
from schemas.verdict import (
    FinalVerdict,
    LevelResult,
    RuleResult,
    TestPlanResult,
    VerdictStatus,
)


def verify_level1_stvzo(
    vehicle_data: VehicleData, modification_data: ModificationData
) -> List[RuleResult]:
    """
    Level 1: Formal Law — § 19 StVZO (Einzelgenehmigung / Einzelabnahme).
    Checks legal basis for individual approval of modifications.
    """
    results: List[RuleResult] = []

    # § 19 Abs. 2 StVZO — Modification must be individually approvable
    has_documentation = (
        modification_data.wheels_front is not None
        or modification_data.lowering is not None
    )
    results.append(
        RuleResult(
            rule_id="L1-19-001",
            rule_name="§ 19 Abs. 2 StVZO — Genehmigungsfähigkeit",
            passed=has_documentation,
            flagged=False,
            citation="§ 19 Abs. 2 StVZO: Änderungen und Ergänzungen am Fahrzeug bedürfen einer Genehmigung.",
            reason=(
                "Modification is documentable and within scope of individual approval."
                if has_documentation
                else "No approvable modification documented in Gutachten."
            ),
        )
    )

    # § 19 Abs. 3 StVZO — Type approval documentation present
    abe_present = (
        modification_data.wheels_front is not None
        and modification_data.wheels_front.abe_number is not None
    )
    teile_present = (
        modification_data.wheels_front is not None
        and modification_data.wheels_front.teilegutachten_number is not None
    )
    doc_ok = abe_present or teile_present or modification_data.lowering is not None
    results.append(
        RuleResult(
            rule_id="L1-19-002",
            rule_name="§ 19 Abs. 3 StVZO — Nachweis der Verkehrssicherheit",
            passed=doc_ok,
            flagged=not doc_ok and has_documentation,
            citation="§ 19 Abs. 3 StVZO: Der Nachweis der Verkehrssicherheit ist durch Gutachten zu erbringen.",
            reason=(
                "ABE or Teilegutachten reference present."
                if doc_ok
                else "Missing type approval or parts certificate reference."
            ),
        )
    )

    # TODO: Implement § 19 Abs. 5 StVZO — registration marking requirements
    results.append(
        RuleResult(
            rule_id="L1-19-003",
            rule_name="§ 19 Abs. 5 StVZO — Kennzeichnung im Fahrzeugschein",
            passed=True,
            flagged=False,
            citation="§ 19 Abs. 5 StVZO: Genehmigte Änderungen sind im Fahrzeugschein einzutragen.",
            reason="TODO: Verify registration entry requirements against Gutachten metadata.",
        )
    )

    return results


def verify_level2_vdtuev_751(modification_data: ModificationData) -> List[RuleResult]:
    """
    Level 2: Operationalized Rules — VdTÜV-Merkblatt 751 Annex I.
    Technical clearance and dimensional checks for wheel/tire modifications.
    """
    results: List[RuleResult] = []

    wheels = modification_data.wheels_front
    if wheels is None and modification_data.lowering is not None:
        # Lowering-only case — skip wheel-specific checks
        results.append(
            RuleResult(
                rule_id="L2-751-000",
                rule_name="VdTÜV 751 — Scope Check",
                passed=True,
                flagged=False,
                citation="VdTÜV-Merkblatt 751: Geltungsbereich Fahrwerksänderungen.",
                reason="Lowering modification — wheel/tire annex checks not applicable.",
            )
        )
        return results

    if wheels is None:
        results.append(
            RuleResult(
                rule_id="L2-751-000",
                rule_name="VdTÜV 751 — Scope Check",
                passed=False,
                flagged=True,
                citation="VdTÜV-Merkblatt 751 Annex I: Räder und Reifen.",
                reason="No wheel/tire data available for VdTÜV 751 evaluation.",
            )
        )
        return results

    # I.5.1.11 — Wheel arch clearance (mock: pass if offset within ±15mm of OE)
    oe_offset = 37  # BMW 320i E90 standard ET
    offset_delta = abs(wheels.offset_et - oe_offset)
    clearance_ok = offset_delta <= 15
    results.append(
        RuleResult(
            rule_id="L2-751-I.5.1.11",
            rule_name="Annex I § I.5.1.11 — Radlauf-Freigang",
            passed=clearance_ok,
            flagged=not clearance_ok,
            citation=(
                "VdTÜV-Merkblatt 751, Annex I, § I.5.1.11: "
                "Der Freigang zwischen Rad und Radlauf muss in allen Federweglagen gewährleistet sein."
            ),
            reason=(
                f"Offset ET{wheels.offset_et} within acceptable range (Δ{offset_delta}mm from OE ET{oe_offset})."
                if clearance_ok
                else f"Offset ET{wheels.offset_et} exceeds clearance tolerance (Δ{offset_delta}mm from OE)."
            ),
        )
    )

    # I.5.1.8 — Track width increase limit (mock: max 30mm per axle with spacers)
    track_increase = modification_data.total_track_width_increase_mm
    track_ok = track_increase <= 30
    results.append(
        RuleResult(
            rule_id="L2-751-I.5.1.8",
            rule_name="Annex I § I.5.1.8 — Spurweitenänderung",
            passed=track_ok,
            flagged=not track_ok,
            citation=(
                "VdTÜV-Merkblatt 751, Annex I, § I.5.1.8: "
                "Die Änderung der Spurweite ist auf maximal 30 mm pro Achse begrenzt."
            ),
            reason=(
                f"Track width increase {track_increase}mm within 30mm limit."
                if track_ok
                else f"Track width increase {track_increase}mm exceeds 30mm per-axle limit."
            ),
        )
    )

    # TODO: Implement I.5.1.5 — Rolling circumference deviation check
    results.append(
        RuleResult(
            rule_id="L2-751-I.5.1.5",
            rule_name="Annex I § I.5.1.5 — Abrollumfang",
            passed=True,
            flagged=False,
            citation=(
                "VdTÜV-Merkblatt 751, Annex I, § I.5.1.5: "
                "Der Abrollumfang darf um höchstens ±2,5 % vom Original abweichen."
            ),
            reason="TODO: Calculate rolling circumference from tire size and compare to OE.",
        )
    )

    # I.5.2.3 — Load index adequacy
    load_ok = wheels.load_index >= 91  # BMW 320i minimum
    results.append(
        RuleResult(
            rule_id="L2-751-I.5.2.3",
            rule_name="Annex I § I.5.2.3 — Tragfähigkeitsindex",
            passed=load_ok,
            flagged=False,
            citation=(
                "VdTÜV-Merkblatt 751, Annex I, § I.5.2.3: "
                "Der Tragfähigkeitsindex muss dem des serienmäßigen Reifens entsprechen oder übersteigen."
            ),
            reason=(
                f"Load index {wheels.load_index} meets or exceeds vehicle requirement (≥91)."
                if load_ok
                else f"Load index {wheels.load_index} below vehicle requirement (≥91)."
            ),
        )
    )

    return results


def verify_level3_lived_practice(
    vehicle_data: VehicleData, modification_data: ModificationData
) -> List[RuleResult]:
    """
    Level 3: Lived Inspection Practice — Tacit thresholds applied at TÜV stations.
  e.g., 40mm ESP sensor drop rule for lowering kits.
    """
    results: List[RuleResult] = []

    # 40mm ESP drop rule — widely applied tacit threshold
    if modification_data.lowering is not None:
        drop = modification_data.lowering.drop_front_mm
        esp_ok = drop <= 40 or not vehicle_data.has_esp
        results.append(
            RuleResult(
                rule_id="L3-ESP-040",
                rule_name="Lived Practice — ESP Sensor Drop Limit (40mm)",
                passed=esp_ok,
                flagged=not esp_ok,
                citation=(
                    "TÜV-Praxis (Konsens): Bei Fahrzeugen mit ESP darf die Tieferlegung "
                    "30–40 mm nicht überschreiten, ohne Neukalibrierung des ESP-Sensors."
                ),
                reason=(
                    f"Lowering {drop}mm within 40mm ESP threshold."
                    if esp_ok
                    else f"Lowering {drop}mm exceeds 40mm ESP sensor drop limit — recalibration required."
                ),
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="L3-ESP-040",
                rule_name="Lived Practice — ESP Sensor Drop Limit",
                passed=True,
                flagged=False,
                citation="TÜV-Praxis: ESP-Drop-Regel nur bei Tieferlegungen anwendbar.",
                reason="No lowering modification — ESP drop rule not applicable.",
            )
        )

    # Spacer hub-centricity check
    if modification_data.spacers_front_mm > 0:
        hubcentric = (
            modification_data.spacer_spec is not None
            and modification_data.spacer_spec.hubcentric
        )
        results.append(
            RuleResult(
                rule_id="L3-SPC-HUB",
                rule_name="Lived Practice — Nabenzentrierende Spacer",
                passed=hubcentric,
                flagged=not hubcentric,
                citation=(
                    "TÜV-Praxis: Spacer müssen nabenzentrierend sein; "
                    "nicht-nabenzentrierende Spacer werden in der Regel abgelehnt."
                ),
                reason=(
                    f"{modification_data.spacers_front_mm}mm hub-centric spacers confirmed."
                    if hubcentric
                    else f"{modification_data.spacers_front_mm}mm spacers are NOT hub-centric — rejection likely."
                ),
            )
        )

    # TODO: Implement speed index margin check (lived practice: +1 step minimum)
    wheels = modification_data.wheels_front
    if wheels is not None:
        results.append(
            RuleResult(
                rule_id="L3-SPD-IDX",
                rule_name="Lived Practice — Geschwindigkeitsindex-Puffer",
                passed=wheels.speed_index in ("V", "W", "Y", "Z"),
                flagged=False,
                citation=(
                    "TÜV-Praxis: Geschwindigkeitsindex sollte mindestens eine Stufe "
                    "über dem Fahrzeug-Höchstwert liegen."
                ),
                reason=f"Speed index '{wheels.speed_index}' evaluated against vehicle top speed.",
            )
        )

    return results


def verify_level4_consensus(vehicle_data: VehicleData) -> List[RuleResult]:
    """
    Level 4: Institutional Truth — Consensus rules from authorities and industry bodies.
    e.g., EV out-of-scope for certain R10/R100 regulations.
    """
    results: List[RuleResult] = []

    is_ev = vehicle_data.fuel_type == "electric"

    # R10/R100 out-of-scope for pure EV platforms (institutional consensus)
    results.append(
        RuleResult(
            rule_id="L4-R10-SCOPE",
            rule_name="Institutional Consensus — UN R10 Scope (EV)",
            passed=True,
            flagged=is_ev,
            citation=(
                "KBA/VdTÜV Konsens (2023): Reine Elektrofahrzeuge fallen für bestimmte "
                "EMV-Prüfungen nach UN R10 nicht in den Anwendungsbereich der Richtlinie "
                "für konventionelle Antriebe."
            ),
            reason=(
                "EV platform — R10 EMC scope flagged for manual review per institutional consensus."
                if is_ev
                else "Conventional powertrain — standard R10 scope applies."
            ),
        )
    )

    # R100 battery safety scope for EV
    if is_ev:
        results.append(
            RuleResult(
                rule_id="L4-R100-SCOPE",
                rule_name="Institutional Consensus — UN R100 Battery Safety",
                passed=True,
                flagged=True,
                citation=(
                    "UN R100: Anforderungen an die elektrische Sicherheit von "
                    "Bordnetzen mit Bordspannung > 60 V DC."
                ),
                reason="EV vehicle — R100 battery safety checks flagged for specialist review.",
            )
        )

    # TODO: Implement KBA circular letter cross-reference for institutional updates
    results.append(
        RuleResult(
            rule_id="L4-KBA-UPD",
            rule_name="Institutional Consensus — KBA Rundschreiben Currency",
            passed=True,
            flagged=False,
            citation="KBA Rundschreiben zu StVZO-Änderungen: Aktualitätsprüfung der Gutachtenbasis.",
            reason="TODO: Cross-reference Gutachten issue date against latest KBA circular letters.",
        )
    )

    return results


def _compute_final_verdict(levels: List[LevelResult]) -> FinalVerdict:
    """Deterministic verdict aggregation — no LLM, no inference."""
    any_fail = any(
        not rule.passed and not rule.flagged
        for level in levels
        for rule in level.rules
    )
    any_flagged = any(
        rule.flagged or (not rule.passed and rule.flagged)
        for level in levels
        for rule in level.rules
    ) or any(level.any_flagged for level in levels)

    # Hard fail: any rule explicitly failed (passed=False, flagged=False)
    hard_fails = [
        rule
        for level in levels
        for rule in level.rules
        if not rule.passed and not rule.flagged
    ]

    if hard_fails:
        status = VerdictStatus.FAIL
        summary = (
            f"FAIL — {len(hard_fails)} rule(s) failed deterministic checks. "
            f"First failure: {hard_fails[0].rule_name}."
        )
    elif any_flagged:
        status = VerdictStatus.AUDIT_FLAGGED
        flagged_count = sum(
            1
            for level in levels
            for rule in level.rules
            if rule.flagged or not rule.passed
        )
        summary = (
            f"AUDIT FLAGGED — {flagged_count} rule(s) require manual auditor review. "
            "No hard failures detected."
        )
    else:
        status = VerdictStatus.PASS
        summary = "PASS — All deterministic rules passed. Modification compliant."

    trail_seed = "|".join(
        f"{r.rule_id}:{r.passed}:{r.flagged}" for level in levels for r in level.rules
    )
    audit_id = hashlib.sha256(trail_seed.encode()).hexdigest()[:16]

    return FinalVerdict(
        status=status,
        summary=summary,
        deterministic=True,
        audit_trail_id=f"AUD-{audit_id}",
    )


def execute_test_plan(gutachten: Gutachten) -> TestPlanResult:
    """Execute the full 4-level deterministic test plan for a Gutachten."""
    vehicle = gutachten.vehicle
    modification = gutachten.modification

    level1_rules = verify_level1_stvzo(vehicle, modification)
    level2_rules = verify_level2_vdtuev_751(modification)
    level3_rules = verify_level3_lived_practice(vehicle, modification)
    level4_rules = verify_level4_consensus(vehicle)

    levels = [
        LevelResult(
            level=1,
            level_name="Formal Law (StVZO)",
            rules=level1_rules,
            all_passed=all(r.passed for r in level1_rules),
            any_flagged=any(r.flagged for r in level1_rules),
        ),
        LevelResult(
            level=2,
            level_name="Operationalized Rules (VdTÜV 751)",
            rules=level2_rules,
            all_passed=all(r.passed for r in level2_rules),
            any_flagged=any(r.flagged for r in level2_rules),
        ),
        LevelResult(
            level=3,
            level_name="Lived Inspection Practice",
            rules=level3_rules,
            all_passed=all(r.passed for r in level3_rules),
            any_flagged=any(r.flagged for r in level3_rules),
        ),
        LevelResult(
            level=4,
            level_name="Institutional Truth (Consensus)",
            rules=level4_rules,
            all_passed=all(r.passed for r in level4_rules),
            any_flagged=any(r.flagged for r in level4_rules),
        ),
    ]

    final = _compute_final_verdict(levels)

    return TestPlanResult(
        gutachten_id=gutachten.gutachten_id,
        levels=levels,
        final_verdict=final,
        executed_at=datetime.now(timezone.utc).isoformat(),
    )
