import type { RuleResult } from "@/types";

export interface DocumentSection {
  id: string;
  label: string;
  content: string;
  page?: number;
}

export interface HighlightRegion {
  page: number;
  top: number;
  left: number;
  width: number;
  height: number;
  label?: string;
}

export interface RegulatoryLink {
  label: string;
  url: string;
}

export interface RuleAnnotation {
  rule_id: string;
  paragraph_ref?: string;
  highlight_section_id: string;
  highlight_text: string;
  ai_explanation: string;
  regulatory_references?: string[];
  regulatory_links?: RegulatoryLink[];
  remediation_hint?: string;
  regions?: HighlightRegion[];
}

export interface GutachtenDocument {
  gutachten_id: string;
  filename: string;
  pdfUrl?: string;
  pageImages?: string[];
  issued_by: string;
  issue_date: string;
  sections: DocumentSection[];
  annotations: RuleAnnotation[];
}

export function getAnnotationForRule(
  document: GutachtenDocument,
  rule: RuleResult
): RuleAnnotation | null {
  const found = document.annotations.find((a) => a.rule_id === rule.rule_id);
  if (found) return found;

  if (!rule.flagged && rule.passed) return null;

  return {
    rule_id: rule.rule_id,
    highlight_section_id: document.sections[0]?.id ?? "page_1",
    highlight_text: rule.rule_name,
    ai_explanation: `Die Prüfung „${rule.rule_name}" wurde ${rule.flagged ? "zur Auditierung markiert" : "nicht bestanden"}.\n\n${rule.reason}`,
    regulatory_references: [rule.citation],
    regulatory_links: [],
    remediation_hint: "",
    regions: [],
  };
}

export function isRuleInspectable(rule: RuleResult): boolean {
  return rule.flagged || !rule.passed;
}
