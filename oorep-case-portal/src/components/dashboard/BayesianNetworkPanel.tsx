"use client";

/**
 * BayesianNetworkPanel.tsx
 * Dashboard panel for Bayesian Rubric Network (Module #127)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ Are two rubrics telling you the same thing? If “fear of death” and  │
 * │ “anxiety about health” always appear together, they are redundant.  │
 * │ This panel builds a Chow-Liu tree of rubric dependencies using     │
 * │ mutual information. It shows which rubrics are independent (add   │
 * │ new information) vs. dependent (redundant). You should weight      │
 * │ independent rubrics higher and drop redundant ones to avoid        │
 * │ inflating one symptom artificially.                                │
 * │                                                                    │
 * │ Real-world use: You have 12 rubrics. The network says “fear of     │
 * │ death” and “wants to be alone” are highly connected (MI = 0.8) —    │
 * │ they are two expressions of the same mental state. You drop one     │
 * │ and replace it with an independent rubric like “worse from cold”    │
 * │ (MI = 0.05 with everything else). Your repertorization becomes       │
 * │ cleaner and more accurate.                                         │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface NetworkEdge {
  from: string;
  to: string;
  mutual_information: number;
  dependency_type: "strong" | "moderate" | "weak";
}

interface RubricNode {
  name: string;
  centrality: number;
  is_independent: boolean;
  n_connections: number;
}

export default function BayesianNetworkPanel() {
  const [edges, setEdges] = useState<NetworkEdge[]>([]);
  const [nodes, setNodes] = useState<RubricNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/bayesian-network")
      .then((r) => r.json())
      .then((data) => {
        setEdges(data.edges || []);
        setNodes(data.nodes || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading Bayesian network...</div>;

  const independentNodes = nodes.filter((n) => n.is_independent);
  const redundantNodes = nodes.filter((n) => !n.is_independent);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Bayesian Rubric Network (Module #127)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Two rubrics can say the same thing. If “fear of death” and “anxiety about health”
          always appear together, they are <strong>redundant</strong> — adding both inflates
          one symptom artificially. This panel builds a <strong>Chow-Liu tree</strong> from
          pairwise mutual information across your case history. It identifies which rubrics
          are <em>independent</em> (each adds unique information) vs. <em>dependent</em>
          (they cluster together). You should weight independent rubrics higher and consider
          dropping redundant ones for a cleaner, more accurate repertorization.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-green-800">Independent Rubrics (Keep These)</h3>
          <div className="space-y-1">
            {independentNodes.slice(0, 8).map((n) => (
              <div key={n.name} className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span>{n.name}</span>
                <span className="text-gray-400 text-xs">({n.n_connections} links)</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-yellow-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-yellow-800">Redundant Clusters (Review These)</h3>
          <div className="space-y-1">
            {redundantNodes.slice(0, 8).map((n) => (
              <div key={n.name} className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                <span>{n.name}</span>
                <span className="text-gray-400 text-xs">({n.n_connections} links)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Connected Pair</th>
              <th className="p-2 text-left">Mutual Information</th>
              <th className="p-2 text-left">Dependency</th>
            </tr>
          </thead>
          <tbody>
            {edges.slice(0, 10).map((e, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                <td className="p-2">{e.from} ↔ {e.to}</td>
                <td className="p-2">{e.mutual_information.toFixed(3)}</td>
                <td className="p-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    e.dependency_type === "strong" ? "bg-red-100 text-red-700" :
                    e.dependency_type === "moderate" ? "bg-yellow-100 text-yellow-700" :
                    "bg-green-100 text-green-700"
                  }`}>
                    {e.dependency_type}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
        <strong>How to use this:</strong> Strong mutual information means two rubrics
        carry the same signal. If both are in your repertorization, you are double-counting.
        Pick the one with higher clinical specificity and drop the other. Independent rubrics
        (low MI with everything) are your anchors — they provide unique information and
        should be weighted higher.
      </div>
    </div>
  );
}
