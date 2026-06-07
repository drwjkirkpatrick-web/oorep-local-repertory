"use client";

export default function DuplicateRemedyPanel({ result }: { result?: { safe?: boolean; warnings?: any[]; proposed_remedy?: string } }) {
  const safe = result?.safe ?? true;
  const warnings = result?.warnings || [];
  return (
    <div className="space-y-3">
      <div className={`text-center py-2 rounded-lg font-semibold text-sm ${safe ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
        {safe ? "✓ Safe to prescribe" : "⚠ Prescription warnings detected"}
      </div>
      {warnings.slice(0, 4).map((w: any, i: number) => (
        <div key={i} className={`text-xs p-2 rounded border-l-4 ${w.severity === "critical" ? "bg-red-50 border-red-500 text-red-700" : w.severity === "warning" ? "bg-amber-50 border-amber-500 text-amber-700" : "bg-blue-50 border-blue-500 text-blue-700"}`}>
          <strong>{w.type.toUpperCase()}:</strong> {w.message}
        </div>
      ))}
    </div>
  );
}
