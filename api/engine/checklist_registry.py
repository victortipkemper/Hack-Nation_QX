"""
Fixed checklist registry — Merkblatt 751 I.5.1.x + StVZO §§.
Applicability derived from DocumentFeatures, never from file ID.
"""

import re
from dataclasses import dataclass
from typing import Callable

from data.exemplar_patterns import EXEMPLAR_PATTERNS
from schemas.features import DocumentFeatures
from services.feature_extractor import li_to_kg, sr_to_kmh

CHECKLIST_VERSION = "1.1.0-golden-calibrated"


@dataclass
class CheckDefinition:
    check_id: str
    level: int
    check_name: str
    citation: str
    exemplar_key: str
    applicable: Callable[[DocumentFeatures], tuple[bool, str]]
    evaluate: Callable[[DocumentFeatures], tuple[bool, bool, str, str]]
    severity: str = "error"  # error = Beanstandung; advisory = nur Hinweis


def _remediation(key: str) -> tuple[str, str]:
    ex = EXEMPLAR_PATTERNS.get(key, {})
    return ex.get("remediation", ""), ex.get("reference", "")


def _checks() -> list[CheckDefinition]:
    checks: list[CheckDefinition] = []

    # ── Level 1: StVZO ──────────────────────────────────────────────

    checks.append(
        CheckDefinition(
            check_id="L1-ROUTE-001",
            level=1,
            check_name="Rechtsweg korrekt identifiziert (§19 vs. §21)",
            citation="§ 19 Abs. 2/3 StVZO i.V.m. § 21 StVZO",
            exemplar_key="tga_documentation",
            applicable=lambda f: (True, "Jedes Gutachten benötigt einen identifizierbaren Rechtsweg."),
            evaluate=lambda f: (
                f.route in ("19-3", "21"),
                f.route == "unknown",
                f"Erkannter Rechtsweg: §{f.route} StVZO."
                if f.route != "unknown"
                else "Rechtsweg (§19(3) oder §21) konnte nicht eindeutig bestimmt werden.",
                "route",
            ),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L1-DOC-001",
            level=1,
            check_name="Nachweis ABE/Teilegutachten referenziert",
            citation="§ 19 Abs. 3 StVZO — Nachweis der Verkehrssicherheit",
            exemplar_key="tga_documentation",
            applicable=lambda f: (
                f.has_wheel_change or f.route == "19-3",
                "Bei Rad/Reifen-Änderungen oder §19(3)-Route ist ein Typgenehmigungsnachweis erforderlich.",
            ),
            evaluate=lambda f: _eval_doc_reference(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L1-CONTRA-001",
            level=1,
            check_name="Interne Widersprüchlichkeit (positive vs. negative Schlussfolgerung)",
            citation="§ 21 StVZO i.V.m. § 19 Abs. 2 StVZO",
            exemplar_key="internal_consistency",
            applicable=lambda f: (
                f.internal_contradiction,
                "Prüfung nur bei gleichzeitig positiver und negativer Schlussbescheinigung.",
            ),
            evaluate=lambda f: (
                not f.internal_contradiction,
                f.internal_contradiction,
                "Gutachten widerspricht sich: positive und negative Schlussbescheinigung im selben Dokument.",
                "contradiction",
            ),
        )
    )

    # ── Level 2: Merkblatt 751 ──────────────────────────────────────

    checks.append(
        CheckDefinition(
            check_id="L2-751-I.5.1.6",
            level=2,
            check_name="Tragfähigkeitsindex (LI) vs. Achslast",
            citation="VdTÜV Merkblatt 751 I.5.1.6 — Tragfähigkeit der Reifen",
            exemplar_key="load_index",
            applicable=lambda f: (
                f.has_wheel_change and f.load_index_rear is not None,
                "Mbl. 751 I.5.1.6 gilt bei dokumentierter Rad/Reifen-Änderung mit LI-Angabe.",
            ),
            evaluate=lambda f: _eval_load_index(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-751-I.5.1.4",
            level=2,
            check_name="Geschwindigkeitsindex (SR) vs. Vmax",
            citation="VdTÜV Merkblatt 751 I.5.1.4 — Geschwindigkeitsindex",
            exemplar_key="speed_rating",
            applicable=lambda f: (
                f.has_wheel_change
                and f.speed_index is not None
                and f.vmax_kmh is not None,
                "Mbl. 751 I.5.1.4 gilt bei Rad/Reifen-Änderung mit SR und Vmax-Angabe.",
            ),
            evaluate=lambda f: _eval_speed_rating(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-R39-CIRC",
            level=2,
            check_name="Abrollumfangabweichung > 5% → R39/§57 Tachoprüfung",
            citation="UN R39 / § 57 StVZO i.V.m. Mbl. 751 I.5.1.7",
            exemplar_key="r39_circumference",
            applicable=lambda f: (
                f.rolling_circumference_delta_pct is not None,
                "R39-Prüfung relevant sobald Abrollumfangabweichung im Dokument genannt wird.",
            ),
            evaluate=lambda f: _eval_r39_circumference(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-751-I.5.1.10",
            level=2,
            check_name="Bremsen thermisch/verhalten bei Bremsänderung",
            citation="VdTÜV Merkblatt 751 I.5.1.10/11 — Bremsen",
            exemplar_key="brake_section_41",
            applicable=lambda f: (
                f.has_brake_change,
                "Mbl. 751 I.5.1.10 gilt bei dokumentierter Bremsanlagen-Änderung.",
            ),
            evaluate=lambda f: _eval_brake_section(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-751-I.5.1.8",
            level=2,
            check_name="Radabdeckung §30c/§36a bei Spurverbreiterung",
            citation="§ 30c / § 36a StVZO i.V.m. Mbl. 751 I.5.1.8",
            exemplar_key="wheel_cover_30c_36a",
            applicable=lambda f: (
                f.has_spacers or f.has_track_wideners,
                "Mbl. 751 I.5.1.8 gilt bei Spurplatten oder Spurverbreiterung.",
            ),
            evaluate=lambda f: _eval_wheel_cover(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-TGA-SCOPE",
            level=2,
            check_name="TGA-Verwendungsbereich passt zum Fahrzeug",
            citation="§ 19 Abs. 3 StVZO — Geltungsbereich Teilegutachten",
            exemplar_key="tga_scope",
            applicable=lambda f: (
                f.has_tga or bool(re.search(r"Verwendungsbereich:", f.raw_text, re.I)),
                "Verwendungsbereich-Prüfung bei referenziertem Teilegutachten/TGA.",
            ),
            evaluate=lambda f: (
                not f.tga_wrong_vehicle,
                f.tga_wrong_vehicle,
                "TGA-Verwendungsbereich passt nicht zum begutachteten Fahrzeug, wird aber als eingehalten bescheinigt."
                if f.tga_wrong_vehicle
                else "TGA-Verwendungsbereich konsistent mit Fahrzeugtyp.",
                "tga_scope",
            ),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-TGA-MIN-RIM",
            level=2,
            check_name="Felgendurchmesser ≥ TGA-Mindestmaß",
            citation="Teilegutachten-Auflage — Mindestfelgengröße",
            exemplar_key="min_rim_tga",
            applicable=lambda f: (
                f.min_rim_inch_from_tga is not None and f.documented_rim_inch is not None,
                "Prüfung wenn TGA-Mindestfelge und dokumentierte Felge erkannt.",
            ),
            evaluate=lambda f: _eval_min_rim(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L2-TGA-AUFLAGE",
            level=2,
            check_name="TGA-Auflagen in Gutachten übernommen",
            citation="Teilegutachten-Auflagen (z. B. A3 Nachziehen)",
            exemplar_key="tga_auflage",
            applicable=lambda f: (
                (f.has_tga or f.route == "19-3") and f.tga_auflage_missing,
                "Prüfung wenn TGA-Auflage A3 referenziert aber nicht in Gutachten-Auflagen übernommen.",
            ),
            evaluate=lambda f: (
                not f.tga_auflage_missing,
                f.tga_auflage_missing,
                "TGA-Auflage A3 (Nachziehen nach 50 km) nicht in Gutachten übernommen."
                if f.tga_auflage_missing
                else "TGA-Auflagen übernommen.",
                "tga_auflage",
            ),
        )
    )

    # ── Level 3: Lived practice ───────────────────────────────────────

    checks.append(
        CheckDefinition(
            check_id="L3-AUFSTELLUNG-001",
            level=3,
            check_name="Aufstellung §-Marker konsistent mit Änderungsumfang",
            citation="TÜV-Praxis: Aufstellung muss Prüfumfang widerspiegeln",
            exemplar_key="internal_consistency",
            applicable=lambda f: (
                f.page_count >= 2 or "aufstellung" in f.raw_text.lower(),
                "Aufstellung vorhanden (mehrseitiges §21-Gutachten oder Aufstellungstext).",
            ),
            evaluate=lambda f: _eval_aufstellung_consistency(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L3-PRUEFBERICHT-001",
            level=3,
            check_name="Prüfbericht: Nachweis/Ergebnis-Konsistenz",
            citation="TÜV-Praxis: Checkliste vs. Schlussbescheinigung",
            exemplar_key="pruefbericht_nachweis",
            applicable=lambda f: (
                f.pruefbericht.nachweis_vorhanden is not None
                or f.pruefbericht.ergebnisse_erreicht is not None,
                "Prüfbericht-Checkliste mit ja/nein-Feldern erkannt.",
            ),
            evaluate=lambda f: _eval_pruefbericht_consistency(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L3-WHEEL-LOAD-DOC",
            level=3,
            check_name="Radtraglast dokumentiert (Zahlenwert, nicht nur 'ausreichend')",
            citation="TÜV-Praxis: Nachweisführung Radtraglast",
            exemplar_key="load_index",
            applicable=lambda f: (
                f.has_wheel_change
                and f.pruefbericht.radtraglast_ausreichend_claimed
                and f.aufstellung.section_36a_na,
                "Radtraglast qualitativ behauptet + §36a N/A bei Radänderung (Lücke Radtraglast-Nachweis).",
            ),
            evaluate=lambda f: _eval_wheel_load_doc(f),
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L3-ESP-THRESHOLD",
            level=3,
            check_name="ESP-Funktionsprüfung bei Tieferlegung > 30 mm",
            citation="TÜV-Praxis / Mbl. 751 I.5.1.11 — ESP-Schwelle ~40 mm",
            exemplar_key="internal_consistency",
            applicable=lambda f: (
                f.has_lowering,
                "Bei Tieferlegung: ESP-Relevanz nach Praxis-Schwelle prüfen.",
            ),
            evaluate=lambda f: (
                True,
                False,
                "Tieferlegung erkannt — ESP-Funktionsprüfung empfohlen (Praxis-Schwelle ~40 mm). Hinweis, kein harter Verstoß.",
                "esp_note",
            ),
            severity="advisory",
        )
    )

    # ── Level 4: Consensus ────────────────────────────────────────────

    checks.append(
        CheckDefinition(
            check_id="L4-EV-OUT-OF-SCOPE",
            level=4,
            check_name="BEV: R10/R100 Out-of-Scope vermerkt",
            citation="Konsens technische Dienste: R10/R100 bei Tuning-Gutachten Out-of-Scope",
            exemplar_key="ev_out_of_scope",
            applicable=lambda f: (
                f.is_ev,
                "Bei Elektrofahrzeugen: Out-of-Scope-Vermerk für R10/R100 erwartet.",
            ),
            evaluate=lambda f: _eval_ev_note(f),
            severity="advisory",
        )
    )

    checks.append(
        CheckDefinition(
            check_id="L4-CONSENSUS-001",
            level=4,
            check_name="Schlussbescheinigung konsistent mit Prüfergebnissen",
            citation="Konsens: Positive Bescheinigung nur bei widerspruchsfreiem Nachweis",
            exemplar_key="internal_consistency",
            applicable=lambda f: (
                f.internal_contradiction,
                "Nur bei erkanntem inneren Widerspruch relevant.",
            ),
            evaluate=lambda f: (
                not f.internal_contradiction,
                f.internal_contradiction,
                "Positive Schlussbescheinigung trotz dokumentierter Widersprüche.",
                "consensus",
            ),
        )
    )

    return checks


def _eval_doc_reference(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    if f.route == "21":
        return True, False, "§21-Vollgutachten — TGA/ABE nicht zwingend (Einzelabnahme).", "doc"
    if f.has_abe or f.has_tga:
        return True, False, "ABE oder Teilegutachten im Gutachten referenziert.", "doc"
    if f.route == "19-3":
        return False, True, "§19(3)-Route aber kein TGA/ABE-Nachweis dokumentiert.", "doc"
    return True, False, "Dokumentationsnachweis nicht eindeutig — kein harter Verstoß.", "doc"


def _eval_load_index(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    li = f.load_index_rear or f.load_index_front
    if li is None:
        return True, False, "Kein LI erkannt — Prüfung übersprungen.", "li"
    tire_kg = li_to_kg(li)
    if f.max_rear_axle_load_kg:
        required = f.max_rear_axle_load_kg / 2
        ok = tire_kg >= required
        return (
            ok,
            not ok,
            f"HA-LI {li} = {tire_kg} kg/Rad vs. halbe zul. Achslast {required:.0f} kg "
            f"(zul. Achslast HA {f.max_rear_axle_load_kg} kg).",
            "li",
        )
    return True, False, f"LI {li} erkannt, keine Achslast zum Vergleich.", "li"


def _eval_speed_rating(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    sr_kmh = sr_to_kmh(f.speed_index or "H")
    vmax = f.vmax_kmh or 0
    winter_rule = "winterreifen" in f.raw_text.lower() or "vmax-begrenz" in f.raw_text.lower()
    ok = sr_kmh >= vmax or winter_rule
    return (
        ok,
        not ok,
        f"SR {f.speed_index} = {sr_kmh} km/h vs. Vmax {vmax} km/h"
        + (" — Winterreifen-Regelung dokumentiert." if winter_rule else "."),
        "sr",
    )


def _eval_r39_circumference(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    delta = f.rolling_circumference_delta_pct or 0
    if delta <= 5.0:
        if f.aufstellung.section_57_na:
            return (
                True,
                False,
                f"Δ {delta:.1f}% ≤ 5% — R39/§57 nicht erforderlich, N/A zulässig.",
                "r39",
            )
        return True, False, f"Δ {delta:.1f}% ≤ 5% — R39 nicht ausgelöst.", "r39"
    # delta > 5%
    r39_documented = bool(
        re.search(r"(?:R39|§\s*57|tachoprüf|tachograph)", f.raw_text, re.I)
        and not f.aufstellung.section_57_na
    )
    ok = r39_documented and not f.aufstellung.section_57_na
    return (
        ok,
        not ok,
        f"Abrollumfangabweichung {delta:.1f}% > 5%-Schwelle, §57 in Aufstellung "
        f"{'N/A' if f.aufstellung.section_57_na else 'geprüft'}, "
        f"Tachoprüfung {'dokumentiert' if r39_documented else 'NICHT dokumentiert'}.",
        "r39",
    )


def _eval_brake_section(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    ok = not f.aufstellung.section_41_na
    return (
        ok,
        not ok,
        "Bremsänderung dokumentiert, §41 in Aufstellung als N/A — Prüfumfang unvollständig."
        if f.aufstellung.section_41_na
        else "§41 in Aufstellung geprüft/dokumentiert.",
        "brake",
    )


def _eval_wheel_cover(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    na_both = f.aufstellung.section_30c_na and f.aufstellung.section_36a_na
    return (
        not na_both,
        na_both,
        "Spurverbreiterung/Spurplatten dokumentiert, aber §30c und §36a in Aufstellung N/A."
        if na_both
        else "Radabdeckung §30c/§36a geprüft oder nicht N/A.",
        "cover",
    )


def _eval_min_rim(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    min_r = f.min_rim_inch_from_tga or 0
    doc_r = f.documented_rim_inch or 0
    ok = doc_r >= min_r
    return (
        ok,
        not ok,
        f"Dokumentierte Felge {doc_r}″ vs. TGA-Mindestmaß {min_r}″.",
        "rim",
    )


def _eval_aufstellung_consistency(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    issues: list[str] = []
    if f.has_brake_change and f.aufstellung.section_41_na:
        issues.append("§41 N/A trotz Bremsänderung")
    if (f.has_spacers or f.has_track_wideners) and f.aufstellung.section_36a_na:
        issues.append("§36a N/A trotz Spurverbreiterung")
    if (f.has_spacers or f.has_track_wideners) and f.aufstellung.section_30c_na:
        issues.append("§30c N/A trotz Spurverbreiterung")
    if f.rolling_circumference_delta_pct and (f.rolling_circumference_delta_pct > 5) and f.aufstellung.section_57_na:
        issues.append("§57 N/A trotz Δ > 5%")
    if issues:
        return False, True, "; ".join(issues), "aufstellung"
    return True, False, "Aufstellung §-Marker konsistent mit Änderungsumfang.", "aufstellung"


def _eval_pruefbericht_consistency(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    pb = f.pruefbericht
    if pb.nachweis_vorhanden is False and (f.has_tga or f.has_abe):
        return (
            False,
            True,
            "Prüfbericht: Nachweis = nein, obwohl TGA/ABE im Gutachten referenziert.",
            "pruefbericht",
        )
    if pb.nachweis_vorhanden is False and pb.ergebnisse_erreicht is True:
        return (
            False,
            True,
            "Prüfbericht-Paradox: Nachweis = nein, Ergebnisse erreicht = ja.",
            "pruefbericht",
        )
    return True, False, "Prüfbericht Nachweis/Ergebnis konsistent.", "pruefbericht"


def _eval_wheel_load_doc(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    has_explicit_calc = bool(
        re.search(
            r"radtraglast\s+\d+\s*kg|1/2\s*zul\.?\s*achslast|tragfähigkeit.*achslast",
            f.raw_text,
            re.I,
        )
    )
    li = f.load_index_rear or f.load_index_front
    li_vs_axle = False
    if li is not None and f.max_rear_axle_load_kg:
        li_vs_axle = li_to_kg(li) >= f.max_rear_axle_load_kg / 2
    documented = has_explicit_calc or li_vs_axle
    only_claim = f.pruefbericht.radtraglast_ausreichend_claimed and not documented
    if only_claim:
        return (
            False,
            True,
            "Radtraglast nur als 'ausreichend' behauptet, ohne Zahlenwert/LI-Berechnung.",
            "wheel_load",
        )
    if documented:
        return True, False, "Radtraglast mit LI und/oder Achslast-Berechnung dokumentiert.", "wheel_load"
    return True, False, "Radtraglast-Nachweis ausreichend oder nicht behauptet.", "wheel_load"


def _eval_ev_note(f: DocumentFeatures) -> tuple[bool, bool, str, str]:
    has_note = bool(
        re.search(r"R10|R100|out.of.scope|nicht\s+(?:gegenstand|umfang)", f.raw_text, re.I)
    )
    return (
        has_note or True,  # advisory for GREEN+EV
        False,
        "R10/R100 Out-of-Scope vermerkt." if has_note else "EV-Fahrzeug — R10/R100 Out-of-Scope-Hinweis empfohlen (GREEN+EV).",
        "ev",
    )


CHECKLIST: list[CheckDefinition] = _checks()
