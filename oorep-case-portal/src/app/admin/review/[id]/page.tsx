"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

interface CaseDoc {
  id: string;
  case_code: string;
  status: string;
  practitioner_email: string;
  practitioner_name: string | null;
  chief_concern: string | null;
  modalities: string | null;
  body: string | null;
  files: Array<{ name: string; size: number; type: string }>;
  created_at: string;
  paid_at: string | null;
  repertory_result: Array<{ abbrev: string; name: string; score: number; match_count: number }> | null;
  draft_pdf_path: string | null;
  final_pdf_path: string | null;
  sent_at: string | null;
}

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [doc, setDoc] = useState<CaseDoc | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [symptoms, setSymptoms] = useState("");
  const [repLoading, setRepLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    fetch(`/api/admin/cases/${id}`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.ok) throw new Error(data.error || "Failed");
        setDoc(data.case);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function runRepertorize() {
    if (!symptoms.trim()) return;
    setRepLoading(true);
    setError(null);
    try {
      const list = symptoms.split(",").map((s) => s.trim()).filter(Boolean);
      const res = await fetch("/api/admin/repertorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: id, symptoms: list }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Failed");
      setDoc((prev) => prev ? { ...prev, repertory_result: data.result, status: "reviewing" } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setRepLoading(false);
    }
  }

  async function generatePdf(mode: "draft" | "final") {
    setPdfLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: id, mode }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Failed");
      setDoc((prev) =>
        prev
          ? {
              ...prev,
              draft_pdf_path: mode === "draft" ? data.pdf_path : prev.draft_pdf_path,
              final_pdf_path: mode === "final" ? data.pdf_path : prev.final_pdf_path,
              status: mode === "final" ? "approved" : prev.status,
            }
          : null
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setPdfLoading(false);
    }
  }

  async function sendCase() {
    setError(null);
    try {
      const res = await fetch(`/api/admin/cases/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "sent", sent_at: new Date().toISOString(), notes_admin: notes }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Failed");
      setDoc((prev) => (prev ? { ...prev, status: "sent", sent_at: new Date().toISOString() } : null));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  if (loading) return <main className="max-w-3xl mx-auto px-6 py-12"><p>Loading...</p></main>;
  if (error && !doc) return <main className="max-w-3xl mx-auto px-6 py-12"><p className="text-red-600">{error}</p></main>;
  if (!doc) return null;

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Review Case</h1>
          <p className="text-sm text-gray-500 font-mono">{doc.case_code}</p>
        </div>
        <button onClick={() => router.push("/admin")} className="text-sm underline text-gray-500">Back to Dashboard</button>
      </div>

      {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4"><p className="text-red-700 text-sm">{error}</p></div>}

      <section className="space-y-6">
        <div className="p-4 border rounded-lg">
          <h2 className="font-semibold mb-2">Practitioner</h2>
          <p className="text-sm">{doc.practitioner_name || "—"} &lt;{doc.practitioner_email}&gt;</p>
          <p className="text-xs text-gray-500 mt-1">Submitted: {new Date(doc.created_at).toLocaleString()}</p>
        </div>

        <div className="p-4 border rounded-lg">
          <h2 className="font-semibold mb-2">Chief Concern</h2>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{doc.chief_concern || "(not provided)"}</p>
        </div>

        <div className="p-4 border rounded-lg">
          <h2 className="font-semibold mb-2">Modalities</h2>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{doc.modalities || "(not provided)"}</p>
        </div>

        {doc.body && (
          <div className="p-4 border rounded-lg">
            <h2 className="font-semibold mb-2">Case Notes</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{doc.body}</p>
          </div>
        )}

        {doc.files && doc.files.length > 0 && (
          <div className="p-4 border rounded-lg">
            <h2 className="font-semibold mb-2">Uploaded Files</h2>
            <ul className="text-sm space-y-1">
              {doc.files.map((f, i) => (
                <li key={i} className="text-gray-600">{f.name} ({Math.round((f.size || 0) / 1024)}KB)</li>
              ))}
            </ul>
          </div>
        )}

        <div className="p-4 border rounded-lg bg-blue-50">
          <h2 className="font-semibold mb-2">Repertorize</h2>
          <p className="text-xs text-gray-600 mb-2">Enter symptoms separated by commas:</p>
          <textarea rows={3} value={symptoms} onChange={(e) => setSymptoms(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="fever evening, thirst, anxiety health" />
          <button onClick={runRepertorize} disabled={repLoading} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
            {repLoading ? "Running..." : "Run OOREP Repertorization"}
          </button>
        </div>

        {doc.repertory_result && doc.repertory_result.length > 0 && (
          <div className="p-4 border rounded-lg">
            <h2 className="font-semibold mb-2">Results ({doc.repertory_result.length} remedies)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="py-1">#</th>
                    <th className="py-1">Abbrev</th>
                    <th className="py-1">Name</th>
                    <th className="py-1">Score</th>
                    <th className="py-1">Matches</th>
                  </tr>
                </thead>
                <tbody>
                  {doc.repertory_result.map((r, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-1">{i + 1}</td>
                      <td className="py-1 font-mono">{r.abbrev}</td>
                      <td className="py-1">{r.name}</td>
                      <td className="py-1">{r.score}</td>
                      <td className="py-1">{r.match_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="p-4 border rounded-lg bg-gray-50">
          <h2 className="font-semibold mb-2">Generate Report PDF</h2>
          <div className="flex gap-2">
            <button onClick={() => generatePdf("draft")} disabled={pdfLoading} className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50">Generate Draft PDF</button>
            <button onClick={() => generatePdf("final")} disabled={pdfLoading} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">Generate Final PDF</button>
          </div>
          {doc.draft_pdf_path && <p className="text-xs text-gray-500 mt-2">Draft: {doc.draft_pdf_path}</p>}
          {doc.final_pdf_path && <p className="text-xs text-gray-500 mt-1">Final: {doc.final_pdf_path}</p>}
        </div>

        {doc.status !== "sent" && (
          <div className="p-4 border rounded-lg">
            <h2 className="font-semibold mb-2">Admin Notes (optional)</h2>
            <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} className="w-full px-3 py-2 border rounded-lg" placeholder="Private admin notes..." />
            <button onClick={sendCase} className="mt-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800">Mark as Sent to Practitioner</button>
          </div>
        )}

        {doc.status === "sent" && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 font-medium">Case sent on {doc.sent_at ? new Date(doc.sent_at).toLocaleString() : "—"}</p>
          </div>
        )}
      </section>
    </main>
  );
}
