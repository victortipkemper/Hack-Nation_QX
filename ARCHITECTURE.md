# How the tool works, end to end

## Big picture

The system is a **deterministic white-box audit engine** for German vehicle-modification Gutachten, with a Next.js frontend (`frontend/`) talking to a FastAPI backend (`api/main.py`). The core design principle, stated in several module docstrings, is: **no LLM and no filename/ID logic in the decision path**. Everything that affects the verdict is regex/rule based and therefore reproducible — an LLM is used only for display-data extraction, and learned corpus data only enriches hint texts, never verdicts.

The backend has five layers:

| Layer | Where | Job |
|---|---|---|
| Ingestion | `services/upload_service.py`, `bundle_processor.py` | PDF/ZIP → raw text, page renders |
| Extraction | `services/pdf_parser.py`, `feature_extractor.py`, `llm_extractor.py` | text → `Gutachten` (display) + `DocumentFeatures` (decisions) |
| Rule engine | `engine/checklist_registry.py`, `checklist_engine.py` | features → per-check results → verdict |
| Knowledge overlays | `services/expert_decisions.py`, `learning_engine.py` | human overrides; corpus-learned hints |
| Presentation | `document_annotator.py`, `explanation_service.py`, `pdf_renderer.py` | page images + paragraph-precise annotations for the viewer |

## 1. Upload and parsing

`POST /api/upload` → `process_upload` (`upload_service.py:15`) routes by extension: `.pdf` goes to the single-document pipeline, `.zip` to the bundle pipeline.

**Single PDF** (`process_pdf_upload`, `upload_service.py:27`): the file is stored under `uploads/<uuid>/original.pdf`, then text is extracted page-by-page with PyMuPDF (falling back to pypdf if missing, `pdf_parser.py:38`). From the same text, two *independent* structures are built:

- **`Gutachten`** (`parse_gutachten_from_pdf`, `pdf_parser.py:245`) — the human-facing record: vehicle data, wheel/tire specs (VA/HA from the `Zu 15.1/2` block), GA number, issuing authority, dates. Here is the **only LLM involvement**: `extract_gutachten_with_llm` (`llm_extractor.py:12`) calls OpenAI via `instructor` with a strict "extract only what's literally in the text, else null" prompt, and if it succeeds, its vehicle/modification data *replaces* the regex-parsed version. Every extracted field is then back-verified against the raw text (`_verify_dict`, `pdf_parser.py:223`) producing `field_verifications` — a per-field boolean "this value literally occurs in the document", which guards against LLM hallucination. If no API key is set or the call fails, the regex parse stands. **This object never feeds the rule engine.**

- **`DocumentFeatures`** (`extract_features`, `feature_extractor.py:280`) — the decision input, built purely with regex. This is what determines which rules fire and how they evaluate (next sections).

**ZIP bundle** (`bundle_processor.py:29`): each member file is classified into a role (Gutachten / Prüfprotokoll / Aufstellung / Foto-Anlagen / other) by `bundle_classifier.resolve_role` using filename and content. All texts are concatenated (with `--- filename (role) ---` separators) into one combined text that goes through the *same* `extract_features`. On top, bundle-specific evidence is collected: protocol sections parsed for pass/fail markers (`protocol_parser`), photo annexes checked for actual embedded images per canonical label (3/4-Ansicht, FIN, Fabrikschild — `image_evidence`), and **every 17-character VIN across all files** is collected to test cross-document consistency. All of this lands in `features.bundle` (`BundleEvidence`, `schemas/features.py:27`). A composite PDF is stitched together so the viewer can show the whole bundle as one paginated document. If the route is still unknown for a bundle, it defaults to `"21"` (`bundle_processor.py:306`).

## 2. How it's determined which rules need to be checked

There is **no dynamic rule discovery**. The checklist is a fixed, ordered registry of 18 `CheckDefinition`s (`checklist_registry.py:17`), organized in four levels mirroring the German regulatory hierarchy:

- **Level 1 — StVZO (formal law):** legal route identified, ABE/TGA evidence referenced, internal contradiction
- **Level 2 — VdTÜV Merkblatt 751:** load index, speed index, rolling circumference/R39, brakes, wheel covers §30c/§36a, TGA scope/min-rim/Auflagen
- **Level 3 — TÜV practice:** Aufstellung consistency, Prüfbericht consistency, wheel-load documentation, ESP advisory, plus the four bundle checks
- **Level 4 — Consensus of technical services:** EV out-of-scope note, final-certificate consistency

