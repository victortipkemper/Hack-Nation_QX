import type { GutachtenDocument } from "@/lib/documentAnnotations";

const PAGES = [
  "/documents/bmw-m4/pages/1.png",
  "/documents/bmw-m4/pages/2.png",
  "/documents/bmw-m4/pages/3.png",
  "/documents/bmw-m4/pages/4.png",
];

export const BMW_M4_WIDERSPRUCH_DOCUMENT: GutachtenDocument = {
  gutachten_id: "case-06-bmw-m4-widerspruch",
  filename: "1146_E_21_BMW_M4_LI_Widerspruch.pdf",
  pdfUrl: "/documents/1146_E_21_BMW_M4_LI_Widerspruch.pdf",
  pageImages: PAGES,
  issued_by: "Technische Prüfstelle für den Kraftfahrzeugverkehr – MUSTER",
  issue_date: "2026-05-25",
  sections: [
    {
      id: "page1_tires",
      label: "Seite 1 — Zu 15.1/2 Bereifung",
      page: 1,
      content: `Zu 15.1/2:
VuH genehm. VA 235/30 R20 88Y a. 9,0Jx20 ET 26 / HA 265/30 R20 89Y a. 10,5Jx20 ET 31 (kein TGA); zul.
Achslast HA 1.250 kg* ***`,
    },
    {
      id: "page1_confirmation",
      label: "Seite 1 — § 21 Schlussbescheinigung",
      page: 1,
      content: `Es wird bestätigt, dass das Fahrzeug mit der/den begutachteten Änderung(en) den geltenden Vorschriften entspricht.`,
    },
    {
      id: "page2_be_erloschen",
      label: "Seite 2 — § 21 BE-Erlöschen",
      page: 2,
      content: `Die frühere Betriebserlaubnis des Fahrzeuges ist erloschen, weil für die Rad-/Reifenkombination kein Teilegutachten vorliegt.`,
    },
    {
      id: "page2_section36",
      label: "Seite 2 — § 36 Bewertung",
      page: 2,
      content: `§36 Bereifung und Laufflächen — Bewertung: Vorschriftsmäßig`,
    },
    {
      id: "page4_checklist",
      label: "Seite 4 — § 36 Prüfbericht",
      page: 4,
      content: `Nachweis vorhanden: nein | Nachweis durch Eigenprüfung: nein | Radtraglast ausreichend`,
    },
  ],
  annotations: [
    {
      rule_id: "L2-751-I.5.2.3-HA",
      paragraph_ref: "VdTÜV 751 Annex I § I.5.2.3 — Zu 15.1/2 HA",
      highlight_section_id: "page1_tires",
      highlight_text: "89Y / Achslast HA 1.250 kg",
      ai_explanation:
        "HA-Reifen 265/30 R20 89Y: LI 89 = 580 kg/Reifen → max. 1.160 kg/Achse. Dokument fordert zul. Achslast HA 1.250 kg. Unterdimensioniert.\n\nRegelwerk: § 36 StVZO i.V.m. VdTÜV-Merkblatt 751",
      regulatory_references: [
        "VdTÜV-Merkblatt 751, Annex I, § I.5.2.3",
        "§ 36 StVZO: Bereifung und Laufflächen",
      ],
      remediation_hint:
        "HA-Reifen mit LI ≥ 92 wählen (z. B. 265/30 R20 92Y). Im Gutachten und Fahrzeugschein Feld 15.2 eintragen.",
      regions: [
        { page: 1, top: 31.3, left: 8.5, width: 88, height: 5.5, label: "Zu 15.1/2 — HA 89Y" },
        { page: 1, top: 33.8, left: 8.5, width: 30, height: 2.5, label: "Achslast HA 1.250 kg" },
      ],
    },
    {
      rule_id: "L1-19-002",
      paragraph_ref: "§ 19 Abs. 3 StVZO — Zu 15.1/2",
      highlight_section_id: "page1_tires",
      highlight_text: "(kein TGA)",
      ai_explanation:
        "Feld Zu 15.1/2: „kein TGA“ — kein Teilegutachten für die Rad-/Reifenkombination.\n\nRegelwerk: § 19 Abs. 3 StVZO",
      regulatory_references: [
        "§ 19 Abs. 3 StVZO: Nachweis der Verkehrssicherheit",
        "VdTÜV-Merkblatt 751: Dokumentationspflicht",
      ],
      remediation_hint:
        "Gültiges Teilegutachten oder ABE für die exakte Rad-/Reifenkombination vorlegen.",
      regions: [
        { page: 1, top: 32.4, left: 67, width: 12, height: 2.5, label: "(kein TGA)" },
        { page: 2, top: 21.8, left: 8.5, width: 88, height: 4, label: "kein Teilegutachten" },
      ],
    },
    {
      rule_id: "L1-21-CONTRA",
      paragraph_ref: "§ 21 StVZO — Widerspruch",
      highlight_section_id: "page2_be_erloschen",
      highlight_text: "BE erloschen vs. Vorschriften entspricht",
      ai_explanation:
        "Interner Widerspruch: Seite 1 bestätigt Vorschriftenentsprechung, Seite 2 erklärt BE für erloschen, § 36 dennoch „vorschriftsmäßig“.",
      regulatory_references: [
        "§ 21 StVZO: Gutachten zur Betriebserlaubnis",
        "§ 19 Abs. 2 StVZO",
        "EG-DOK 4.8.0",
      ],
      remediation_hint:
        "Gutachten zurückweisen. Mängel beheben oder widerspruchsfreies Neugutachten ausstellen.",
      regions: [
        { page: 1, top: 47.3, left: 28, width: 45, height: 2.5, label: "§21: entspricht Vorschriften" },
        { page: 2, top: 21.8, left: 8.5, width: 88, height: 4, label: "BE erloschen" },
        { page: 2, top: 30.8, left: 73, width: 18, height: 2.5, label: "§36: Vorschriftsmäßig" },
      ],
    },
    {
      rule_id: "L3-CHECK-PARADOX",
      paragraph_ref: "§ 36 Prüfbericht — Checkliste",
      highlight_section_id: "page4_checklist",
      highlight_text: "Nachweis: nein / Ergebnis: ja",
      ai_explanation:
        "§36-Prüfbericht: Nachweis fehlt, trotzdem „Ergebnisse erreicht: ja“ und „Radtraglast ausreichend“.",
      regulatory_references: ["EG-DOK 4.8.0 § 36 Prüfbericht", "VdTÜV-Merkblatt 751"],
      remediation_hint:
        "TGA/ABE beifügen und Checkliste korrigieren, oder Schlussbestätigung verweigern.",
      regions: [
        { page: 4, top: 22.8, left: 8, width: 88, height: 6, label: "Checkliste: Nachweis nein" },
        { page: 4, top: 34.4, left: 26, width: 50, height: 2.5, label: "Radtraglast ausreichend" },
      ],
    },
  ],
};
