"use client";

export default function SurvivalAnalysisPanel({ result }: { result?: { remedy?: string; n?: number; median_survival_time?: number; curve?: any[] } }) {
  const curve = result?.curve ?? [];
  const median = result?.median_survival_time;
  return (
    <div className="p-4">
      <p className="text-xs text-slate-500 italic leading-relaxed mb-3">
        See how long a remedy's beneficial effect typically lasts in your case base, using a Kaplan-Meier survival curve. The median survival time (red dashed line) is when 50% of patients experienced a return of symptoms. Steep drops in the curve indicate shorter action duration; gentle slopes mean longer-lasting relief. Useful for planning potency escalation timing.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Survival Analysis ({result?.remedy ?? "—"})</span>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500">Median Survival</div>
          <div className="text-xl font-bold text-blue-600">{median?.toFixed(1) ?? "—"} days</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500">N</div>
          <div className="text-xl font-bold text-purple-600">{result?.n ?? "—"}</div>
        </div>
      </div>
      <div className="bg-white border rounded-lg p-3">
        <div className="text-xs font-semibold text-gray-600 mb-2">Kaplan-Meier Curve</div>
        <svg width="260" height="160" className="mx-auto">
          <line x1="30" y1="140" x2="250" y2="140" stroke="#374151" strokeWidth={2} />
          <line x1="30" y1="20" x2="30" y2="140" stroke="#374151" strokeWidth={2} />
          {curve.length > 1 && (
            <path d={curve.map((p, i) => `${i === 0 ? "M" : "L"} ${30 + (p.time / 30) * 200} ${140 - p.survival * 120}`).join(" ")} fill="none" stroke="#3b82f6" strokeWidth={2} />
          )}
          {median && (
            <line x1={30 + (median / 30) * 200} y1={20} x2={30 + (median / 30) * 200} y2={140} stroke="#dc2626" strokeWidth={1} strokeDasharray="4 4" />
          )}
          <text x="140" y="156" fontSize={10} textAnchor="middle" fill="#6b7280">Days</text>
          <text x="15" y="80" fontSize={10} textAnchor="middle" fill="#6b7280" transform="rotate(-90, 15, 80)">Survival</text>
        </svg>
      </div>
    </div>
  );
}
