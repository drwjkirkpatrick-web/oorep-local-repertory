"use client";

/**
 * LatentEmbeddingPanel.tsx
 * Dashboard panel for Latent Symptom Embedding (Module #124)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │ PRACTITIONER BENEFIT:                                              │
 * │ The repertory is 143,408 rubrics × 2,432 remedies. That is too big  │
 * │ to see patterns. This panel compresses it into a low-dimensional  │
 * │ “latent space” where similar remedies cluster together. You can     │
 * │ visually see: Pulsatilla sits near Sepia (both weepy, warm),      │
 * │ Natrum-mur near Ignatia (both grief), Sulphur near Psorinum        │
 * │ (both dirty, itchy). The current case is a point in this space;    │
 * │ the closest remedies are the ones most similar in their overall    │
 * │ symptom profile — not just one rubric at a time.                   │
 * │                                                                    │
 * │ Real-world use: After entering the case, the patient’s point in    │
 * │ latent space is closest to Pulsatilla. But nearby are Sepia (20%   │
 * │ away), Lycopodium (35% away), and Sulphur (50% away). This tells │
 * │ you the “remedy neighborhood” — the group of remedies most similar  │
 * │ to this patient overall.                                           │
 * └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect } from "react";

interface EmbeddingPoint {
  remedy: string;
  x: number;
  y: number;
  distance: number;
  similarity: number;
}

export default function LatentEmbeddingPanel() {
  const [points, setPoints] = useState<EmbeddingPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/latent-embedding")
      .then((r) => r.json())
      .then((data) => {
        setPoints(data.neighbors || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading latent embedding...</div>;

  const maxDist = Math.max(...points.map((p) => p.distance), 1);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold">Latent Symptom Embedding (Module #124)</h2>
        <p className="text-sm text-gray-600 mt-1">
          The full repertory is 143,408 rubrics × 2,432 remedies — too large to see patterns.
          This panel uses <strong>truncated SVD</strong> (singular value decomposition) to
          compress the entire repertory into a low-dimensional “latent space.” In this space,
          remedies with similar <em>overall</em> symptom profiles cluster together:
          Pulsatilla near Sepia (both weepy, warm), Natrum-mur near Ignatia (both grief),
          Sulphur near Psorinum (both dirty, itchy). Your case is a point in this space,
          and the closest remedies are the ones most similar across <em>all</em> rubrics —
          not just the ones you happened to search for.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 relative h-64">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <div className="text-4xl mb-2">🎯</div>
              <div className="text-sm">Case Position</div>
              <div className="text-xs mt-1">{points.length} nearest remedies shown</div>
            </div>
          </div>
          {points.slice(0, 8).map((p, i) => {
            const angle = (i / Math.min(points.length, 8)) * 2 * Math.PI;
            const radius = (p.distance / maxDist) * 40 + 10;
            const left = 50 + Math.cos(angle) * radius;
            const top = 50 + Math.sin(angle) * radius;
            return (
              <div
                key={p.remedy}
                className="absolute transform -translate-x-1/2 -translate-y-1/2 px-2 py-1 bg-white rounded shadow text-xs font-medium border"
                style={{ left: `${left}%`, top: `${top}%` }}
              >
                {p.remedy}
                <span className="text-gray-400 ml-1">({(p.similarity * 100).toFixed(0)}%)</span>
              </div>
            );
          })}
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">Nearest Remedies</h3>
          {points.map((p, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-20 text-sm font-bold">{p.remedy}</div>
              <div className="flex-1 h-2 bg-gray-100 rounded-full">
                <div
                  className="h-2 bg-blue-500 rounded-full"
                  style={{ width: `${p.similarity * 100}%` }}
                />
              </div>
              <div className="w-16 text-sm text-right">{(p.similarity * 100).toFixed(1)}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
