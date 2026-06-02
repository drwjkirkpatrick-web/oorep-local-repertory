"use client";

import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function RubricDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const { data, error, isLoading } = useSWR(
    id ? `/api/rubrics/${encodeURIComponent(id)}` : null,
    fetcher,
    { refreshInterval: 0 }
  );
  const rubric = data?.rubric;
  const remedies = data?.remedies || [];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 font-mono text-sm">
      <button
        onClick={() => router.back()}
        className="mb-4 text-slate-400 hover:text-slate-100 transition-colors"
      >
        ← Back to dashboard
      </button>

      {isLoading && <p className="text-slate-500">Loading rubric data…</p>}
      {error && (
        <div className="text-red-400">Failed to load: {error.message || "Unknown error"}</div>
      )}
      {rubric && (
        <>
          <h1 className="text-lg font-bold mb-1">{rubric.fullpath}</h1>
          <p className="text-slate-500 mb-4">
            ID: {rubric.id} • Source: {rubric.source || "unknown"} • Remedy count: {remedies.length}
          </p>

          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400">
                <th className="text-left py-2 px-3">Remedy</th>
                <th className="text-left py-2 px-3">Abbrev</th>
                <th className="text-center py-2 px-3">Weight (Grade)</th>
                <th className="text-left py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {remedies.map((rem: any) => (
                <tr
                  key={rem.remedy_id}
                  className="border-b border-slate-800 hover:bg-slate-800/40 transition-colors cursor-pointer"
                  onClick={() => router.push(`/remedies/${encodeURIComponent(rem.abbrev)}`)}
                >
                  <td className="py-2 px-3">{rem.name}</td>
                  <td className="py-2 px-3 text-slate-400">{rem.abbrev}</td>
                  <td className="py-2 px-3 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold ${
                        rem.weight >= 4
                          ? "bg-emerald-900 text-emerald-300"
                          : rem.weight >= 3
                          ? "bg-blue-900 text-blue-300"
                          : rem.weight >= 2
                          ? "bg-amber-900 text-amber-300"
                          : "bg-slate-700 text-slate-300"
                      }`}
                    >
                      {rem.weight}
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <span className="text-blue-400 hover:underline">View →</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  );
}
