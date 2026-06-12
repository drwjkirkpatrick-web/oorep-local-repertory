"use client";

/**
 * RubricBanditPanel.tsx
 * Dashboard panel for Multi-Armed Bandit Rubric Selection (Module #112)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Which rubric should you search first? This panel uses the UCB1     │
 * │ multi-armed bandit algorithm — the same math used by Netflix to    │
 * │ recommend movies — to learn which rubrics in your practice most    │
 * │ often lead to the correct remedy. It balances trying new rubrics   │
 * │ (exploration) with using rubrics that have already worked          │
 * │ (exploitation). Over time, it learns your personal “best rubric    │
 * │ repertoire” — the set of rubrics that discriminate best in your    │
 * │ patient population.                                                │
 * │                                                                    │
 * │ Real-world use: After 30 cases, the panel shows “fear of death in   │
 * │ heart disease” has a 78% success rate in your practice, while      │
 * │ “headache, location unspecified” only has 23%. You now know which   │
 * │ rubrics to prioritize when time is short.                          │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from 'react';

interface RubricUCB {
  fullpath: string;
  ucb_score: number;
  trials: number;
  successes: number;
  empirical_mean: number;
}

interface BanditStats {
  total_rubrics_tracked: number;
  total_trials: number;
  total_successes: number;
  overall_success_rate: number;
  top_performing_rubrics: Array<{
    rubric: string;
    trials: number;
    successes: number;
    rate: number;
  }>;
}

export default function RubricBanditPanel() {
  const [rubrics, setRubrics] = useState<RubricUCB[]>([]);
  const [stats, setStats] = useState<BanditStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/rubric-bandit')
      .then(r => r.json())
      .then(data => {
        setRubrics(data.selected_rubrics || []);
        setStats(data.stats || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading UCB Selection...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">UCB1 Rubric Selection (Module #112)</h2>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          <div className="bg-indigo-50 p-3 rounded text-center">
            <div className="text-2xl font-bold">{stats.total_rubrics_tracked}</div>
            <div className="text-xs text-gray-600">Rubrics Tracked</div>
          </div>
          <div className="bg-indigo-50 p-3 rounded text-center">
            <div className="text-2xl font-bold">{stats.total_trials}</div>
            <div className="text-xs text-gray-600">Total Trials</div>
          </div>
          <div className="bg-indigo-50 p-3 rounded text-center">
            <div className="text-2xl font-bold">{(stats.overall_success_rate * 100).toFixed(1)}%</div>
            <div className="text-xs text-gray-600">Success Rate</div>
          </div>
          <div className="bg-indigo-50 p-3 rounded text-center">
            <div className="text-2xl font-bold">{stats.top_performing_rubrics?.length || 0}</div>
            <div className="text-xs text-gray-600">Top Performers</div>
          </div>
        </div>
      )}

      {/* Selected Rubrics */}
      <div className="mb-6">
        <h3 className="font-semibold mb-3">Selected Rubrics (UCB Scored)</h3>
        <div className="space-y-2">
          {rubrics.map((rubric, i) => (
            <div key={rubric.fullpath} className="flex items-center justify-between bg-gray-50 p-3 rounded">
              <div className="flex-1">
                <div className="font-medium text-sm">{rubric.fullpath}</div>
                <div className="text-xs text-gray-500">
                  Trials: {rubric.trials} | Successes: {rubric.successes} | 
                  Empirical: {(rubric.empirical_mean * 100).toFixed(1)}%
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-indigo-600">{rubric.ucb_score.toFixed(3)}</div>
                <div className="text-xs text-gray-500">UCB Score</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Performers */}
      {stats?.top_performing_rubrics && stats.top_performing_rubrics.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Top Performing Rubrics</h3>
          <div className="space-y-2">
            {stats.top_performing_rubrics.slice(0, 5).map((rubric) => (
              <div key={rubric.rubric} className="flex items-center justify-between bg-green-50 p-2 rounded text-sm">
                <span>{rubric.rubric}</span>
                <span className="font-medium text-green-700">{(rubric.rate * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        <p>UCB1 balances exploration (untested rubrics) vs exploitation (proven discriminators).</p>
      </div>
    </div>
  );
}
