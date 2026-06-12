"use client";

/**
 * ActiveLearningIntakePanel.tsx
 * Dashboard panel for Active Learning Intake Tracker (Module #129)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ You have 20 minutes. Where should you spend them? This panel tracks │
 * │ your case-taking in real time: chapter coverage, redundancy, pace,   │
 * │ and information gain per minute. It tells you: “You are 60% done,   │
 * │ but Generals is only 15% covered — spend your next 5 minutes on    │
 * │ thermal state and thirst.” It prevents both under-taking (rushed    │
 * │ prescriptions) and over-taking (2-hour interviews with diminishing │
 * │ returns).                                                          │
 * │                                                                    │
 * │ Real-world use: After 10 minutes, the panel shows Mind at 85%,       │
 * │ Generals at 20%, Modalities at 40%. It suggests: “Ask about thermal  │
 * │ state next — expected IG 1.8 bits, will push Generals to 65%.”     │
 * │ You follow the suggestion and finish a complete case in 15 minutes.│
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface ChapterProgress {
  chapter: string;
  covered: number;
  total: number;
  pct: number;
  last_question: string;
  minutes_spent: number;
}

interface IntakeSuggestion {
  next_question: string;
  target_chapter: string;
  expected_ig: number;
  expected_coverage_boost: number;
  reason: string;
}

interface IntakeStats {
  total_minutes: number;
  overall_pct: number;
  redundancy_score: number;
  pace_score: number;
}

export default function ActiveLearningIntakePanel() {
  const [chapters, setChapters] = useState<ChapterProgress[]>([]);
  const [suggestion, setSuggestion] = useState<IntakeSuggestion | null>(null);
  const [stats, setStats] = useState<IntakeStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/active-learning-intake")
      .then((r) => r.json())
      .then((data) => {
        setChapters(data.chapters || []);
        setSuggestion(data.suggestion || null);
        setStats(data.stats || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading intake tracker...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Active Learning Intake Tracker (Module #129)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Case-taking is a time-budgeting problem. This panel <strong>tracks your interview
          in real time</strong>: how many minutes per chapter, how much redundancy (asking the
          same thing twice), and the <strong>information gain per minute</strong>. It then
          <em>recommends the next question</em> — the one that maximally increases coverage
          of the weakest chapter. This prevents both <strong>under-taking</strong> (rushed
          prescriptions from incomplete data) and <strong>over-taking</strong> (2-hour
          interviews with diminishing returns). Every minute is spent where it matters most.
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Time Elapsed</div>
            <div className="text-2xl font-bold">{stats.total_minutes} min</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Overall Coverage</div>
            <div className="text-2xl font-bold">{Math.round(stats.overall_pct)}%</div>
          </div>
          <div className={`p-3 rounded ${stats.pace_score > 0.7 ? "bg-green-50" : "bg-yellow-50"}`}>
            <div className="text-sm text-gray-600">Pace Score</div>
            <div className="text-2xl font-bold">{(stats.pace_score * 100).toFixed(0)}%</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="space-y-2">
          <h3 className="font-semibold">Chapter Coverage</h3>
          {chapters.map((ch) => (
            <div key={ch.chapter} className="flex items-center gap-3">
              <div className="w-24 text-sm">{ch.chapter}</div>
              <div className="flex-1 h-2 bg-gray-100 rounded-full">
                <div className="h-2 bg-blue-500 rounded-full" style={{ width: `${Math.min(ch.pct, 100)}%` }} />
              </div>
              <div className="w-16 text-sm text-right">{Math.round(ch.pct)}%</div>
              <div className="w-12 text-xs text-gray-400">{ch.minutes_spent}m</div>
            </div>
          ))}
        </div>

        {suggestion && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-semibold mb-2 text-blue-800">🎯 Suggested Next Question</h3>
            <div className="text-lg font-medium text-gray-900 mb-2">{suggestion.next_question}</div>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Target chapter: {suggestion.target_chapter}</div>
              <div>Expected information gain: {suggestion.expected_ig.toFixed(2)} bits</div>
              <div>Coverage boost: +{Math.round(suggestion.expected_coverage_boost * 100)}%</div>
              <div className="text-xs text-gray-500 mt-2 italic">{suggestion.reason}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
