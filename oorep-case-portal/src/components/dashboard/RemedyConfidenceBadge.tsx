"use client";

/**
 * RemedyConfidenceBadge.tsx
 * Visual confidence badges with color-coded hierarchy
 */

import React from 'react';

interface ConfidenceBadgeProps {
  score: number;
  maxScore: number;
  cycleCoverage?: number;
  hasCycleMatch?: boolean;
  srpBoost?: number;
  phantomRisk?: number;
  size?: 'sm' | 'md' | 'lg';
}

export default function RemedyConfidenceBadge({
  score,
  maxScore,
  cycleCoverage = 0,
  hasCycleMatch = false,
  srpBoost = 1,
  phantomRisk = 0,
  size = 'md',
}: ConfidenceBadgeProps) {
  // Calculate confidence score (0-100)
  const normalizedScore = (score / Math.max(maxScore, 1)) * 100;
  
  // Base confidence from score
  let confidence = normalizedScore * 0.5;
  
  // Add cycle coverage contribution
  confidence += (cycleCoverage * 100) * 0.3;
  
  // SRP boost bonus
  if (srpBoost > 1) confidence += 10;
  
  // Phantom risk penalty
  confidence -= (phantomRisk * 20);
  
  // Clamp to 0-100
  confidence = Math.max(0, Math.min(100, confidence));

  // Determine tier
  let tier: 'high' | 'medium' | 'low' = 'low';
  if (confidence >= 70) tier = 'high';
  else if (confidence >= 40) tier = 'medium';

  // Size classes
  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5',
    md: 'text-xs px-2 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  // Color schemes
  const colors = {
    high: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-amber-100 text-amber-800 border-amber-200',
    low: 'bg-gray-100 text-gray-600 border-gray-200',
  };

  // Icons
  const icons = {
    high: '★',
    medium: '◆',
    low: '○',
  };

  return (
    <div className="flex items-center gap-1">
      <span 
        className={`inline-flex items-center gap-1 font-medium rounded border ${sizeClasses[size]} ${colors[tier]}`}
        title={`Confidence: ${confidence.toFixed(0)}% (Score: ${score}, Cycle: ${(cycleCoverage * 100).toFixed(0)}%)`}
      >
        <span>{icons[tier]}</span>
        <span>{confidence.toFixed(0)}%</span>
      </span>
      
      {/* Additional indicators */}
      <div className="flex gap-0.5">
        {hasCycleMatch && (
          <span 
            className="text-green-500" 
            title="Cycle match confirmed"
          >
            🔄
          </span>
        )}
        {srpBoost > 1 && (
          <span 
            className="text-purple-500" 
            title={`SRP boost ×${srpBoost.toFixed(1)}`}
          >
            ⚡
          </span>
        )}
        {phantomRisk > 0.1 && (
          <span 
            className="text-amber-500" 
            title={`${phantomRisk.toFixed(1)} phantom rubrics flagged`}
          >
            ⚠️
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * RemedyComparisonRow - Enhanced row with confidence badges
 */
interface RemedyComparisonRowProps {
  rank: number;
  name: string;
  abbrev: string;
  score: number;
  maxScore: number;
  matchCount: number;
  cycleCoverage?: number;
  hasCycleMatch?: boolean;
  isPinned?: boolean;
  onPin?: () => void;
  onView: () => void;
  onExpand: () => void;
}

export function RemedyComparisonRow({
  rank,
  name,
  abbrev,
  score,
  maxScore,
  matchCount,
  cycleCoverage = 0,
  hasCycleMatch = false,
  isPinned = false,
  onPin,
  onView,
  onExpand,
}: RemedyComparisonRowProps) {
  const isTop3 = rank <= 3;
  
  return (
    <tr className={`border-b hover:bg-gray-50 transition ${isTop3 ? 'bg-blue-50/30' : ''}`}>
      <td className="py-3 px-2">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
          rank === 1 ? 'bg-blue-600 text-white' : 
          rank === 2 ? 'bg-blue-400 text-white' :
          rank === 3 ? 'bg-blue-300 text-white' :
          'bg-gray-100 text-gray-500'
        }`}>
          {rank}
        </div>
      </td>
      <td className="py-3 px-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">{name}</span>
          <span className="text-xs text-gray-400 font-mono">{abbrev}</span>
        </div>
      </td>
      <td className="py-3 px-2">
        <div className="flex items-center gap-3">
          <div className="flex-1 max-w-[120px]">
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full ${rank === 1 ? 'bg-blue-500' : 'bg-gray-400'}`}
                style={{ width: `${(score / maxScore) * 100}%` }}
              />
            </div>
          </div>
          <span className="text-xs font-bold text-gray-700 w-8 text-right">{score}</span>
        </div>
      </td>
      <td className="py-3 px-2">
        <RemedyConfidenceBadge
          score={score}
          maxScore={maxScore}
          cycleCoverage={cycleCoverage}
          hasCycleMatch={hasCycleMatch}
          size="sm"
        />
      </td>
      <td className="py-3 px-2 text-xs text-gray-500">{matchCount} matches</td>
      <td className="py-3 px-2">
        <div className="flex gap-1">
          {onPin && (
            <button
              onClick={onPin}
              className={`p-1.5 rounded transition ${isPinned ? 'text-blue-600 bg-blue-50' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'}`}
              title={isPinned ? 'Unpin' : 'Pin remedy'}
            >
              <svg className="w-4 h-4" fill={isPinned ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
            </button>
          )}
          <button
            onClick={onView}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition"
            title="View remedy details"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
          
          <button
            onClick={onExpand}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition"
            title="View rubrics"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </td>
    </tr>
  );
}
