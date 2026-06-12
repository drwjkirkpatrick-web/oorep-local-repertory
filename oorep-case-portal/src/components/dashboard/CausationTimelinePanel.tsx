"use client";

/**
 * CausationTimelinePanel.tsx
 * Dashboard panel for Causation & Timeline (Module #136)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Hahnemann taught: find the cause. This panel identifies “ailments   │
 * │ from” etiology — grief, anger, cold dry wind, vaccination, head      │
 * │ injury, suppressed menses, never been well since... — and maps them│
 * │ to the classical remedies known for each cause. It also builds a  │
 * │ chronological timeline and scores miasmatic affinity (Psora,     │
 * │ Sycosis, Syphilis, Tubercular). The timeline reveals suppressed   │
 * │ layers: antibiotics at age 5, steroids at 12, now autoimmune at 30.│
 * │                                                                    │
 * │ Real-world use: Patient says “I was never the same after my        │
 * │ father’s death.” The panel flags: “Ailment from grief” → Ignatia,  │
 * │ Natrum-mur, Phosphoric-acid. Timeline shows: grief (age 28) →     │
 * │ anxiety (30) → insomnia (32) → chronic fatigue (35). Miasm:        │
 * │ Psora-dominant with Syphilitic tinge. You prescribe Natrum-mur,    │
 * │ understanding the full causal chain.                               │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface TimelineEvent {
  age: number | null;
  event: string;
  etiology_type: string;
  suggested_remedies: string[];
  miasm_hint: string;
}

interface CausationSummary {
  never_been_well_since: string | null;
  dominant_miasm: string;
  miasm_scores: Record<string, number>;
  timeline_events: TimelineEvent[];
}

export default function CausationTimelinePanel() {
  const [summary, setSummary] = useState<CausationSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/causation-timeline")
      .then((r) => r.json())
      .then((data) => {
        setSummary(data.summary || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading causation analysis...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Causation & Timeline (Module #136)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Hahnemann’s first rule: find the <strong>cause</strong>. This panel identifies
          “ailments from” etiology from patient narrative — grief, anger, cold dry wind,
          vaccination, head injury, suppressed menses, “never been well since...” — and maps
          each to the classical remedies known for that cause. It builds a <strong>chronological
          timeline</strong> revealing suppression chains (antibiotics at 5, steroids at 12,
          autoimmune at 30) and scores <strong>miasmatic affinity</strong> (Psora, Sycosis,
          Syphilis, Tubercular). The cause, the timeline, and the miasm together give the
          deepest layer of the case.
        </p>
      </div>

      {summary && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Dominant Miasm</div>
              <div className="text-xl font-bold">{summary.dominant_miasm}</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-sm text-gray-600">Timeline Events</div>
              <div className="text-xl font-bold">{summary.timeline_events.length}</div>
            </div>
            <div className="bg-yellow-50 p-3 rounded">
              <div className="text-sm text-gray-600">Never Well Since</div>
              <div className="text-sm font-bold">{summary.never_been_well_since || "None detected"}</div>
            </div>
          </div>

          <div className="mb-4">
            <h3 className="font-semibold mb-2">Miasm Scores</h3>
            <div className="flex gap-4">
              {Object.entries(summary.miasm_scores).map(([miasm, score]) => (
                <div key={miasm} className="flex-1">
                  <div className="text-sm text-center mb-1">{miasm}</div>
                  <div className="h-24 bg-gray-100 rounded relative">
                    <div
                      className="absolute bottom-0 left-0 right-0 bg-blue-500 rounded-b"
                      style={{ height: `${score * 100}%` }}
                    />
                  </div>
                  <div className="text-center text-sm font-bold mt-1">{(score * 100).toFixed(0)}%</div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold">Chronological Timeline</h3>
            {summary.timeline_events.map((event, i) => (
              <div key={i} className="flex gap-4 border-l-2 border-blue-300 pl-4">
                <div className="shrink-0 w-16 text-sm font-bold text-blue-600">
                  {event.age ? `Age ${event.age}` : "Unknown"}
                </div>
                <div className="flex-1 pb-4">
                  <div className="font-medium">{event.event}</div>
                  <div className="text-xs text-gray-500">Type: {event.etiology_type}</div>
                  <div className="text-xs text-gray-500">Miasm hint: {event.miasm_hint}</div>
                  <div className="text-xs text-blue-600 mt-1">Remedies: {event.suggested_remedies.join(", ")}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
