"use client";

/**
 * CausalRemedyEffectsPanel.tsx
 * Dashboard panel for Causal Remedy Effects (Module #119)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Did Pulsatilla cure the patient, or would they have gotten better │
 * │ anyway? This panel answers the causal question using the “potential │
 * │ outcomes” framework: it compares patients who got Pulsatilla to   │
 * │ statistically matched patients who did not, adjusting for how sick  │
 * │ they were before. The result is an ATE (Average Treatment Effect)   │
 * │ with confidence intervals — real causal evidence, not just          │
 * │ correlation.                                                         │
 * │                                                                    │
 * │ Real-world use: After prescribing Arsenicum for 20 anxious cases,  │
 * │ this panel shows an ATE of +2.3 (95% CI [1.1, 3.5]) on the       │
 * │ GAD-7 anxiety scale — meaning Arsenicum patients improved 2.3    │
 * │ points more than matched controls. That is publishable evidence.   │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface CausalResult {
  remedy: string;
  ate: number;
  ci_lower: number;
  ci_upper: number;
  n_treated: number;
  n_control: number;
  balance_score: number;
  method: string;
}

export default function CausalRemedyEffectsPanel() {
  const [results, setResults] = useState<CausalResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/causal-effects")
      .then((r) => r.json())
      .then((data) => {
        setResults(data.results || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading causal effects...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Causal Remedy Effects (Module #119)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Correlation is not causation. This panel uses the potential-outcomes framework
          (the gold standard in epidemiology) to answer: “Did this remedy actually cause
          the improvement, or would the patient have improved anyway?” It matches treated
          patients to statistically similar untreated patients (propensity matching), then
          measures the Average Treatment Effect (ATE) with 95% confidence intervals. The
          balance score tells you whether the groups were truly comparable (higher = more
          trustworthy). This turns anecdotal “it worked for me” into measurable causal
          evidence.
        </p>
      </div>

      <div className="space-y-4">
        {results.map((res) => {
          const isSignificant = res.ci_lower > 0 || res.ci_upper < 0;
          const barWidth = Math.min(Math.abs(res.ate) * 30, 100);
          const barColor = res.ate > 0 ? "bg-green-500" : "bg-red-500";

          return (
            <div key={res.remedy} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-lg">{res.remedy}</span>
                <span className={`text-sm font-medium px-2 py-1 rounded ${isSignificant ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                  {isSignificant ? "✅ Statistically Significant" : "⚠ Not Significant"}
                </span>
              </div>

              <div className="flex items-center gap-3 mb-2">
                <span className="text-sm text-gray-600">ATE:</span>
                <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div className={`h-full ${barColor}`} style={{ width: `${barWidth}%`, marginLeft: res.ate < 0 ? "auto" : "0" }} />
                </div>
                <span className={`font-bold ${res.ate > 0 ? "text-green-600" : "text-red-500"}`}>
                  {res.ate > 0 ? "+" : ""}{res.ate.toFixed(2)}
                </span>
              </div>

              <div className="text-sm text-gray-600">
                95% CI: [{res.ci_lower.toFixed(2)}, {res.ci_upper.toFixed(2)}] ·
                Treated: {res.n_treated} · Control: {res.n_control} ·
                Balance: {(res.balance_score * 100).toFixed(0)}% ·
                Method: {res.method}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm text-gray-700">
        <strong>How to interpret:</strong> ATE = Average Treatment Effect. Positive means the
        remedy group improved more than matched controls. The 95% CI must not cross zero
        for the result to be statistically significant. Balance score ≥ 80% means the
        groups were well-matched on baseline characteristics — the causal inference is
        trustworthy. This is the same framework used in drug efficacy trials (randomized
        controlled trials are the ideal; propensity matching is the best observational
        alternative).
      </div>
    </div>
  );
}
