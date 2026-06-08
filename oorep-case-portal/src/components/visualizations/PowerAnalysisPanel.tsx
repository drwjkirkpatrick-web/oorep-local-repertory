"use client";

export default function PowerAnalysisPanel({ result }: { result?: { sample_size_per_group?: number; total_sample_size?: number; achievable_power?: number; power_curve?: any[]; minimum_detectable_difference?: number } }) {
  const curve = result?.power_curve ?? [];
  return (
    <div className="p-4">
      <p className="text-xs text-slate-500 italic leading-relaxed mb-3">
        See how many patients you'd need in a study (or case series) to reliably detect a treatment effect. The three cards show required sample size per group, total sample, and the statistical power (probability of detecting a real effect). The power curve shows how power increases with sample size. Essential for designing clinical studies or evaluating published research.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">INTERMEDIATE</span>
        <span className="text-sm font-semibold text-gray-700">Power Analysis</span>
      </div>
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="bg-gray-50 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-blue-600">{result?.sample_size_per_group ?? "—"}</div>
          <div className="text-xs text-gray-500">Per group</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-purple-600">{result?.total_sample_size ?? "—"}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-green-600">{result?.achievable_power?.toFixed(2) ?? "—"}</div>
          <div className="text-xs text-gray-500">Power</div>
        </div>
      </div>
      {curve.length > 0 && (
        <div className="bg-white border rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-600 mb-2">Power Curve</div>
          <svg width="260" height="140" className="mx-auto">
            <line x1="30" y1="120" x2="250" y2="120" stroke="#374151" strokeWidth={2} />
            <line x1="30" y1="20" x2="30" y2="120" stroke="#374151" strokeWidth={2} />
            <path d={`M ${30 + curve[0].n * 1.1} ${120 - curve[0].power * 100} ` + curve.slice(1).map(p => `L ${30 + p.n * 1.1} ${120 - p.power * 100}`).join(" ")} fill="none" stroke="#3b82f6" strokeWidth={2} />
            <text x="140" y="136" fontSize={10} textAnchor="middle" fill="#6b7280">Sample Size (n)</text>
            <text x="15" y="70" fontSize={10} textAnchor="middle" fill="#6b7280" transform="rotate(-90, 15, 70)">Power</text>
          </svg>
        </div>
      )}
    </div>
  );
}
