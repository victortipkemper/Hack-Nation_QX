# Autocomply

RegTech-Plattform für Einzelabnahme (Fahrzeug-Gutachten).

## Schnellstart (Windows)

**Doppelklick auf `start.bat`** im Ordner `autocomply`.

Das öffnet zwei Fenster (API + Frontend) und den Browser.

## Manuell starten

### Terminal 1 — API
```powershell
cd C:\Users\morit\autocomply\api
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8010
```

### Terminal 2 — Frontend
```powershell
cd C:\Users\morit\autocomply\frontend
npm install
npm run dev
```

### Browser öffnen
**http://localhost:3000**

## Nutzung

1. **PDF oder ZIP hochladen** — einzelnes Gutachten-PDF oder Dokumentenpaket (Protokoll + Anlagen + Aufstellung)
2. **White-Box-Checkliste** (rechts) — jeder Prüfschritt mit Anwendbarkeit, Nachweis, Korrekturhinweis
3. **Beanstandete Prüfung anklicken** — PDF-Markierung + verlinkte Gesetzestexte
4. Tabs: **White-Box** | **Gutachten-Daten** | **PDF-Dokument**

## Deterministische Checkliste

- Feste Prüfliste nach VdTÜV Merkblatt 751 I.5.1.x + StVZO (kein Hardcoding pro Datei-ID)
- Anwendbarkeit wird aus extrahierten Dokumentmerkmalen abgeleitet
- Korrekturhinweise basieren auf GREEN-Exemplar-Mustern (`api/data/exemplar_patterns.py`)
- Golden-Corpus-Evaluation: `POST /api/evaluate-corpus` (nur zur Bewertung, nicht in der Prüflogik)

## Probleme?

| Problem | Lösung |
|---------|--------|
| Seite lädt nicht | `start.bat` erneut ausführen |
| Port 3000 belegt | http://localhost:3001 probieren |
| API-Fehler | Prüfen ob Terminal 1 läuft (Port 8010) |
| Leere Seite | Hard-Refresh: `Ctrl+Shift+R` |

## API-Dokumentation
http://localhost:8010/docs

## Unstrukturierte Dokumentenpakete (ZIP)

ZIP mit mehreren PDFs (z. B. `Protokoll.pdf`, `Anl.pdf`, `NW_Nat.pdf`):

- **Rollen-Erkennung** — Protokoll, Anlagen/Fotos, nationale Aufstellung
- **Prüfprotokoll** — C1/C3-Abschnitte, Schlussbewertung Ja/Nein
- **Fotonachweise** — Labels (3/4-Ansicht, FIN, Fabrikschild) + Bildinhalt pro Seite
- **FIN-Konsistenz** — gleiche Fahrzeug-ID über alle Dateien
