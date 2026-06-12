"use client";

/**
 * IntakeAnalyzerPanel.tsx
 * Dashboard panel for Intake Analyzer (Module #140)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ The final quality check before you prescribe. This panel scores    │
 * │ the entire intake (0–100), identifies strengths and gaps, builds   │
 * │ the Total Symptom Picture (TSP) for repertorization, ranks the      │
 * │ differential, applies Hering’s directions of cure, and tells you    │
 * │ whether the case is ready to prescribe or needs more data. It is   │
 * │ your final safety net — preventing premature prescription from      │
 * │ incomplete data.                                                   │
 * │                                                                    │
 * │ Real-world use: After a 20-minute intake, the panel says:          │
 * │ “Quality: 82/100. Strengths: Mind (90%), Modalities (85%). Gaps:   │
 * │ Generals (45%). TSP built: 14 symptoms, 7 SRP. Differential:      │
 * │ Pulsatilla 8.4, Sulphur 5.2, Arsenicum 3.1. Hering: no suppression │
 * │ detected. Ready to prescribe: ✅ YES.” You prescribe with          │
 * │ confidence, knowing the case is complete and the differential is   │
 * │ statistically sound.                                               │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface CaseQuality {
  overall: number;
  strengths: string[];
  gaps: string[];
  recommendations: string[];
}

interface DifferentialItem {
  remedy: string;
  score: number;
  confidence: number;
}

interface HeringCheck {
  direction: string;
  is_followed: boolean;
  notes: string;
}

interface IntakeAnalysis {
  case_quality: CaseQuality;
  tsp_symptoms: number;
  srp_symptoms: number;
  differential: DifferentialItem[];
  hering_checks: HeringCheck[];
  ready_to_prescribe: boolean;
  prescription_recommendation: string;
}

export default function IntakeAnalyzerPanel() {
  const [analysis, setAnalysis] = useState<IntakeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/intake-analysis")
      .then((r) => r.json())
      .then((data) => {
        setAnalysis(data.analysis || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading intake analysis...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Intake Analyzer (Module #140)</h2>
        <p className="text-sm text-gray-600 mt-1">
          The <strong>final quality check</strong> before you prescribe. This panel scores the
          entire intake (0–100), identifies strengths and gaps, builds the <strong>Total
          Symptom Picture</strong> (TSP) for repertorization, ranks the differential, applies
          <strong>Hering’s directions of cure</strong>, and tells you whether the case is ready
          to prescribe or needs more data. It is your safety net — preventing premature
          prescription from incomplete data. When the panel says “✅ Ready to prescribe,” you
          can proceed with confidence; when it says “⏳ Not yet,” it tells you exactly which
          gaps to fill.
        </p>
      </div>

      {analysis && (
        <>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className={`p-3 rounded ${analysis.ready_to_prescribe ? "bg-green-50" : "bg-yellow-50"}`}>
              <div className="text-sm text-gray-600">Ready?</div>
              <div className="text-xl font-bold">{analysis.ready_to_prescribe ? "✅ YES" : "⏳ Not Yet"}</div>
            </div>
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Case Quality</div>
              <div className="text-xl font-bold">{analysis.case_quality.overall}/100</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-sm text-gray-600">TSP Symptoms</div>
              <div className="text-xl font-bold">
                {analysis.tsp_symptoms} ({analysis.srp_symptoms} SRP)
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Recommendation</div>
              <div className="text-sm font-bold">{analysis.prescription_recommendation}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2 text-green-800">✅ Strengths</h3>
              <ul className="space-y-1">
                {analysis.case_quality.strengths.map((s, i) => (
                  <li key={i} className="text-sm text-gray-700">• {s}</li>
                ))}
              </ul>
            </div>

            <div className="bg-red-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2 text-red-800">🔴 Gaps to Fill</h3>
              <ul className="space-y-1">
                {analysis.case_quality.gaps.map((g, i) => (
                  <li key={i} className="text-sm text-gray-700">• {g}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-2 mb-6">
            <h3 className="font-semibold">Differential Ranking</h3>
            {analysis.differential.map((d, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 text-sm font-bold text-center">{i + 1}</div>
                <div className="w-24 text-sm font-bold">{d.remedy}</div>
                <div className="flex-1 h-2 bg-gray-100 rounded-full">
                  <div
                    className="h-2 bg-blue-500 rounded-full"
                    style={{ width: `${Math.min(d.score * 10, 100)}%` }}
                  />
                </div>
                <div className="w-20 text-sm text-right">{d.score.toFixed(1)}</div>
                <div className="w-20 text-xs text-right text-gray-500">{(d.confidence * 100).toFixed(0)}% conf</div>
              </div>
            ))}
          </div>

          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-semibold mb-2 text-blue-800">📋 Hering's Directions of Cure</h3>
            <div className="space-y-2">
              {analysis.hering_checks.map((h, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className={h.is_followed ? "text-green-600" : "text-yellow-600"}>
                    {h.is_followed ? "✓" : "○"}
                  </span>
                  <span className="text-sm">{h.direction}</span>
                  <span className="text-xs text-gray-500">— {h.notes}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
