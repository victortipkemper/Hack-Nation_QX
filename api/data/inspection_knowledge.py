"""
Inspection knowledge base — rule ↔ paragraph mapping, references, remediation.
Seed corpus for future document-based training. Verdict stays in rules engine.
"""

from dataclasses import dataclass, field


@dataclass
class ParagraphAnchor:
    """Where to look in a Gutachten document for a given rule violation."""
    paragraph_ref: str
    search_phrases: list[str]
    page_hint: int | None = None  # optional expected page
    merge_phrases: list[str] = field(default_factory=list)  # expand bbox across these


@dataclass
class RuleKnowledge:
    rule_id: str
    paragraph_ref: str
    stvzo_paragraph: str
    regulatory_references: list[str]
    explanation: str
    remediation: str
    anchors: list[ParagraphAnchor]


INSPECTION_KNOWLEDGE: dict[str, RuleKnowledge] = {
    "L1-21-CONTRA": RuleKnowledge(
        rule_id="L1-21-CONTRA",
        paragraph_ref="§ 21 StVZO — Schlussbescheinigung vs. BE-Erlöschen",
        stvzo_paragraph="§ 21 StVZO i.V.m. § 19 Abs. 2 StVZO",
        regulatory_references=[
            "§ 21 StVZO: Gutachten zur Erlangung der Betriebserlaubnis",
            "§ 19 Abs. 2 StVZO: Technische Änderungen bedürfen einer Genehmigung",
            "EG-DOK 4.8.0 — Widerspruchsfreiheit des Gutachtens",
        ],
        explanation=(
            "Das Gutachten enthält einen internen Widerspruch: Auf Seite 1 wird bestätigt, "
            "dass das Fahrzeug den geltenden Vorschriften entspricht (§ 21 positive "
            "Schlussbescheinigung). Gleichzeitig wird auf Seite 2 das Erlöschen der "
            "Betriebserlaubnis begründet — und § 36 wird dennoch als „vorschriftsmäßig“ bewertet."
        ),
        remediation=(
            "Gutachten zurückweisen. Sachverständiger muss entweder (a) die positive "
            "Schlussbescheinigung entfernen und Mangel dokumentieren, oder (b) die "
            "Mängel beheben (TGA vorlegen, Bereifung korrigieren) und neues Gutachten "
            "ausstellen. § 36-Bewertung muss mit der Begründung übereinstimmen."
        ),
        anchors=[
            ParagraphAnchor(
                "§ 21 Schlussbescheinigung",
                ["geltenden Vorschriften entspricht"],
                page_hint=1,
            ),
            ParagraphAnchor(
                "§ 21 BE-Erlöschen",
                [
                    "Betriebserlaubnis des Fahrzeuges ist erloschen",
                    "frühere Betriebserlaubnis",
                ],
                page_hint=2,
                merge_phrases=["kein Teilegutachten vorliegt"],
            ),
            ParagraphAnchor(
                "§ 36 Bewertung",
                ["§36", "Vorschriftsmäßig"],
                page_hint=2,
            ),
        ],
    ),
    "L1-19-002": RuleKnowledge(
        rule_id="L1-19-002",
        paragraph_ref="§ 19 Abs. 3 StVZO — Nachweis / Zu 15.1/2",
        stvzo_paragraph="§ 19 Abs. 3 StVZO",
        regulatory_references=[
            "§ 19 Abs. 3 StVZO: Nachweis der Verkehrssicherheit",
            "VdTÜV-Merkblatt 751: Dokumentationspflicht für Radsätze",
            "EG-DOK Feld 15.1/15.2 — Eintragung der Bereifung",
        ],
        explanation=(
            "Im Feld Zu 15.1/2 ist „kein TGA“ vermerkt — es liegt kein Teilegutachten "
            "und keine ABE für die Rad-/Reifenkombination vor. Ohne diesen Nachweis "
            "kann die Verkehrssicherheit der Änderung nicht belegt werden."
        ),
        remediation=(
            "Fahrzeughalter muss ein gültiges Teilegutachten (TGA) oder eine ABE für "
            "die exakte Rad-/Reifenkombination auf dem konkreten Fahrzeug vorlegen. "
            "Alternativ: Radsatz gegen dokumentierten Serien- oder TGA-Radsatz tauschen."
        ),
        anchors=[
            ParagraphAnchor(
                "Zu 15.1/2",
                ["(kein TGA)", "kein TGA"],
                page_hint=1,
            ),
            ParagraphAnchor(
                "Begründung BE-Erlöschen",
                ["kein Teilegutachten vorliegt"],
                page_hint=2,
            ),
        ],
    ),
    "L2-751-I.5.2.3-HA": RuleKnowledge(
        rule_id="L2-751-I.5.2.3-HA",
        paragraph_ref="VdTÜV 751 Annex I § I.5.2.3 — Zu 15.1/2 HA",
        stvzo_paragraph="§ 36 StVZO i.V.m. VdTÜV-Merkblatt 751",
        regulatory_references=[
            "VdTÜV-Merkblatt 751, Annex I, § I.5.2.3: Tragfähigkeitsindex",
            "§ 36 StVZO: Bereifung und Laufflächen",
            "EU-Richtlinie 92/23/EWG — Tragfähigkeitsindex-Tabelle",
        ],
        explanation=(
            "HA-Reifen 265/30 R20 89Y: Tragfähigkeitsindex 89 = 580 kg/Reifen, "
            "max. 1.160 kg/Achse. Das Dokument nennt gleichzeitig zul. Achslast HA "
            "1.250 kg. Die Bereifung ist für die dokumentierte Achslast unterdimensioniert."
        ),
        remediation=(
            "HA-Reifen mit Tragfähigkeitsindex ≥ 92 wählen (92 = 630 kg/Reifen → "
            "1.260 kg/Achse). Reifengröße 265/30 R20 beibehalten, aber LI auf 92Y "
            "oder höher. Im Gutachten und Fahrzeugschein (Feld 15.2) korrekt eintragen."
        ),
        anchors=[
            ParagraphAnchor(
                "Zu 15.1/2 — HA",
                ["89Y", "Achslast HA 1.250", "zul. Achslast HA"],
                page_hint=1,
                merge_phrases=["Zu 15.1/2"],
            ),
        ],
    ),
    "L2-751-I.5.2.3": RuleKnowledge(
        rule_id="L2-751-I.5.2.3",
        paragraph_ref="VdTÜV 751 Annex I § I.5.2.3 — Zu 15.1/2 VA",
        stvzo_paragraph="§ 36 StVZO i.V.m. VdTÜV-Merkblatt 751",
        regulatory_references=[
            "VdTÜV-Merkblatt 751, Annex I, § I.5.2.3",
            "§ 36 StVZO: Bereifung",
        ],
        explanation=(
            "VA-Reifen 235/30 R20 88Y — Tragfähigkeitsindex 88 (= 560 kg/Reifen). "
            "Für den BMW M4 an der Grenze; in Kombination mit fehlendem TGA kritisch."
        ),
        remediation=(
            "VA-Reifen mit LI ≥ 91 prüfen und ggf. auf 91Y oder 94Y aufrüsten. "
            "Tragfähigkeit gegen Hersteller-Achslastdaten verifizieren."
        ),
        anchors=[
            ParagraphAnchor(
                "Zu 15.1/2 — VA",
                ["88Y", "235/30 R20"],
                page_hint=1,
            ),
        ],
    ),
    "L3-CHECK-PARADOX": RuleKnowledge(
        rule_id="L3-CHECK-PARADOX",
        paragraph_ref="§ 36 Prüfbericht — Checkliste",
        stvzo_paragraph="§ 36 StVZO — Prüfbericht Bereifung",
        regulatory_references=[
            "EG-DOK 4.8.0 § 36 Prüfbericht",
            "VdTÜV-Merkblatt 751: Nachweispflicht",
        ],
        explanation=(
            "§36-Prüfbericht: „Nachweis vorhanden: nein“ und „Eigenprüfung: nein“, "
            "aber „notwendige Prüfungen nachgewiesen: ja“ und „Radtraglast ausreichend“. "
            "Ohne Nachweis ist die positive Schlussbestätigung nicht valide."
        ),
        remediation=(
            "Prüfbericht korrigieren: Entweder Nachweis (TGA/ABE) beifügen und "
            "Checkliste auf „ja“ setzen, oder Schlussbestätigung verweigern. "
            "Radtraglast-Bemerkung nur bei belegtem LI zulässig."
        ),
        anchors=[
            ParagraphAnchor(
                "§ 36 Checkliste",
                ["Nachweis (System", "Nachweis durch Eigenprüfung"],
                page_hint=4,
            ),
            ParagraphAnchor(
                "§ 36 Bemerkungen",
                ["Radtraglast ausreichend"],
                page_hint=4,
            ),
        ],
    ),
    "L3-SPC-HUB": RuleKnowledge(
        rule_id="L3-SPC-HUB",
        paragraph_ref="TÜV-Praxis — Spacer-Spezifikation",
        stvzo_paragraph="§ 36 StVZO / VdTÜV 751 Annex I",
        regulatory_references=["VdTÜV-Merkblatt 751, Annex I § I.5.1.8", "TÜV-Praxis Spacer"],
        explanation="Spacer sind nicht nabenzentrierend — in der TÜV-Praxis regelmäßige Ablehnung.",
        remediation="Nabenzentrierende Spacer verwenden oder Spacer entfernen.",
        anchors=[ParagraphAnchor("Spacer", ["nicht nabenzentrierend", "Spacer"])],
    ),
    "L3-ESP-040": RuleKnowledge(
        rule_id="L3-ESP-040",
        paragraph_ref="TÜV-Praxis — ESP-Sensor",
        stvzo_paragraph="§ 38 StVZO / TÜV-Praxis",
        regulatory_references=["TÜV-Praxis ESP-Drop-Regel (40 mm)"],
        explanation="Tieferlegung überschreitet 40 mm ESP-Schwelle.",
        remediation="ESP-Sensor neu kalibrieren oder Tieferlegung auf ≤ 40 mm reduzieren.",
        anchors=[ParagraphAnchor("Tieferlegung", ["Tieferlegung", "ESP"])],
    ),
}
