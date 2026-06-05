"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

/* ─── Types ─── */
interface RepertoryMatch {
  rubric_id?: number;
  rubric?: string;
  weight?: number;
  grade?: number;
}

interface CycleAnalysis {
  remedy_cycle?: string | null;
  segment_matches?: string[];
  segments_matched_count?: number;
  total_segments?: number;
  segment_coverage?: number;
  coverage?: number;
  cycle_sentence?: string | null;
  map_of_hierarchy_phase?: number | null;
  meets_threshold?: boolean;
}

interface RemedyResult {
  abbrev: string;
  name: string;
  score: number;
  match_count: number;
  matches?: RepertoryMatch[];
  cycle_analysis?: CycleAnalysis;
}

interface RepertorizationPanelProps {
  remedies: RemedyResult[];
  phantomCount?: number;
  totalRubrics?: number;
  srpBoost?: number;
  pinnedRemedies?: Set<string>;
  onTogglePin?: (abbrev: string) => void;
  onRemedyClick?: (abbrev: string) => void;
  onRubricClick?: (rubric: string, rubricId?: string) => void;
}

/* ─── Grade color scale ─── */
const GRADE_COLORS = ["#e5e7eb", "#7dd3fc", "#38bdf8", "#0ea5e9", "#0284c7"];

