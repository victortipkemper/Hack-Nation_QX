"""
Structured expert / inspection-practice knowledge per checklist rule.
Level 3 (TÜV-Praxis) + Merkblatt 751 procedural steps — not used in verdict logic.
"""

from dataclasses import dataclass, field


@dataclass
class ProcedureStep:
    order: int
    title: str
    instruction: str
    acceptance_criteria: str = ""
    tools: list[str] = field(default_factory=list)


@dataclass
class ExpertProcedure:
    check_id: str
    merkblatt_sections: list[str]
    practice_level: str  # "Merkblatt 751" | "TÜV-Praxis" | "Konsens"
    summary: str
    standard_procedure: list[ProcedureStep]
    nachpruefung: list[ProcedureStep]
    documentation_checklist: list[str]
    practice_notes: list[str]


EXPERT_PROCEDURES: dict[str, ExpertProcedure] = {
    "L2-751-I.5.1.6": ExpertProcedure(
        check_id="L2-751-I.5.1.6",
        merkblatt_sections=["I.5.1.6", "I.5.2.3"],
        practice_level="Merkblatt 751",
        summary="Tragfähigkeitsindex der Bereifung gegen zulässige Rad-/Achslast prüfen.",
        standard_procedure=[
            ProcedureStep(
                1,
                "Reifenkennzeichnung erfassen",
                "LI aus Zu 15.1/2 oder Reifentabelle ablesen (z. B. 97H → LI 97).",
                "LI je Rad dokumentiert.",
                ["Gutachten Zu 15.1/2", "Reifentabelle TGA"],
            ),
            ProcedureStep(
                2,
                "Zulässige Achslast ermitteln",
                "Zul. Achslast HA aus Fahrzeugdaten / CoC entnehmen.",
                "Achslast HA in kg notiert.",
                ["CoC", "Fahrzeugdatenblatt"],
            ),
            ProcedureStep(
                3,
                "LI in kg umrechnen und vergleichen",
                "LI→kg-Tabelle nutzen; halbe Achslast = Mindesttragfähigkeit pro Rad.",
                "LI-kg ≥ zul. Achslast HA / 2.",
                ["LI-Umrechnungstabelle"],
            ),
        ],
        nachpruefung=[
            ProcedureStep(
                1,
                "Berechnung im Prüfbericht nachreichen",
                "LI, kg/Rad und zul. Achslast HA mit Formel ausweisen.",
                "Zahlenwert-Nachweis vollständig.",
            ),
            ProcedureStep(
                2,
                "Alternative Bereifung prüfen",
                "Reifen mit höherem LI wählen oder Achslast reduzieren (nicht zulässig ohne Nachweis).",
                "Neue Bereifung deckt Achslast ab.",
            ),
        ],
        documentation_checklist=[
            "Zu 15.1/2 mit LI/SR je Achse",
            "Prüfbericht §36: Radtraglast mit Zahlenwert",
            "Bei TGA: LI-Mindestanforderung aus Teilegutachten",
        ],
        practice_notes=[
            "Qualitative Formulierung „Radtraglast ausreichend“ ohne LI-Rechnung reicht in der Praxis nicht.",
            "HA-Achse ist bei Sportbereifung häufig der Engpass.",
        ],
    ),
    "L2-751-I.5.1.4": ExpertProcedure(
        check_id="L2-751-I.5.1.4",
        merkblatt_sections=["I.5.1.4"],
        practice_level="Merkblatt 751",
        summary="Geschwindigkeitsindex gegen bauartbedingte Höchstgeschwindigkeit prüfen.",
        standard_procedure=[
            ProcedureStep(
                1,
                "SR aus Reifenangabe ablesen",
                "Letzter Buchstabe der Reifengröße (z. B. H, V, W) → km/h laut Tabelle.",
                "SR dokumentiert.",
            ),
            ProcedureStep(
                2,
                "Vmax des Fahrzeugs ermitteln",
                "Bauartbedingte Höchstgeschwindigkeit aus Gutachten/CoC.",
                "Vmax in km/h notiert.",
            ),
            ProcedureStep(
                3,
                "Vergleich SR ≥ Vmax",
                "Bei Winterreifen: Vmax-Begrenzung oder Regelung im Gutachten prüfen.",
                "SR deckt Vmax ab oder Ausnahme dokumentiert.",
            ),
        ],
        nachpruefung=[
            ProcedureStep(
                1,
                "Reifen mit höherem SR wählen",
                "Alternative Bereifung mit ausreichendem Geschwindigkeitsindex.",
                "SR ≥ Vmax.",
            ),
            ProcedureStep(
                2,
                "Winterreifen-Regelung vermerken",
                "Vmax-Begrenzung auf 210 km/h o. ä. im Gutachten ausweisen.",
                "Regelung im Prüfbericht.",
            ),
        ],
        documentation_checklist=["Zu 15.1/2 SR", "Vmax Fahrzeug", "Winterreifen-Hinweis falls zutreffend"],
        practice_notes=["Bei M+S Winterbereifung oft separate Vmax-Regelung nötig."],
    ),
    "L2-R39-CIRC": ExpertProcedure(
        check_id="L2-R39-CIRC",
        merkblatt_sections=["I.5.1.7"],
        practice_level="Merkblatt 751",
        summary="Abrollumfangabweichung > 5 % → Tachoprüfung nach §57 / UN R39.",
        standard_procedure=[
            ProcedureStep(
                1,
                "Abrollumfang berechnen",
                "Neuer vs. Serien-Reifen: Abweichung in % dokumentieren.",
                "Prozentwert im Gutachten.",
            ),
            ProcedureStep(
                2,
                "Schwelle 5 % prüfen",
                "Bei > 5 %: Tachoprüfung erforderlich.",
                "Entscheidung dokumentiert.",
            ),
            ProcedureStep(
                3,
                "Tachoprüfung durchführen",
                "Prüfstand oder Rollenprüfstand gemäß §57 / R39.",
                "Tachoprüfprotokoll liegt vor.",
                ["Tachoprüfstand"],
            ),
        ],
        nachpruefung=[
            ProcedureStep(1, "Tachoprüfung nachholen", "Prüfprotokoll §57 beifügen.", "Protokoll im Anhang."),
            ProcedureStep(2, "§57 in Aufstellung setzen", "N/A entfernen, Prüfung als durchgeführt markieren.", "Aufstellung konsistent."),
        ],
        documentation_checklist=["Abrollumfang-Berechnung", "Tachoprüfprotokoll", "§57 Aufstellung"],
        practice_notes=["Aufstellung oft fälschlich §57 = N/A obwohl Abweichung > 5 %."],
    ),
    "L2-751-I.5.1.10": ExpertProcedure(
        check_id="L2-751-I.5.1.10",
        merkblatt_sections=["I.5.1.10", "I.5.1.11"],
        practice_level="Merkblatt 751",
        summary="Bei Bremsänderung thermische Belastung und Bremsverhalten prüfen.",
        standard_procedure=[
            ProcedureStep(1, "Bremsänderung identifizieren", "Größere Scheiben, andere Beläge, andere Kolben — Umfang klären.", "Änderung dokumentiert."),
            ProcedureStep(2, "§41 Aufstellung prüfen", "§41 darf nicht N/A sein wenn Bremsen geändert.", "§41 als geprüft markiert."),
            ProcedureStep(3, "Bremsprüfung / Eigenprüfung", "Bremskraft oder Hersteller-Eigenprüfung gemäß Mbl. 751.", "Nachweis im Prüfbericht."),
        ],
        nachpruefung=[
            ProcedureStep(1, "§41 Prüfbericht ergänzen", "Bremsen-Checkliste mit Nachweis ja/Nein korrigieren.", "Widerspruch beseitigt."),
            ProcedureStep(2, "Bremsprüfung nachholen", "Rollenprüfstand oder dokumentierte Eigenprüfung.", "Ergebnis erreicht = ja."),
        ],
        documentation_checklist=["§41 Aufstellung", "Prüfbericht Bremsen", "TGA Bremsnachweise"],
        practice_notes=["Widerspruch „Nachweis nein“ + „Ergebnis ja“ ist häufiger Audit-Fund."],
    ),
    "L2-751-I.5.1.8": ExpertProcedure(
        check_id="L2-751-I.5.1.8",
        merkblatt_sections=["I.5.1.8"],
        practice_level="Merkblatt 751",
        summary="Radabdeckung §30c/§36a bei Spurplatten oder Spurverbreiterung.",
        standard_procedure=[
            ProcedureStep(1, "Spurmaß ermitteln", "Mit/ohne Spacer: Spurweite messen.", "Spurweite dokumentiert."),
            ProcedureStep(2, "Radabdeckung prüfen", "§30c Außenkante, §36a Abdeckung — Mindestabstände.", "Freigang ≥ Vorgaben."),
            ProcedureStep(3, "Fotodokumentation", "3/4-Ansicht, Rad in Lenkeinschlag.", "Fotos im Anhang."),
        ],
        nachpruefung=[
            ProcedureStep(1, "Nachmessung mit korrekter Bereifung", "Abdeckung unter Last/Lenkeinschlag erneut prüfen.", "Mindestabstände eingehalten."),
            ProcedureStep(2, "§30c/§36a Aufstellung korrigieren", "N/A entfernen wenn Spacer verbaut.", "Aufstellung konsistent."),
        ],
        documentation_checklist=["Spurweite", "§30c/§36a Aufstellung", "Fotos Radabdeckung"],
        practice_notes=["Spurplatten ohne §36a-Prüfung ist klassischer Gelb-Fund."],
    ),
    "L2-TGA-SCOPE": ExpertProcedure(
        check_id="L2-TGA-SCOPE",
        merkblatt_sections=["I.5.1.1"],
        practice_level="Merkblatt 751",
        summary="Teilegutachten-Verwendungsbereich muss zum Fahrzeug passen.",
        standard_procedure=[
            ProcedureStep(1, "Fahrzeugtyp aus Gutachten", "Hersteller, Typ, FIN/Baureihe erfassen.", "Fahrzeug identifiziert."),
            ProcedureStep(2, "TGA-Verwendungsbereich lesen", "Zulässige Fahrzeuge im Teilegutachten abgleichen.", "Überlappung vorhanden."),
        ],
        nachpruefung=[
            ProcedureStep(1, "Passendes TGA beschaffen", "Teilegutachten für exakte Baureihe/Fahrzeugklasse.", "Verwendungsbereich deckt Fahrzeug ab."),
        ],
        documentation_checklist=["TGA Verwendungsbereich", "Fahrzeug-Ident im Gutachten"],
        practice_notes=[],
    ),
    "L3-AUFSTELLUNG-001": ExpertProcedure(
        check_id="L3-AUFSTELLUNG-001",
        merkblatt_sections=[],
        practice_level="TÜV-Praxis",
        summary="Aufstellung muss zum dokumentierten Änderungsumfang passen.",
        standard_procedure=[
            ProcedureStep(1, "Änderungsumfang listen", "Räder, Bremsen, Fahrwerk, Spacer — was wurde geändert?", "Liste vollständig."),
            ProcedureStep(2, "Aufstellung § für § abgleichen", "Jeder relevante § muss geprüft oder begründet N/A sein.", "Kein § fälschlich N/A."),
        ],
        nachpruefung=[
            ProcedureStep(1, "Aufstellung korrigieren", "Betroffene §§ von N/A auf geprüft setzen.", "Aufstellung = Änderungsumfang."),
            ProcedureStep(2, "Fehlende Prüfungen nachholen", "Nachgelagerte Messungen/Protokolle ergänzen.", "Prüfberichte vollständig."),
        ],
        documentation_checklist=["Aufstellung technische Vorschriften", "Änderungsbeschreibung"],
        practice_notes=["Aufstellung ist die häufigste Quelle für verdeckte Lücken."],
    ),
    "L3-WHEEL-LOAD-DOC": ExpertProcedure(
        check_id="L3-WHEEL-LOAD-DOC",
        merkblatt_sections=["I.5.2.3"],
        practice_level="TÜV-Praxis",
        summary="Radtraglast nur mit Zahlenwert-Nachweis, nicht nur qualitativ.",
        standard_procedure=[
            ProcedureStep(1, "Prüfbericht Radtraglast suchen", "Feld Radtraglast / LI-Berechnung.", "Zahlenwerte vorhanden."),
        ],
        nachpruefung=[
            ProcedureStep(1, "LI-Berechnung einfügen", "LI, kg/Rad, zul. Achslast — Formel ausweisen.", "Kein rein qualitativer Text."),
        ],
        documentation_checklist=["Prüfbericht §36 Radtraglast"],
        practice_notes=["Gleiche Wurzel wie L2-LI, aber L3 fokussiert Dokumentationsqualität."],
    ),
    "L3-ESP-THRESHOLD": ExpertProcedure(
        check_id="L3-ESP-THRESHOLD",
        merkblatt_sections=["I.5.1.11"],
        practice_level="TÜV-Praxis",
        summary="Bei Tieferlegung nahe 40 mm ESP-Funktionsprüfung empfohlen.",
        standard_procedure=[
            ProcedureStep(1, "Tieferlegung quantifizieren", "mm-Angabe aus Gutachten / Messung.", "Höhenänderung dokumentiert."),
            ProcedureStep(2, "Schwelle ~40 mm anwenden", "Ab ~40 mm: ESP-Test empfohlen (Praxis-Konsens).", "Empfehlung begründet."),
            ProcedureStep(3, "ESP-Funktionsprüfung", "Diagnosegerät oder Rollenprüfstand.", "ESP funktionsfähig."),
        ],
        nachpruefung=[
            ProcedureStep(1, "ESP-Test durchführen", "Funktionsprüfung dokumentieren.", "Protokoll oder Diagnose-Log."),
            ProcedureStep(2, "Hinweis ins Gutachten", "Bei 30 mm: Advisory-Hinweis mit Begründung.", "Transparenz für Audit."),
        ],
        documentation_checklist=["Tieferlegung mm", "ESP-Prüfnachweis oder Advisory"],
        practice_notes=["40-mm-Schwelle ist Praxis-Konsens, nicht Gesetzestext."],
    ),
    "L1-CONTRA-001": ExpertProcedure(
        check_id="L1-CONTRA-001",
        merkblatt_sections=[],
        practice_level="StVZO",
        summary="Interne Widersprüche im Gutachten beseitigen.",
        standard_procedure=[
            ProcedureStep(1, "Schlussbescheinigung lesen", "Positive/negative Formulierung identifizieren.", "Widerspruch erkannt."),
        ],
        nachpruefung=[
            ProcedureStep(1, "Gutachten zurück an SV", "Entweder Mängel beheben oder negative Schlussfolgerung.", "Einheitliche Bewertung."),
        ],
        documentation_checklist=["Schlussbescheinigung", "BE-Erlöschen-Text"],
        practice_notes=[],
    ),
}

# Default fallback for checks without explicit procedure
DEFAULT_NACHPRUEFUNG = [
    ProcedureStep(1, "Befund im Gutachten verifizieren", "Markierte Stelle im PDF und Prüfbericht gegenlesen."),
    ProcedureStep(2, "Fehlenden Nachweis ergänzen", "Dokumentation oder Messung nachreichen."),
    ProcedureStep(3, "Gutachten aktualisieren", "Korrigierte Aufstellung und Prüfbericht einreichen."),
]
