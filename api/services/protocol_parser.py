"""Parse TÜV Prüfprotokolle (C1/C3 …) from unstructured bundle PDFs."""

import re
from dataclasses import dataclass, field


@dataclass
class ProtocolSection:
    section_id: str
    title: str
    final_passed: bool | None = None
    final_reason: str = ""
    fulfilled_markers: int = 0
    open_markers: int = 0


@dataclass
class ProtocolAnalysis:
    gutachten_nr: str = ""
    vin: str = ""
    sections: list[ProtocolSection] = field(default_factory=list)
    all_passed: bool = True
    summary: str = ""


_SECTION_HEADER = re.compile(
    r"(C\d+)\s+(?:Prüfbericht zu\s+(.+?)|(.+?))(?=\nAllgemeine Daten|\nZu GA)",
    re.I | re.S,
)
_GA_NR = re.compile(r"(?:GA[- ]?Nr\.?|Zu GA Nr\.?)\s*:?\s*([A-Z0-9-]+)", re.I)
_VIN = re.compile(r"(?:FIN|Fahrzeug-Ident\.?-Nr\.?)\s*:?\s*([A-Z0-9]{17})", re.I)
_FINAL_JA = re.compile(
    r"(?:Die\s+)?(?:Anforderungen|entsprechenden\s+Anforderungen).*?"
    r"(?:bestanden|erfüllt).*?\n\s*Ja:\s*(T|£|X)\s*Nein:\s*(T|£|X)",
    re.I | re.S,
)
_SIMPLE_FINAL = re.compile(r"Ja:\s*(T|£)\s*Nein:\s*(T|£)", re.I)


def _count_markers(block: str) -> tuple[int, int]:
    """Count T (fulfilled) vs £ (open) column markers in protocol grids."""
    fulfilled = len(re.findall(r"(?:^|\n)\s*T\s*(?:£|\n)", block))
    open_marks = block.count("£")
    return fulfilled, open_marks


def _parse_final(block: str) -> tuple[bool | None, str]:
    m = _FINAL_JA.search(block) or _SIMPLE_FINAL.search(block)
    if not m:
        if re.search(r"nicht\s+bestanden|nicht\s+erfüllt", block, re.I):
            return False, "Explizit nicht bestanden/erfüllt."
        return None, "Kein Schluss-Ja/Nein im Protokollabschnitt."

    ja_mark, nein_mark = m.group(1).upper(), m.group(2).upper()
    if ja_mark == "T" and nein_mark != "T":
        return True, "Protokoll-Schluss: Ja markiert (T)."
    if nein_mark == "T":
        return False, "Protokoll-Schluss: Nein markiert (T)."
    return False, "Protokoll-Schluss unklar (kein Ja:T)."


def parse_protocol(text: str) -> ProtocolAnalysis:
    analysis = ProtocolAnalysis()
    ga = _GA_NR.search(text)
    if ga:
        analysis.gutachten_nr = ga.group(1).strip()
    vin = _VIN.search(text)
    if vin:
        analysis.vin = vin.group(1).strip()

    parts = re.split(r"(?=C\d+\s+(?:Prüfbericht zu|Notfall-|Lenk))", text, flags=re.I)
    for part in parts:
        header = _SECTION_HEADER.search(part)
        if not header:
            m2 = re.match(r"(C\d+)\s+(.+)", part.strip())
            if not m2:
                continue
            sec_id = m2.group(1).upper()
            title = re.sub(r"\s+", " ", m2.group(2).strip())[:80]
        else:
            sec_id = header.group(1).upper()
            title = re.sub(
                r"\s+",
                " ",
                (header.group(2) or header.group(3) or "").strip(),
            )[:80]
        passed, reason = _parse_final(part)
        fulfilled, open_m = _count_markers(part)
        section = ProtocolSection(
            section_id=sec_id,
            title=title,
            final_passed=passed,
            final_reason=reason,
            fulfilled_markers=fulfilled,
            open_markers=open_m,
        )
        analysis.sections.append(section)
        if passed is False:
            analysis.all_passed = False

    if not analysis.sections:
        passed, reason = _parse_final(text)
        if passed is not None:
            analysis.sections.append(
                ProtocolSection(
                    section_id="PROTO",
                    title="Prüfprotokoll",
                    final_passed=passed,
                    final_reason=reason,
                )
            )
            analysis.all_passed = passed

    if analysis.sections:
        statuses = [s.final_passed for s in analysis.sections if s.final_passed is not None]
        if statuses:
            analysis.all_passed = all(statuses)
        ids = ", ".join(f"{s.section_id}={'OK' if s.final_passed else 'FAIL' if s.final_passed is False else '?'}" for s in analysis.sections)
        analysis.summary = f"{len(analysis.sections)} Protokollabschnitt(e): {ids}"
    else:
        analysis.all_passed = False
        analysis.summary = "Kein Prüfprotokoll (C1/C3) erkannt."

    return analysis
