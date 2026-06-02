"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";

type CaseDoc = {
  case_code: string;
  status: string;
  chief_concern: string | null;
  modalities: string | null;
  body: string | null;
  created_at: string;
  paid_at: string | null;
  final_pdf_path: string | null;
  sent_at: string | null;
};

const statusLabels: Record<string, string> = {
  pending_payment: "Awaiting Payment",
  paid: "Paid — In Queue",
  reviewing: "Under Review",
  draft_ready: "Draft Ready (Admin Review)",
  approved: "Approved — Finalizing",
  sent: "Complete — Delivered",
  refunded: "Refunded",
};

export default function StatusPage() {
  const searchParams = useSearchParams();
  const initialCode = searchParams.get("code") || "";
  const [code, setCode] = useState(initialCode);
  const [doc, setDoc] = useState<CaseDoc | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function checkStatus() {
    setLoading(true);
    setError(null);
    setDoc(null);
    try {
      const res = await fetch(`/api/status?code=${encodeURIComponent(code.trim().toUpperCase())}`);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Not found");
      setDoc(data.case as CaseDoc);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold mb-6">Check Case Status</h1>
      <div className="flex gap-2 mb-6">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Enter case code (e.g., OO-A1B2C3D4)"
          className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button onClick={checkStatus} disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {loading ? "Loading..." : "Check"}
        </button>
      </div>

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4"><p className="text-red-700 text-sm">{error}</p></div>}

      {doc && (
        <div className="border rounded-lg p-5 space-y-4">
          <div className="flex justify-between items-center">
            <span className="font-mono text-sm text-gray-500">{doc.case_code}</span>
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">{statusLabels[doc.status] || doc.status}</span>
          </div>
          <div>
            <p className="text-sm font-medium">Chief Concern</p>
            <p className="text-sm text-gray-600">{doc.chief_concern || "(not provided)"}</p>
          </div>
          {doc.modalities && (
            <div>
              <p className="text-sm font-medium">Modalities</p>
              <p className="text-sm text-gray-600">{doc.modalities}</p>
            </div>
          )}
          <div className="flex gap-6 text-xs text-gray-500">
            <span>Submitted: {new Date(doc.created_at).toLocaleDateString()}</span>
            {doc.paid_at && <span>Paid: {new Date(doc.paid_at).toLocaleDateString()}</span>}
            {doc.sent_at && <span>Sent: {new Date(doc.sent_at).toLocaleDateString()}</span>}
          </div>
          {doc.status === "sent" && doc.final_pdf_path && (
            <div className="pt-2 border-t">
              <p className="text-sm text-green-700 font-medium">Your report is ready!</p>
              <p className="text-xs text-gray-500 mt-1">Contact admin for download link.</p>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
