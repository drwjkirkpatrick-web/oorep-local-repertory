"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type CaseBrief = {
  id: string;
  case_code: string;
  status: string;
  practitioner_email: string;
  chief_concern: string | null;
  created_at: string;
  paid_at: string | null;
};

const statusClasses: Record<string, string> = {
  pending_payment: "bg-gray-100 text-gray-700",
  paid: "bg-yellow-50 text-yellow-700",
  reviewing: "bg-blue-50 text-blue-700",
  draft_ready: "bg-purple-50 text-purple-700",
  approved: "bg-green-50 text-green-700",
  sent: "bg-green-100 text-green-800",
  refunded: "bg-red-50 text-red-700",
};

export default function AdminPage() {
  const router = useRouter();
  const [cases, setCases] = useState<CaseBrief[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/admin/cases")
      .then((res) => res.json())
      .then((data) => {
        if (!data.ok) throw new Error(data.error || "Failed");
        setCases(data.cases);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = cases.filter((c) =>
    filter ? c.status === filter : true
  );

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">OORep Admin Dashboard</h1>
        <button onClick={() => router.push("/")} className="text-sm underline text-gray-500">Back to Portal</button>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        {["", "pending_payment", "paid", "reviewing", "draft_ready", "approved", "sent", "refunded"].map((s) => (
          <button key={s} onClick={() => setFilter(s)} className={`px-3 py-1 rounded-full text-xs border ${filter === s ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}>
            {s ? s.replace("_", " ") : "All"}
          </button>
        ))}
      </div>

      {loading && <p className="text-gray-500">Loading cases...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <div className="space-y-2">
          {filtered.length === 0 && <p className="text-gray-500">No cases.</p>}
          {filtered.map((c) => (
            <div key={c.id} onClick={() => router.push(`/admin/review/${c.id}`)} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-gray-400">{c.case_code}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusClasses[c.status] || "bg-gray-100"}`}>{c.status.replace("_", " ")}</span>
                </div>
                <p className="text-sm font-medium truncate mt-1">{c.chief_concern || "(no concern)"}</p>
                <p className="text-xs text-gray-500">{c.practitioner_email}</p>
              </div>
              <div className="text-right text-xs text-gray-400 pl-4">
                <p>{new Date(c.created_at).toLocaleDateString()}</p>
                {c.paid_at && <p className="text-green-600">Paid</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
