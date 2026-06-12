"use client";

/**
 * GaussianProcessPanel.tsx
 * Dashboard panel for Gaussian Process Surrogate (Module #118)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ You have 20 rubrics. Which 3 should you ask next? This panel      │
 * │ builds a Gaussian Process surrogate — a smooth surface over the   │
 * │ “remedy possibility space” — and identifies regions of high       │
 * │ uncertainty. Those uncertain regions are exactly where you should │
 * │ ask your next questions. It balances exploration (uncertain areas)  │
 * │ with exploitation (areas that already look promising).             │
 * │                                                                    │
 * │ Real-world use: After the chief complaint, the GP says “your case │
 * │ is well-understood for thermal state but completely uncertain for  │
 * │ mental symptoms — ask about fears and consolation next.”          │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface GPPrediction {
  remedy: string;
  mean_score: number;
  uncertainty: number;
  acquisition_ucb: number;
}

export default function GaussianProcessPanel() {
  const [predictions, setPredictions] = useState<GPPrediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/gaussian-process")
      .then((r) => r.json())
      .then((data) => {
        setPredictions(data.predictions || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading Gaussian Process surrogate...</div>;

  const topExploration = [...predictions].sort((a, b) => b.acquisition_ucb - a.acquisition_ucb).slice(0, 5);
  const topExploitation = [...predictions].sort((a, b) => b.mean_score - a.mean_score).slice(0, 5);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Gaussian Process Surrogate (Module #118)</h2>
        <p className="text-sm text-gray-600 mt-1">
          A Gaussian Process is a mathematical model that builds a smooth “possibility surface”
          over remedy space. It knows what it knows (high confidence = narrow surface) and
          what it does not know (high uncertainty = wide surface). This panel shows both:
          the <em>exploitation</em> view (which remedies already look good) and the
          <em>exploration</em> view (which symptoms are still uncertain and therefore
          the most valuable to ask next). It is the mathematical foundation of “efficient
          case-taking” — every question is chosen to maximally reduce uncertainty.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">🎯 Exploitation — Likely Remedies</h3>
          <div className="space-y-2">
            {topExploitation.map((p) => (
              <div key={p.remedy} className="flex items-center gap-3">
                <div className="w-20 text-sm font-bold">{p.remedy}</div>
                <div className="flex-1 h-2 bg-gray-200 rounded-full">
                  <div className="h-2 bg-green-500 rounded-full" style={{ width: `${Math.min(p.mean_score * 10, 100)}%` }} />
                </div>
                <div className="w-12 text-sm text-right">{p.mean_score.toFixed(1)}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">🔍 Exploration — Highest Uncertainty</h3>
          <div className="space-y-2">
            {topExploration.map((p) => (
              <div key={p.remedy} className="flex items-center gap-3">
                <div className="w-20 text-sm font-bold">{p.remedy}</div>
                <div className="flex-1 h-2 bg-gray-200 rounded-full">
                  <div className="h-2 bg-blue-500 rounded-full" style={{ width: `${Math.min(p.uncertainty * 100, 100)}%` }} />
                </div>
                <div className="w-12 text-sm text-right">±{p.uncertainty.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Remedy</th>
              <th className="p-2 text-left">Predicted Score</th>
              <th className="p-2 text-left">Uncertainty</th>
              <th className="p-2 text-left">UCB Acquisition</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((p, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                <td className="p-2 font-medium">{p.remedy}</td>
                <td className="p-2">{p.mean_score.toFixed(2)}</td>
                <td className="p-2 text-blue-600">±{p.uncertainty.toFixed(3)}</td>
                <td className="p-2 font-semibold">{p.acquisition_ucb.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
