"use client";

export default function ClinicalTipsPanel({ result }: { result?: { total_tips?: number; by_reliability?: Record<string, number> } }) {
  const reliability = result?.by_reliability || {};
  const colors: Record<string, string> = { anecdotal: "bg-slate-300", clinical: "bg-blue-400", proven: "bg-emerald-400", controversial: "bg-amber-400" };
  return (
    <div className="space-y-3">
      <div className="text-center">
        <div className="text-2xl font-bold text-slate-800">{result?.total_tips || 0}</div>
        <div className="text-xs text-slate-500">Clinical tips stored</div>
      </div>
      <div className="space-y-1">
        {Object.entries(reliability).map(([rel, count]) => (
          <div key={rel} className="flex items-center gap-2 text-xs">
            <div className={`w-3 h-3 rounded-full ${colors[rel] || "bg-slate-300"}`}></div>
            <span className="text-slate-600 capitalize">{rel}</span>
            <span className="ml-auto font-medium">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