The engine (`execute_checklist`, `checklist_engine.py:31`) iterates over **all 18 checks in order, every time**. Selection happens per check via its `applicable(features) -> (bool, reason)` predicate — a pure function of `DocumentFeatures`. Examples:

- `L1-ROUTE-001` is *always* applicable ("every Gutachten needs a legal route").
- `L2-751-I.5.1.6` (load index) applies only if `has_wheel_change and load_index_rear is not None` — i.e. the feature extractor found tire/wheel keywords *and* parsed an LI like `91Y` out of the `Zu 15.1/2` block.
- `L2-751-I.5.1.10` (brakes) applies only if `has_brake_change` (regex hits like "Bremsscheiben VA" in section 3 of the document).
- The four `L3-BUNDLE-*` checks apply only when `features.bundle.is_bundle` is true, so they're silently skipped for single PDFs.
- `L1-CONTRA-001` is a special pattern: its applicability condition *is* the defect (`f.internal_contradiction`) — the check only "exists" for documents that simultaneously contain a positive and negative Schlussbescheinigung.

A non-applicable check isn't dropped — it's recorded as a `WhiteBoxStep` with `applicable=False`, `executed=False` and a skip reason (`checklist_engine.py:46-66`). That's deliberate: the UI can show the full checklist with transparent reasoning for *why* each check did or didn't run, and applicable/executed counts come out of the same loop.

So the answer to "how does it know which rules to check" is: **the feature extractor decides**. Each boolean/value in `DocumentFeatures` is a gate. The interesting extraction logic includes:

- **Route detection** (`_detect_route`, `feature_extractor.py:121`): phrases like "Gutachten nach §21" → route `"21"`; "Änderungsabnahme nach §19 Abs. 3" or "Komponentengutachten" → `"19-3"`; otherwise `"unknown"`.
- **Modification detection** (`_detect_modifications`): keyword regexes for wheels (`zu 15.1/2|mischbereifung|räder|reifen|felgen`), brakes, lowering, spacers, track wideners — partly scoped to document section 3 ("Begutachtete …") to avoid false hits.
- **Aufstellung table parsing** (`_parse_aufstellung_sections`, `feature_extractor.py:88`): finds the "Aufstellung der technischen Vorschriften" table, locates §30c/§36/§36a/§41/§57 rows (tolerating broken `§` encodings), and reads the Bewertung in the following lines (`N/A*` vs `Vorschriftsmäßig`). These N/A flags power several cross-checks.
- **Numeric values**: rear axle load ("Achslast HA 1.250 kg", German thousands separator), Vmax, rolling-circumference delta in %, rim diameters, TGA minimum rim size, LI/SI pairs (`91Y`) preferentially from the `Zu 15.1/2` block.

## 3. How the rules are actually checked

Each applicable check runs `evaluate(features) -> (passed, flagged, reason, evidence_key)`. The `reason` string doubles as the evidence shown to the user and as the input for expert-decision fingerprinting. The evaluations fall into three families:

**a) Numeric comparisons against legal limits.** The clearest example is `L2-751-I.5.1.6` (`_eval_load_index`, `checklist_registry.py:423`): the tire load index is converted to kg via the EU LI table (`LI_TO_KG`, `feature_extractor.py:12`, with a linear fallback formula), then compared against **half the permissible rear axle load**: `li_to_kg(91) = 615 kg/Rad vs. 1250/2 = 625 kg` → fail, with the full arithmetic in the evidence string. Similarly `L2-751-I.5.1.4` maps speed index H/V/W/Y/Z → 210–300 km/h and requires `SR ≥ Vmax`, *unless* a Winterreifen/Vmax-Begrenzung clause is documented (that exception is itself a regex on the raw text). `L2-TGA-MIN-RIM` compares documented rim diameter against the TGA minimum.

**b) Conditional-obligation checks ("if X was modified, Y must have been examined").** These cross-reference the modification flags against the Aufstellung N/A flags: brakes changed but §41 marked N/A → flag (`_eval_brake_section`); spacers fitted but *both* §30c and §36a N/A → flag; rolling-circumference delta > 5% but §57 N/A or no Tachoprüfung/R39 mention anywhere → flag (`_eval_r39_circumference`, which also explicitly *passes* the ≤5% case as "N/A zulässig"). `L3-AUFSTELLUNG-001` re-runs all four of these correlations in one consistency check.

