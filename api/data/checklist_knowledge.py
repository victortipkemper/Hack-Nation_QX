"""
Knowledge base for checklist rule IDs — anchors, explanations, regulatory links.
Maps to engine/checklist_registry.py check_ids.
"""

from dataclasses import dataclass, field

from data.regulatory_links import RegulatoryLink, links_for_citation


@dataclass
class ParagraphAnchor:
    paragraph_ref: str
    search_phrases: list[str]
    page_hint: int | None = None
    merge_phrases: list[str] = field(default_factory=list)


@dataclass
class ChecklistRuleKnowledge:
    check_id: str
    paragraph_ref: str
    explanation_template: str
    anchors: list[ParagraphAnchor]
    extra_references: list[str] = field(default_factory=list)

    def regulatory_links(self, citation: str) -> list[RegulatoryLink]:
        return links_for_citation(citation, self.extra_references)


CHECKLIST_KNOWLEDGE: dict[str, ChecklistRuleKnowledge] = {
    "L1-ROUTE-001": ChecklistRuleKnowledge(
        check_id="L1-ROUTE-001",
        paragraph_ref="Rechtsweg § 19 / § 21 StVZO",
        explanation_template="Der Rechtsweg (Änderungsabnahme § 19 Abs. 3 oder Vollgutachten § 21) muss eindeutig erkennbar sein.",
        anchors=[ParagraphAnchor("Kopfdaten", ["§ 19 Abs. 3", "§ 21 StVZO", "Änderungsabnahme"], page_hint=1)],
        extra_references=["§ 19 StVZO", "§ 21 StVZO"],
    ),
    "L1-DOC-001": ChecklistRuleKnowledge(
        check_id="L1-DOC-001",
        paragraph_ref="§ 19 Abs. 3 — Nachweis ABE/Teilegutachten",
        explanation_template="Für § 19(3)-Änderungsabnahmen muss ein gültiger ABE- oder Teilegutachten-Nachweis referenziert sein.",
        anchors=[
            ParagraphAnchor("Zu 15.1/2", ["Zu 15.1/2", "(kein TGA)", "kein TGA"], page_hint=1),
            ParagraphAnchor("Prüfzeugnis", ["Teilegutachten Nr.", "TGA Nr.", "ABE"], page_hint=1),
        ],
        extra_references=["§ 19 Abs. 3 StVZO", "VdTÜV Merkblatt 751"],
    ),
    "L1-CONTRA-001": ChecklistRuleKnowledge(
        check_id="L1-CONTRA-001",
        paragraph_ref="§ 21 — Interne Widersprüchlichkeit",
        explanation_template="Positive und negative Schlussbescheinigung widersprechen sich — Gutachten ist nicht valide.",
        anchors=[
            ParagraphAnchor("Schlussbescheinigung", ["geltenden Vorschriften entspricht"], page_hint=1),
            ParagraphAnchor("Negativ", ["nicht den geltenden Vorschriften", "Widerspruch"], page_hint=1),
        ],
        extra_references=["§ 21 StVZO", "§ 19 Abs. 2 StVZO"],
    ),
    "L2-751-I.5.1.6": ChecklistRuleKnowledge(
        check_id="L2-751-I.5.1.6",
        paragraph_ref="Mbl. 751 I.5.1.6 — Tragfähigkeitsindex (LI)",
        explanation_template="Der Tragfähigkeitsindex der Bereifung muss die zulässige Achslast abdecken (halbe Achslast pro Rad).",
        anchors=[
            ParagraphAnchor("Zu 15.1/2 — LI", ["Zu 15.1/2", "Achslast HA", "89Y", "88Y"], page_hint=1,
                            merge_phrases=["zul. Achslast"]),
            ParagraphAnchor("Prüfbericht LI", ["Radtraglast", "Tragfähigkeit"], page_hint=4),
        ],
        extra_references=["VdTÜV Merkblatt 751 I.5.1.6", "§ 36 StVZO"],
    ),
    "L2-751-I.5.1.4": ChecklistRuleKnowledge(
        check_id="L2-751-I.5.1.4",
        paragraph_ref="Mbl. 751 I.5.1.4 — Geschwindigkeitsindex (SR)",
        explanation_template="Der Geschwindigkeitsindex muss zur bauartbedingten Höchstgeschwindigkeit passen.",
        anchors=[
            ParagraphAnchor("Zu 15.1/2 — SR", ["Zu 15.1/2", " km/h"], page_hint=1),
            ParagraphAnchor("Vmax", ["Bauartbedingte Höchstgeschwindigkeit", "250 km/h", "210 km/h"], page_hint=1),
        ],
        extra_references=["VdTÜV Merkblatt 751 I.5.1.4", "§ 36 StVZO"],
    ),
    "L2-R39-CIRC": ChecklistRuleKnowledge(
        check_id="L2-R39-CIRC",
        paragraph_ref="§ 57 StVZO / UN R39 — Tachoprüfung",
        explanation_template="Bei Abrollumfangabweichung > 5 % ist eine Tachoprüfung nach § 57 / UN R39 erforderlich.",
        anchors=[
            ParagraphAnchor("Abrollumfang", ["Abrollumfang", "Abrollumfangabweichung", "%"], page_hint=1),
            ParagraphAnchor("§57 Aufstellung", ["§57", "Geschwindigkeitsmessgerät"], page_hint=3),
            ParagraphAnchor("Tachoprüfung", ["Tachoprüfung", "R39"], page_hint=4),
        ],
        extra_references=["§ 57 StVZO", "UN R39", "VdTÜV Merkblatt 751 I.5.1.7"],
    ),
    "L2-751-I.5.1.10": ChecklistRuleKnowledge(
        check_id="L2-751-I.5.1.10",
        paragraph_ref="Mbl. 751 I.5.1.10 — Bremsen bei Bremsänderung",
        explanation_template="Bei Änderung der Bremsanlage muss § 41 geprüft und dokumentiert werden.",
        anchors=[
            ParagraphAnchor("Bremsänderung", ["Bremsscheib", "Bremsanlage", "Bremsscheiben VA"], page_hint=1),
            ParagraphAnchor("§41 Aufstellung", ["§41", "Bremsen und Unterlegkeile"], page_hint=2),
        ],
        extra_references=["§ 41 StVZO", "VdTÜV Merkblatt 751 I.5.1.10"],
    ),
    "L2-751-I.5.1.8": ChecklistRuleKnowledge(
        check_id="L2-751-I.5.1.8",
        paragraph_ref="§ 30c / § 36a StVZO — Radabdeckung",
        explanation_template="Bei Spurverbreiterung oder Spurplatten müssen § 30c und § 36a geprüft werden.",
        anchors=[
            ParagraphAnchor("Spurverbreiterung", ["Spurverbreiterung", "Spurplatte", "Distanzscheib"], page_hint=1),
            ParagraphAnchor("§36a", ["§36a", "Radabdeckungen"], page_hint=2),
            ParagraphAnchor("§30c", ["§30c", "Außenkanten"], page_hint=2),
        ],
        extra_references=["§ 30c StVZO", "§ 36a StVZO", "VdTÜV Merkblatt 751 I.5.1.8"],
    ),
    "L2-TGA-SCOPE": ChecklistRuleKnowledge(
        check_id="L2-TGA-SCOPE",
        paragraph_ref="Teilegutachten — Verwendungsbereich",
        explanation_template="Das Teilegutachten muss zum konkreten Fahrzeugtyp/Baureihe passen.",
        anchors=[
            ParagraphAnchor("Verwendungsbereich", ["Verwendungsbereich", "Zuordnung des Prüfzeugnisses"], page_hint=1),
            ParagraphAnchor("Fahrzeugtyp", ["Fahrzeughersteller / Typ", "Fahrzeug-Ident"], page_hint=1),
        ],
        extra_references=["§ 19 Abs. 3 StVZO"],
    ),
    "L2-TGA-MIN-RIM": ChecklistRuleKnowledge(
        check_id="L2-TGA-MIN-RIM",
        paragraph_ref="TGA — Mindestfelgendurchmesser",
        explanation_template="Der dokumentierte Felgendurchmesser muss dem TGA-Mindestmaß entsprechen.",
        anchors=[
            ParagraphAnchor("Mindestfelge", ["Mindest-Felgengröße", "Mindest", "Zoll"], page_hint=1),
            ParagraphAnchor("Dokumentierte Felge", ["Jx", "Räder", "Felge"], page_hint=1),
        ],
        extra_references=["§ 19 Abs. 3 StVZO", "VdTÜV Merkblatt 751"],
    ),
    "L2-TGA-AUFLAGE": ChecklistRuleKnowledge(
        check_id="L2-TGA-AUFLAGE",
        paragraph_ref="TGA-Auflagen — Übernahme ins Gutachten",
        explanation_template="Alle TGA-Auflagen (z. B. A3 Nachziehen nach 50 km) müssen ins Gutachten übernommen werden.",
        anchors=[
            ParagraphAnchor("TGA Auflagen", ["Auflagen A1", "Auflage A3", "Nachziehen"], page_hint=1),
            ParagraphAnchor("Gutachten Auflagen", ["5  Auflagen", "Auflagen"], page_hint=1),
        ],
        extra_references=["§ 19 Abs. 3 StVZO"],
    ),
    "L3-AUFSTELLUNG-001": ChecklistRuleKnowledge(
        check_id="L3-AUFSTELLUNG-001",
        paragraph_ref="Aufstellung — §-Marker vs. Änderungsumfang",
        explanation_template="Die Aufstellung markiert relevante §§ als N/A, obwohl der Änderungsumfang eine Prüfung erfordert.",
        anchors=[
            ParagraphAnchor("Aufstellung", ["Aufstellung der technischen Vorschriften"], page_hint=2),
            ParagraphAnchor("§57 N/A", ["§57", "N/A"], page_hint=3),
            ParagraphAnchor("§41 N/A", ["§41", "N/A"], page_hint=2),
        ],
        extra_references=["§ 36 StVZO", "VdTÜV Merkblatt 751"],
    ),
    "L3-PRUEFBERICHT-001": ChecklistRuleKnowledge(
        check_id="L3-PRUEFBERICHT-001",
        paragraph_ref="§ 36 Prüfbericht — Checkliste",
        explanation_template="Prüfbericht-Checkliste widerspricht sich (Nachweis nein / Ergebnis ja).",
        anchors=[
            ParagraphAnchor("Nachweis", ["Nachweis", "vorhanden"], page_hint=4),
            ParagraphAnchor("Ergebnis", ["Ergebnisse erreicht", "Eigenprüfung"], page_hint=4),
        ],
        extra_references=["§ 36 StVZO", "VdTÜV Merkblatt 751"],
    ),
    "L3-WHEEL-LOAD-DOC": ChecklistRuleKnowledge(
        check_id="L3-WHEEL-LOAD-DOC",
        paragraph_ref="Radtraglast — Zahlenwert-Nachweis",
        explanation_template="Radtraglast wird nur qualitativ als 'ausreichend' behauptet, ohne LI-/Achslast-Berechnung.",
        anchors=[
            ParagraphAnchor("Radtraglast", ["Radtraglast ausreichend", "Radtraglast"], page_hint=4),
        ],
        extra_references=["§ 36 StVZO", "VdTÜV Merkblatt 751 I.5.1.6"],
    ),
    "L3-ESP-THRESHOLD": ChecklistRuleKnowledge(
        check_id="L3-ESP-THRESHOLD",
        paragraph_ref="ESP-Funktionsprüfung bei Tieferlegung",
        explanation_template="Bei Tieferlegung nahe der Praxis-Schwelle (~40 mm) ESP-Funktionsprüfung empfohlen.",
        anchors=[ParagraphAnchor("Tieferlegung", ["Tieferlegung", "Sportfedern", "Fahrwerk"])],
        extra_references=["VdTÜV Merkblatt 751 I.5.1.11", "§ 38 StVZO"],
    ),
    "L4-EV-OUT-OF-SCOPE": ChecklistRuleKnowledge(
        check_id="L4-EV-OUT-OF-SCOPE",
        paragraph_ref="BEV — R10/R100 Out-of-Scope",
        explanation_template="Bei Elektrofahrzeugen R10/R100 als Out-of-Scope vermerken.",
        anchors=[ParagraphAnchor("EV Hinweis", ["R10", "R100", "Out-of-Scope", "BEV", "Hochvolt"])],
        extra_references=["UN R10", "UN R100"],
    ),
    "L4-CONSENSUS-001": ChecklistRuleKnowledge(
        check_id="L4-CONSENSUS-001",
        paragraph_ref="Schlussbescheinigung — Konsistenz",
        explanation_template="Schlussbescheinigung widerspricht den dokumentierten Prüfergebnissen.",
        anchors=[ParagraphAnchor("Schluss", ["geltenden Vorschriften entspricht"], page_hint=1)],
        extra_references=["§ 21 StVZO"],
    ),
}