export default function RepertorizationPanel({
  remedies,
  phantomCount = 0,
  totalRubrics = 143408,
  srpBoost = 1,
  pinnedRemedies,
  onTogglePin,
  onRemedyClick,
  onRubricClick,
}: RepertorizationPanelProps) {
  const router = useRouter();
  const [expandedRemedy, setExpandedRemedy] = useState<string | null>(null);

  const maxScore = useMemo(
    () => Math.max(...remedies.map((r) => r.score || 0), 1),
    [remedies]
  );

  const top = remedies[0];

  const confidenceStatement = useMemo(() => {
    if (!top) return "";
    const ca = top.cycle_analysis;
    const cycleText = ca?.meets_threshold
      ? `strong cycle coverage (${Math.round((ca.segment_coverage || 0) * 100)}%)`
      : ca?.segment_coverage && ca.segment_coverage > 0
      ? `partial cycle match (${Math.round(ca.segment_coverage * 100)}%)`
      : "no cycle match";
    const phantomText =
      phantomCount > 0
        ? `${phantomCount} phantom rubric${phantomCount > 1 ? "s" : ""} flagged — review before finalizing.`
        : "No phantom rubrics flagged.";
    const srpText = srpBoost > 1 ? `SRP boost ×${srpBoost.toFixed(1)} applied.` : "";
    return `${top.name} leads with score ${top.score} and ${cycleText}. ${srpText} ${phantomText}`;
  }, [top, phantomCount, srpBoost]);

  const toggleExpand = (abbrev: string) => {
    setExpandedRemedy((prev) => (prev === abbrev ? null : abbrev));
  };

  return (
    <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
      {/* ── HEADER ── */}
      <div className="px-5 pt-5 pb-3 flex items-start justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Classical Repertorization</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Ranked by multi-symptom grade score · {remedies.length} remedies · {totalRubrics.toLocaleString()} rubrics
          </p>
        </div>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 shrink-0">
          PRIMARY
        </span>
      </div>

      {/* ── HERO CARD (Top Remedy) ── */}
      {top && (
        <div className="mx-5 mb-4 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 p-4 flex items-center gap-5">
          {/* Rank circle */}
          <div className="shrink-0 w-14 h-14 rounded-full bg-blue-600 text-white flex items-center justify-center text-2xl font-bold shadow-sm">
            1
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xl font-bold text-gray-900">{top.name}</span>
              <span className="text-sm text-gray-500 font-mono">({top.abbrev})</span>
              {top.cycle_analysis?.meets_threshold && (
                <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-green-100 text-green-700">
                  ✓ Cycle
                </span>
              )}
            </div>

            {/* Score bar */}
            <div className="mt-2 flex items-center gap-3">
              <div className="flex-1 h-2.5 bg-blue-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full transition-all"
                  style={{ width: `${(top.score / maxScore) * 100}%` }}
                />
              </div>
              <span className="text-sm font-bold text-blue-700 tabular-nums">{top.score}</span>
            </div>

            <div className="mt-1.5 flex gap-3 text-xs text-gray-500">
              <span>{top.match_count} rubric matches</span>
              {top.cycle_analysis && (
                <span>
                  Cycle {Math.round((top.cycle_analysis.segment_coverage || 0) * 100)}%
                  ({top.cycle_analysis.segments_matched_count || 0}/{top.cycle_analysis.total_segments || 0})
                </span>
              )}
            </div>
          </div>

          <div className="shrink-0 flex flex-col gap-2">
            <button
              onClick={() => {
                if (onRemedyClick) onRemedyClick(top.abbrev);
                else router.push(`/remedies/${encodeURIComponent(top.abbrev)}`);
              }}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 transition"
            >
              View Remedy
            </button>
            {top.cycle_analysis?.cycle_sentence && (
              <button
                onClick={() => toggleExpand(top.abbrev)}
                className="px-3 py-1.5 bg-white border text-blue-600 text-xs font-medium rounded-md hover:bg-blue-50 transition"
              >
                {expandedRemedy === top.abbrev ? "Hide Cycle" : "Cycle Analysis"}
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── CYCLE SENTENCE EXPAND (hero) ── */}
      {expandedRemedy === top?.abbrev && top?.cycle_analysis?.cycle_sentence && (
        <div className="mx-5 mb-4 p-3 bg-gray-50 rounded-md border text-sm text-gray-700 leading-relaxed italic">
          “{top.cycle_analysis.cycle_sentence}”
          {top.cycle_analysis.map_of_hierarchy_phase && (
            <div className="mt-1 text-xs text-gray-400 not-italic">
              Map of Hierarchy — Phase {top.cycle_analysis.map_of_hierarchy_phase}
            </div>
          )}
        </div>
      )}

      {/* ── RANKED TABLE ── */}
      <div className="px-5 pb-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-xs text-gray-400">
              <th className="text-left py-2 font-medium w-10">#</th>
              <th className="text-left py-2 font-medium">Remedy</th>
              <th className="text-left py-2 font-medium w-32">Score</th>
              <th className="text-left py-2 font-medium w-24">Matches</th>
              <th className="text-left py-2 font-medium w-28">Cycle</th>
              <th className="text-left py-2 font-medium w-16">Pin</th>
              <th className="text-left py-2 font-medium w-24">Actions</th>
            </tr>
          </thead>
          <tbody>
            {remedies.map((rem, idx) => {
              const isTop = idx === 0;
              const ca = rem.cycle_analysis;
              const coverage = ca?.segment_coverage || 0;
              const cycleLabel = ca?.meets_threshold
                ? `${Math.round(coverage * 100)}% ✓`
                : coverage > 0
                ? `${Math.round(coverage * 100)}%`
                : "—";
              const cycleColor = ca?.meets_threshold
                ? "text-green-600"
                : coverage > 0
                ? "text-amber-600"
                : "text-gray-400";

              return (
                <tr
                  key={rem.abbrev}
                  className={`border-b last:border-0 hover:bg-gray-50 transition ${
                    isTop ? "bg-blue-50/30" : ""
                  }`}
                >
                  {/* Rank */}
                  <td className="py-2.5">
                    <span
                      className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                        isTop
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {idx + 1}
                    </span>
                  </td>

                  {/* Name */}
                  <td className="py-2.5">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-gray-800">{rem.name}</span>
                      <span className="text-xs text-gray-400 font-mono">{rem.abbrev}</span>
                    </div>
                  </td>

                  {/* Score bar */}
                  <td className="py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            isTop ? "bg-blue-500" : "bg-gray-400"
                          }`}
                          style={{ width: `${(rem.score / maxScore) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-gray-700 tabular-nums w-6 text-right">
                        {rem.score}
                      </span>
                    </div>
                  </td>

                  {/* Matches */}
                  <td className="py-2.5 text-xs text-gray-500 tabular-nums">
                    {rem.match_count}
                  </td>

                  {/* Cycle badge */}
                  <td className="py-2.5">
                    <span className={`text-xs font-medium tabular-nums ${cycleColor}`}>
                      {cycleLabel}
                    </span>
                  </td>

                  {/* Pin */}
                  <td className="py-2.5">
                    {onTogglePin && (
                      <button
                        onClick={() => onTogglePin(rem.abbrev)}
                        className={`text-xs px-2 py-1 rounded border transition ${
                          pinnedRemedies?.has(rem.abbrev)
                            ? "bg-blue-50 border-blue-200 text-blue-600"
                            : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"
                        }`}
                        title={pinnedRemedies?.has(rem.abbrev) ? "Unpin" : "Pin remedy"}
                      >
                        {pinnedRemedies?.has(rem.abbrev) ? "📌" : "📍"}
                      </button>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="py-2.5">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          if (onRemedyClick) onRemedyClick(rem.abbrev);
                          else router.push(`/remedies/${encodeURIComponent(rem.abbrev)}`);
                        }}
                        className="text-[10px] px-2 py-1 rounded border text-gray-600 hover:bg-gray-100 transition"
                      >
                        View
                      </button>
                      {rem.matches && rem.matches.length > 0 && (
                        <button
                          onClick={() => toggleExpand(rem.abbrev)}
                          className="text-[10px] px-2 py-1 rounded border text-gray-600 hover:bg-gray-100 transition"
                        >
                          {expandedRemedy === rem.abbrev ? "Hide" : "Rubrics"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── DIFFERENTIATING RUBRICS EXPAND ── */}
      {expandedRemedy && (
        <div className="mx-5 mb-4 border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-700">
              Rubric matches for{" "}
              {remedies.find((r) => r.abbrev === expandedRemedy)?.name}
            </span>
            <button
              onClick={() => setExpandedRemedy(null)}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              Close
            </button>
          </div>
          <div className="p-3 max-h-64 overflow-y-auto">
            {remedies
              .find((r) => r.abbrev === expandedRemedy)
              ?.matches?.map((m, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 py-1.5 border-b last:border-0 text-sm"
                >
                  {/* Grade dot */}
                  <span
                    className="inline-block w-3 h-3 rounded-sm shrink-0"
                    style={{
                      backgroundColor:
                        GRADE_COLORS[Math.min(m.grade || m.weight || 0, 4)],
                    }}
                  />
                  <span className="text-xs font-mono text-gray-400 w-5 text-right">
                    {m.grade || m.weight || 0}
                  </span>
                  <span
                    className="text-gray-700 cursor-pointer hover:text-blue-600 transition truncate"
                    onClick={() => {
                      if (onRubricClick)
                        onRubricClick(m.rubric || "", m.rubric_id ? String(m.rubric_id) : undefined);
                      else if (m.rubric_id)
                        router.push(`/rubrics/${encodeURIComponent(m.rubric_id)}`);
                    }}
                    title={m.rubric || ""}
                  >
                    {m.rubric || `Rubric ${m.rubric_id}`}
                  </span>
                </div>
              )) || (
              <div className="text-xs text-gray-400 italic">
                No detailed rubric data available for this remedy.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── CONFIDENCE STATEMENT ── */}
      {confidenceStatement && (
        <div className="mx-5 mb-5 p-3 bg-gray-50 rounded-lg border border-gray-100">
          <div className="flex items-start gap-2">
            <span className="text-blue-500 text-lg shrink-0">💡</span>
            <p className="text-sm text-gray-700 leading-relaxed">{confidenceStatement}</p>
          </div>
        </div>
      )}
    </div>
  );
}
