"use client";

/**
 * ThompsonSamplingPanel.tsx
 * Dashboard panel for Bayesian Remedy Ranking with Thompson Sampling (Module #111)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ When a remedy has only been used 3 times and scored well, is it    │
 * │ a hidden gem or a fluke? Thompson Sampling answers this using      │
 * │ Bayesian beta distributions. Remedies with fewer trials get        │
 * │ “exploration bonus” — they are tested more to see if they are      │
 * │ truly good. Remedies with many trials get “exploitation” — if      │
 * │ they consistently work, they are ranked higher. The result is a      │
 * │ ranking that discovers hidden effective remedies while trusting    │
 * │ proven ones.                                                       │
 * │                                                                    │
 * │ Real-world use: Calcarea-silicate has only 5 uses in your         │
 * │ practice but 4 successes (80%). Pulsatilla has 50 uses with 35     │
 * │ successes (70%). Thompson Sampling gives Calc-sil. a higher        │
 * │ exploration-adjusted score because it may be under-discovered.     │
 * │ You try it on the next similar case and confirm it is a hidden gem.  │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from 'react';

interface ThompsonScore {
  remedy: string;
  thompson_score: number;
  uncertainty: number;
  alpha: number;
  beta: number;
  observations: number;
  posterior_mean: number;
}

interface LearningStats {
  total_observations: number;
  remedies_with_data: number;
  avg_outcome_global: number;
  remedy_counts: Record<string, { n: number; avg_score: number }>;
}

export default function ThompsonSamplingPanel() {
  const [scores, setScores] = useState<ThompsonScore[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch from API
    fetch('/api/bayesian-ranking')
      .then(r => r.json())
      .then(data => {
        setScores(data.scores || []);
        setStats(data.stats || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading Thompson Sampling...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Thompson Sampling (Module #111)</h2>
      
      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Total Observations</div>
            <div className="text-2xl font-bold">{stats.total_observations}</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Remedies with Data</div>
            <div className="text-2xl font-bold">{stats.remedies_with_data}</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Avg Outcome</div>
            <div className="text-2xl font-bold">{(stats.avg_outcome_global * 100).toFixed(1)}%</div>
          </div>
        </div>
      )}

      {/* Thompson Scores Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Remedy</th>
              <th className="p-2 text-left">Thompson Score</th>
              <th className="p-2 text-left">Uncertainty</th>
              <th className="p-2 text-left">Observations</th>
              <th className="p-2 text-left">Posterior Mean</th>
              <th className="p-2 text-left">α/β</th>
            </tr>
          </thead>
          <tbody>
            {scores.map((score, i) => (
              <tr key={score.remedy} className={i % 2 === 0 ? 'bg-gray-50' : ''}>
                <td className="p-2 font-medium">{score.remedy}</td>
                <td className="p-2">
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${score.thompson_score * 100}%` }}
                      />
                    </div>
                    {score.thompson_score.toFixed(3)}
                  </div>
                </td>
                <td className="p-2 text-orange-600">±{score.uncertainty.toFixed(3)}</td>
                <td className="p-2">{score.observations}</td>
                <td className="p-2">{(score.posterior_mean * 100).toFixed(1)}%</td>
                <td className="p-2 text-xs text-gray-500">{score.alpha.toFixed(1)}/{score.beta.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        <p>Bayesian bandit optimization: remedies with fewer observations get higher exploration weight.</p>
      </div>
    </div>
  );
}
