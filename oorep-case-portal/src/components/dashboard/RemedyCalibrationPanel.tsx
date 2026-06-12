"use client";

/**
 * RemedyCalibrationPanel.tsx
 * Dashboard panel for Remedy Confidence Calibration (Module #130)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ A repertorization score of 20 “feels” strong, but is it really 90% │
 * │ likely to be correct? This panel calibrates raw scores into true   │
 * │ probabilities using Platt scaling (logistic regression on historical│
 * │ outcomes) and isotonic regression (PAVA — monotonic calibration).  │
 * │ It tells you: “Score 20 → 73% probability. Score 15 → 45%. Score   │
 * │ 8 → 12%.” No more gut-feeling prescriptions — you know the exact    │
 * │ calibrated confidence before you prescribe.                      │
 * │                                                                    │
 * │ Real-world use: You see Pulsatilla at score 18. The panel says:   │
 * │ “Calibrated probability: 68%. Historical calibration curve shows   │
 * │ you tend to overestimate at this score (predicted 85%, actual 68%).│
 * │ Consider a second-look or confirmatory Materia Medica check.”      │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface CalibrationPoint {
  bin_midpoint: number;
  predicted_prob: number;
  observed_freq: number;
  n_cases: number;
  calibrated_prob: number;
}

interface CalibrationSummary {
  brier_score: number;
  reliability: number;
  resolution: number;
  n_bins: number;
  method: string;
}

export default function RemedyCalibrationPanel() {
  const [points, setPoints] = useState<CalibrationPoint[]>([]);
  const [summary, setSummary] = useState<CalibrationSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/remedy-calibration")
      .then((r) => r.json())
      .then((data) => {
        setPoints(data.calibration_points || []);
        setSummary(data.summary || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading calibration data...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Remedy Confidence Calibration (Module #130)</h2>
        <p className="text-sm text-gray-600 mt-1">
          A repertorization score of 20 “feels” strong, but what is the <strong>actual</strong>
          probability it is correct? This panel <strong>calibrates raw scores into true
          probabilities</strong> using two gold-standard methods: <em>Platt scaling</em>
          (logistic regression on your historical outcomes) and <em>isotonic regression</em>
          (PAVA — pool-adjacent-violators algorithm for monotonic calibration). It tells you:
          “Score 20 → 73% probability. Score 15 → 45%. Score 8 → 12%.” No more gut-feeling
          prescriptions — you know the exact calibrated confidence before you decide.
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Brier Score</div>
            <div className="text-2xl font-bold">{summary.brier_score.toFixed(3)}</div>
            <div className="text-xs text-gray-500">Lower = better calibrated</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Reliability</div>
            <div className="text-2xl font-bold">{summary.reliability.toFixed(3)}</div>
            <div className="text-xs text-gray-500">Predicted ≈ Observed?</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Resolution</div>
            <div className="text-2xl font-bold">{summary.resolution.toFixed(3)}</div>
            <div className="text-xs text-gray-500">Can it distinguish outcomes?</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">Method</div>
            <div className="text-xl font-bold">{summary.method}</div>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Score Bin</th>
              <th className="p-2 text-left">Predicted Probability</th>
              <th className="p-2 text-left">Observed Frequency</th>
              <th className="p-2 text-left">Calibrated Probability</th>
              <th className="p-2 text-left">Cases in Bin</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p, i) => {
              const bias = p.predicted_prob - p.observed_freq;
              const biasColor = Math.abs(bias) < 0.05 ? "text-green-600" : Math.abs(bias) < 0.15 ? "text-yellow-600" : "text-red-500";
              return (
                <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                  <td className="p-2 font-medium">{p.bin_midpoint.toFixed(1)}</td>
                  <td className="p-2">{(p.predicted_prob * 100).toFixed(1)}%</td>
                  <td className="p-2">{(p.observed_freq * 100).toFixed(1)}%</td>
                  <td className={`p-2 font-bold ${biasColor}`}>{(p.calibrated_prob * 100).toFixed(1)}%</td>
                  <td className="p-2">{p.n_cases}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> The Brier score measures calibration quality
        (lower = better). A Brier of 0.15 means your predictions are reasonably well-calibrated.
        If the predicted probability is consistently higher than observed (overconfidence),
        the panel will adjust downward. Use the calibrated probability, not the raw score, as
        your confidence threshold for prescribing. Many practitioners set a calibrated
        threshold of 70% before finalizing a prescription.
      </div>
    </div>
  );
}
