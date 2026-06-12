"use client";

/**
 * QuickFilterBar.tsx
 * Quick filters for remedy kingdom, family, and other attributes
 */

import React, { useState } from 'react';

interface FilterOption {
  id: string;
  label: string;
  count?: number;
  color?: string;
}

interface QuickFilterBarProps {
  selectedFilters: string[];
  onFilterChange: (filters: string[]) => void;
  remedyCounts?: {
    plant: number;
    mineral: number;
    animal: number;
    nosode: number;
  };
}

const KINGDOMS: FilterOption[] = [
  { id: 'plant', label: 'Plant', color: '#22c55e' },
  { id: 'mineral', label: 'Mineral', color: '#3b82f6' },
  { id: 'animal', label: 'Animal', color: '#f97316' },
  { id: 'nosode', label: 'Nosode', color: '#8b5cf6' },
];

const TIERS = [
  { id: 'polycrest', label: 'Polycrest', count: 50 },
  { id: 'frequent', label: 'Frequent', count: 200 },
  { id: 'rare', label: 'Rare', count: 2182 },
];

export default function QuickFilterBar({
  selectedFilters,
  onFilterChange,
  remedyCounts,
}: QuickFilterBarProps) {
  const [expanded, setExpanded] = useState(false);

  const toggleFilter = (id: string) => {
    if (selectedFilters.includes(id)) {
      onFilterChange(selectedFilters.filter(f => f !== id));
    } else {
      onFilterChange([...selectedFilters, id]);
    }
  };

  const clearFilters = () => {
    onFilterChange([]);
  };

  return (
    <div className="bg-white border-b px-4 py-3">
      <div className="flex items-center gap-4 flex-wrap">
        {/* Kingdom Filters */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Kingdom:</span>
          <div className="flex gap-1">
            {KINGDOMS.map((kingdom) => {
              const isSelected = selectedFilters.includes(kingdom.id);
              return (
                <button
                  key={kingdom.id}
                  onClick={() => toggleFilter(kingdom.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition ${
                    isSelected
                      ? 'text-white shadow-sm'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  style={{ backgroundColor: isSelected ? kingdom.color : undefined }}
                >
                  <span 
                    className={`w-2 h-2 rounded-full ${isSelected ? 'bg-white' : ''}`}
                    style={{ backgroundColor: isSelected ? undefined : kingdom.color }}
                  />
                  {kingdom.label}
                  {remedyCounts?.[kingdom.id as keyof typeof remedyCounts] && (
                    <span className="text-[10px] opacity-70">
                      ({remedyCounts[kingdom.id as keyof typeof remedyCounts]})
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="h-6 w-px bg-gray-200" />

        {/* Usage Tiers */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Tier:</span>
          <div className="flex gap-1">
            {TIERS.map((tier) => {
              const isSelected = selectedFilters.includes(tier.id);
              return (
                <button
                  key={tier.id}
                  onClick={() => toggleFilter(tier.id)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition ${
                    isSelected
                      ? 'bg-amber-100 text-amber-800 border border-amber-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {tier.label}
                  <span className="text-[10px] opacity-70 ml-1">({tier.count})</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex-1" />

        {/* Clear Filters */}
        {selectedFilters.length > 0 && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Clear ({selectedFilters.length})
          </button>
        )}

        {/* Expand/Collapse */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-gray-400 hover:text-gray-600 transition"
        >
          {expanded ? 'Less' : 'More filters'}
        </button>
      </div>

      {/* Expanded Filters */}
      {expanded && (
        <div className="mt-3 pt-3 border-t flex gap-6 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Min Score:</span>
            <input
              type="range"
              min="0"
              max="50"
              className="w-24"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Cycle Match:</span>
            <select className="text-xs border rounded px-2 py-1">
              <option>Any</option>
              <option>Required</option>
              <option>{'>'}50%</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Sort By:</span>
            <select className="text-xs border rounded px-2 py-1">
              <option>Classical Score</option>
              <option>Thompson Score</option>
              <option>Confidence</option>
              <option>Cycle Coverage</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
