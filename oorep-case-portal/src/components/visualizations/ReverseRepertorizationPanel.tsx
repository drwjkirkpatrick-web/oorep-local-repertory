"use client";

export default function ReverseRepertorizationPanel({ result }: { result?: { remedy?: string; total_rubrics?: number; by_chapter?: Record<string, any[]> } }) {
  const chapters = result?.by_chapter || {};
  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 italic leading-relaxed">
        See all the rubrics where a chosen remedy is marked in the repertory, grouped by chapter (Mind, Head, Generals, etc.). Helpful when a practitioner already has a remedy in mind and wants to confirm where it shines, spot its strongholds, and notice gaps where it has little coverage.
      </p>
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800">{result?.remedy || "Remedy"}</span>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">{result?.total_rubrics || 0} rubrics</span>
      </div>
      {Object.entries(chapters).slice(0, 6).map(([chapter, rubrics]) => (
        <div key={chapter} className="border-l-4 border-blue-300 pl-3 py-1">
          <div className="text-sm font-medium text-slate-700">{chapter}</div>
          <div className="text-xs text-slate-500">{(rubrics as any[]).length} rubrics</div>
        </div>
      ))}
    </div>
  );
}
