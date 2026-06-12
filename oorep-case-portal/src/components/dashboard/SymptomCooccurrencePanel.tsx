"use client";

/**
 * SymptomCooccurrencePanel.tsx
 * Dashboard panel for Symptom Co-occurrence Lift (Module #128)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Which symptoms form “syndromes” — groups that appear together more  │
 * │ often than chance? If “burning pain” and “worse from heat” co-occur │
 * │ at 5× the expected rate, that is a syndrome with strong remedy     │
 * │ predictive power. This panel mines association rules: support,    │
 * │ confidence, lift, and conviction. High-lift pairs are your        │
 * │ “signature patterns” — when you see one, you know to ask about    │
 * │ the other.                                                         │
 * │                                                                    │
 * │ Real-world use: A patient has “worse from motion.” The lift       │
 * │ analysis shows “worse from motion” + “stitching pain” have lift    │
 * │ 4.2 — they form a syndrome pointing to Bryonia. You now ask about  │
 * │ pain character, and Bryonia moves to #1.                           │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface AssociationRule {
  antecedent: string;
  consequent: string;
  support: number;
  confidence: number;
  lift: number;
  conviction: number;
}

export default function SymptomCooccurrencePanel() {
  const [rules, setRules] = useState<AssociationRule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/cooccurrence-lift")
      .then((r) => r.json())
      .then((data) => {
        setRules(data.rules || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading co-occurrence analysis...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Symptom Co-occurrence Lift (Module #128)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Some symptoms travel together. If a patient has “burning pain,” the chance they also
          have “worse from heat” is much higher than random. This panel mines <strong>association
          rules</strong> from the full repertory: <em>support</em> (how common the pair is),
          <em>confidence</em> (if A, how likely is B), <em>lift</em> (how much more likely
          than chance), and <em>conviction</em> (strength of the directional rule). High-lift
          pairs are your “signature syndromes” — when you see one symptom, you immediately
          ask about the other, because they form a remedy-predictive pattern.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Rule</th>
              <th className="p-2 text-left">Support</th>
              <th className="p-2 text-left">Confidence</th>
              <th className="p-2 text-left">Lift</th>
              <th className="p-2 text-left">Conviction</th>
              <th className="p-2 text-left">Strength</th>
            </tr>
          </thead>
          <tbody>
            {rules.slice(0, 15).map((r, i) => {
              const strength = r.lift > 3 ? "strong" : r.lift > 1.5 ? "moderate" : "weak";
              const strengthColor =
                strength === "strong" ? "bg-green-100 text-green-700" :
                strength === "moderate" ? "bg-yellow-100 text-yellow-700" :
                "bg-gray-100 text-gray-600";
              return (
                <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                  <td className="p-2 font-medium">{r.antecedent} → {r.consequent}</td>
                  <td className="p-2">{(r.support * 100).toFixed(1)}%</td>
                  <td className="p-2">{(r.confidence * 100).toFixed(1)}%</td>
                  <td className="p-2 font-bold text-blue-600">{r.lift.toFixed(2)}x</td>
                  <td className="p-2">{r.conviction.toFixed(2)}</td>
                  <td className="p-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${strengthColor}`}>{strength}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> Lift > 3 means the symptoms co-occur at 3× the
        expected rate — this is a strong syndrome. When you see the antecedent in a case,
        immediately ask about the consequent; the pair together has strong remedy predictive
        power. Conviction > 1.5 means the rule is directionally reliable (A predicts B better
        than B predicts A). Use these rules as “if-then” clinical prompts during case-taking.
      </div>
    </div>
  );
}
