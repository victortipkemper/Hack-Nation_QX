"use client";

import { useMemo } from "react";
import {
  ArrowLeft,
  BookOpen,
  Bot,
  ExternalLink,
  FileText,
  Highlighter,
  Wrench,
} from "lucide-react";
import { ExpertNachpruefungPanel } from "./ExpertNachpruefung";
import { PdfHijackViewer } from "./PdfHijackViewer";
import type { RuleAnnotation, GutachtenDocument } from "@/lib/documentAnnotations";
import type { RuleResult } from "@/types";

interface DocumentViewerProps {
  document: GutachtenDocument;
  rule: RuleResult;
  annotation: RuleAnnotation;
  uploadId?: string | null;
  onClose: () => void;
}

export function DocumentViewer({
  document: doc,
  rule,
  annotation,
  uploadId,
  onClose,
}: DocumentViewerProps) {
  const activeRegions = annotation.regions ?? [];
  const activePage = useMemo(() => {
    if (activeRegions.length > 0) {
      return activeRegions[0].page;
    }
    const section = doc.sections.find(
      (s) => s.id === annotation.highlight_section_id
    );
    return section?.page ?? 1;
  }, [activeRegions, doc.sections, annotation.highlight_section_id]);

  const hasPageImages = doc.pageImages && doc.pageImages.length > 0;
  const links = annotation.regulatory_links ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onClose}
          className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-brand-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Zurück zur Checkliste
        </button>
        <div className="flex items-center gap-2">
          {doc.pdfUrl && (
            <a
              href={doc.pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline"
            >
              <ExternalLink className="w-3 h-3" />
              Original-PDF
            </a>
          )}
          <span className="text-xs text-slate-400 font-mono truncate max-w-[160px]">
            {doc.filename}
          </span>
        </div>
      </div>

      {annotation.paragraph_ref && (
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg px-3 py-2 border border-slate-200">
          <BookOpen className="w-3.5 h-3.5 text-brand-600" />
          Paragraph: {annotation.paragraph_ref}
        </div>
      )}

      <div className="bg-gradient-to-r from-red-50 to-amber-50 border border-red-200 rounded-xl p-4 space-y-3">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-red-100 rounded-lg shrink-0">
            <Bot className="w-5 h-5 text-red-700" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-red-800 uppercase tracking-wide flex items-center gap-1.5">
              <Highlighter className="w-3.5 h-3.5" />
              Erläuterung — {rule.rule_id}
            </p>
            <p className="text-sm text-red-950 mt-1 leading-relaxed whitespace-pre-line">
              {annotation.ai_explanation}
            </p>
          </div>
        </div>

        {(links.length > 0 || (annotation.regulatory_references?.length ?? 0) > 0) && (
          <div className="pl-11 space-y-2">
            <p className="text-xs font-semibold text-red-800/80 uppercase">
              Regelwerke & Gesetzestexte
            </p>
            {links.length > 0 ? (
              <ul className="space-y-1">
                {links.map((lnk) => (
                  <li key={lnk.url}>
                    <a
                      href={lnk.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-brand-700 hover:text-brand-900 hover:underline font-medium"
                    >
                      <ExternalLink className="w-3 h-3 shrink-0" />
                      {lnk.label}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <ul className="text-xs text-red-900/80 space-y-0.5">
                {annotation.regulatory_references?.map((ref) => (
                  <li key={ref} className="flex items-start gap-1.5">
                    <span className="text-red-400 mt-0.5">•</span>
                    {ref}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {annotation.remediation_hint && (
          <div className="pl-11 pt-2 border-t border-red-200/60">
            <p className="text-xs font-semibold text-emerald-800 uppercase flex items-center gap-1.5">
              <Wrench className="w-3.5 h-3.5" />
              Korrekturhinweis
            </p>
            <p className="text-sm text-emerald-900 mt-1 leading-relaxed">
              {annotation.remediation_hint}
            </p>
          </div>
        )}
      </div>

      {uploadId && rule.flagged && rule.rule_id !== "—" && (
        <ExpertNachpruefungPanel
          uploadId={uploadId}
          checkId={rule.rule_id}
          checkName={rule.rule_name}
        />
      )}

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 bg-slate-800 text-white">
          <FileText className="w-4 h-4" />
          <div>
            <p className="text-sm font-semibold">
              Gutachten — Paragraph markiert
            </p>
            <p className="text-xs text-slate-300">
              {doc.issued_by} · Seite {activePage}
              {activeRegions.length > 1 &&
                ` · ${activeRegions.length} Markierungen`}
            </p>
          </div>
        </div>

        <div className="p-4 bg-slate-100 max-h-[min(640px,calc(100vh-360px))] overflow-y-auto scrollbar-thin">
          {hasPageImages ? (
            <PdfHijackViewer
              pageImages={doc.pageImages!}
              activeRegions={activeRegions}
              activePage={activePage}
            />
          ) : (
            <p className="text-sm text-slate-500 p-4">
              Keine Seitenbilder verfügbar.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
