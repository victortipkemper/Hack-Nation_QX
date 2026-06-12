"use client";

import { BookOpen, Brain, ClipboardList, Loader2, RefreshCw } from "lucide-react";
import { useCallback, useState } from "react";
import { fetchExpertNachpruefung, type ExpertNachpruefungResponse } from "@/lib/api";

interface ExpertNachpruefungProps {
  uploadId: string;
  checkId: string;
  checkName: string;
}

export function ExpertNachpruefungPanel({
  uploadId,
  checkId,
  checkName,
}: ExpertNachpruefungProps) {
  const [data, setData] = useState<ExpertNachpruefungResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useLlm, setUseLlm] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchExpertNachpruefung(uploadId, checkId, useLlm);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Laden fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }, [uploadId, checkId, useLlm]);

  const item = data?.items[0];

  return (
    <div className="border border-violet-200 rounded-xl bg-violet-50/40 overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-4 py-3 bg-violet-100/60 border-b border-violet-200">
        <div className="flex items-center gap-2 min-w-0">
          <Brain className="w-4 h-4 text-violet-700 shrink-0" />
          <p className="text-sm font-semibold text-violet-900 truncate">
            Expertenwissen — Nachprüfung
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg bg-violet-700 text-white hover:bg-violet-800 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <RefreshCw className="w-3.5 h-3.5" />
          )}
          Anleitung laden
        </button>
      </div>

      <div className="px-4 py-3 space-y-3 text-xs">
        <p className="text-violet-800/90">
          Für <span className="font-mono font-medium">{checkId}</span> — {checkName}
        </p>

        <label className="flex items-center gap-2 text-violet-700 cursor-pointer">
          <input
            type="checkbox"
            checked={useLlm}
            onChange={(e) => setUseLlm(e.target.checked)}
            className="rounded border-violet-300"
          />
          Mit LLM aufbereiten (falls OPENAI_API_KEY gesetzt)
        </label>

        {error && (
          <p className="text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        {item && (
          <div className="space-y-3">
            {data?.llm_used && (
              <span className="inline-block text-[10px] uppercase tracking-wide bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
                LLM: {data.llm_model}
              </span>
            )}
            {!data?.llm_used && data && (
              <span className="inline-block text-[10px] uppercase tracking-wide bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                Strukturierte Vorlage (ohne LLM)
              </span>
            )}

            {item.merkblatt_excerpt && (
              <div className="p-2.5 bg-white border border-violet-100 rounded-lg">
                <p className="font-semibold text-violet-800 mb-1 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" />
                  Merkblatt 751
                  {item.merkblatt_sections.length > 0 && (
                    <span className="font-mono font-normal text-violet-600">
                      ({item.merkblatt_sections.join(", ")})
                    </span>
                  )}
                </p>
                <p className="text-slate-700 leading-relaxed line-clamp-4">
                  {item.merkblatt_excerpt.slice(0, 400)}…
                </p>
              </div>
            )}

            {item.nachpruefung_steps.length > 0 && (
              <div className="p-2.5 bg-white border border-violet-100 rounded-lg">
                <p className="font-semibold text-violet-800 mb-2 flex items-center gap-1.5">
                  <ClipboardList className="w-3.5 h-3.5" />
                  Schritte zur Nachprüfung
                </p>
                <ol className="space-y-2 list-decimal list-inside text-slate-800">
                  {item.nachpruefung_steps.map((s) => (
                    <li key={s.order} className="leading-relaxed">
                      <span className="font-medium">{s.title}</span> — {s.instruction}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            <div className="p-2.5 bg-white border border-violet-100 rounded-lg prose prose-sm max-w-none">
              <p className="font-semibold text-violet-800 mb-2">Aufbereitete Anleitung</p>
              <div className="text-slate-800 whitespace-pre-wrap leading-relaxed text-xs">
                {item.llm_guide}
              </div>
            </div>
          </div>
        )}

        {!item && !loading && !error && (
          <p className="text-violet-700/80 italic">
            Klicken Sie „Anleitung laden“, um Prüfschritte, Merkblatt-Auszüge und
            Nachprüf-Hinweise aus dem Expertenwissen zu erhalten.
          </p>
        )}
      </div>
    </div>
  );
}
