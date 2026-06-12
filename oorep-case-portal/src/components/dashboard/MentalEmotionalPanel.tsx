"use client";

/**
 * MentalEmotionalPanel.tsx
 * Dashboard panel for Mental/Emotional Prober (Module #137)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Vithoulkas: “The mental state is the most important level.” This   │
 * │ panel deep-probes mental symptoms across 23 categories: fears,     │
 * │ reactions to consolation/company/criticism, delusions, grief,      │
 * │ indignation, jealousy, restlessness. It identifies characteristic│
 * │ remedies with confidence weights. You do not get a vague “anxious”│
 * │ label — you get “fear of death with desire for company + worse     │
 * │ alone + suicidal thoughts on seeing blood” — the exact mental       │
 * │ picture that repertorizes to Aurum metallicum.                     │
 * │                                                                    │
 * │ Real-world use: Patient says “I am just stressed.” The panel      │
 * │ probes deeper: “What kind of stress? Do you fear something        │
 * │ specific? How do you react when someone tries to comfort you?      │
 * │ Do you prefer to be alone or with people when you feel bad?”     │
 * │ It surfaces: fear of death, worse from consolation, wants to be    │
 * │ alone, suicidal thoughts on seeing knives. Aurum metallicum #1.    │
 * │ You would have missed this with a superficial “anxiety” label.     │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface MentalSymptom {
  category: string;
  symptom: string;
  confidence: number;
  suggested_remedies: string[];
  is_characteristic: boolean;
}

interface MentalProfile {
  overall_dominant_remedy: string;
  categories_covered: number;
  total_categories: number;
  srp_mental_symptoms: number;
  symptoms: MentalSymptom[];
}

export default function MentalEmotionalPanel() {
  const [profile, setProfile] = useState<MentalProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/mental-emotional")
      .then((r) => r.json())
      .then((data) => {
        setProfile(data.profile || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading mental/emotional profile...</div>;

  const srpSymptoms = profile?.symptoms.filter((s) => s.is_characteristic) || [];
  const regularSymptoms = profile?.symptoms.filter((s) => !s.is_characteristic) || [];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Mental/Emotional Prober (Module #137)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Vithoulkas: “<strong>The mental state is the most important level.</strong>” This panel
          deep-probes across 23 mental categories: fears, consolation reactions, company
          preferences, criticism reactions, delusions, grief, indignation, jealousy,
          restlessness. It does not give you a vague “anxious” label — it surfaces the
          <strong>exact mental picture</strong>: “fear of death + worse from consolation +
          wants to be alone + suicidal thoughts on seeing blood.” That picture
          repertorizes directly to Aurum metallicum. Without this deep probe, you would
          miss the characteristic mental symptom and prescribe a superficial match.
        </p>
      </div>

      {profile && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-sm text-gray-600">Dominant Mental Remedy</div>
              <div className="text-xl font-bold">{profile.overall_dominant_remedy}</div>
            </div>
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Categories Covered</div>
              <div className="text-xl font-bold">
                {profile.categories_covered}/{profile.total_categories}
              </div>
            </div>
            <div className="bg-green-50 p-3 rounded">
              <div className="text-sm text-gray-600">SRP Mental Symptoms</div>
              <div className="text-xl font-bold">{profile.srp_mental_symptoms}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-purple-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2 text-purple-800">🌟 Characteristic Mental Symptoms</h3>
              <div className="space-y-2">
                {srpSymptoms.map((s, i) => (
                  <div key={i} className="border-b pb-2 last:border-0">
                    <div className="flex justify-between">
                      <span className="font-medium">{s.symptom}</span>
                      <span className="text-purple-600 font-bold">{(s.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {s.category} · {s.suggested_remedies.slice(0, 3).join(", ")}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2 text-gray-600">Additional Mental Notes</h3>
              <div className="space-y-2">
                {regularSymptoms.map((s, i) => (
                  <div key={i} className="border-b pb-2 last:border-0">
                    <div className="flex justify-between">
                      <span>{s.symptom}</span>
                      <span className="text-gray-400">{(s.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="text-xs text-gray-500">{s.category}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
