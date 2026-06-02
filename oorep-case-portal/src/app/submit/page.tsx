"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";

type CaseState = "idle" | "creating" | "payment" | "paying" | "done" | "error";

export default function SubmitPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [chief, setChief] = useState("");
  const [modalities, setModalities] = useState("");
  const [body, setBody] = useState("");
  const [caseState, setCaseState] = useState<CaseState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [caseCode, setCaseCode] = useState("");
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [files, setFiles] = useState<FileList | null>(null);

  const createCase = useCallback(async () => {
    setError(null);
    if (!email.includes("@")) {
      setError("Valid email required");
      return;
    }
    if (!chief.trim()) {
      setError("Chief concern required");
      return;
    }
    setCaseState("creating");
    try {
      const res = await fetch("/api/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          practitioner_email: email.trim(),
          practitioner_name: name.trim(),
          chief_concern: chief.trim(),
          modalities: modalities.trim(),
          body: body.trim(),
          files: [],
        }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Failed");
      setCaseCode(data.case.case_code);
      setCaseId(data.case.id);

      // Upload files if any
      if (files && files.length > 0) {
        const fd = new FormData();
        for (let i = 0; i < files.length; i++) fd.append("file", files[i]);
        await fetch(`/api/upload?case_code=${data.case.case_code}`, { method: "POST", body: fd });
      }

      // Create payment intent
      const piRes = await fetch("/api/payment/intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_code: data.case.case_code,
          practitioner_email: email.trim(),
          practitioner_name: name.trim(),
        }),
      });
      const piData = await piRes.json();
      if (!piData.ok) throw new Error(piData.error || "Payment init failed");
      setClientSecret(piData.client_secret);
      setCaseState("payment");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
      setCaseState("error");
    }
  }, [email, name, chief, modalities, body, files]);

  const confirmPayment = useCallback(async () => {
    if (!clientSecret || !caseId) return;
    setCaseState("paying");
    try {
      const piId = clientSecret.split("_secret_")[0];
      const res = await fetch("/api/payment/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payment_intent_id: piId, case_id: caseId }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Payment failed");
      setCaseState("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment error");
      setCaseState("error");
    }
  }, [clientSecret, caseId]);

  return (
    <main className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold mb-2">Submit a Case — $49</h1>
      <p className="text-gray-600 mb-8">All fields marked * are required.</p>

      {caseState === "done" && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-6">
          <p className="font-semibold text-green-800">Payment confirmed!</p>
          <p className="text-green-700 text-sm">Your case code: <span className="font-mono font-bold">{caseCode}</span></p>
          <p className="text-green-700 text-sm mt-1">Save this code. Check status at /status</p>
          <button onClick={() => router.push(`/status?code=${caseCode}`)} className="mt-3 text-sm underline text-green-800">Check Status</button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-6">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {caseState !== "done" && caseState !== "payment" && caseState !== "paying" && (
        <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); createCase(); }}>
          <div>
            <label className="block text-sm font-medium mb-1">Practitioner Email *</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Practitioner Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Chief Concern / Symptoms *</label>
            <textarea required rows={3} value={chief} onChange={(e) => setChief(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Describe the main symptoms and the patient's condition" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Modalities * (crucial for precision)</label>
            <textarea required rows={4} value={modalities} onChange={(e) => setModalities(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Time (morning/night), heat/cold, motion/rest, eating, sleep, weather, company/solitude, laterality, etc." />
            <p className="text-xs text-gray-500 mt-1">Include when worse/better, triggers, and anything that modifies the chief concern.</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Case Notes / Body</label>
            <textarea rows={5} value={body} onChange={(e) => setBody(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Full case details, mental/emotional symptoms, relevant history, etc." />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Upload Files</label>
            <input type="file" multiple onChange={(e) => setFiles(e.target.files)} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
            <p className="text-xs text-gray-500 mt-1">Accepted: .txt, .md, .pdf, .doc, .docx, audio (mp3, wav, ogg, m4a)</p>
          </div>
          <button type="submit" disabled={caseState === "creating"} className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {caseState === "creating" ? "Creating case..." : "Continue to Payment — $49"}
          </button>
        </form>
      )}

      {caseState === "payment" && clientSecret && (
        <div className="p-6 border rounded-lg bg-gray-50">
          <h2 className="text-lg font-semibold mb-2">Complete Payment</h2>
          <p className="text-sm text-gray-600 mb-4">Case code: <span className="font-mono font-bold">{caseCode}</span></p>
          <p className="text-sm text-gray-600 mb-4">Amount: $49.00 USD</p>
          <button onClick={confirmPayment} className="w-full px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors">
            Confirm Payment (Demo)
          </button>
          <p className="text-xs text-gray-500 mt-3">In production this will redirect to Stripe Checkout. For testing, click Confirm.</p>
        </div>
      )}

      {caseState === "paying" && (
        <div className="p-6 border rounded-lg bg-gray-50 text-center">
          <p className="text-gray-600">Processing payment...</p>
        </div>
      )}
    </main>
  );
}
