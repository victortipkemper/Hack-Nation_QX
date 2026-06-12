"""
Prüf- und Korrekturmuster — aus Gutachten-Korpus intern gelernt.
Nur verification + remediation an die UI; keine Verweise auf andere Dokumente.
Verdict-Logik nutzt diese Daten nicht.
"""

EXEMPLAR_PATTERNS: dict[str, dict] = {
    "load_index": {
        "pattern": "LI/SR explizit geprüft; HA-LI ≥ halbe zulässige Achslast pro Rad.",
        "verification": (
            "Im Feld Zu 15.1/2 oder Reifentabelle LI je Achse ablesen. "
            "Zulässige Achslast HA aus Fahrzeugdaten entnehmen, durch 2 teilen — "
            "Tragfähigkeit pro Rad (LI→kg) muss diesen Wert erreichen oder überschreiten. "
            "Berechnung im Prüfbericht ausweisen."
        ),
        "remediation": (
            "Reifen mit höherem LI wählen oder Achslast-Berechnung mit Zahlenwert "
            "im Prüfbericht dokumentieren (LI, kg/Rad, zul. Achslast)."
        ),
    },
    "speed_rating": {
        "pattern": "Geschwindigkeitsindex ≥ Vmax oder Winterreifen-Regelung dokumentiert.",
        "verification": (
            "SR aus Reifenangabe (z. B. 97H) in km/h umrechnen und mit dokumentierter "
            "Vmax des Fahrzeugs vergleichen. Bei Winterbereifung: Vmax-Begrenzung "
            "oder entsprechende Regelung im Gutachten prüfen."
        ),
        "remediation": (
            "Reifen mit ausreichendem SR wählen oder Vmax-Begrenzung / "
            "Winterreifen-Hinweis im Gutachten vermerken."
        ),
    },
    "r39_circumference": {
        "pattern": "Bei Δ > 5%: R39/§57 dokumentiert; bei Δ ≤ 5%: begründete N/A zulässig.",
        "verification": (
            "Abrollumfangabweichung aus Reifendaten berechnen oder im Dokument suchen. "
            "Liegt Δ über 5 %, muss Tachoprüfung nach UN R39 / §57 durchgeführt und "
            "im Gutachten belegt sein. Unter 5 % darf §57 als N/A stehen, sofern begründet."
        ),
        "remediation": (
            "Tachoprüfung durchführen und Ergebnis dokumentieren — oder bei Δ ≤ 5 % "
            "die Nicht-Anwendbarkeit von §57 nachvollziehbar begründen."
        ),
    },
    "brake_section_41": {
        "pattern": "Bei Bremsänderung: §41 geprüft, nicht pauschal N/A.",
        "verification": (
            "In der Aufstellung prüfen, ob §41 als geprüft oder vorschriftsmäßig "
            "eingetragen ist, wenn Bremskomponenten geändert wurden. "
            "Prüfbericht auf Wirkungsprüfung / thermische Belastbarkeit prüfen."
        ),
        "remediation": (
            "§41 in der Aufstellung auf „Vorschriftsmäßig“ setzen und "
            "Bremsprüfung (Scheiben, Beläge, Wirkungsprüfung) dokumentieren."
        ),
    },
    "wheel_cover_30c_36a": {
        "pattern": "Bei Spurverbreiterung: §30c und §36a geprüft, Radabdeckung belegt.",
        "verification": (
            "Bei Spurplatten oder Spurverbreiterung in Aufstellung §30c und §36a "
            "auf N/A prüfen — beide dürfen nicht ohne Prüfung N/A sein. "
            "Fotonachweis oder Messprotokoll Radabdeckung/Außenkante einbeziehen."
        ),
        "remediation": (
            "Radabdeckung und Außenkanten nach §30c/§36a prüfen, in Aufstellung "
            "bewerten und mit Foto oder Messwert belegen."
        ),
    },
    "tga_scope": {
        "pattern": "TGA-Verwendungsbereich passt zu FIN/Baureihe des Fahrzeugs.",
        "verification": (
            "Fahrzeugtyp/FIN/Baureihe aus Gutachten mit dem Verwendungsbereich "
            "des referenzierten Teilegutachtens abgleichen. "
            "Typcodes und Baureihen müssen übereinstimmen oder der TGA muss "
            "das konkrete Fahrzeug explizit abdecken."
        ),
        "remediation": (
            "Passendes Teilegutachten für die exakte Baureihe/FIN verwenden "
            "oder Verwendungsbereich im Gutachten korrekt eingrenzen."
        ),
    },
    "tga_auflage": {
        "pattern": "TGA-Auflagen (z. B. A3 Nachziehen) in Gutachten übernommen.",
        "verification": (
            "Auflagen aus dem Teilegutachten (A1, A2, A3 …) mit dem "
            "Auflagen-Abschnitt im Gutachten vergleichen. "
            "Jede relevante TGA-Auflage muss im Gutachten und ggf. Fahrzeugschein stehen."
        ),
        "remediation": (
            "Fehlende TGA-Auflagen (z. B. A3 Nachziehen nach 50 km) "
            "in Gutachten-Auflagen und Fahrzeugschein übernehmen."
        ),
    },
    "tga_documentation": {
        "pattern": "ABE oder TGA-Nummer im Gutachten referenziert.",
        "verification": (
            "Prüfen, ob im Gutachten eine gültige ABE- oder Teilegutachten-Nummer "
            "im Feld Zu 15.1/2 oder Nachweis-Abschnitt genannt wird. "
            "Bei §19(3)-Route ist ein Typgenehmigungsnachweis Pflicht."
        ),
        "remediation": (
            "Gültiges TGA oder ABE beifügen und im Gutachten unter Zu 15.1/2 "
            "oder Nachweis referenzieren."
        ),
    },
    "pruefbericht_nachweis": {
        "pattern": "Prüfbericht-Checkliste konsistent mit vorhandenem Nachweis.",
        "verification": (
            "Im §36-Prüfbericht Felder „Nachweis vorhanden“ und „Ergebnisse erreicht“ "
            "mit dem tatsächlich beigefügten TGA/ABE abgleichen. "
            "„Nein“ bei Nachweis und „Ja“ bei Ergebnis ist ein Widerspruch."
        ),
        "remediation": (
            "Prüfbericht-Checkliste korrigieren: Nachweis auf „ja“ wenn TGA/ABE liegt, "
            "oder fehlenden Nachweis beifügen."
        ),
    },
    "min_rim_tga": {
        "pattern": "Felgendurchmesser ≥ TGA-Mindestmaß.",
        "verification": (
            "Mindestfelgendurchmesser aus TGA-Auflagen lesen und mit der "
            "im Gutachten dokumentierten Felge (Zu 15.1/2) vergleichen. "
            "Dokumentierte Felge darf nicht unter dem TGA-Minimum liegen."
        ),
        "remediation": (
            "Felge mit ausreichendem Durchmesser verwenden oder TGA mit "
            "passendem Mindestmaß wählen — Maß im Gutachten ausweisen."
        ),
    },
    "internal_consistency": {
        "pattern": "Aufstellung, Prüfbericht und Schlussbescheinigung widerspruchsfrei.",
        "verification": (
            "Schlussbescheinigung (positiv/negativ) mit Aufstellung, "
            "Begründung BE erloschen und Prüfbericht-Ergebnissen abgleichen. "
            "Prozedurale BE-Erlöschen-Begründung bei §21 ist kein Widerspruch."
        ),
        "remediation": (
            "Widersprüche auflösen: keine positive Schlussbescheinigung bei "
            "dokumentierten Verstößen; §-Bewertungen zur Begründung passend setzen."
        ),
    },
    "bundle_docs": {
        "pattern": "GA-Paket: Gutachten/Protokoll + Foto-Anlagen (+ ggf. Aufstellung).",
        "verification": (
            "ZIP-Inhalt prüfen: mindestens Gutachten oder Prüfprotokoll, "
            "Foto-Anhang (Anl) mit beschrifteten Nachweisen, optional Aufstellung. "
            "Alle Dateien müssen dieselbe GA-Nr. und FIN tragen."
        ),
        "remediation": (
            "Vollständiges Paket zusammenstellen: Gutachten oder C1/C3-Protokoll, "
            "Foto-Anlagen (3/4-Ansicht, FIN, Fabrikschild), Aufstellung falls vorhanden."
        ),
    },
    "bundle_protocol": {
        "pattern": "Protokollabschnitte mit Schluss „Ja: T“ abgeschlossen.",
        "verification": (
            "Jeden Protokollabschnitt (C1, C3, …) auf Schlusszeile prüfen: "
            "„Ja: T“ bedeutet bestanden, „Nein: T“ bedeutet nicht bestanden. "
            "Offene Anforderungsraster vor Schlussbewertung nachvollziehen."
        ),
        "remediation": (
            "Offene Prüfpunkte nacharbeiten oder Schlussbewertung erst setzen, "
            "wenn alle Anforderungen erfüllt und dokumentiert sind."
        ),
    },
    "bundle_photos": {
        "pattern": "Foto-Anhang: beschriftete Seiten enthalten Bild/Scan.",
        "verification": (
            "Anlagen-PDF Seite für Seite: unter Labels wie 3/4-Ansicht vorn/hinten, "
            "FIN, Fabrikschild, ZBI muss ein Foto- oder Scan-Inhalt erkennbar sein — "
            "nicht nur Text aus Aufstellung (z. B. §59 Fabrikschilder)."
        ),
        "remediation": (
            "Fehlende Fotos als eingebettete Bilder oder Scans in den "
            "Foto-Anhang aufnehmen (3/4-Ansichten, FIN-Lesung, Fabrikschild)."
        ),
    },
    "ev_out_of_scope": {
        "pattern": "BEV: R10/R100 Out-of-Scope vermerkt, relevante Prüfungen dokumentiert.",
        "verification": (
            "Bei Elektrofahrzeugen prüfen, ob R10/R100 als nicht anwendbar "
            "gekennzeichnet sind und stattdessen einschlägige Prüfungen "
            "(z. B. R79 Lenkanlage) im Protokoll vorliegen."
        ),
        "remediation": (
            "Out-of-Scope-Vermerk für R10/R100 setzen und einschlägige "
            "EU-Verordnungen/Prüfprotokolle dokumentieren."
        ),
    },
}
