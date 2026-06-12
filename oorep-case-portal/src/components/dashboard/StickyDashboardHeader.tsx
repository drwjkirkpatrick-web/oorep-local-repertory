"use client";

/**
 * StickyDashboardHeader.tsx
 * Sticky header with quick actions, patient context, and real-time indicators
 */

import React, { useState, useEffect } from 'react';

interface PatientContext {
  id: string;
  name: string;
  age?: number;
  lastVisit?: string;
  constitutionalRemedy?: string;
}

interface StickyDashboardHeaderProps {
  patient?: PatientContext;
  activeModules: number;
  totalModules: number;
  onRunAll: () => void;
  onClearAll: () => void;
  onExport: () => void;
  isRunning: boolean;
  lastUpdated?: Date;
}

export default function StickyDashboardHeader({
  patient,
  activeModules,
  totalModules,
  onRunAll,
  onClearAll,
  onExport,
  isRunning,
  lastUpdated,
}: StickyDashboardHeaderProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        switch (e.key) {
          case 'Enter':
            e.preventDefault();
            onRunAll();
            break;
          case 'e':
            e.preventDefault();
            onExport();
            break;
          case 'k':
            e.preventDefault();
            setShowShortcuts(true);
            break;
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onRunAll, onExport]);

  return (
    <>
      <header 
        className={`sticky top-0 z-50 transition-all duration-200 ${
          isScrolled 
            ? 'bg-white/95 backdrop-blur-md shadow-md border-b border-gray-200' 
            : 'bg-white border-b border-gray-200'
        }`}
      >
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Left: Logo & Patient Context */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">O</span>
                </div>
                <div>
                  <h1 className="font-bold text-gray-900 text-sm">Clinical Mission Control</h1>
                  <p className="text-[10px] text-gray-500">OOREP v3.8</p>
                </div>
              </div>

              {/* Patient Context */}
              {patient && (
                <div className="hidden md:flex items-center gap-3 pl-4 border-l border-gray-200">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center text-xs">
                      {patient.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-900">{patient.name}</p>
                      {patient.constitutionalRemedy && (
                        <p className="text-[10px] text-purple-600">
                          Const: {patient.constitutionalRemedy}
                        </p>
                      )}
                    </div>
                  </div>
                  {patient.lastVisit && (
                    <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      Last: {patient.lastVisit}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Center: Module Status */}
            <div className="hidden lg:flex items-center gap-2">
              <div className="flex items-center gap-1.5 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-full">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>{activeModules} of {totalModules} modules active</span>
              </div>
              {lastUpdated && (
                <span className="text-[10px] text-gray-400">
                  Updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>

            {/* Right: Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={onClearAll}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Clear
              </button>

              <button
                onClick={onExport}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export
                <kbd className="hidden xl:inline-block px-1 bg-gray-200 rounded text-[10px]">⌘E</kbd>
              </button>

              <div className="h-6 w-px bg-gray-200 mx-1" />

              <button
                onClick={onRunAll}
                disabled={isRunning}
                className={`flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md transition ${
                  isRunning
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
                }`}
              >
                {isRunning ? (
                  <>
                    <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Running...
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Run All
                    <kbd className="hidden xl:inline-block px-1 bg-blue-500 rounded text-[10px]">⌘↵</kbd>
                  </>
                )}
              </button>

              <button
                onClick={() => setShowShortcuts(true)}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition"
                title="Keyboard shortcuts"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Keyboard Shortcuts Modal */}
      {showShortcuts && (
        <div 
          className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4"
          onClick={() => setShowShortcuts(false)}
        >
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4">Keyboard Shortcuts</h3>
            <div className="space-y-2">
              {[
                { key: '⌘ + Enter', action: 'Run all active modules' },
                { key: '⌘ + E', action: 'Export report' },
                { key: '⌘ + K', action: 'Show this help' },
                { key: 'Esc', action: 'Close modals/panels' },
                { key: '↑ / ↓', action: 'Navigate remedy list' },
                { key: 'Space', action: 'Toggle remedy pin' },
              ].map((shortcut, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                  <span className="text-sm text-gray-600">{shortcut.action}</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">{shortcut.key}</kbd>
                </div>
              ))}
            </div>
            <button 
              onClick={() => setShowShortcuts(false)}
              className="mt-4 w-full py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
