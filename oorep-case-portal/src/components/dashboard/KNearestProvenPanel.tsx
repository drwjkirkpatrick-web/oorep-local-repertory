"use client";

/**
 * KNearestProvenPanel.tsx
 * Dashboard panel for K-Nearest Proven Cases (Module #126)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ “Has anyone had a case like this before, and what worked?” This   │
 * │ panel searches your entire case history (or the global OOREP      │
 * │ database) for the most similar past cases, using Jaccard similarity│
 * │ on the rubric set. It then shows you the remedies that actually   │
 * │ worked in those similar cases, weighted by outcome quality. This  │
 * │ is collaborative filtering for homeopathy — your past successful   │
 * │ cases vote on the current one.                                     │
 * │                                                                    │
 * │ Real-world use: A patient presents with “burning, right-sided      │
 * │ headache, worse from sun, irritable.” The KNN finds 3 similar past  │
 * │ cases: two resolved with Belladonna (excellent outcome), one with │
 * │ Nux-vomica (good). The weighted vote says Belladonna 67%, Nux-v.   │
 * │ 33%. You now have historical precedent, not just repertorization.   │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface HistoricalCase {
  case_id: string;
  similarity: number;
  remedy: string;
  outcome: string;
  outcome_score: number;
  rubric_overlap: number;
  total_rubrics: number;
}

interface KNNResult {
  remedy: string;
  vote_weight: number;
  avg_similarity: number;
  n_cases: number;
  avg_outcome: number;
}

export default function KNearestProvenPanel() {
  const [cases, setCases] = useState<HistoricalCase[]>([]);
  const [votes, setVotes] = useState<KNNResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/knn-proven")
      .then((r) => r.json())
      .then((data) => {
        setCases(data.cases || []);
        setVotes(data.votes || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading proven cases...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">K-Nearest Proven Cases (Module #126)</h2>
        <p className="text-sm text-gray-600 mt-1">
          The best evidence for choosing a remedy is: “Has a case like this worked with that
          remedy before?” This panel searches your entire case history (and the global OOREP
          proven-case database) for the most <strong>similar past cases</strong> — using
          Jaccard similarity on the rubric overlap. It then <strong>votes</strong>: remedies
          that worked in similar cases get weighted votes proportional to similarity × outcome
          quality. The result is a recommendation grounded in your own (or the community’s)
          historical success — not just abstract repertorization scores.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">Weighted Vote Results</h3>
          <div className="space-y-2">
            {votes.map((v) => (
              <div key={v.remedy} className="flex items-center gap-3">
                <div className="w-20 text-sm font-bold">{v.remedy}</div>
                <div className="flex-1 h-2 bg-gray-200 rounded-full">
                  <div className="h-2 bg-blue-500 rounded-full" style={{ width: `${v.vote_weight * 100}%` }} />
                </div>
                <div className="text-sm text-right w-24">
                  {(v.vote_weight * 100).toFixed(1)}% · {v.n_cases} cases
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">Most Similar Past Cases</h3>
          <div className="space-y-2">
            {cases.slice(0, 5).map((c, i) => (
              <div key={i} className="text-sm border-b pb-2 last:border-0">
                <div className="flex justify-between">
                  <span className="font-medium">Case {c.case_id}</span>
                  <span className="text-blue-600 font-bold">{(c.similarity * 100).toFixed(1)}% similar</span>
                </div>
                <div className="text-gray-500 text-xs mt-0.5">
                  {c.remedy} · {c.outcome} (score {c.outcome_score}) · {c.rubric_overlap}/{c.total_rubrics} rubrics overlap
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
