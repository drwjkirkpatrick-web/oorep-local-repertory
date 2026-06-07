"use client";

export default function ConstitutionalTrackerPanel({ result }: { result?: { constitutional_remedy?: string; escalation?: any[]; max_potency?: string } }) {
  const esc = result?.escalation || [];
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
        <span className="font-semibold text-slate-800">Constitutional: {result?.constitutional_remedy || "—"}</span>
      </div>
      <div className="text-xs text-slate-500">Max potency: {result?.max_potency || "—"}</div>
      <div className="space-y-1">
        {esc.slice(-5).map((e: any, i: number) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div className={`w-2 h-2 rounded-full ${e.direction === "escalated" ? "bg-emerald-400" : e.direction === "reduced" ? "bg-red-400" : "bg-slate-300"}`}></div>
            <span className="text-slate-600">{e.date} — {e.remedy} {e.potency}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
