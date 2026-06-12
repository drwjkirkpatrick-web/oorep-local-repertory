"use client";

/**
 * ModalityPanel.tsx
 * Dashboard panel for Modality Extractor (Module #135)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Modalities are the fingerprint of the remedy. “Better from cold”    │
 * │ is not a preference — it is a constitutional signal that separates  │
 * │ Pulsatilla from Nux-vomica from Sulphur. This panel extracts      │
 * │ modalities across 11 axes from free-text narrative, identifies SRP   │
 * │ modalities (e.g., “better at exactly 3 a.m.”), and builds a       │
 * │ complete modality grid for repertorization. You never miss a       │
 * │ modality because the patient buried it in a long story.            │
 * │                                                                    │
 * │ Real-world use: Patient says “I feel awful in the morning, but    │
 * │ by afternoon I can function, and I really need fresh air.” The    │
 * │ panel extracts: worse morning (time), better open air (weather),   │
 * │ worse first motion then better continued (motion). It flags “worse │
 * │ morning then better afternoon” as SRP — a strong Nux-vomica signal. │
 * │ You add all three to repertorization. Nux-v. jumps to #2.         │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface ModalityItem {
  axis: string;
  direction: string;
  value: string;
  srp_flag: boolean;
  confidence: number;
  source_text: string;
}

export default function ModalityPanel() {
  const [modalities, setModalities] = useState<ModalityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/modalities")
      .then((r) => r.json())
      .then((data) => {
        setModalities(data.modalities || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading modality extraction...</div>;

  const srpModalities = modalities.filter((m) => m.srp_flag);
  const regularModalities = modalities.filter((m) => !m.srp_flag);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Modality Extractor (Module #135)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Modalities are the <strong>fingerprint of the remedy</strong>. “Better from cold”
          is not a preference — it is a constitutional signal that separates Pulsatilla from
          Nux-vomica from Sulphur. This panel extracts modalities across <strong>11 axes</strong>
          (time, temperature, motion, position, food, emotion, weather, company, consolation,
          function, pressure) from free-text patient narrative. It identifies <em>SRP
          modalities</em> (e.g. “better at exactly 3 a.m.”) that carry extraordinary
          discriminative weight. You never miss a modality because the patient buried it in
          a long story.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-purple-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-purple-800">🌟 SRP Modalities (High Weight)</h3>
          <div className="space-y-2">
            {srpModalities.map((m, i) => (
              <div key={i} className="border-b pb-2 last:border-0">
                <div className="flex justify-between">
                  <span className="font-medium">{m.axis}: {m.direction} {m.value}</span>
                  <span className="text-purple-600 font-bold">SRP ✓</span>
                </div>
                <div className="text-xs text-gray-500 mt-1 italic">“{m.source_text}”</div>
                <div className="text-xs text-gray-400">Confidence: {(m.confidence * 100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-gray-600">Standard Modalities</h3>
          <div className="space-y-2">
            {regularModalities.map((m, i) => (
              <div key={i} className="border-b pb-2 last:border-0">
                <div className="font-medium">{m.axis}: {m.direction} {m.value}</div>
                <div className="text-xs text-gray-500 mt-1 italic">“{m.source_text}”</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
