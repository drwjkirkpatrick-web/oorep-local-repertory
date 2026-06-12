"use client";

/**
 * InformationTheoreticPanel.tsx
 * Dashboard panel for Information-Theoretic Case Workup (Module #122)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ “Is my case complete enough to prescribe?” This panel quantifies  │
 * │ case completeness in bits — the same unit information theory uses. │
 * │ It tells you: you have 4.2 bits of 7.0 needed (60% complete).      │
 * │ Which chapters are empty? Mind is 90% covered, Stomach is 0%.        │
 * │ You know exactly where to focus your remaining interview time.      │
 * │                                                                    │
 * │ Real-world use: A rushed 15-minute acute case shows 45% complete. │
 * │ The panel says: “Generals at 20% — ask thermal state, thirst, and  │
 * │ sleep position. Mind at 80% — skip it.” You finish in 5 minutes. │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface ChapterCoverage {
  chapter: string;
  bits_covered: number;
  bits_needed: number;
  pct: number;
  status: "sufficient" | "partial" | "missing";
}

interface WorkupSummary {
  total_bits_covered: number;
  total_bits_needed: number;
  pct_complete: number;
  ready_to_prescribe: boolean;
  sufficient_chapters: string[];
  missing_chapters: string[];
}

export default function InformationTheoreticPanel() {
  const [chapters, setChapters] = useState<ChapterCoverage[]>([]);
  const [summary, setSummary] = useState<WorkupSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/case-workup")
      .then((r) => r.json())
      .then((data) => {
        setChapters(data.chapters || []);
        setSummary(data.summary || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading case workup analysis...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Information-Theoretic Case Workup (Module #122)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Case-taking is an information-gathering problem. This panel quantifies your progress
          in <strong>bits</strong> — the fundamental unit of information. It tells you exactly
          how much information you have gathered, how much you still need, and which chapters
          are the biggest gaps. Instead of vague intuition (“I think I have enough”), you get
          a precise percentage: 60% complete, with Mind at 90% and Generals at 20%. You then
          know to spend your remaining 5 minutes on thermal state, thirst, and sleep position.
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className={`p-3 rounded ${summary.ready_to_prescribe ? "bg-green-50" : "bg-yellow-50"}`}>
            <div className="text-sm text-gray-600">Ready to Prescribe?</div>
            <div className="text-xl font-bold">{summary.ready_to_prescribe ? "✅ Yes" : "⏳ Not Yet"}</div>
          </div>
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Bits Covered</div>
            <div className="text-xl font-bold">{summary.total_bits_covered.toFixed(1)}</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Bits Needed</div>
            <div className="text-xl font-bold">{summary.total_bits_needed.toFixed(1)}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">% Complete</div>
            <div className="text-xl font-bold">{Math.round(summary.pct_complete)}%</div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {chapters.map((ch) => {
          const statusColor =
            ch.status === "sufficient"
              ? "bg-green-100 text-green-800"
              : ch.status === "partial"
              ? "bg-yellow-100 text-yellow-800"
              : "bg-red-100 text-red-800";
          return (
            <div key={ch.chapter} className="flex items-center gap-3">
              <div className="w-32 text-sm font-medium">{ch.chapter}</div>
              <div className="flex-1 h-3 bg-gray-100 rounded-full">
                <div
                  className="h-3 bg-blue-500 rounded-full transition-all"
                  style={{ width: `${Math.min(ch.pct, 100)}%` }}
                />
              </div>
              <div className="w-16 text-sm text-right">{Math.round(ch.pct)}%</div>
              <span className={`text-xs px-2 py-0.5 rounded ${statusColor}`}>
                {ch.status}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> A “bit” is the amount of information needed to
        distinguish between two equally likely alternatives. The more bits you gather, the
        more certain your remedy selection becomes. The panel recommends continuing the
        interview until ≥ 70% complete, or until you have at least 3 sufficient chapters
        (including Mind or Generals). This prevents both under-taking (premature prescription)
        and over-taking (unnecessary 2-hour interviews).
      </div>
    </div>
  );
}
