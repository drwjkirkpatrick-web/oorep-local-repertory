"use client";

/**
 * CollapsiblePanel.tsx
 * Collapsible sections for dashboard organization
 */

import React, { useState, useCallback } from 'react';

interface CollapsiblePanelProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  badge?: string | number;
  badgeColor?: 'blue' | 'green' | 'amber' | 'red' | 'purple';
  level?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  actions?: React.ReactNode;
  onRefresh?: () => void;
  isLoading?: boolean;
}

const levelColors = {
  BEGINNER: 'bg-blue-50 text-blue-700',
  INTERMEDIATE: 'bg-amber-50 text-amber-700',
  ADVANCED: 'bg-purple-50 text-purple-700',
};

const badgeColors = {
  blue: 'bg-blue-100 text-blue-700',
  green: 'bg-green-100 text-green-700',
  amber: 'bg-amber-100 text-amber-700',
  red: 'bg-red-100 text-red-700',
  purple: 'bg-purple-100 text-purple-700',
};

export default function CollapsiblePanel({
  title,
  subtitle,
  children,
  defaultExpanded = true,
  badge,
  badgeColor = 'blue',
  level,
  actions,
  onRefresh,
  isLoading,
}: CollapsiblePanelProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    if (!onRefresh || isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh, isRefreshing]);

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          {/* Expand/Collapse Icon */}
          <button
            className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 transition"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            <svg 
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Title Group */}
          <div>
            <div className="flex items-center gap-2">
              {level && (
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${levelColors[level]}`}>
                  {level}
                </span>
              )}
              <h3 className="font-semibold text-gray-800">{title}</h3>
              
              {badge !== undefined && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${badgeColors[badgeColor]}`}>
                  {badge}
                </span>
              )}
            </div>
            
            {subtitle && (
              <p className="text-[10px] text-gray-400 mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {actions}
          
          {onRefresh && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRefresh();
              }}
              disabled={isRefreshing || isLoading}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition disabled:opacity-50"
              title="Refresh panel"
            >
              <svg 
                className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div 
        className={`transition-all duration-200 overflow-hidden ${
          isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="p-4 pt-0 border-t">
          {isLoading ? (
            <div className="py-8 flex items-center justify-center">
              <div className="flex items-center gap-2 text-gray-400">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span className="text-sm">Loading...</span>
              </div>
            </div>
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * PanelSection - Group of collapsible panels
 */
interface PanelSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  count?: number;
}

export function PanelSection({
  title,
  children,
  defaultExpanded = true,
  count,
}: PanelSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="mb-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 mb-3 text-gray-700 hover:text-gray-900 transition"
      >
        <svg 
          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="font-semibold">{title}</span>
        {count !== undefined && (
          <span className="text-xs text-gray-400">({count})</span>
        )}
      </button>
      
      <div className={`space-y-4 transition-all ${isExpanded ? '' : 'hidden'}`}>
        {children}
      </div>
    </div>
  );
}
