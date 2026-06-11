"use client";

import { useEffect, useRef } from "react";
import { AlertTriangle } from "lucide-react";
import type { HighlightRegion } from "@/lib/documentAnnotations";

interface PdfHijackViewerProps {
  pageImages: string[];
  activeRegions: HighlightRegion[];
  activePage: number;
}

export function PdfHijackViewer({
  pageImages,
  activeRegions,
  activePage,
}: PdfHijackViewerProps) {
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    const el = pageRefs.current[activePage];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [activePage, activeRegions]);

  return (
    <div className="space-y-6">
      {pageImages.map((src, index) => {
        const pageNum = index + 1;
        const pageRegions = activeRegions.filter((r) => r.page === pageNum);
        const isActivePage = pageNum === activePage;

        return (
          <div
            key={`${src}-${pageNum}`}
            ref={(el) => {
              pageRefs.current[pageNum] = el;
            }}
            className={`relative rounded-lg overflow-hidden shadow-md border-2 transition-all ${
              isActivePage && pageRegions.length > 0
                ? "border-amber-400 ring-4 ring-amber-100"
                : "border-slate-200"
            }`}
          >
            <div className="absolute top-2 left-2 z-20 bg-slate-900/75 text-white text-xs font-mono px-2 py-1 rounded">
              Seite {pageNum} / {pageImages.length}
            </div>

            <div className="relative w-full">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={src}
                alt={`Gutachten Seite ${pageNum}`}
                className="w-full h-auto block"
              />

              {pageRegions.map((region, i) => (
                <div
                  key={`${pageNum}-${i}`}
                  className="absolute z-10 pointer-events-none"
                  style={{
                    top: `${region.top}%`,
                    left: `${region.left}%`,
                    width: `${region.width}%`,
                    height: `${region.height}%`,
                  }}
                >
                  <div className="w-full h-full bg-red-500/30 border-2 border-red-600 rounded-sm shadow-[0_0_16px_rgba(239,68,68,0.6)] ring-1 ring-red-400" />
                  {region.label && (
                    <div className="absolute -top-7 left-0 z-20 flex items-center gap-1 bg-red-600 text-white text-[10px] font-semibold px-2 py-0.5 rounded whitespace-nowrap shadow-lg max-w-[220px] truncate">
                      <AlertTriangle className="w-3 h-3 shrink-0" />
                      {region.label}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
