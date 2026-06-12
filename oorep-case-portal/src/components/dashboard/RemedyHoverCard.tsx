"use client";

/**
 * RemedyHoverCard.tsx
 * Hover preview cards for remedy quick info
 */

import React, { useState, useRef } from 'react';

interface RemedyHoverCardProps {
  children: React.ReactNode;
  remedy: {
    name: string;
    abbrev: string;
    kingdom?: string;
    family?: string;
    source?: string;
    provingDate?: string;
    keySymptoms?: string[];
    miasmaticAffinity?: string[];
    complementary?: string[];
    antidotes?: string[];
  };
  delay?: number;
}

export default function RemedyHoverCard({
  children,
  remedy,
  delay = 300,
}: RemedyHoverCardProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPosition({
      x: rect.right + 10,
      y: rect.top,
    });
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // Kingdom color mapping
  const kingdomColors: Record<string, string> = {
    plant: 'bg-green-100 text-green-800',
    mineral: 'bg-blue-100 text-blue-800',
    animal: 'bg-orange-100 text-orange-800',
    nosode: 'bg-purple-100 text-purple-800',
  };

  return (
    <div
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="inline-block"
    >
      {children}
      
      {isVisible && (
        <div
          className="fixed z-50 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 animate-in fade-in zoom-in-95 duration-150"
          style={{
            left: position.x,
            top: position.y,
            maxHeight: 'calc(100vh - 40px)',
            overflowY: 'auto',
          }}
        >
          {/* Header */}
          <div className="p-4 border-b bg-gradient-to-r from-gray-50 to-white">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-bold text-gray-900">{remedy.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-mono text-gray-500">{remedy.abbrev}</span>
                  {remedy.kingdom && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${kingdomColors[remedy.kingdom] || 'bg-gray-100 text-gray-600'}`}>
                      {remedy.kingdom.charAt(0).toUpperCase() + remedy.kingdom.slice(1)}
                    </span>
                  )}
                </div>
              </div>
              
              {remedy.family && (
                <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-1 rounded">
                  {remedy.family}
                </span>
              )}
            </div>
            
            {(remedy.source || remedy.provingDate) && (
              <div className="mt-2 text-[10px] text-gray-400">
                {remedy.source && <span>Source: {remedy.source}</span>}
                {remedy.provingDate && <span className="ml-2">Proving: {remedy.provingDate}</span>}
              </div>
            )}
          </div>

          {/* Key Symptoms */}
          {remedy.keySymptoms && remedy.keySymptoms.length > 0 && (
            <div className="p-4 border-b">
              <h5 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-2">Key Symptoms</h5>
              <ul className="space-y-1">
                {remedy.keySymptoms.slice(0, 5).map((symptom, i) => (
                  <li key={i} className="text-xs text-gray-700 flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span className="line-clamp-2">{symptom}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Relationships */}
          <div className="p-4">
            <div className="grid grid-cols-2 gap-3">
              {remedy.complementary && remedy.complementary.length > 0 && (
                <div>
                  <h5 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Complementary</h5>
                  <div className="flex flex-wrap gap-1">
                    {remedy.complementary.map((comp, i) => (
                      <span key={i} className="text-[10px] px-1.5 py-0.5 bg-green-50 text-green-700 rounded">
                        {comp}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {remedy.antidotes && remedy.antidotes.length > 0 && (
                <div>
                  <h5 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Antidotes</h5>
                  <div className="flex flex-wrap gap-1">
                    {remedy.antidotes.map((ant, i) => (
                      <span key={i} className="text-[10px] px-1.5 py-0.5 bg-red-50 text-red-700 rounded">
                        {ant}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Miasmatic Affinity */}
            {remedy.miasmaticAffinity && remedy.miasmaticAffinity.length > 0 && (
              <div className="mt-3 pt-3 border-t">
                <h5 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Miasmatic Affinity</h5>
                <div className="flex gap-1">
                  {remedy.miasmaticAffinity.map((miasm, i) => (
                    <span key={i} className="text-[10px] px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded">
                      {miasm}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 bg-gray-50 border-t text-center">
            <span className="text-[10px] text-gray-400">Click for full remedy profile →</span>
          </div>
        </div>
      )}
    </div>
  );
}
