"use client";

/**
 * GeneralsSurveyPanel.tsx
 * Dashboard panel for Generals Survey (Module #138)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ “Generals” are the whole-person symptoms — thermal state, sleep     │
 * │ position, food cravings, dreams, weather preference, energy, side  │
 * │ affinity. They carry enormous constitutional weight because they    │
 * │ describe the patient’s baseline, not just the acute complaint.    │
 * │ This panel captures 40+ general categories and maps them to        │
 * │ characteristic remedies. A “warm-blooded, craves salt, sleeps on   │
 * │ left side, dreams of fire” patient is unmistakably Pulsatilla —    │
 * │ even before you repertorize a single rubric.                       │
 * │                                                                    │
 * │ Real-world use: Patient says “I am always cold, love salt, and      │
 * │ sleep curled up on my left side.” The panel instantly flags:      │
 * │ chilly → Calcarea, Arsenicum, Nux-vomica. Craves salt → Natrum-mur, │
 * │ Phosphorus. Left side → Pulsatilla, Lachesis. Dreams of fire →     │
 * │ Sulphur, Phosphorus. The intersection: Natrum-mur rises because it   │
 * │ hits the most generals. You now have a constitutional direction     │
 * │ before opening the repertory.                                      │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface GeneralItem {
  category: string;
  value: string;
  remedy_hints: string[];
  constitutional_weight: number;
}

interface GeneralsProfile {
  thermal_state: string;
  sleep_position: string;
  food_cravings: string[];
  food_aversions: string[];
  dream_themes: string[];
  weather_preference: string;
  energy_pattern: string;
  side_affinity: string;
  items: GeneralItem[];
}

export default function GeneralsSurveyPanel() {
  const [profile, setProfile] = useState<GeneralsProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/generals-survey")
      .then((r) => r.json())
      .then((data) => {
        setProfile(data.profile || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading generals survey...</div>;

  const topItems = profile?.items
    .sort((a, b) => b.constitutional_weight - a.constitutional_weight)
    .slice(0, 8) || [];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Generals Survey (Module #138)</h2>
        <p className="text-sm text-gray-600 mt-1">
          <strong>Generals</strong> are the whole-person symptoms that describe the patient’s
          constitutional baseline — not just the acute complaint. Thermal state, sleep
          position, food cravings, dreams, weather preference, energy pattern, side
          affinity. These carry enormous weight because they persist across all acute
          episodes. This panel captures 40+ general categories and maps each to
          characteristic remedies. A “warm-blooded, craves salt, sleeps left side, dreams of
          fire” patient is unmistakably Pulsatilla <em>even before you open the repertory</em>.
          The generals give you constitutional direction; the particulars confirm it.
        </p>
      </div>

      {profile && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-6">
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Thermal State</div>
              <div className="text-lg font-bold">{profile.thermal_state}</div>
            </div>
            <div className="bg-green-50 p-3 rounded">
              <div className="text-sm text-gray-600">Sleep Position</div>
              <div className="text-lg font-bold">{profile.sleep_position}</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-sm text-gray-600">Weather</div>
              <div className="text-lg font-bold">{profile.weather_preference}</div>
            </div>
            <div className="bg-yellow-50 p-3 rounded">
              <div className="text-sm text-gray-600">Side Affinity</div>
              <div className="text-lg font-bold">{profile.side_affinity}</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm font-semibold mb-2">Food Cravings</div>
              <div className="flex flex-wrap gap-1">
                {profile.food_cravings.map((c, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">{c}</span>
                ))}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm font-semibold mb-2">Food Aversions</div>
              <div className="flex flex-wrap gap-1">
                {profile.food_aversions.map((a, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">{a}</span>
                ))}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm font-semibold mb-2">Dream Themes</div>
              <div className="flex flex-wrap gap-1">
                {profile.dream_themes.map((d, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">{d}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold">Top Constitutional Indicators</h3>
            {topItems.map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-40 text-sm font-medium">{item.category}: {item.value}</div>
                <div className="flex-1 h-2 bg-gray-100 rounded-full">
                  <div
                    className="h-2 bg-blue-500 rounded-full"
                    style={{ width: `${Math.min(item.constitutional_weight * 100, 100)}%` }}
                  />
                </div>
                <div className="w-32 text-xs text-right">
                  {item.remedy_hints.slice(0, 3).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
