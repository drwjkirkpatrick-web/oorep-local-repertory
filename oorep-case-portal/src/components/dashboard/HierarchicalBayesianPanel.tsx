"use client";

/**
 * HierarchicalBayesianPanel.tsx
 * Dashboard panel for Hierarchical Bayesian Similarity (Module #115)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ When you have 3,000 rubrics and need to find the hidden pattern,  │
 * │ this panel uses biological taxonomy (Plant / Animal / Mineral /   │
 * │ Nosode families) as Bayesian priors. A Natrum case looks “salty”   │
 * │ and “isolated” — that is the Mineral kingdom, Salt family. This    │
 * │ panel weights similarity by kingdom first, then family, then genus.  │
 * │ It prevents a generic “everything matches” result by saying: if the │
 * │ patient’s language is animal-like (predatory, territorial,         │
 * │ hierarchical), Animal remedies get a prior boost before any rubric  │
 * │ is even counted.                                                   │
 * │                                                                    │
 * │ Real-world use: A patient says “I feel like a wounded animal” —    │
 * │ this panel pushes Tarentula, Lachesis, and Lac-can. up the list   │
 * │ even before you open the repertory.                                │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface TaxonomyNode {
  name: string;
  prior: number;
  posterior: number;
  posterior_weight: number;
  evidence_count: number;
  children?: TaxonomyNode[];
}

export default function HierarchicalBayesianPanel() {
  const [kingdoms, setKingdoms] = useState<TaxonomyNode[]>([]);
  const [selectedKingdom, setSelectedKingdom] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/hierarchical-similarity")
      .then((r) => r.json())
      .then((data) => {
        setKingdoms(data.kingdoms || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading hierarchical Bayes...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Hierarchical Bayesian Similarity (Module #115)</h2>
        <p className="text-sm text-gray-600 mt-1">
          Uses biological taxonomy — Plant, Animal, Mineral, Nosode — as layered Bayesian
          priors. A patient whose language is “salty, structured, brittle” gets a Mineral
          kingdom boost; one who is “territorial, predatory, hierarchical” gets an Animal
          boost. This happens <em>before</em> any rubric is counted, preventing the
          “everything matches” problem and surfacing the right kingdom first, then the
          right family, then the exact remedy.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        {kingdoms.map((k) => {
          const isSelected = selectedKingdom === k.name;
          return (
            <button
              key={k.name}
              onClick={() => setSelectedKingdom(isSelected ? null : k.name)}
              className={`p-4 rounded-lg border text-left transition ${
                isSelected ? "bg-blue-50 border-blue-300" : "bg-gray-50 border-gray-200 hover:bg-gray-100"
              }`}
            >
              <div className="text-lg font-bold">{k.name}</div>
              <div className="text-2xl font-bold text-blue-600 mt-1">
                {(k.posterior * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Prior {(k.prior * 100).toFixed(1)}% → Posterior {(k.posterior * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {k.evidence_count} rubrics
              </div>
            </button>
          );
        })}
      </div>

      {selectedKingdom && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold mb-3">{selectedKingdom} Families</h3>
          <div className="space-y-2">
            {(kingdoms.find((k) => k.name === selectedKingdom)?.children || []).map(
              (child) => (
                <div key={child.name} className="flex items-center gap-3">
                  <div className="w-32 text-sm font-medium">{child.name}</div>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full">
                    <div
                      className="h-2 bg-blue-500 rounded-full"
                      style={{ width: `${child.posterior_weight * 100}%` }}
                    />
                  </div>
                  <div className="w-16 text-sm text-right">
                    {(child.posterior * 100).toFixed(1)}%
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