**c) Documentary/consistency checks.** `L1-DOC-001` (`_eval_doc_reference`, `checklist_registry.py:413`) is route-dependent: a §21 Vollgutachten passes outright (TGA/ABE not mandatory for Einzelabnahme); §19(3) without any ABE/TGA reference fails; ambiguous cases pass softly. `L3-PRUEFBERICHT-001` catches paradoxes like "Nachweis vorhanden: nein" while a TGA is referenced, or "Nachweis nein / Ergebnisse erreicht ja". The bundle checks verify package completeness, VIN consistency across files, protocol sections all concluded "Ja", and that each photo label actually has an image behind it.

Two checks (`L3-ESP-THRESHOLD`, `L4-EV-OUT-OF-SCOPE`) have `severity="advisory"`: they always "pass" but emit a recommendation, and they're excluded from verdict computation.

## 4. After evaluation: overlays, dedupe, verdict

Per executed step, the engine then (`checklist_engine.py:69-121`):

1. **Attaches hints** via `_remediation(exemplar_key, reason)` — the seed text from `EXEMPLAR_PATTERNS` merged with corpus-learned statistics from the learning engine (the "Aus 19 bestandenen Gutachten…" text).
2. **Applies expert knowledge**: for every error-severity finding, a fingerprint `sha256(check_id + "|" + normalized_evidence)[:16]` is looked up in `expert_knowledge.json` (`expert_decisions.py:31`). An earlier expert **approve** flips the step to passed ("Durch Expertenwissen freigegeben (ek-…)"); a **reject** keeps it flagged but marks it expert-confirmed. Matching is deliberately exact — a decision only generalizes to documents producing the *identical* evidence string, so the same finding in the next upload auto-resolves but nothing broader does. Decisions come in through `POST /api/expert-review` and are append-logged to `expert_decisions.jsonl` for audit.
3. **Dedupes**: if `L3-AUFSTELLUNG-001` flagged and one of the specific L2 checks already flagged the same root cause (mapping in `data/gap_check_mapping.py`), the L3 step is neutralized to avoid a double Beanstandung (`_dedupe_aufstellung`, `checklist_engine.py:150`).
4. **Builds levels**: only executed *error*-severity steps are projected into the four `LevelResult` groups that the frontend shows as the compliance ladder.
5. **Computes the verdict** (`_compute_verdict`, `checklist_engine.py:213`): no error flags → **PASS**; any error flags → **AUDIT_FLAGGED** (the system never auto-fails); flags exist *and every one* has been expert-confirmed as a genuine defect → **FAIL**. So a hard FAIL always requires a human in the loop. Each verdict gets a hashed audit-trail ID.

## 5. Output assembly and the feedback loops

The response bundles the verdict with a viewer-ready document: pages rendered to PNG (`pdf_renderer`), and for every flagged rule a `RuleAnnotation` (`document_annotator.py`) that locates the offending paragraph on the page (percent-based bounding boxes from `pdf_blocks`) with an explanation from `explanation_service` — that's what lets the frontend highlight "this paragraph triggered L2-751-I.5.1.6".

Finally, two persistence loops close the system:

- Every upload is saved as a **training exemplar** (`training_store.py`) and immediately fed to the **learning engine** (`learning_engine.py`), which updates per-check pass/fail counts, anchor phrases and evidence samples used in the hint texts — guidance only, never verdicts.
- The **calibration/corpus tooling** (`/api/evaluate-corpus`, `/api/calibrate`, `corpus_evaluator.py`) runs the whole pipeline over the 50 hackathon PDFs and compares against the Lösungsschlüssel, which is how the regexes and thresholds were tuned (the engine version string `0.3.1-learning` / checklist `1.2.1-bundle-photos` tracks this).

## Summary

The honest characterization: it's an **expert system** — a hand-built, regulation-derived decision table over regex-extracted features — wrapped with LLM-assisted display extraction, human-override memory, and corpus-statistics hints. Its strength is full traceability (every step has applicability reason, evidence, citation); its fragility is the extraction layer, since any applicability gate is only as good as the keyword patterns feeding it (e.g. `has_wheel_change` matches the very common word "Reifen" anywhere in the text, which is why L1-DOC-001 fires on nearly every document).
