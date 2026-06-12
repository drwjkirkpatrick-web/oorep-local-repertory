"use client";

/**
 * QuestionBankPanel.tsx
 * Dashboard panel for Interview Question Bank (Module #132)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ This is your “script” for the patient interview — 30+ canonical    │
 * │ questions organized by classical phase, each tagged with depth,    │
 * │ SRP potential, modality axes, and which remedies they discriminate.│
 * │ You never run out of the right question. Instead of improvising,  │
 * │ you ask questions that have been validated by 200 years of        │
 * │ homeopathic literature.                                            │
 * │                                                                    │
 * │ Real-world use: The patient says “I have a headache.” Instead of   │
 * │ “where does it hurt?” (too generic), the bank suggests: “Describe │
 * │ the character of the pain — is it throbbing, stitching, burning,   │
 * │ or pressing? Does it stay in one place or move around? What makes  │
 * │ it better or worse?” These are Kent-quality questions, pre-loaded. │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface QuestionItem {
  question: string;
  phase: string;
  depth: "surface" | "deep" | "constitutional";
  srp_potential: number;
  modality_axes: string[];
  discriminates: string[];
  follow_ups: string[];
}

export default function QuestionBankPanel() {
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [selectedPhase, setSelectedPhase] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/question-bank")
      .then((r) => r.json())
      .then((data) => {
        setQuestions(data.questions || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading question bank...</div>;

  const phases = ["all", ...Array.from(new Set(questions.map((q) => q.phase)))];
  const filtered = selectedPhase === "all" ? questions : questions.filter((q) => q.phase === selectedPhase);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Interview Question Bank (Module #132)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Your canonical interview script. Every question is drawn from 200 years of
          homeopathic literature — Hahnemann’s Organon, Kent’s Lectures, Vithoulkas’s
          Essence, Herscu’s cycles — and tagged with clinical metadata: how deep it probes,
          its SRP potential, which modality axes it explores, and which remedies it
          discriminates. Instead of improvising generic questions (“where does it hurt?”),
          you ask the ones that have consistently surfaced the characteristic symptom.
        </p>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        {phases.map((phase) => (
          <button
            key={phase}
            onClick={() => setSelectedPhase(phase)}
            className={`px-3 py-1 text-xs rounded-full border transition ${
              selectedPhase === phase
                ? "bg-blue-100 text-blue-700 border-blue-300"
                : "bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100"
            }`}
          >
            {phase === "all" ? "All Phases" : phase}
          </button>
        ))}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filtered.slice(0, 20).map((q, i) => (
          <div key={i} className="border rounded-lg p-4 hover:shadow-md transition">
            <div className="flex items-start gap-3">
              <div className="shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                {i + 1}
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900">{q.question}</div>
                <div className="flex items-center gap-3 mt-2 text-xs">
                  <span className="px-2 py-0.5 bg-gray-100 rounded">{q.phase}</span>
                  <span className={`px-2 py-0.5 rounded ${
                    q.depth === "constitutional" ? "bg-purple-100 text-purple-700" :
                    q.depth === "deep" ? "bg-blue-100 text-blue-700" :
                    "bg-gray-100 text-gray-600"
                  }`}>
                    {q.depth}
                  </span>
                  <span className="text-gray-500">SRP: {(q.srp_potential * 100).toFixed(0)}%</span>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Discriminates: {q.discriminates.join(", ")}
                </div>
                {q.follow_ups.length > 0 && (
                  <div className="mt-1 text-xs text-blue-600">
                    Follow-ups: {q.follow_ups.join("; ")}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
