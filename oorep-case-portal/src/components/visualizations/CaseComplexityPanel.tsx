"use client";

export default function CaseComplexityPanel({ result }: { result?: { complexity_score?: number; components?: any; interpretation?: string } }) {
  const score = result?.complexity_score ?? 0;
  const comp = result?.components ?? {};
  const bars = [
    { label: "Symptom Entropy", value: comp?.symptom_entropy ?? 0, color: "#3b82f6" },
    { label: "Coverage Penalty", value: comp?.coverage_penalty ?? 0, color: "#ef4444" },
    { label: "Redundancy", value: comp?.symptom_redundancy ?? 0, color: "#f59e0b" },
    { label: "Specificity", value: comp?.symptom_specificity ?? 0, color: "#10b981" },
  ];
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">INTERMEDIATE</span>
        <span className="text-sm font-semibold text-gray-700">Case Complexity</span>
      </div>
      <div className="bg-gray-50 rounded-lg p-4 text-center mb-3">
        <div className="text-3xl font-bold" style={{ color: score > 0.7 ? "#dc2626" : score > 0.4 ? "#d97706" : "#059669" }}>
          {(score * 100).toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500 mt-1">{result?.interpretation ?? "—"}</div>
      </div>
      <div className="space-y-2">
        {bars.map((b) => (
          <div key={b.label} className="flex items-center gap-2">
            <span className="text-xs text-gray-500 w-24 shrink-0">{b.label}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${(b.value * 100).toFixed(0)}%`, backgroundColor: b.color }} />
            </div>
            <span className="text-xs text-gray-400 w-10 text-right">{(b.value * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
