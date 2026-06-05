"use client";

import { useState } from "react";

export interface CaseFormData {
  patient_pseudonym: string;
  chief_concern: string;
  modalities: string;
  body: string;
}

interface CaseEntryPanelProps {
  onSave: (data: CaseFormData) => void;
  onUpload: (file: File) => void;
  onSymptomsExtracted: (symptoms: string) => void;
  savedCount: number;
}

export default function CaseEntryPanel({
  onSave,
  onUpload,
  onSymptomsExtracted,
  savedCount,
}: CaseEntryPanelProps) {
  const [form, setForm] = useState<CaseFormData>({
    patient_pseudonym: "",
    chief_concern: "",
    modalities: "",
    body: "",
  });
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const update = (field: keyof CaseFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setStatus("idle");
    setError(null);
  };

  const handleSave = () => {
    setError(null);
    if (!form.chief_concern.trim()) {
      setError("Chief concern is required");
      return;
    }
    setStatus("saving");
    onSave(form);
    setStatus("saved");
    // Reset form after brief delay so user sees confirmation
    setTimeout(() => {
      setForm({ patient_pseudonym: "", chief_concern: "", modalities: "", body: "" });
      setStatus("idle");
    }, 1200);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      // If it's a text file, extract symptoms inline for convenience
      if (file.type.startsWith("text/") || file.name.endsWith(".md") || file.name.endsWith(".txt")) {
        const text = await file.text();
        // Simple heuristic: lines that look like symptoms (short, start with lowercase)
        const lines = text
          .split("\n")
          .map((l) => l.trim())
          .filter((l) => l.length > 3 && l.length < 200);
        if (lines.length > 0) {
          onSymptomsExtracted(lines.join("\n"));
        }
      }
      onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-sm text-gray-800">Case Entry</h2>
        <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded">
          {savedCount} saved
        </span>
      </div>

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          {error}
        </div>
      )}

      {status === "saved" && (
        <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
          Case saved successfully
        </div>
      )}

      <div className="space-y-3">
        <div>
          <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Patient Pseudonym
          </label>
          <input
            type="text"
            value={form.patient_pseudonym}
            onChange={(e) => update("patient_pseudonym", e.target.value)}
            placeholder="e.g. Patient-Alpha (no real names)"
            className="w-full border rounded-md px-2 py-1.5 text-sm"
          />
        </div>

        <div>
          <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Chief Concern *
          </label>
          <textarea
            rows={2}
            value={form.chief_concern}
            onChange={(e) => update("chief_concern", e.target.value)}
            placeholder="Main symptoms or presenting complaint"
            className="w-full border rounded-md px-2 py-1.5 text-sm"
          />
        </div>

        <div>
          <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Modalities (crucial)
          </label>
          <textarea
            rows={3}
            value={form.modalities}
            onChange={(e) => update("modalities", e.target.value)}
            placeholder="Time, heat/cold, motion/rest, eating, sleep, weather, company/solitude, laterality…"
            className="w-full border rounded-md px-2 py-1.5 text-sm"
          />
        </div>

        <div>
          <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Full Case Notes
          </label>
          <textarea
            rows={4}
            value={form.body}
            onChange={(e) => update("body", e.target.value)}
            placeholder="Mental/emotional symptoms, history, generals, particulars…"
            className="w-full border rounded-md px-2 py-1.5 text-sm"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={status === "saving"}
            className="flex-1 px-3 py-2 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {status === "saving" ? "Saving…" : "Save Case"}
          </button>
          <label className="px-3 py-2 bg-gray-100 text-gray-700 text-xs font-medium rounded-md hover:bg-gray-200 transition cursor-pointer shrink-0">
            {uploading ? "Uploading…" : "Upload File"}
            <input
              type="file"
              className="hidden"
              accept=".txt,.md,.pdf,.doc,.docx,audio/*"
              onChange={handleFileChange}
            />
          </label>
        </div>
      </div>
    </div>
  );
}
