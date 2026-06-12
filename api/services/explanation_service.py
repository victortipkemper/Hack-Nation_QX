"""
Build structured rule explanations with regulatory links and remediation hints.
Verdict remains in checklist engine — this layer only explains findings.
"""

import re

from data.checklist_knowledge import CHECKLIST_KNOWLEDGE, ChecklistRuleKnowledge
from data.regulatory_links import RegulatoryLink, links_for_citation
from schemas.upload import HighlightRegion, RegulatoryLink as RegulatoryLinkSchema, RuleAnnotation
from schemas.verdict import RuleResult
from schemas.whitebox import ChecklistExecution, WhiteBoxStep
from services.pdf_blocks import find_anchor_regions, find_regions_from_evidence


def _step_for_rule(execution: ChecklistExecution | None, rule_id: str) -> WhiteBoxStep | None:
    if not execution:
        return None
    for step in execution.steps:
        if step.check_id == rule_id:
            return step
    return None


def _build_explanation(
    knowledge: ChecklistRuleKnowledge | None,
    rule: RuleResult,
    step: WhiteBoxStep | None,
) -> str:
    parts: list[str] = []
    if knowledge:
        parts.append(knowledge.explanation_template)
    parts.append(f"\n\nPrüfung: {rule.rule_name}")
    parts.append(f"Regelwerk: {rule.citation}")
    if step and step.verification_hint:
        parts.append(f"\n\nSo überprüfbar: {step.verification_hint}")
    if step and step.evidence:
        parts.append(f"\n\nNachweis im Dokument: {step.evidence}")
    parts.append(f"\n\nEngine-Begründung: {rule.reason}")
    return "".join(parts)


def _extract_evidence_phrases(evidence: str) -> list[str]:
    """Pull searchable phrases from checklist evidence text."""
    phrases: list[str] = []
    if not evidence:
        return phrases

    patterns = [
        r"\d{2,3}/\d{2}\s*R\d{2}",
        r"\d{2}[YWHVZ]",
        r"Achslast\s*HA\s*[\d.]+\s*kg",
        r"Abrollumfang[^\d]*[+-]?\d+[,.]?\d*\s*%",
        r"§\s*\d+[a-z]?",
        r"Zu\s*15\.1/2",
        r"kein\s*TGA",
        r"Verwendungsbereich",
        r"Mindest-Felgengröße",
        r"Radtraglast",
        r"Bremsscheib",
        r"Spurverbreiterung",
        r"Spurplatte",
    ]
    for pat in patterns:
        for m in re.finditer(pat, evidence, re.I):
            phrases.append(m.group().strip())

    # Numeric tokens (LI values, percentages)
    for m in re.finditer(r"\b\d{1,3}[,.]?\d*\s*%", evidence):
        phrases.append(m.group().strip())
    for m in re.finditer(r"\bLI\s*\d{2}\b", evidence, re.I):
        phrases.append(m.group().strip())

    return list(dict.fromkeys(phrases))[:8]


def _find_regions(
    pdf_path: str,
    knowledge: ChecklistRuleKnowledge | None,
    step: WhiteBoxStep | None,
) -> list[HighlightRegion]:
    regions: list[HighlightRegion] = []

    if knowledge:
        for anchor in knowledge.anchors:
            found = find_anchor_regions(
                pdf_path,
                anchor.search_phrases,
                page_hint=anchor.page_hint,
                merge_phrases=anchor.merge_phrases,
                label=anchor.paragraph_ref,
            )
            regions.extend(found)

    if step and step.evidence:
        evidence_phrases = _extract_evidence_phrases(step.evidence)
        if evidence_phrases:
            regions.extend(
                find_regions_from_evidence(
                    pdf_path,
                    evidence_phrases,
                    label=step.check_name[:40],
                )
            )

    # Deduplicate by page+position
    seen: set[tuple] = set()
    unique: list[HighlightRegion] = []
    for r in regions:
        key = (r.page, round(r.top, 1), round(r.left, 1))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def build_rule_annotation(
    rule: RuleResult,
    pdf_path: str,
    checklist_execution: ChecklistExecution | None = None,
) -> RuleAnnotation:
    """Create annotation with paragraph-precise regions and linked references."""
    step = _step_for_rule(checklist_execution, rule.rule_id)
    knowledge = CHECKLIST_KNOWLEDGE.get(rule.rule_id)

    remediation_parts: list[str] = []
    if step and step.verification_hint:
        remediation_parts.append(f"So überprüfbar: {step.verification_hint}")
    if step and step.remediation_hint:
        remediation_parts.append(f"Maßnahme: {step.remediation_hint}")
    elif knowledge and knowledge.explanation_template:
        remediation_parts.append(knowledge.explanation_template)
    remediation = "\n\n".join(remediation_parts) or (
        "Manuelle Prüfung durch Sachverständigen erforderlich."
    )

    all_regions = _find_regions(pdf_path, knowledge, step)
    highlight_text = (
        all_regions[0].label
        if all_regions and all_regions[0].label
        else (knowledge.paragraph_ref if knowledge else rule.rule_name)
    )
    section_id = f"page_{all_regions[0].page}" if all_regions else "page_1"

    refs = list(knowledge.extra_references) if knowledge else [rule.citation]
    reg_links: list[RegulatoryLink] = (
        knowledge.regulatory_links(rule.citation) if knowledge else links_for_citation(rule.citation, refs)
    )

    return RuleAnnotation(
        rule_id=rule.rule_id,
        paragraph_ref=knowledge.paragraph_ref if knowledge else rule.rule_name,
        highlight_section_id=section_id,
        highlight_text=highlight_text,
        ai_explanation=_build_explanation(knowledge, rule, step),
        regulatory_references=refs,
        regulatory_links=[
            RegulatoryLinkSchema(label=lnk.label, url=lnk.url) for lnk in reg_links
        ],
        remediation_hint=remediation,
        regions=all_regions,
    )
