"use client";

/**
 * CVWeightLearningPanel.tsx
 * Dashboard panel for CV Symptom Weight Learning (Module #116)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ How do you know your rubric weights (1, 2, 3, 4) are “right”?    │
 * │ This panel cross-validates them: it hides part of your case,       │
 * │ learns weights on the remainder, and tests whether the hidden part  │
 * │ still points to the right remedy. If 3-fold CV says weight 3.5   │
 * │ is better than 4.0 for “fear of death,” that is the weight you use. │
 * │ This removes practitioner bias in weight assignment and replaces  │
 * │ it with statistical evidence from your own case outcomes.            │
 * │                                                                    │
 * │ Real-world use: After 50 confirmed cases, run this module. It      │
 * │ discovers that “worse from cold” should weight 4.2 (not 3) in      │
 * │ your practice because it discriminates better in your patient      │
 * │ population.                                                        │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface WeightResult {
  axis: string;
  direction: string;
  base_weight: number;
  learned_weight: number;
  improvement: number;
  ci_lower: number;
  ci_upper: number;
}

interface CVSummary {
  fold_scores: number[];
  mean_score: number;
  std_score: number;
  best_params: Record<string, number>;
}

export default function CVWeightLearningPanel() {
  const [weights, setWeights] = useState<WeightResult[]>([]);
  const [summary, setSummary] = useState<CVSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/cv-weights")
      .then((r) => r.json())
      .then((data) => {
        setWeights(data.weights || []);
        setSummary(data.summary || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading CV weight learning...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Cross-Validated Symptom Weight Learning (Module #116)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Cross-validation is the gold standard for validating any prediction model. This
          module hides part of each historical case, learns optimal rubric weights from the
          visible part, and tests whether those weights still recover the correct remedy on
          the hidden part. If “fear of death” consistently needs weight 4.2 (not 3) in your
          practice, this panel discovers it — replacing subjective weight assignment with
          statistical evidence from your own confirmed outcomes.
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Mean CV Score</div>
            <div className="text-2xl font-bold">{summary.mean_score.toFixed(3)}</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Std. Deviation</div>
            <div className="text-2xl font-bold">{summary.std_score.toFixed(3)}</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Parameters Tuned</div>
            <div className="text-2xl font-bold">{Object.keys(summary.best_params).length}</div>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Axis / Direction</th>
              <th className="p-2 text-left">Base Weight</th>
              <th className="p-2 text-left">Learned Weight</th>
              <th className="p-2 text-left">Improvement</th>
              <th className="p-2 text-left">95% CI</th>
            </tr>
          </thead>
          <tbody>
            {weights.map((w, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                <td className="p-2 font-medium">
                  {w.axis} — {w.direction}
                </td>
                <td className="p-2">{w.base_weight.toFixed(1)}</td>
                <td className="p-2 font-semibold text-blue-600">{w.learned_weight.toFixed(1)}</td>
                <td className="p-2">
                  <span className={w.improvement > 0 ? "text-green-600" : "text-red-500"}>
                    {w.improvement > 0 ? "+" : ""}
                    {w.improvement.toFixed(2)}
                  </span>
                </td>
                <td className="p-2 text-xs text-gray-500">
                  [{w.ci_lower.toFixed(1)}, {w.ci_upper.toFixed(1)}]
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> After you have 30–50 confirmed cases, run this module.
        It learns the weights that maximize recovery of the correct remedy on held-out data.
        The 95% confidence interval tells you whether the improvement is real (CI excludes
        zero) or noise (CI overlaps zero). Apply the learned weights as your new default
        rubric scoring in the repertorization engine.
      </div>
    </div>
  );
}
