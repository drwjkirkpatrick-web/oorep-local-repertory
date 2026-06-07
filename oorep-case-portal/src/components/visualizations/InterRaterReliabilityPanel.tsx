"use client";

export default function InterRaterReliabilityPanel({ result }: { result?: { kappa?: any; icc?: any } }) {
  const k = result?.kappa;
  const icc = result?.icc;
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Inter-Rater Reliability</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500 mb-1">Cohen's Kappa</div>
          <div className="text-2xl font-bold text-blue-600">{k?.kappa?.toFixed(3) ?? "—"}</div>
          <div className="text-xs text-gray-400 mt-1">{k?.interpretation ?? "—"}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500 mb-1">ICC Consistency</div>
          <div className="text-2xl font-bold text-purple-600">{icc?.icc?.toFixed(3) ?? "—"}</div>
          <div className="text-xs text-gray-400 mt-1">{icc?.interpretation ?? "—"}</div>
        </div>
      </div>
    </div>
  );
}
