import type { GutachtenDocument } from "@/lib/documentAnnotations";
import type { UploadedDocument } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export function uploadedDocumentToGutachtenDocument(
  doc: UploadedDocument,
  gutachtenId: string
): GutachtenDocument {
  return {
    gutachten_id: gutachtenId,
    filename: doc.filename,
    pdfUrl: `${API_BASE}${doc.pdf_url}`,
    pageImages: doc.page_urls.map((url) => `${API_BASE}${url}`),
    issued_by: "Upload",
    issue_date: new Date().toISOString().slice(0, 10),
    sections: doc.sections.map((s) => ({
      id: s.id,
      label: s.label,
      content: s.content,
      page: s.page ?? undefined,
    })),
    annotations: doc.annotations.map((a) => ({
      rule_id: a.rule_id,
      paragraph_ref: a.paragraph_ref,
      highlight_section_id: a.highlight_section_id,
      highlight_text: a.highlight_text,
      ai_explanation: a.ai_explanation,
      regulatory_references: a.regulatory_references,
      regulatory_links: a.regulatory_links,
      remediation_hint: a.remediation_hint,
      regions: a.regions?.map((r) => ({
        page: r.page,
        top: r.top,
        left: r.left,
        width: r.width,
        height: r.height,
        label: r.label ?? undefined,
      })),
    })),
  };
}
