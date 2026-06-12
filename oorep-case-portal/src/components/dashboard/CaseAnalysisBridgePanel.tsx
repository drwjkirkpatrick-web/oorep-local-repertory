"use client";

/**
 * CaseAnalysisBridgePanel.tsx
 * Dashboard panel for Case Analysis Bridge — cross-references Confusion Matrix + Co-occurrence Lift
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ When two remedies are confused in your practice history, this      │
 * │ panel finds the symptom syndromes that differentiate them. It       │
 * │ combines:                                                            │
 * │   • Confusion pairs — which remedies get mixed up                    │
 * │   • Co-occurrence lift — which symptom pairs predict which remedy  │
 * │   • Precision/recall thresholds — when to trust the score            │
 * │ The result: when you see Pulsatilla and Sepia close in the ranking, │
 * │ you know exactly which questions to ask and at what score threshold  │
 * │ to make the call.                                                    │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface DifferentiatingSyndrome {
  symptom_a: string;
  symptom_b: string;
  lift: number;
  confidence: number;
  remedy_a_prevalence: number;
  remedy_b_prevalence: number;
  discriminative_power: number;
}

interface ConfusedPairAnalysis {
  remedy_a: string;
  remedy_b: string;
  historical_confusion_rate: number;
  total_cases_a: number;
  total_cases_b: number;
  precision_at_threshold: number;
  recall_at_threshold: number;
  recommended_threshold: number;
  differentiating_syndromes: DifferentiatingSyndrome[];
  recommended_questions: string[];
}

interface CaseAnalysisReport {
  top_confused_pairs: ConfusedPairAnalysis[];
  strong_syndromes: Array<{
    antecedent: string;
    consequent: string;
    lift: number;
    confidence: number;
    remedy_affinity: string[];
  }>;
  current_case_recommendations: string[];
  overall_precision_at_70: number;
  overall_precision_at_80: number;
  overall_precision_at_90: number;
}

export default function CaseAnalysisBridgePanel() {
  const [report, setReport] = useState<CaseAnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPair, setSelectedPair] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/case-analysis")
      .then((r) => r.json())
      .then((data) => {
        setReport(data.report || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading case analysis...</div>;
  if (!report) return <div className="p-4">No analysis data available.</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Case Analysis Bridge (Confusion + Co-occurrence)</h2>
        <p className="text-sm text-gray-600 mt-1">
          When two remedies are confused in your practice history, this panel finds the
          <strong> symptom syndromes that differentiate them</strong>. It cross-references
          confusion matrix data with co-occurrence lift to tell you exactly which questions
          to ask when two remedies are close in the ranking, and at what score threshold
          to trust the result.
        </p>
      </div>

      {/* Precision thresholds */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-3 rounded text-center">
          <div className="text-sm text-gray-600">Precision at Score ≥ 7</div>
          <div className="text-2xl font-bold">{(report.overall_precision_at_70 * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-green-50 p-3 rounded text-center">
          <div className="text-sm text-gray-600">Precision at Score ≥ 8</div>
          <div className="text-2xl font-bold">{(report.overall_precision_at_80 * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-purple-50 p-3 rounded text-center">
          <div className="text-sm text-gray-600">Precision at Score ≥ 9</div>
          <div className="text-2xl font-bold">{(report.overall_precision_at_90 * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Confused pairs */}
      <div className="space-y-4 mb-6">
        <h3 className="font-semibold">Top Confused Remedy Pairs</h3>
        {report.top_confused_pairs.map((pair) => {
          const isSelected = selectedPair === `${pair.remedy_a}-${pair.remedy_b}`;
          return (
            <div
              key={`${pair.remedy_a}-${pair.remedy_b}`}
              className={`border rounded-lg p-4 cursor-pointer transition ${
                isSelected ? "border-blue-400 bg-blue-50" : "hover:shadow-md"
              }`}
              onClick={() =>
                setSelectedPair(isSelected ? null : `${pair.remedy_a}-${pair.remedy_b}`)
              }
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-lg">{pair.remedy_a}</span>
                  <span className="text-gray-400">↔</span>
                  <span className="font-bold text-lg">{pair.remedy_b}</span>
                  <span className="text-sm text-red-600 font-bold ml-2">
                    {(pair.historical_confusion_rate * 100).toFixed(0)}% confused
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  Threshold ≥ {pair.recommended_threshold} · Precision {(pair.precision_at_threshold * 100).toFixed(0)}%
                </div>
              </div>

              {isSelected && (
                <div className="mt-4 space-y-3">
                  {/* Recommended questions */}
                  <div className="bg-yellow-50 rounded-lg p-3">
                    <div className="text-sm font-semibold text-yellow-800 mb-2">
                      🎯 When these two are close in ranking, ask:
                    </div>
                    <ul className="space-y-1">
                      {pair.recommended_questions.map((q, i) => (
                        <li key={i} className="text-sm text-gray-700">
                          {i + 1}. {q}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Differentiating syndromes */}
                  <div>
                    <div className="text-sm font-semibold mb-2">Differentiating Syndromes:</div>
                    <div className="space-y-2">
                      {pair.differentiating_syndromes.slice(0, 4).map((s, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm">
                          <div className="w-2 h-2 rounded-full bg-blue-500" />
                          <span className="font-medium">
                            {s.symptom_a} + {s.symptom_b}
                          </span>
                          <span className="text-blue-600 font-bold">
                            lift {s.lift.toFixed(1)}x
                          </span>
                          <span className="text-gray-400">
                            ({pair.remedy_a}: {(s.remedy_a_prevalence * 100).toFixed(0)}% vs{" "}
                            {pair.remedy_b}: {(s.remedy_b_prevalence * 100).toFixed(0)}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Strong syndromes */}
      <div className="mb-6">
        <h3 className="font-semibold mb-2">Strong Syndromes Across All Remedies</h3>
        <div className="grid grid-cols-2 gap-2">
          {report.strong_syndromes.slice(0, 6).map((s, i) => (
            <div key={i} className="bg-gray-50 rounded p-2 text-sm">
              <div className="font-medium">
                {s.antecedent} → {s.consequent}
              </div>
              <div className="text-gray-500 text-xs">
                Lift {s.lift.toFixed(1)}x · {s.remedy_affinity.join(", ")}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current case recommendations */}
      {report.current_case_recommendations.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">
            💡 Active Case Recommendations
          </h3>
          <ul className="space-y-2">
            {report.current_case_recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-gray-700">
                • {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> When two remedies are within 1–2 points in the
        repertorization, click their pair above to see the differentiating questions. The
        recommended score threshold tells you when the evidence is strong enough to make the
        call. Higher confusion rate → higher threshold needed. The syndromes show which symptom
        pairs break the tie — ask those questions first.
      </div>
    </div>
  );
}
