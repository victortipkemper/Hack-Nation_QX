"""
Optional LLM layer for expert Nachprüfung guides.
Verdict stays deterministic — LLM only formats procedural guidance.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _default_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def prepare_nachpruefung_guide(context: dict[str, Any]) -> tuple[str, bool, str | None]:
    """
    Returns (guide_text, llm_used, model_name).
    Falls back to structured template when no API key or on error.
    """
    if not llm_available():
        return template_guide(context), False, None

    model = _default_model()
    system = (
        "Du bist erfahrener TÜV-Sachverständiger für Rad/Reifen-Gutachten. "
        "Erstelle eine präzise Nachprüf-Anleitung auf Deutsch. "
        "Nutze NUR die gelieferten Fakten — erfinde keine Gesetze. "
        "Struktur: 1) Befund 2) Was fehlt/falsch ist 3) Schritt-für-Schritt Nachprüfung "
        "4) Benötigte Unterlagen 5) Abnahmekriterium. "
        "Keine Verweise auf andere Gutachten-IDs. Zitiere Regelwerk (StVZO, Mbl. 751)."
    )
    user = json.dumps(context, ensure_ascii=False, indent=2)

    try:
        text = _call_openai_compatible(system, user, model)
        if text:
            return text.strip(), True, model
    except Exception:
        pass

    return template_guide(context), False, None


def _call_openai_compatible(system: str, user: str, model: str) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def template_guide(context: dict[str, Any]) -> str:
    """Deterministic fallback — no LLM required."""
    lines: list[str] = []
    lines.append(f"## Nachprüf-Anleitung: {context.get('check_name', '')}")
    lines.append(f"**Regelwerk:** {context.get('citation', '')}")
    lines.append(f"**Befund:** {context.get('finding', '')}")
    lines.append("")

    if context.get("merkblatt_excerpt"):
        lines.append("### Merkblatt 751 (Auszug)")
        lines.append(context["merkblatt_excerpt"][:800] + "…")
        lines.append("")

    lines.append("### Standardprüfung (Expertenwissen)")
    for step in context.get("standard_procedure", []):
        lines.append(f"{step.get('order')}. **{step.get('title')}** — {step.get('instruction')}")
        if step.get("acceptance_criteria"):
            lines.append(f"   _Kriterium:_ {step['acceptance_criteria']}")

    lines.append("")
    lines.append("### Nachprüfung bei Beanstandung")
    for step in context.get("nachpruefung_steps", []):
        lines.append(f"{step.get('order')}. **{step.get('title')}** — {step.get('instruction')}")

    if context.get("documentation_checklist"):
        lines.append("")
        lines.append("### Dokumentations-Checkliste")
        for item in context["documentation_checklist"]:
            lines.append(f"- {item}")

    if context.get("practice_notes"):
        lines.append("")
        lines.append("### TÜV-Praxis-Hinweise")
        for note in context["practice_notes"]:
            lines.append(f"- {note}")

    if context.get("learned_remediation"):
        lines.append("")
        lines.append(f"**Aus Lernkorpus:** {context['learned_remediation'][:400]}")

    return "\n".join(lines)
