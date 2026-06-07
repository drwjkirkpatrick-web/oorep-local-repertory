"use client";

/**
 * Outcome Comparator Panel — Module #66
 * Mann-Whitney U, odds ratio, Cohen's d visualization
 */

export default function OutcomeComparatorPanel({
  result,
}: {
  result?: {
    mann_whitney?: { u_statistic: number; p_value: number; z_score: number };
    odds_ratio?: { odds_ratio: number; ci_95: [number, number] };
    cohens_d?: { cohens_d: number; interpretation: string };
  };
}) {
  const mw = result?.mann_whitney;
  const or = result?.odds_ratio;
  const cd = result?.cohens_d;

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">STATISTICS</span>
        <span className="text-sm font-semibold text-gray-700">Outcome Comparator</span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {/* Mann-Whitney */}
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500 mb-1">Mann-Whitney U</div>
          <div className="text-lg font-bold text-blue-600">{mw?.u_statistic ?? "—"}</div>
          <div className="text-xs text-gray-400">p = {mw?.p_value?.toFixed(3) ?? "—"}</div>
          {mw && (
            <div className={`text-xs mt-1 font-medium ${mw.p_value < 0.05 ? "text-green-600" : "text-gray-500"}`}>
              {mw.p_value < 0.05 ? "✓ Significant" : "Not significant"}
            </div>
          )}
        </div>

        {/* Odds Ratio */}
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500 mb-1">Odds Ratio</div>
          <div className="text-lg font-bold text-purple-600">{or?.odds_ratio?.toFixed(2) ?? "—"}</div>
          <div className="text-xs text-gray-400">CI: [{or?.ci_95?.[0]?.toFixed(2) ?? "—"}, {or?.ci_95?.[1]?.toFixed(2) ?? "—"}]</div>
          {or && or.odds_ratio > 1 && (
            <div className="text-xs text-green-600 mt-1 font-medium">Favors treatment</div>
          )}
        </div>

        {/* Cohen's d */}
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500 mb-1">Cohen's d</div>
          <div className="text-lg font-bold text-orange-600">{cd?.cohens_d?.toFixed(2) ?? "—"}</div>
          <div className="text-xs text-gray-400">{cd?.interpretation ?? "—"}</div>
        </div>
      </div>
    </div>
  );
}
