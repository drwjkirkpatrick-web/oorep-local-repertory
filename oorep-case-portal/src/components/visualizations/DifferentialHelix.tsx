"use client";

/**
 * DifferentialHelix — 3D Spiral Remedy Similarity Visualization
 *
 * Remedies are arranged along a spiral helix according to their similarity
 * to one another. The helix carries four colored tracks, one per miasm
 * (Psora=blue, Sycosis=green, Syphilis=red, Tubercular=amber). Each remedy
 * sits on the track matching its dominant miasm. Radius increases with score,
 * so higher-scoring remedies float farther from the center axis. The
 * practitioner can drag to rotate, hover for details, and click to select.
 * Clustering along the spiral reveals differential relationships; isolation
 * shows outlier remedies.
 */

import React, { useMemo, useState, useCallback, useRef, useEffect } from "react";
import { project3D, sphereProject, depthSort, deg } from "@/lib/projection3d";

interface Remedy {
  abbrev: string;
  name: string;
  score: number;
  miasm?: "psora" | "sycosis" | "syphilis" | "tubercular";
  cycle_analysis?: {
    meets_threshold?: boolean;
  };
}

interface DifferentialHelixProps {
  remedies: Remedy[];
  onRemedyClick?: (abbrev: string) => void;
}

const MIASM_COLORS: Record<string, string> = {
  psora: "#3b82f6",       // blue
  sycosis: "#16a34a",     // green
  syphilis: "#dc2626",    // red
  tubercular: "#f59e0b",  // amber
};

const MIASM_LABELS: Record<string, string> = {
  psora: "Psora",
  sycosis: "Sycosis",
  syphilis: "Syphilis",
  tubercular: "Tubercular",
};

const CX = 400;
const CY = 320;
const SCALE = 160;
const FOV = 900;
const DEFAULT_ROT_Y = 35;
const DEFAULT_ROT_X = -20;

// Helix parameters
const BASE_RADIUS = 80;
const RADIUS_SCORE_FACTOR = 0.6;
const HEIGHT_PER_TURN = 140;
const TURNS = 3;
const TRACK_OFFSET = 14; // lateral offset per miasm track from helix spine

interface HelixItem {
  abbrev: string;
  name: string;
  score: number;
  miasm: string;
  color: string;
  t: number; // angle parameter along helix
  center: { x: number; y: number; z: number };
  radius: number;
  depth: number;
  projX: number;
  projY: number;
  projR: number;
}

