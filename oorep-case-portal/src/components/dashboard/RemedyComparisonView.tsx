"use client";

/**
 * RemedyComparisonView.tsx
 * Side-by-side remedy comparison for differential analysis
 */

import React, { useState } from 'react';

interface RemedyData {
  name: string;
  abbrev: string;
  score: number;
  matches: Array<{
    rubric: string;
    weight: number;
    grade?: number;
  }>;
  cycleCoverage: number;
  kingdom?: string;
  miasm?: string;
}

interface RemedyComparisonViewProps {
  remedies: RemedyData[];
  isOpen: boolean;
  onClose: () => void;
  onRemoveRemedy: (abbrev: string) => void;
}

export default function RemedyComparisonView({
  remedies,
  isOpen,
  onClose,
  onRemoveRemedy,
}: RemedyComparisonViewProps) {
  const [activeTab, setActiveTab] = useState<'rubrics' | 'scores' | 'cycles'>('rubrics');

  if (!isOpen || remedies.length < 2) return null;

  // Find common rubrics between all selected remedies
  const allRubrics = remedies.map(r => new Set(r.matches.map(m => m.rubric)));
  const commonRubrics = allRubrics.reduce((acc, set) => {
    return new Set(Array.from(acc).filter(x => set.has(x)));
  });

  // Find unique rubrics for each remedy
  const uniqueRubrics = remedies.map((r, i) => {
    const otherSets = allRubrics.filter((_, idx) => idx !== i);
    const others = otherSets.reduce((acc, set) => {
      const combined = new Set(acc);
      Array.from(set).forEach((x) => combined.add(x));
      return combined;
    }, new Set<string>());
    return r.matches.filter(m => !others.has(m.rubric));
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Remedy Comparison</h2>
            <p className="text-xs text-gray-500">Comparing {remedies.length} remedies side-by-side</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          {[
            { id: 'rubrics', label: 'Rubric Comparison', count: commonRubrics.size },
            { id: 'scores', label: 'Score Breakdown' },
            { id: 'cycles', label: 'Cycle Analysis' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex-1 py-3 text-sm font-medium transition ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1.5 px-1.5 py-0.5 text-[10px] bg-gray-100 rounded-full">{tab.count}</span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'rubrics' && (
            <div className="space-y-6">
              {/* Common Rubrics */}
              {commonRubrics.size > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full" />
                    Common Rubrics ({commonRubrics.size})
                  </h3>
                  <div className="bg-green-50 rounded-lg p-3">
                    <div className="grid gap-2">
                      {Array.from(commonRubrics).slice(0, 10).map((rubric, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <span className="w-1.5 h-1.5 bg-green-400 rounded-full" />
                          <span className="text-gray-700">{rubric}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Unique Rubrics per Remedy */}
              <div className="grid gap-4">
                {remedies.map((remedy, idx) => (
                  <div key={remedy.abbrev} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900">{remedy.name}</span>
                        <span className="text-xs text-gray-500">({remedy.abbrev})</span>
                      </div>
                      <button
                        onClick={() => onRemoveRemedy(remedy.abbrev)}
                        className="text-xs text-red-500 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </div>
                    
                    <p className="text-xs text-gray-500 mb-2">
                      {uniqueRubrics[idx].length} unique differentiating rubrics
                    </p>
                    
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {uniqueRubrics[idx].slice(0, 8).map((match, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs py-1">
                          <span 
                            className="w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold text-white"
                            style={{ 
                              backgroundColor: match.weight >= 4 ? '#3b82f6' : 
                                              match.weight === 3 ? '#60a5fa' : '#93c5fd' 
                            }}
                          >
                            {match.weight}
                          </span>
                          <span className="text-gray-600 line-clamp-1">{match.rubric}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'scores' && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                {remedies.map((remedy) => (
                  <div key={remedy.abbrev} className="border rounded-lg p-4">
                    <div className="text-center mb-4">
                      <p className="font-semibold text-gray-900">{remedy.name}</p>
                      <p className="text-2xl font-bold text-blue-600 mt-2">{remedy.score}</p>
                      <p className="text-xs text-gray-500">total score</p>
                    </div>
                    
                    <div className="space-y-2">
                      {[
                        { label: 'Grade 4 (Bold)', count: remedy.matches.filter(m => m.weight >= 4).length, color: '#1e40af' },
                        { label: 'Grade 3 (Italic)', count: remedy.matches.filter(m => m.weight === 3).length, color: '#3b82f6' },
                        { label: 'Grade 2 (Roman)', count: remedy.matches.filter(m => m.weight === 2).length, color: '#60a5fa' },
                        { label: 'Grade 1 (Light)', count: remedy.matches.filter(m => m.weight === 1).length, color: '#93c5fd' },
                      ].map((grade) => (
                        <div key={grade.label} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span 
                              className="w-3 h-3 rounded-sm"
                              style={{ backgroundColor: grade.color }}
                            />
                            <span className="text-gray-600">{grade.label}</span>
                          </div>
                          <span className="font-medium">{grade.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'cycles' && (
            <div className="space-y-4">
              {remedies.map((remedy) => (
                <div key={remedy.abbrev} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-gray-900">{remedy.name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-purple-500 rounded-full transition-all"
                          style={{ width: `${remedy.cycleCoverage * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-gray-600 w-10 text-right">
                        {(remedy.cycleCoverage * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-gray-500">Kingdom: </span>
                      <span className="font-medium capitalize">{remedy.kingdom || 'Unknown'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Miasm: </span>
                      <span className="font-medium">{remedy.miasm || 'Unknown'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition"
          >
            Close
          </button>
          <button
            onClick={() => {/* Export comparison */}}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition"
          >
            Export Comparison
          </button>
        </div>
      </div>
    </div>
  );
}
