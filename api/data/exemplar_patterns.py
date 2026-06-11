"""
Exemplar patterns from GREEN reference cases — used for remediation hints only.
NOT used to hardcode verdicts per file.
"""

EXEMPLAR_PATTERNS: dict[str, dict] = {
    "load_index": {
        "reference": "Gut-01 BMW 320i E90 (1106 TGA Referenz)",
        "pattern": "LI/SR explizit geprüft und dokumentiert; HA-LI ≥ berechnete Mindestanforderung aus Achslast.",
        "remediation": "HA-Reifen mit ausreichendem Tragfähigkeitsindex wählen (LI ≥ 92 bei 1.250 kg Achslast). Wie in Referenzfall 1106: konkrete LI-Werte und Achslast-Berechnung im Prüfbericht ausweisen.",
    },
    "speed_rating": {
        "reference": "Gut-04 Audi A4 B9 (ABE)",
        "pattern": "Geschwindigkeitsindex ≥ Vmax oder dokumentierte Winterreifen-Regelung.",
        "remediation": "SR auf mindestens Vmax-Stufe erhöhen (z. B. W/Y statt H bei Vmax 250) oder Vmax-Begrenzung im Gutachten vermerken — wie bei ABE-Fällen 1101–1104.",
    },
    "r39_circumference": {
        "reference": "Gut-03 Sprinter (YELLOW Demo) vs. Gut-01 (GREEN, Δ 1.1%)",
        "pattern": "Bei Abrollumfangabweichung > 5%: §57/R39 Tachoprüfung durchführen und dokumentieren.",
        "remediation": "Tachoprüfung nach UN R39 / §57 StVZO durchführen und im Prüfbericht dokumentieren. Bei Δ ≤ 5% (wie Gut-01/Gut-04): R39 als nicht erforderlich begründen.",
    },
    "brake_section_41": {
        "reference": "1112 BMW M140i Bremsanlage (GREEN+AUFL)",
        "pattern": "Bei Bremsänderung: §41 in Aufstellung prüfen, nicht N/A; Prüfbericht §41/Wirkungsprüfung.",
        "remediation": "§41 in Aufstellung auf 'Vorschriftsmäßig' setzen und Bremsscheiben-/Belag-Prüfbericht beifügen — wie Fall 1112/1135 (Corrado Bremsanlage).",
    },
    "wheel_cover_30c_36a": {
        "reference": "1111 Golf Spurverbreiterung (GREEN+AUFL)",
        "pattern": "Bei Spurverbreiterung: §30c und §36a prüfen, Radabdeckung dokumentieren.",
        "remediation": "Radabdeckungs- und Außenkantenprüfung nach §30c/§36a durchführen — wie bei Spurverbreiterungs-Fällen 1111/1138 mit dokumentierter Abdeckungsprüfung.",
    },
    "tga_scope": {
        "reference": "1106 BMW 320i TGA Referenz (GREEN)",
        "pattern": "TGA-Fahrzeugliste muss zum konkreten Fahrzeug (FIN/Baureihe) passen.",
        "remediation": "Fahrzeugspezifisches Teilegutachten für die exakte Baureihe/FIN verwenden — Referenz 1106 zeigt vollständige TGA-Dokumentation für E90.",
    },
    "tga_auflage": {
        "reference": "1111 Golf Spurverbreiterung (GREEN+AUFL)",
        "pattern": "TGA-Auflagen (z. B. A3 Nachziehen nach 50 km) in Änderungsabnahme übernehmen.",
        "remediation": "Alle TGA-Auflagen (A1, A2, A3…) in Gutachten und Fahrzeugschein übertragen — wie Fall 1111 mit dokumentierten Auflagen.",
    },
    "tga_documentation": {
        "reference": "1106/1108 TGA Referenz (GREEN)",
        "pattern": "ABE oder Teilegutachten-Nummer im Gutachten referenziert.",
        "remediation": "Gültiges TGA oder ABE für die Rad-/Reifenkombination beifügen und im Feld Zu 15.1/2 referenzieren.",
    },
    "pruefbericht_nachweis": {
        "reference": "1106 TGA Referenz (GREEN)",
        "pattern": "Prüfbericht: Nachweis vorhanden = ja, wenn TGA/ABE belegt.",
        "remediation": "Checkliste im §36-Prüfbericht korrigieren: Nachweis auf 'ja' setzen wenn TGA/ABE vorliegt, oder Nachweis beifügen.",
    },
    "min_rim_tga": {
        "reference": "1108 Golf GTI TGA (GREEN)",
        "pattern": "Felgendimension ≥ TGA-Mindestanforderung.",
        "remediation": "Felgendurchmesser gemäß TGA-Mindestmaß (z. B. ≥ 18″) verwenden und dokumentieren.",
    },
    "internal_consistency": {
        "reference": "Alle GREEN-Fälle",
        "pattern": "Aufstellung, Prüfbericht und Schlussbescheinigung widerspruchsfrei.",
        "remediation": "Gutachten intern konsistent machen: Wenn BE erloschen → keine positive Schlussbescheinigung; §36-Bewertung muss zu Begründung passen.",
    },
    "ev_out_of_scope": {
        "reference": "Gut-05 Tesla Model 3 (GREEN+EV)",
        "pattern": "Bei BEV: R10/R100 als Out-of-Scope vermerken, R79/R13H dokumentieren.",
        "remediation": "EV-Hinweis nach Vorbild Gut-05: R10/R100 Out-of-Scope-Knoten setzen, relevante Prüfungen (R79) dokumentieren.",
    },
}
