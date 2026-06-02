"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function RemedyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const abbrev = params?.abbrev as string;

  const [data, setData] = useState(null as any);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!abbrev) return;
    setLoading(true);
    fetch(`/api/remedies/${encodeURIComponent(abbrev)}`)
      .then((r) => r.json())
      .then((json) => {
        if (json.ok) setData(json.remedy);
        else setError(json.error || "Failed to load");
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [abbrev]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 font-mono text-sm">
      <button
        onClick={() => router.back()}
        className="mb-4 text-slate-400 hover:text-slate-100 transition-colors"
      >
        ← Back to dashboard
      </button>

      {loading && <p className="text-slate-500">Loading remedy profile…</p>}
      {error && <div className="text-red-400">{error}</div>}
      {data && (
        <>
          <h1 className="text-xl font-bold mb-2">{data.name}</h1>
          <h2 className="text-lg text-slate-400 mb-4">Abbreviation: {data.abbrev}</h2>
          <div className="bg-slate-900 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Classification</h3>
            <pre className="text-xs text-slate-400 whitespace-pre-wrap">{JSON.stringify(data.classification || {}, null, 2)}</pre>
          </div>
        </>
      )}
    </main>
  );
}
