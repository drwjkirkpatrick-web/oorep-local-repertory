"use client";

/**
 * PropensityScoredPanel.tsx
 * Dashboard panel for Propensity-Scored Outcome Prediction (Module #113)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Not all cases are equally difficult. A remedy prescribed 50 times   │
 * │ to easy acute cases will look better than one prescribed 20 times │
 * │ to complex chronic cases. This panel corrects that bias using        │
 * │ Inverse Probability Weighting (IPW) — a technique from epidemiology  │
 * │ that makes “apples-to-apples” comparisons. The result: remedies     │
 * │ are ranked by their true effectiveness, not by how easy their      │
 * │ patients were.                                                     │
 * │                                                                    │
 * │ Real-world use: Pulsatilla shows 85% raw success rate. But the IPW  │
 * │ panel reveals it was mostly prescribed to simple acute cases.     │
 * │ After adjusting for case difficulty, its true effectiveness is 67%.│
 * │ Meanwhile, Medorrhinum shows 60% raw but 72% adjusted — it was     │
 * │ prescribed to harder cases and performed better than it looks.     │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from 'react';

interface IPWPrediction {
  remedy: string;
  ipw_outcome: number | null;
  raw_outcome: number | null;
  propensity_score: number;
  n_observations: number;
  adjustment_factor: number;
}

interface BalanceStats {
  chronicity?: { overall_mean: number; max_smd: number };
  severity?: { overall_mean: number; max_smd: number };
  complexity?: { overall_mean: number; max_smd: number };
}

export default function PropensityScoredPanel() {
  const [predictions, setPredictions] = useState<IPWPrediction[]>([]);
  const [balance, setBalance] = useState<BalanceStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/propensity-prediction')
      .then(r => r.json())
      .then(data => {
        setPredictions(data.predictions || []);
        setBalance(data.balance || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading IPW Predictions...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Propensity-Scored Prediction (Module #113)</h2>

      {/* Balance Check */}
      {balance && (
        <div className="mb-6 p-3 bg-yellow-50 rounded">
          <h3 className="font-semibold mb-2 text-sm">Covariate Balance Check</h3>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {Object.entries(balance).map(([feature, stats]) => (
              <div key={feature} className={`p-2 rounded ${(stats.max_smd || 0) < 0.1 ? 'bg-green-100' : 'bg-red-100'}`}>
                <div className="font-medium capitalize">{feature}</div>
                <div>Max SMD: {(stats.max_smd || 0).toFixed(3)}</div>
                <div className="text-xs">{(stats.max_smd || 0) < 0.1 ? '✓ Balanced' : '✗ Imbalanced'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Predictions Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Remedy</th>
              <th className="p-2 text-left">IPW Outcome</th>
              <th className="p-2 text-left">Raw Outcome</th>
              <th className="p-2 text-left">Propensity</th>
              <th className="p-2 text-left">Adjustment</th>
              <th className="p-2 text-left">N</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((pred) => (
              <tr key={pred.remedy} className="border-b">
                <td className="p-2 font-medium">{pred.remedy}</td>
                <td className="p-2">
                  {pred.ipw_outcome !== null ? (
                    <span className="font-bold text-blue-600">{(pred.ipw_outcome * 100).toFixed(1)}%</span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="p-2">
                  {pred.raw_outcome !== null ? (
                    <span>{(pred.raw_outcome * 100).toFixed(1)}%</span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="p-2">{(pred.propensity_score * 100).toFixed(1)}%</td>
                <td className="p-2">
                  <span className={pred.adjustment_factor > 1 ? 'text-green-600' : 'text-red-600'}>
                    {pred.adjustment_factor.toFixed(2)}x
                  </span>
                </td>
                <td className="p-2">{pred.n_observations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        <p>Inverse Probability Weighting corrects for selection bias. Remedies prescribed to easier cases get adjusted scores.</p>
      </div>
    </div>
  );
}
