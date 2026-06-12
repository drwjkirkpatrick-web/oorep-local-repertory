"use client";

/**
 * SPRTPanel.tsx
 * Dashboard panel for Sequential Remedy Testing (Module #117)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Should you keep repertorizing, or do you have enough to decide?   │
 * │ This panel implements Wald’s SPRT — the same sequential test used   │
 * │ in clinical trials to stop early when the evidence is conclusive.  │
 * │ It tells you: stop now (Aremedy is clearly better), stop now (no   │
 * │ remedy is emerging), or keep going (more data needed). This         │
 * │ prevents “paralysis by analysis” — the tendency to keep adding    │
 * │ rubrics when the first 5 already decided the case.                 │
 * │                                                                    │
 * │ Real-world use: After entering 7 rubrics, this panel says “stop — │
 * │ Pulsatilla is 4× more likely than placebo, p < 0.01”. You stop    │
 * │ repertorizing and move to materia medica confirmation.              │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface SPRTRun {
  remedy: string;
  llr: number;
  llr_history: number[];
  upper_boundary: number;
  lower_boundary: number;
  status: "continue" | "accept_h1" | "accept_h0";
  n_samples: number;
}

export default function SPRTPanel() {
  const [runs, setRuns] = useState<SPRTRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/sequential-testing")
      .then((r) => r.json())
      .then((data) => {
        setRuns(data.runs || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading sequential testing...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Sequential Remedy Testing (Module #117)</h2>
        <p className="text-sm text-gray-600 mt-1">
          How many rubrics are “enough”? This panel implements Wald’s Sequential Probability
          Ratio Test — the same technique clinical trials use to stop early when evidence is
          conclusive. After each rubric, it asks: “Is this remedy clearly better than placebo
          (stop and prescribe), clearly not (stop and look elsewhere), or still ambiguous
          (keep going)?” This prevents paralysis by analysis — the common trap of adding
          rubric after rubric when the first 5 already decided the case.
        </p>
      </div>

      <div className="space-y-4">
        {runs.map((run) => {
          const statusColor =
            run.status === "accept_h1"
              ? "bg-green-50 border-green-300 text-green-800"
              : run.status === "accept_h0"
              ? "bg-red-50 border-red-300 text-red-800"
              : "bg-yellow-50 border-yellow-300 text-yellow-800";
          const statusLabel =
            run.status === "accept_h1"
              ? "✅ STOP — Remedy confirmed"
              : run.status === "accept_h0"
              ? "❌ STOP — No remedy emerging"
              : "⏳ CONTINUE — More data needed";

          return (
            <div key={run.remedy} className={`rounded-lg border p-4 ${statusColor}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-lg">{run.remedy}</span>
                <span className="text-sm font-medium">{statusLabel}</span>
              </div>

              <div className="flex items-center gap-2 text-sm mb-2">
                <span className="text-gray-600">LLR: {run.llr.toFixed(2)}</span>
                <span className="text-gray-400">|</span>
                <span className="text-gray-600">Boundaries: [{run.lower_boundary.toFixed(1)}, {run.upper_boundary.toFixed(1)}]</span>
                <span className="text-gray-400">|</span>
                <span className="text-gray-600">{run.n_samples} rubrics tested</span>
              </div>

              {/* LLR history sparkline */}
              <div className="flex items-end gap-1 h-12 mt-2">
                {run.llr_history.map((val, i) => {
                  const maxVal = Math.max(...run.llr_history.map(Math.abs), run.upper_boundary, Math.abs(run.lower_boundary));
                  const height = maxVal > 0 ? (Math.abs(val) / maxVal) * 100 : 0;
                  const isInRange = val > run.lower_boundary && val < run.upper_boundary;
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div
                        className={`w-full rounded-sm ${isInRange ? "bg-gray-300" : val > 0 ? "bg-green-400" : "bg-red-400"}`}
                        style={{ height: `${Math.max(height, 4)}%` }}
                      />
                      <span className="text-[8px] text-gray-400 mt-0.5">{i + 1}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
        <strong>How to read this:</strong> LLR (log-likelihood ratio) measures how much the
        evidence favors the remedy over placebo. As you add rubrics, it drifts. If it crosses
        the upper boundary → stop, the remedy is confirmed. If it crosses the lower boundary
        → stop, no remedy is emerging. If it stays between → keep interviewing. This is the
        mathematically optimal stopping rule for sequential clinical decisions.
      </div>
    </div>
  );
}
