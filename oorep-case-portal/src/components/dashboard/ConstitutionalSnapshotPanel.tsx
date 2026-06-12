"use client";

/**
 * ConstitutionalSnapshotPanel.tsx
 * Dashboard panel for Constitutional Snapshot (Module #139)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Every patient has a constitutional type — the remedy that matches  │
 * │ their baseline across all conditions. This panel compares the      │
 * │ case against 12 classical constitutional archetypes (Pulsatilla,     │
 * │ Nux-vomica, Arsenicum, Sulphur, Medorrhinum, Thuja, Aurum,         │
 * │ Calcarea-phos, Calcarea, Lycopodium, Natrum-mur, Silica) and       │
 * │ scores the match. It then separates constitutional remedy from      │
 * │ acute remedy: “This patient is constitutionally Pulsatilla, but      │
 * │ acutely needs Belladonna for this headache.” You treat the acute   │
 * │ and address the constitutional layer in follow-up.                  │
 * │                                                                    │
 * │ Real-world use: The snapshot says: 78% Pulsatilla, 45% Sulphur,   │
 * │ 32% Arsenicum. Constitutional diagnosis: Pulsatilla. The acute    │
 * │ complaint (throbbing right-sided headache, worse heat) points to   │
 * │ Belladonna. You prescribe Belladonna 30C now, and note for       │
 * │ follow-up: consider Pulsatilla LM for the constitutional layer.    │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface ArchetypeMatch {
  remedy: string;
  match_score: number;
  matching_generals: string[];
  matching_mentals: string[];
  key_differentiator: string;
}

interface ConstitutionalProfile {
  constitutional_remedy: string;
  constitutional_score: number;
  acute_remedy: string | null;
  acute_score: number;
  stability_index: number;
  archetypes: ArchetypeMatch[];
  interpretation: string;
}

export default function ConstitutionalSnapshotPanel() {
  const [profile, setProfile] = useState<ConstitutionalProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/constitutional-snapshot")
      .then((r) => r.json())
      .then((data) => {
        setProfile(data.profile || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading constitutional snapshot...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Constitutional Snapshot (Module #139)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Every patient has a <strong>constitutional type</strong> — the remedy that matches
          their baseline across all acute episodes. This panel compares the case against 12
          classical archetypes (Pulsatilla, Nux-vomica, Arsenicum, Sulphur, Medorrhinum,
          Thuja, Aurum, Calcarea, Lycopodium, Natrum-mur, Silica) and scores each match. It
          then <strong>separates constitutional from acute</strong>: “Constitutionally
          Pulsatilla, but acutely Belladonna for this headache.” You treat the acute now
          and address the constitutional layer in follow-up — the classical layered approach
          that prevents relapse.
        </p>
      </div>

      {profile && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Constitutional</div>
              <div className="text-xl font-bold">{profile.constitutional_remedy}</div>
              <div className="text-xs text-gray-500">Score: {(profile.constitutional_score * 100).toFixed(0)}%</div>
            </div>
            <div className="bg-green-50 p-3 rounded">
              <div className="text-sm text-gray-600">Acute Remedy</div>
              <div className="text-xl font-bold">{profile.acute_remedy || "Not determined"}</div>
              <div className="text-xs text-gray-500">Score: {(profile.acute_score * 100).toFixed(0)}%</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-sm text-gray-600">Stability Index</div>
              <div className="text-xl font-bold">{(profile.stability_index * 100).toFixed(0)}%</div>
              <div className="text-xs text-gray-500">How clear is the picture?</div>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 mb-6">
            <div className="text-sm font-semibold text-yellow-800 mb-1">💡 Interpretation</div>
            <div className="text-sm text-gray-700">{profile.interpretation}</div>
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold">Archetype Matches</h3>
            {profile.archetypes.map((a, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-24 text-sm font-bold">{a.remedy}</div>
                <div className="flex-1 h-2 bg-gray-100 rounded-full">
                  <div
                    className="h-2 bg-blue-500 rounded-full"
                    style={{ width: `${a.match_score * 100}%` }}
                  />
                </div>
                <div className="w-16 text-sm text-right">{(a.match_score * 100).toFixed(0)}%</div>
                <div className="w-48 text-xs text-gray-500 truncate">{a.key_differentiator}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
