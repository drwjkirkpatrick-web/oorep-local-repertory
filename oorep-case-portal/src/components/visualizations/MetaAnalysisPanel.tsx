"use client";

export default function MetaAnalysisPanel({ result }: { result?: { model?: string; pooled_proportion?: number; ci_95?: [number, number]; heterogeneity?: any; studies?: any[] } }) {
  const pp = result?.pooled_proportion;
  const ci = result?.ci_95;
  const het = result?.heterogeneity;
  const studies = result?.studies ?? [];
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Meta-Analysis</span>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500">Pooled Rate</div>
          <div className="text-xl font-bold text-blue-600">{pp?.toFixed(2) ?? "—"}</div>
          <div className="text-xs text-gray-400">CI: [{ci?.[0]?.toFixed(2) ?? "—"}, {ci?.[1]?.toFixed(2) ?? "—"}]</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500">Heterogeneity (I²)</div>
          <div className="text-xl font-bold" style={{ color: (het?.I_squared ?? 0) < 25 ? "#059669" : (het?.I_squared ?? 0) < 50 ? "#d97706" : "#dc2626" }}>
            {het?.I_squared?.toFixed(1) ?? "—"}%
          </div>
          <div className="text-xs text-gray-400">{het?.interpretation ?? "—"}</div>
        </div>
      </div>
    </div>
  );
}
