"use client";

/**
 * RubricDiscriminationPanel.tsx
 * Dashboard panel for Rubric Discrimination Indices (Module #114)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Why did a great rubric drop to 5th place? This panel tells you.   │
 * │ It measures how well each rubric separates a “true” remedy from   │
 * │ the rest — using the same statistics educational tests use (KR-20   │
 * │ reliability). If a rubric has low discrimination, you know it's    │
 * │ adding noise, not signal. You can then weight it down or drop it. │
 * │                                                                    │
 * │ Real-world use: If “headache > Pulsatilla” keeps appearing in your │
 * │ top 3 but never the right remedy, this panel flags it as a noisy  │
 * │ distractor and suggests higher-discrimination alternatives.        │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface DiscriminationItem {
  rubric: string;
  item_total_correlation: number;
  point_biserial: number;
  pass_rate: number;
  n_with_symptom: number;
  n_without: number;
}

interface ReliabilityStats {
  kr20_coefficient: number;
  scale_mean: number;
  scale_sd: number;
  n_items: number;
  n_cases: number;
}

export default function RubricDiscriminationPanel() {
  const [items, setItems] = useState<DiscriminationItem[]>([]);
  const [stats, setStats] = useState<ReliabilityStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/rubric-discrimination")
      .then((r) => r.json())
      .then((data) => {
        setItems(data.items || []);
        setStats(data.stats || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading discrimination analysis...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Rubric Discrimination Indices (Module #114)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Which rubrics actually separate the right remedy from the rest? Like a test-item
          that good students get right and bad students get wrong — a rubric with high
          discrimination appears in cases that eventually confirm the remedy, and rarely
          in cases that miss it. Low-discrimination rubrics add noise; this panel flags
          them so you can weight them down or drop them from your analysis.
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">KR-20 Reliability</div>
            <div className="text-2xl font-bold">{stats.kr20_coefficient.toFixed(2)}</div>
            <div className="text-xs text-gray-500">≥ 0.70 = trustworthy scale</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Rubrics Analyzed</div>
            <div className="text-2xl font-bold">{stats.n_items}</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Historical Cases</div>
            <div className="text-2xl font-bold">{stats.n_cases}</div>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Rubric</th>
              <th className="p-2 text-left">Discrimination</th>
              <th className="p-2 text-left">Point-Biserial</th>
              <th className="p-2 text-left">Pass Rate</th>
              <th className="p-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => {
              const disc = item.item_total_correlation;
              let status = "Acceptable";
              let statusColor = "text-green-600";
              if (disc > 0.4) { status = "Excellent"; statusColor = "text-blue-600"; }
              else if (disc < 0.1) { status = "Weak — consider removing"; statusColor = "text-red-500"; }
              else if (disc < 0.2) { status = "Marginal"; statusColor = "text-amber-600"; }
              return (
                <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                  <td className="p-2 font-medium">{item.rubric}</td>
                  <td className="p-2">
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.min(disc * 200, 100)}%` }} />
                      </div>
                      {disc.toFixed(3)}
                    </div>
                  </td>
                  <td className="p-2">{item.point_biserial.toFixed(3)}</td>
                  <td className="p-2">{(item.pass_rate * 100).toFixed(1)}%</td>
                  <td className={`p-2 font-medium ${statusColor}`}>{status}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> Rubrics with <em>excellent</em> discrimination are your
        anchors — they separate confirmed cases from misses. <em>Marginal</em> rubrics may be
        too common (everyone has them) or too rare (only 1 case). <em>Weak</em> rubrics
        actively mislead the repertorization; consider down-weighting them. This is the same
        quality-control technique standardized educational tests use (KR-20 reliability).
      </div>
    </div>
  );
}
