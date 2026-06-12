"use client";

/**
 * DiscriminantRubricPanel.tsx
 * Dashboard panel for Discriminant Rubric Selector (Module #121)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ You have 3 top remedies tied at similar scores. What do you ask    │
 * │ the patient next to break the tie? This panel reverse-engineers the │
 * │ questions: it finds rubrics where the top remedies DIFFER most,    │
 * │ ranks them by expected information gain, and tells you the exact  │
 * │ question to ask. Instead of guessing, you ask the mathematically  │
 * │ optimal next question every time.                                  │
 * │                                                                    │
 * │ Real-world use: Pulsatilla, Sulphur, and Arsenicum are tied. This  │
 * │ panel says: “Ask about thermal state — Puls. is warm-blooded,      │
 * │ Ars. is chilly, Sulph. is hot. This one question has 2.3 bits of  │
 * │ information gain and will break the tie 80% of the time.”          │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface DifferentialItem {
  rubric: string;
  entropy_reduction: number;
  information_gain: number;
  candidate_counts: Record<string, number>;
  recommended_question: string;
  expected_posterior_variance: number;
}

export default function DiscriminantRubricPanel() {
  const [items, setItems] = useState<DifferentialItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/discriminant-rubrics")
      .then((r) => r.json())
      .then((data) => {
        setItems(data.discriminating_rubrics || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading discriminant analysis...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Discriminant Rubric Selector (Module #121)</h2>
        <p className="text-sm text-gray-600 mt-1">
          When your top 3 remedies are separated by only 1–2 points, the case is
          unresolved. This panel <strong>reverse-engineers the optimal next question</strong>.
          It finds rubrics where the leading candidates differ maximally, ranks them by
          expected information gain (in bits), and gives you the <em>exact question to ask</em>.
          Instead of fishing for more symptoms, you ask the one question that mathematically
          breaks the tie with the highest probability. This is 20-questions applied to
          homeopathic differential diagnosis.
        </p>
      </div>

      <div className="space-y-3">
        {items.slice(0, 8).map((item, i) => (
          <div key={i} className="border rounded-lg p-4 hover:shadow-md transition">
            <div className="flex items-start gap-3">
              <div className="shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                {i + 1}
              </div>
              <div className="flex-1">
                <div className="font-semibold text-gray-900">{item.rubric}</div>
                <div className="text-sm text-blue-700 mt-1 font-medium">
                  → {item.recommended_question}
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <span>IG: {item.information_gain.toFixed(2)} bits</span>
                  <span>Entropy ↓: {item.entropy_reduction.toFixed(2)}</span>
                  <span>Variance: {item.expected_posterior_variance.toFixed(3)}</span>
                </div>
                <div className="flex gap-2 mt-2">
                  {Object.entries(item.candidate_counts).map(([rem, count]) => (
                    <span key={rem} className="text-xs px-2 py-1 bg-gray-100 rounded">
                      {rem}: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
