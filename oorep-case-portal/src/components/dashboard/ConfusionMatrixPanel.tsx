"use client";

/**
 * ConfusionMatrixPanel.tsx
 * Dashboard panel for Confusion Matrix Differential (Module #125)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Which remedies get confused with each other most often? This       │
 * │ panel shows the full confusion matrix from your historical cases:   │
 * │ “Pulsatilla was prescribed 50 times, but 8 of those were actually │
 * │ Sepia cases.” At every score threshold, it shows precision and    │
 * │ recall. You can set a threshold: only prescribe when score ≥ 15,   │
 * │ which gives 90% precision. This replaces guesswork with calibrated│
 * │ decision rules from your own outcomes.                             │
 * │                                                                    │
 * │ Real-world use: You see Pulsatilla at score 12, Sepia at 11. The   │
 * │ confusion matrix shows Puls-Sepia is the #1 confusion pair in your  │
 * │ practice. You now know to ask the discriminating question (thermal  │
 * │ state) before deciding, because that is where these two diverge.  │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface ThresholdResult {
  threshold: number;
  precision: number;
  recall: number;
  f1: number;
  tp: number;
  fp: number;
  fn: number;
}

interface ConfusionPair {
  remedy_a: string;
  remedy_b: string;
  confusion_count: number;
  total_a: number;
  total_b: number;
  rate: number;
}

export default function ConfusionMatrixPanel() {
  const [thresholds, setThresholds] = useState<ThresholdResult[]>([]);
  const [pairs, setPairs] = useState<ConfusionPair[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/confusion-matrix")
      .then((r) => r.json())
      .then((data) => {
        setThresholds(data.thresholds || []);
        setPairs(data.confusion_pairs || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading confusion analysis...</div>;

  const bestF1 = thresholds.reduce((best, t) => (t.f1 > best.f1 ? t : best), thresholds[0]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Confusion Matrix Differential (Module #125)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Every practitioner has “confusion pairs” — remedies they mix up. This panel
          mines your historical outcomes to find them objectively. It shows:
          (1) <strong>Precision/Recall curves</strong> at every score threshold,
          so you can set a calibrated rule like “only prescribe when score ≥ 15
          (90% precision)”; and (2) <strong>Confusion pairs</strong> — which remedies
          were actually the right ones in cases where you prescribed something else.
          This turns retrospective learning into predictive guardrails.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">Optimal Threshold</h3>
          {bestF1 && (
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Threshold:</span>
                <span className="font-bold">≥ {bestF1.threshold}</span>
              </div>
              <div className="flex justify-between">
                <span>Precision:</span>
                <span className="font-bold text-green-600">{(bestF1.precision * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Recall:</span>
                <span className="font-bold">{(bestF1.recall * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span>F1 Score:</span>
                <span className="font-bold text-blue-600">{bestF1.f1.toFixed(3)}</span>
              </div>
            </div>
          )}
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">Top Confusion Pairs</h3>
          <div className="space-y-2">
            {pairs.slice(0, 5).map((pair, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="font-medium">{pair.remedy_a}</span>
                <span className="text-gray-400">↔</span>
                <span className="font-medium">{pair.remedy_b}</span>
                <span className="text-red-500 font-bold ml-auto">{(pair.rate * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> If Pulsatilla ↔ Sepia is your top confusion
        pair, the next time you see these two close in the repertorization, ask the
        discriminating question (thermal state: Puls. warm, Sepia chilly) before deciding.
        Set your prescription threshold at the F1-optimal point to maximize correct
        prescriptions while minimizing false positives.
      </div>
    </div>
  );
}
