"use client";

export default function CaseSimilarityPanel({ result }: { result?: { what_worked?: any[] } }) {
  const worked = result?.what_worked || [];
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-slate-700">Remedies That Worked for Similar Cases</div>
      {worked.slice(0, 5).map((w: any, i: number) => (
        <div key={i} className="flex items-center justify-between text-sm">
          <span className="font-medium text-slate-800">{w.remedy}</span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">{w.count} cases</span>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">{w.avg_similarity}</span>
          </div>
        </div>
      ))}
      {worked.length === 0 && <div className="text-sm text-slate-400 italic">No similar cases indexed</div>}
    </div>
  );
}
