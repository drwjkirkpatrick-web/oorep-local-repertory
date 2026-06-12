"use client";

/**
 * PatientIntakePanel.tsx
 * Dashboard panel for Patient Intake Engine (Module #131)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ This is the central command center for the entire patient         │
 * │ interview. It shows you where you are in the 9-phase flow          │
 * │ (Opening → Chief Complaint → History → Modalities → Concomitants   │
 * │ → Mind → Generals → Constitution → Review), what has been captured, │
 * │ what is still missing, and what the next optimal question is. You   │
 * │ never lose track of the interview structure. It is like having    │
 * │ Kent and Vithoulkas whispering in your ear, keeping you on track.  │
 * │                                                                    │
 * │ Real-world use: You are 12 minutes into a complex chronic case.   │
 * │ The panel shows: Mind 90%, Generals 30%, Modalities 70%. It says:  │
 * │ “Next: ask about thermal state (Generals gap). Expected to raise   │
 * │ case quality from 62 to 78.” You ask. The patient says “chilly.”   │
 * │ Pulsatilla drops, Arsenicum rises. You are now confident.           │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface IntakePhase {
  name: string;
  status: "pending" | "active" | "complete" | "skipped";
  symptoms_captured: number;
  questions_asked: number;
  minutes_spent: number;
}

interface IntakeStatus {
  session_id: string;
  current_phase: string;
  overall_quality: number;
  minutes_elapsed: number;
  ready_to_prescribe: boolean;
  phases: IntakePhase[];
  next_recommended_question: string;
  expected_quality_after: number;
}

export default function PatientIntakePanel() {
  const [status, setStatus] = useState<IntakeStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/intake-status")
      .then((r) => r.json())
      .then((data) => {
        setStatus(data.status || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading intake status...</div>;
  if (!status) return <div className="p-4">No active intake session.</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Patient Intake Engine (Module #131)</h2>
        <p className="text-sm text-gray-600 mt-1">
          The central command center for your entire patient interview. This panel shows
          your position in the 9-phase classical case-taking flow, what has been captured,
          what is missing, and the mathematically optimal next question. It is like having
          Kent and Vithoulkas guiding you in real time — keeping the interview structured,
          complete, and efficient. No more losing track in a 45-minute chronic case.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className={`p-3 rounded ${status.ready_to_prescribe ? "bg-green-50" : "bg-yellow-50"}`}>
          <div className="text-sm text-gray-600">Ready?</div>
          <div className="text-xl font-bold">{status.ready_to_prescribe ? "✅ Yes" : "⏳ No"}</div>
        </div>
        <div className="bg-blue-50 p-3 rounded">
          <div className="text-sm text-gray-600">Case Quality</div>
          <div className="text-xl font-bold">{Math.round(status.overall_quality)}/100</div>
        </div>
        <div className="bg-purple-50 p-3 rounded">
          <div className="text-sm text-gray-600">Time Elapsed</div>
          <div className="text-xl font-bold">{status.minutes_elapsed} min</div>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <div className="text-sm text-gray-600">Current Phase</div>
          <div className="text-xl font-bold">{status.current_phase}</div>
        </div>
      </div>

      <div className="space-y-2 mb-6">
        <h3 className="font-semibold">Phase Progress</h3>
        {status.phases.map((phase) => {
          const statusColor =
            phase.status === "complete"
              ? "bg-green-500"
              : phase.status === "active"
              ? "bg-blue-500"
              : phase.status === "skipped"
              ? "bg-gray-300"
              : "bg-gray-200";
          return (
            <div key={phase.name} className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: statusColor }} />
              <div className="w-32 text-sm font-medium">{phase.name}</div>
              <div className="flex-1 h-2 bg-gray-100 rounded-full">
                <div
                  className="h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min((phase.questions_asked / 5) * 100, 100)}%`,
                    backgroundColor: statusColor,
                  }}
                />
              </div>
              <div className="text-xs text-gray-500 w-24 text-right">
                {phase.symptoms_captured} symptoms · {phase.minutes_spent}m
              </div>
            </div>
          );
        })}
      </div>

      {status.next_recommended_question && (
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-blue-700 font-semibold mb-1">🎯 Recommended Next Question</div>
          <div className="text-lg font-medium text-gray-900">{status.next_recommended_question}</div>
          <div className="text-sm text-gray-600 mt-1">
            Expected case quality: {Math.round(status.overall_quality)} →{" "}
            {Math.round(status.expected_quality_after)}
          </div>
        </div>
      )}
    </div>
  );
}