export default function DifferentialHelix({ remedies, onRemedyClick }: DifferentialHelixProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotY, setRotY] = useState(deg(DEFAULT_ROT_Y));
  const [rotX, setRotX] = useState(deg(DEFAULT_ROT_X));
  const [dragging, setDragging] = useState(false);
  const [lastPos, setLastPos] = useState<{ x: number; y: number } | null>(null);
  const [hoveredAbbrev, setHoveredAbbrev] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    remedy: Remedy;
    miasm: string;
  } | null>(null);

  // ── New state for auto-rotation, speed, and track filters ──
  const [isPaused, setIsPaused] = useState(false);
  const [autoRotateSpeed, setAutoRotateSpeed] = useState(0.5); // degrees per frame
  const [visibleTracks, setVisibleTracks] = useState<Record<string, boolean>>({
    psora: true,
    sycosis: true,
    syphilis: true,
    tubercular: true,
  });

  // ── Auto-rotation loop ──
  useEffect(() => {
    let rafId: number;
    const loop = () => {
      if (!dragging && !isPaused) {
        setRotY((prev) => prev + deg(autoRotateSpeed));
      }
      rafId = requestAnimationFrame(loop);
    };
    rafId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafId);
  }, [dragging, isPaused, autoRotateSpeed]);

  const maxScore = useMemo(() => Math.max(1, ...remedies.map((r) => r.score)), [remedies]);

  // ── Compute helix positions for remedies ──
  const items: HelixItem[] = useMemo(() => {
    const totalAngle = TURNS * 2 * Math.PI;

    // Assign each remedy an angle t spread across the spiral, with small
    // jitter so similar scores don't perfectly overlap.
    const raw = remedies.map((r, i) => {
      const miasm = r.miasm || "psora";
      const color = MIASM_COLORS[miasm] || MIASM_COLORS.psora;

      // Spread remedies along the spiral by score rank; higher scores near top
      const rank = remedies
        .map((x) => x.score)
        .sort((a, b) => b - a)
        .indexOf(r.score);
      const fraction = remedies.length > 1 ? rank / (remedies.length - 1) : 0.5;
      const t = fraction * totalAngle + (i * 0.08); // tiny offset per index

      // Radius grows with score
      const radius = BASE_RADIUS + (r.score / maxScore) * 60 * RADIUS_SCORE_FACTOR;

      // Helix spine
      const spineX = radius * Math.cos(t);
      const spineZ = radius * Math.sin(t);
      const spineY = -(t / (2 * Math.PI)) * HEIGHT_PER_TURN; // negative Y = upward in screen

      // Track offset: push remedy outward perpendicular to helix tangent
      // to create 4 parallel tracks. Offset direction = outward normal in XZ plane.
      const trackIndex = ["psora", "sycosis", "syphilis", "tubercular"].indexOf(miasm);
      const offset = (trackIndex - 1.5) * TRACK_OFFSET;
      const offX = offset * Math.cos(t);
      const offZ = offset * Math.sin(t);

      const center = {
        x: spineX + offX,
        y: spineY,
        z: spineZ + offZ,
      };

      const sphereRadius = 5 + (r.score / maxScore) * 10;

      const proj = sphereProject(center, sphereRadius, rotY, rotX, CX, CY, SCALE, FOV);

      return {
        abbrev: r.abbrev,
        name: r.name,
        score: r.score,
        miasm,
        color,
        t,
        center,
        radius: sphereRadius,
        depth: proj.depth,
        projX: proj.x,
        projY: proj.y,
        projR: proj.r,
      };
    });

    return depthSort(raw);
  }, [remedies, rotY, rotX, maxScore]);

  // ── Build helix spine guide lines (one per track) ──
  const trackLines = useMemo(() => {
    const lines: { x1: number; y1: number; x2: number; y2: number; color: string; miasm: string }[] = [];
    const steps = 120;
    const totalAngle = TURNS * 2 * Math.PI;

    ["psora", "sycosis", "syphilis", "tubercular"].forEach((miasm, trackIndex) => {
      const color = MIASM_COLORS[miasm];
      const offset = (trackIndex - 1.5) * TRACK_OFFSET;

      for (let i = 0; i < steps; i++) {
        const t1 = (i / steps) * totalAngle;
        const t2 = ((i + 1) / steps) * totalAngle;

        // Use average score for radius so track is a smooth ribbon
        const avgScore = maxScore * 0.6;
        const radius = BASE_RADIUS + avgScore * 0.6 * RADIUS_SCORE_FACTOR;

        const x1 = (radius + offset) * Math.cos(t1);
        const z1 = (radius + offset) * Math.sin(t1);
        const y1 = -(t1 / (2 * Math.PI)) * HEIGHT_PER_TURN;

        const x2 = (radius + offset) * Math.cos(t2);
        const z2 = (radius + offset) * Math.sin(t2);
        const y2 = -(t2 / (2 * Math.PI)) * HEIGHT_PER_TURN;

        const p1 = project3D({ x: x1, y: y1, z: z1 }, rotY, rotX, CX, CY, SCALE, FOV);
        const p2 = project3D({ x: x2, y: y2, z: z2 }, rotY, rotX, CX, CY, SCALE, FOV);

        lines.push({ x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y, color, miasm });
      }
    });

    return lines;
  }, [remedies, rotY, rotX, maxScore]);

  // ── Drag handlers ──
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setDragging(true);
    setLastPos({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (dragging && lastPos) {
        const dx = e.clientX - lastPos.x;
        const dy = e.clientY - lastPos.y;
        setRotY((prev) => prev + dx * 0.005);
        setRotX((prev) => {
          const next = prev - dy * 0.005;
          const min = deg(-60);
          const max = deg(20);
          return Math.max(min, Math.min(max, next));
        });
        setLastPos({ x: e.clientX, y: e.clientY });
      }
      if (tooltip) {
        const rect = containerRef.current?.getBoundingClientRect();
        if (rect) {
          setTooltip((t) =>
            t
              ? {
                  ...t,
                  x: e.clientX - rect.left,
                  y: e.clientY - rect.top,
                }
              : null
          );
        }
      }
    },
    [dragging, lastPos, tooltip]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(false);
    setLastPos(null);
  }, []);

  return (
    <div className="w-full rounded-xl border border-slate-700 bg-slate-900/60 p-4 shadow-lg">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-100">Differential Helix</h3>
          <p className="mt-1 max-w-xl text-sm text-slate-400">
            Remedies spiral through 3D space along four miasm tracks. Similar remedies cluster;
            isolated remedies stand apart. Drag to rotate. Size reflects score, radius reflects
            prominence.
          </p>
        </div>
        <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-xs font-semibold text-indigo-300">
          ADVANCED
        </span>
      </div>

      {/* Legend */}
      <div className="mb-2 flex flex-wrap items-center gap-3">
        {Object.entries(MIASM_COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-1.5 text-xs text-slate-300">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: color }}
            />
            {MIASM_LABELS[key]}
          </div>
        ))}
      </div>

      {/* Track filter buttons */}
      <div className="mb-3 flex flex-wrap gap-2">
        {Object.entries(MIASM_COLORS).map(([key, color]) => {
          const active = visibleTracks[key];
          return (
            <button
              key={key}
              onClick={() =>
                setVisibleTracks((prev) => ({ ...prev, [key]: !prev[key] }))
              }
              className={`flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition-opacity ${
                active ? "opacity-100" : "opacity-40 line-through"
              }`}
              style={{
                backgroundColor: color + "20",
                color,
                border: `1px solid ${color}`,
              }}
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: color }}
              />
              {MIASM_LABELS[key]}
            </button>
          );
        })}
      </div>

      {/* 3D Canvas */}
      <div
        ref={containerRef}
        className="relative cursor-move select-none overflow-hidden rounded-lg border border-slate-700 bg-slate-950"
        style={{ width: "100%", height: 520 }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg width="100%" height="100%" viewBox={`0 0 ${CX * 2} ${CY * 2}`}>
          {/* Helix track lines (back-to-front-ish via simple opacity layering) */}
          <g opacity={0.35}>
            {trackLines
              .filter((ln) => visibleTracks[ln.miasm])
              .map((ln, i) => (
                <line
                  key={`t-${i}`}
                  x1={ln.x1}
                  y1={ln.y1}
                  x2={ln.x2}
                  y2={ln.y2}
                  stroke={ln.color}
                  strokeWidth={2}
                />
              ))}
          </g>

          {/* Remedy spheres */}
          {items
            .filter((item) => visibleTracks[item.miasm])
            .map((item) => {
              const isHovered = hoveredAbbrev === item.abbrev;
              const ringR = item.projR + (item.score / maxScore) * 15;
              return (
                <g
                  key={item.abbrev}
                  onMouseEnter={(e) => {
                    setHoveredAbbrev(item.abbrev);
                    const rect = containerRef.current?.getBoundingClientRect();
                    if (rect) {
                      setTooltip({
                        x: e.clientX - rect.left,
                        y: e.clientY - rect.top,
                        remedy: {
                          abbrev: item.abbrev,
                          name: item.name,
                          score: item.score,
                          miasm: item.miasm as Remedy["miasm"],
                        },
                        miasm: item.miasm,
                      });
                    }
                  }}
                  onMouseLeave={() => {
                    setHoveredAbbrev(null);
                    setTooltip(null);
                  }}
                  onClick={() => onRemedyClick?.(item.abbrev)}
                  style={{ cursor: "pointer" }}
                >
                  {/* Glow */}
                  <circle
                    cx={item.projX}
                    cy={item.projY}
                    r={item.projR * (isHovered ? 2.2 : 1.6)}
                    fill={item.color}
                    opacity={isHovered ? 0.25 : 0.12}
                  />
                  {/* Score ring */}
                  <circle
                    cx={item.projX}
                    cy={item.projY}
                    r={ringR}
                    fill="none"
                    stroke={item.color}
                    strokeWidth={1.5}
                    opacity={0.8}
                  />
                  {/* Core sphere */}
                  <circle
                    cx={item.projX}
                    cy={item.projY}
                    r={item.projR}
                    fill={item.color}
                    stroke={isHovered ? "#ffffff" : "rgba(255,255,255,0.2)"}
                    strokeWidth={isHovered ? 2 : 1}
                  />
                  {/* Label (only when hovered or large) */}
                  {(isHovered || item.projR > 9) && (
                    <text
                      x={item.projX}
                      y={item.projY - item.projR - 6}
                      textAnchor="middle"
                      fill="#e2e8f0"
                      fontSize={11}
                      fontWeight={600}
                      style={{ pointerEvents: "none" }}
                    >
                      {item.abbrev}
                    </text>
                  )}
                </g>
              );
            })}
        </svg>

        {/* Tooltip */}
        {tooltip && (
          <div
            className="pointer-events-none absolute z-10 rounded-md border border-slate-600 bg-slate-800/95 px-3 py-2 text-xs shadow-xl"
            style={{
              left: Math.min(tooltip.x + 14, (containerRef.current?.clientWidth || 800) - 180),
              top: Math.max(tooltip.y - 10, 8),
            }}
          >
            <div className="font-semibold text-slate-100">{tooltip.remedy.name}</div>
            <div className="mt-0.5 text-slate-300">
              <span
                className="mr-1 inline-block h-2 w-2 rounded-full align-middle"
                style={{ backgroundColor: MIASM_COLORS[tooltip.miasm] }}
              />
              {MIASM_LABELS[tooltip.miasm]} · Score {tooltip.remedy.score.toFixed(1)}
            </div>
            {tooltip.remedy.cycle_analysis?.meets_threshold && (
              <div className="mt-1 text-emerald-400">Meets cycle threshold</div>
            )}
          </div>
        )}

        {/* Drag hint */}
        <div className="pointer-events-none absolute bottom-2 right-2 text-[10px] text-slate-500">
          Drag to rotate · Scroll to zoom (not implemented)
        </div>
      </div>

      {/* Controls: Pause + Speed */}
      <div className="mt-3 flex items-center gap-4">
        <button
          onClick={() => setIsPaused((p) => !p)}
          className="rounded bg-slate-700 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-slate-600"
        >
          {isPaused ? "▶ Play" : "⏸ Pause"}
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Speed:</span>
          {[0.2, 0.5, 1.0].map((speed) => (
            <button
              key={speed}
              onClick={() => setAutoRotateSpeed(speed)}
              className={`rounded px-2 py-0.5 text-xs ${
                autoRotateSpeed === speed
                  ? "bg-indigo-500/20 text-indigo-300"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {speed === 0.2 ? "Slow" : speed === 0.5 ? "Medium" : "Fast"}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
