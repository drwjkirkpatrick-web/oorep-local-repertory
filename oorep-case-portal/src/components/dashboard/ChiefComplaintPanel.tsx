"use client";

/**
 * ChiefComplaintPanel.tsx
 * Dashboard panel for Chief Complaint Triager (Module #133)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ The first 60 seconds of the interview set the trajectory. This    │
 * │ panel instantly classifies the patient’s free-text complaint:     │
 * │ which body system, acute/chronic/recurring, and urgency level.    │
 * │ It also flags 19 red-alert patterns (chest pain, suicidal          │
 * │ ideation, sudden severe headache) that mandate medical referral.   │
 * │ You never miss a medical emergency hiding inside a “routine” visit. │
 * │                                                                    │
 * │ Real-world use: Patient says “I have terrible chest pain when I    │
 * │ walk.” The panel instantly flags: 🚨 EMERGENCY — cardiac red flag.   │
 * │ Category: Acute. Urgency: Immediate medical referral required.     │
 * │ You refer to the ER and then schedule a constitutional follow-up.   │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface TriageResult {
  complaint: string;
  chapter: string;
  category: string;
  urgency: "routine" | "priority" | "emergency";
  red_flags: string[];
  urgency_score: number;
}

export default function ChiefComplaintPanel() {
  const [result, setResult] = useState<TriageResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/chief-complaint")
      .then((r) => r.json())
      .then((data) => {
        setResult(data.triage || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading triage analysis...</div>;

  const urgencyColor =
    result?.urgency === "emergency"
      ? "bg-red-50 border-red-300 text-red-800"
      : result?.urgency === "priority"
      ? "bg-yellow-50 border-yellow-300 text-yellow-800"
      : "bg-green-50 border-green-300 text-green-800";

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Chief Complaint Triager (Module #133)</h2>
        <p className="text-sm text-gray-600 mt-1">
          The first 60 seconds determine everything. This panel instantly classifies the
          patient’s free-text complaint into body system, category (acute/chronic/recurring),
          and urgency level. Crucially, it detects <strong>19 red-flag patterns</strong>
          — chest pain, suicidal ideation, sudden severe headache, one-sided weakness, etc. —
          that mandate immediate medical referral. You never miss a life-threatening
          condition hiding inside what sounds like a routine homeopathic visit.
        </p>
      </div>

      {result && (
        <>
          <div className={`rounded-lg border p-4 mb-4 ${urgencyColor}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-75">Patient said:</div>
                <div className="text-lg font-bold">“{result.complaint}”</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">
                  {result.urgency === "emergency" ? "🚨" : result.urgency === "priority" ? "⚠️" : "✅"}
                </div>
                <div className="text-sm font-bold uppercase">{result.urgency}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Body System</div>
              <div className="text-xl font-bold">{result.chapter}</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-sm text-gray-600">Category</div>
              <div className="text-xl font-bold capitalize">{result.category}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Urgency Score</div>
              <div className="text-xl font-bold">{result.urgency_score.toFixed(1)}</div>
            </div>
          </div>

          {result.red_flags.length > 0 && (
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <h3 className="font-bold text-red-800 mb-2">🚨 Red Flags Detected</h3>
              <ul className="space-y-1">
                {result.red_flags.map((flag, i) => (
                  <li key={i} className="text-sm text-red-700">• {flag}</li>
                ))}
              </ul>
              <div className="mt-2 text-sm font-bold text-red-800">
                ⚠️ Immediate medical evaluation required before homeopathic prescribing.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
