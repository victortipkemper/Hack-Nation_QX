"""
Regulatory reference URLs — linked in explanations (not used in verdict logic).
"""

import re
from dataclasses import dataclass


@dataclass
class RegulatoryLink:
    label: str
    url: str


STVZO_BASE = "https://www.gesetze-im-internet.de/stvzo_2012"

STVZO_PARAGRAPHS: dict[str, str] = {
    "19": f"{STVZO_BASE}/__19.html",
    "21": f"{STVZO_BASE}/__21.html",
    "30c": f"{STVZO_BASE}/__30c.html",
    "36": f"{STVZO_BASE}/__36.html",
    "36a": f"{STVZO_BASE}/__36a.html",
    "41": f"{STVZO_BASE}/__41.html",
    "57": f"{STVZO_BASE}/__57.html",
}

OTHER_LINKS: dict[str, RegulatoryLink] = {
    "mbl751": RegulatoryLink(
        label="VdTÜV Merkblatt 751 — Rad/Reifen-Änderungen",
        url="https://www.vdtuev.de/de/dienstleistungen/fahrzeugtechnik/merkblaetter",
    ),
    "r39": RegulatoryLink(
        label="UN Regulation No. 39 — Speedometer / Odometer",
        url="https://unece.org/transport/documents/2021/04/standards/addendum-regulation-no-39",
    ),
    "r10": RegulatoryLink(
        label="UN Regulation No. 10 — EMC",
        url="https://unece.org/transport/documents/2021/04/standards/regulation-no-10",
    ),
    "r100": RegulatoryLink(
        label="UN Regulation No. 100 — Electric Power Train",
        url="https://unece.org/transport/documents/2021/04/standards/regulation-no-100",
    ),
    "r30": RegulatoryLink(
        label="UN Regulation No. 30 — Tyres (passenger cars)",
        url="https://unece.org/transport/documents/2021/04/standards/regulation-no-30",
    ),
}


def links_for_citation(citation: str, references: list[str] | None = None) -> list[RegulatoryLink]:
    """Resolve clickable links from citation text and reference strings."""
    seen: set[str] = set()
    links: list[RegulatoryLink] = []
    blob = citation + " " + " ".join(references or [])

    for para, url in STVZO_PARAGRAPHS.items():
        patterns = [
            rf"§\s*{re.escape(para)}\b",
            rf"§\s*{re.escape(para)}\s",
            rf"StVZO.*{re.escape(para)}",
        ]
        if any(re.search(p, blob, re.I) for p in patterns):
            key = f"stvzo-{para}"
            if key not in seen:
                seen.add(key)
                links.append(
                    RegulatoryLink(
                        label=f"§ {para} StVZO (Gesetzestext)",
                        url=url,
                    )
                )

    keyword_map = [
        (r"Merkblatt\s*751|751\s*I\.5", "mbl751"),
        (r"\bR39\b|UN\s*R39|Tachopr", "r39"),
        (r"\bR10\b|UN\s*R10", "r10"),
        (r"\bR100\b|UN\s*R100", "r100"),
        (r"\bR30\b|UN\s*R30", "r30"),
    ]
    for pattern, key in keyword_map:
        if re.search(pattern, blob, re.I) and key not in seen:
            seen.add(key)
            links.append(OTHER_LINKS[key])

    return links
