"use client";

/**
 * PanelSkeleton.tsx
 * Loading skeletons for dashboard panels
 */

import React from 'react';

interface PanelSkeletonProps {
  height?: 'sm' | 'md' | 'lg' | 'xl';
  showHeader?: boolean;
  rows?: number;
}

export default function PanelSkeleton({
  height = 'md',
  showHeader = true,
  rows = 4,
}: PanelSkeletonProps) {
  const heightClasses = {
    sm: 'h-32',
    md: 'h-48',
    lg: 'h-64',
    xl: 'h-96',
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 animate-pulse">
      {showHeader && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-gray-200 rounded-full" />
            <div className="h-4 bg-gray-200 rounded w-32" />
          </div>
          <div className="h-3 bg-gray-200 rounded w-16" />
        </div>
      )}

      <div className={`${heightClasses[height]} bg-gray-50 rounded-md`}>
        {rows > 0 && (
          <div className="p-3 space-y-3">
            {Array.from({ length: rows }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gray-200 rounded-full shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-3/4" />
                  <div className="h-2 bg-gray-200 rounded w-1/2" />
                </div>
                <div className="w-12 h-6 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * RemedyRowSkeleton - Skeleton for remedy list rows
 */
export function RemedyRowSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-2 animate-pulse">
          <div className="w-6 h-6 bg-gray-200 rounded-full" />
          <div className="w-24 h-4 bg-gray-200 rounded" />
          <div className="flex-1 h-2 bg-gray-100 rounded-full">
            <div className="h-full bg-gray-200 rounded-full w-2/3" />
          </div>
          <div className="w-8 h-4 bg-gray-200 rounded" />
        </div>
      ))}
    </div>
  );
}

/**
 * ChartSkeleton - Skeleton for chart/visualization panels
 */
export function ChartSkeleton() {
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="h-4 bg-gray-200 rounded w-40" />
        <div className="h-3 bg-gray-200 rounded w-20" />
      </div>
      
      <div className="h-64 bg-gray-50 rounded-md flex items-end justify-center gap-2 p-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div 
            key={i}
            className="w-8 bg-gray-200 rounded-t"
            style={{ height: `${20 + Math.random() * 60}%` }}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * TableSkeleton - Skeleton for table panels
 */
export function TableSkeleton({ columns = 4, rows = 5 }: { columns?: number; rows?: number }) {
  return (
    <div className="bg-white rounded-lg border shadow-sm animate-pulse">
      <div className="p-4 border-b">
        <div className="h-4 bg-gray-200 rounded w-32" />
      </div>
      
      <div className="p-4">
        <div className="flex gap-4 mb-3">
          {Array.from({ length: columns }).map((_, i) => (
            <div key={i} className="flex-1 h-3 bg-gray-200 rounded" />
          ))}
        </div>
        
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4 py-2 border-b last:border-0">
            {Array.from({ length: columns }).map((_, j) => (
              <div key={j} className="flex-1 h-3 bg-gray-100 rounded" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
