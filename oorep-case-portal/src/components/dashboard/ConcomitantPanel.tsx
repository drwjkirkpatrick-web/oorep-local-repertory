"use client";

/**
 * ConcomitantPanel.tsx
 * Dashboard panel for Concomitant Detector (Module #134)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Kent said: “The concomitants decide the case.” This panel          │
 * │ automatically detects symptoms that accompany the chief complaint  │
 * │ and scores each by SRP (strange-rare-peculiar) potential. A       │
 * │ concomitant that is odd, unexpected, or highly specific is worth   │
 * │ more than the chief complaint itself. You stop fishing and start    │
 * │ capturing the symptoms that truly differentiate the remedy.        │
 * │                                                                    │
 * │ Real-world use: Chief complaint: headache. Concomitants detected:  │
 * │ “irritability” (common, low SRP), “vision flashes” (rare, high SRP), │
 * │ “must lie down in dark room” (peculiar, high SRP). The panel says:  │
 * │ “Weight ‘vision flashes’ and ‘must lie in dark’ heavily — these are  │
 * │ the case-deciders.” You add them to repertorization. Belladonna     │
 * │ rises to #1.                                                       │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface ConcomitantItem {
  symptom: string;
  chapter: string;
  srp_score: number;
  discriminative_value: number;
  associated_remedies: string[];
  is_srp: boolean;
}

export default function ConcomitantPanel() {
  const [concomitants, setConcomitants] = useState<ConcomitantItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/concomitants")
      .then((r) => r.json())
      .then((data) => {
        setConcomitants(data.concomitants || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading concomitant analysis...</div>;

  const srpItems = concomitants.filter((c) => c.is_srp);
  const commonItems = concomitants.filter((c) => !c.is_srp);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Concomitant Detector (Module #134)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Kent’s most important rule: “<strong>The concomitants decide the case.</strong>”
          This panel automatically detects symptoms that accompany the chief complaint
          and scores each by SRP potential. A concomitant that is odd, unexpected, or
          highly specific (e.g. “must have ice on head during headache”) is worth more
          than the chief complaint itself. The panel separates <em>SRP concomitants</em>
          (the case-deciders) from <em>common accompanying symptoms</em> (background noise).
          You weight the SRP ones heavily and add them to repertorization first.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-purple-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-purple-800">🌟 SRP Concomitants (Weight These)</h3>
          <div className="space-y-2">
            {srpItems.map((c, i) => (
              <div key={i} className="border-b pb-2 last:border-0">
                <div className="flex justify-between">
                  <span className="font-medium">{c.symptom}</span>
                  <span className="text-purple-600 font-bold">SRP {(c.srp_score * 100).toFixed(0)}%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {c.chapter} · Discrimination: {c.discriminative_value.toFixed(2)} ·{" "}
                  {c.associated_remedies.slice(0, 3).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-gray-600">Common Accompanying Symptoms</h3>
          <div className="space-y-2">
            {commonItems.map((c, i) => (
              <div key={i} className="border-b pb-2 last:border-0">
                <div className="flex justify-between">
                  <span className="font-medium">{c.symptom}</span>
                  <span className="text-gray-400">SRP {(c.srp_score * 100).toFixed(0)}%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {c.chapter} · {c.associated_remedies.slice(0, 3).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
