"use client";

export default function PosologySchedulerPanel({ result }: { result?: { case_type?: string; recommended_potency?: string; repetition?: string; assess_after?: string; max_doses?: number } }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800">{result?.case_type || "Case"}</span>
        <span className="text-xs bg-violet-100 text-violet-700 px-2 py-1 rounded-full">{result?.recommended_potency || "—"}</span>
      </div>
      <div className="space-y-2">
        {result?.repetition && <div className="text-sm text-slate-600"><strong>Repeat:</strong> {result.repetition}</div>}
        {result?.assess_after && <div className="text-sm text-slate-600"><strong>Assess after:</strong> {result.assess_after}</div>}
        {result?.max_doses && <div className="text-sm text-slate-600"><strong>Max doses:</strong> {result.max_doses}</div>}
      </div>
    </div>
  );
}
