"use client";

import { useState, useRef, useEffect } from "react";
import { BookOpen, Info } from "lucide-react";
import type { RuleResult } from "@/types";

interface CitationPopoverProps {
  rule: RuleResult;
  children: React.ReactNode;
}

export function CitationPopover({ rule, children }: CitationPopoverProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        aria-label={`Citation for ${rule.rule_name}`}
      >
        {children}
      </button>

      {open && (
        <div className="absolute z-50 left-0 top-full mt-2 w-80 sm:w-96 animate-in fade-in slide-in-from-top-1">
          <div className="rounded-lg border border-slate-200 bg-white shadow-xl p-4 space-y-3">
            <div className="flex items-start gap-2">
              <BookOpen className="w-4 h-4 text-brand-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Regulatory Citation
                </p>
                <p className="text-sm font-medium text-slate-900 mt-0.5">
                  {rule.rule_id}
                </p>
              </div>
            </div>
            <blockquote className="text-sm text-slate-700 border-l-2 border-brand-400 pl-3 italic leading-relaxed">
              {rule.citation}
            </blockquote>
            <div className="flex items-start gap-2 pt-1 border-t border-slate-100">
              <Info className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
              <p className="text-xs text-slate-600 leading-relaxed">
                {rule.reason}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
