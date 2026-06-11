"use client";

/**
 * EnsembleStackingPanel.tsx
 * Dashboard panel for Ensemble Retrieval with Stacking (Module #120)
 */

import React, { useState, useEffect } from 'react';

interface EnsembleResult {
  remedy: string;
  ensemble_score: number;
  layer_contributions: Record<string, number>;
}

interface FeatureImportance {
  [layer: string]: number;
}

export default function EnsembleStackingPanel() {
  const [results, setResults] = useState<EnsembleResult[]>([]);
  const [importance, setImportance] = useState<FeatureImportance>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/ensemble-stacking')
      .then(r => r.json())
      .then(data => {
        setResults(data.results || []);
        setImportance(data.feature_importance || {});
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-4">Loading Ensemble...</div>;

  const layers = Object.keys(importance);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Ensemble Stacking (Module #120)</h2>

      {/* Feature Importance */}
      {layers.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold mb-3">Layer Importance (Learned Weights)</h3>
          <div className="space-y-2">
            {layers.map(layer => (
              <div key={layer} className="flex items-center">
                <div className="w-24 text-sm capitalize">{layer}</div>
                <div className="flex-1 mx-2">
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                      style={{ width: `${(importance[layer] * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
                <div className="w-12 text-right text-sm font-medium">{(importance[layer] * 100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ensemble Results */}
      <div>
        <h3 className="font-semibold mb-3">Ensemble Rankings</h3>
        <div className="space-y-3">
          {results.slice(0, 5).map((result, i) => (
            <div key={result.remedy} className="bg-gray-50 p-3 rounded">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs mr-2">
                    {i + 1}
                  </span>
                  <span className="font-bold">{result.remedy}</span>
                </div>
                <span className="text-lg font-bold text-blue-600">{result.ensemble_score.toFixed(3)}</span>
              </div>
              
              {/* Layer contributions */}
              <div className="flex gap-1 mt-2">
                {Object.entries(result.layer_contributions).map(([layer, score]) => (
                  <div 
                    key={layer}
                    className="flex-1 bg-gray-200 rounded overflow-hidden"
                    title={`${layer}: ${(score * 100).toFixed(0)}%`}
                  >
                    <div 
                      className="h-2 bg-blue-400"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        <p>Stacked ensemble combines lexical, vector, SRP, keynote, family, and cycle layers with learned weights.</p>
      </div>
    </div>
  );
}
