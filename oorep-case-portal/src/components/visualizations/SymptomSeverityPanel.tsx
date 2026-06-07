"use client";

export default function SymptomSeverityPanel({ result }: { result?: { avg_severity?: number; max_severity?: number; n_rated?: number } }) {
  const avg = result?.avg_severity || 0;
  const color = avg >= 7 ? "bg-red-500" : avg >= 4 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="space-y-3">
      <div className="text-center">
        <div className="text-3xl font-bold text-slate-800">{avg.toFixed(1)}<span className="text-sm text-slate-400">/10</span></div>
        <div className="text-xs text-slate-500">Average severity</div>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-3">
        <div className={`${color} h-3 rounded-full transition-all`} style={{ width: `${avg * 10}%` }}></div>
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span>Max: {result?.max_severity || "—"}</span>
        <span>{result?.n_rated || 0} rated</span>
      </div>
    </div>
  );
}
