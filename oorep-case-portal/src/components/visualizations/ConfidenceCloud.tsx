"use client";

/**
 * ConfidenceCloud — 3D Uncertainty-Space Remedy Visualization
 *
 * Remedy candidates float as spheres in 3D space. Sphere size = score.
 * Sphere opacity = confidence. Low-confidence remedies appear ghostly
 * (faint, small), high-confidence remedies appear solid and prominent.
 * This lets the practitioner visually filter noise at a glance.
 *
 * Features:
 *  • Auto-rotation with pause/play toggle (0.4°/frame)
 *  • Ghost-filter slider hides low-confidence remedies
 *  • Gentle vertical float animation per sphere (cycle-coverage driven)
 */

import React, { useMemo, useState, useCallback, useRef, useEffect } from "react";
import { project3D, sphereProject, depthSort, deg, Point3D } from "@/lib/projection3d";

interface Remedy {
  abbrev: string;
  name: string;
  score: number;
  cycle_analysis?: {
    segment_coverage?: number;
    meets_threshold?: boolean;
  };
  outcome_rate?: number;
  phantom_risk?: number;
}

interface ConfidenceCloudProps {
  remedies: Remedy[];
  onRemedyClick?: (abbrev: string) => void;
}

const DEFAULT_ROT_Y = 35;
const DEFAULT_ROT_X = -25;
const CX = 400;
const CY = 300;
const SCALE = 2.5;
const FOV = 900;

function getConfidence(r: Remedy): number {
  let sum = 0;
  let count = 0;

  if (r.phantom_risk !== undefined) {
    sum += Math.max(0, Math.min(1, 1 - r.phantom_risk));
    count += 1;
  }
  if (r.cycle_analysis?.meets_threshold !== undefined) {
    sum += r.cycle_analysis.meets_threshold ? 1 : 0;
    count += 1;
  }
  if (r.cycle_analysis?.segment_coverage !== undefined) {
    sum += r.cycle_analysis.segment_coverage;
    count += 1;
  }
  if (r.outcome_rate !== undefined) {
    sum += r.outcome_rate;
    count += 1;
  }

  if (count === 0) return 0.5;
  return Math.max(0.1, Math.min(1, sum / count));
}

function getColor(r: Remedy, thresholdScore: number): string {
  if (r.cycle_analysis?.meets_threshold) return "#22c55e"; // green
  if (r.score >= thresholdScore) return "#f59e0b"; // amber
  return "#9ca3af"; // gray
}

interface BaseItem {
  abbrev: string;
  name: string;
  score: number;
  confidence: number;
  meetsThreshold: boolean;
  baseCenter: Point3D;
  radius: number;
  color: string;
  coverage: number;
  phaseOffset: number;
}

interface SphereItem extends BaseItem {
  depth: number;
  projX: number;
  projY: number;
  projR: number;
}

export default function ConfidenceCloud({ remedies, onRemedyClick }: ConfidenceCloudProps) {
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
    confidence: number;
  } | null>(null);
  const [ghostFilter, setGhostFilter] = useState(0);
  const [autoRotatePaused, setAutoRotatePaused] = useState(false);
  const [time, setTime] = useState(0);

  /* ---------- rAF loop: time + auto-rotation ---------- */
  useEffect(() => {
    let raf: number;
    let prev = performance.now();
    const tick = (now: number) => {
      setTime(now);
      if (!dragging && !autoRotatePaused) {
        const dt = Math.min((now - prev) / 1000, 0.05);
        setRotY((rPrev) => rPrev + dt * 0.419); // ≈0.4°/frame at 60 fps
      }
      prev = now;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [dragging, autoRotatePaused]);

  const maxScore = useMemo(() => Math.max(1, ...remedies.map((r) => r.score)), [remedies]);
  const thresholdScore = maxScore * 0.3;

  /* ---------- static base data (no animation) ---------- */
  const baseItems: BaseItem[] = useMemo(() => {
    return remedies.map((r, i) => {
      const confidence = getConfidence(r);
      const coverage = r.cycle_analysis?.segment_coverage ?? 0.5;
      const outcome = r.outcome_rate ?? 0.5;

      // 3D position
      const x = ((r.score / maxScore) * 240) - 120;
      const y = -(outcome * 200) + 100; // higher outcome = higher up (more negative Y)
      const z = (coverage * 200) - 100;

      return {
        abbrev: r.abbrev,
        name: r.name,
        score: r.score,
        confidence,
        meetsThreshold: r.cycle_analysis?.meets_threshold ?? false,
        baseCenter: { x, y, z },
        radius: (r.score / maxScore) * 20,
        color: getColor(r, thresholdScore),
        coverage,
        phaseOffset: i * 1.7,
      };
    });
  }, [remedies, maxScore, thresholdScore]);

  /* ---------- animated projection (float + sort) ---------- */
  const spheres: SphereItem[] = useMemo(() => {
    const items = baseItems.map((item) => {
      // Float: higher coverage → faster freq & larger amplitude
      const freq = 0.001 + item.coverage * 0.002; // rad/ms
      const amp = item.coverage * 12; // world units
      const floatY = Math.sin(time * freq + item.phaseOffset) * amp;

      const center: Point3D = {
        x: item.baseCenter.x,
        y: item.baseCenter.y + floatY,
        z: item.baseCenter.z,
      };

      const proj = sphereProject(center, item.radius, rotY, rotX, CX, CY, SCALE, FOV);

      return {
        ...item,
        depth: proj.depth,
        projX: proj.x,
        projY: proj.y,
        projR: proj.r,
      };
    });

    return depthSort(items);
  }, [baseItems, time, rotY, rotX]);

  const gridLines = useMemo(() => {
    const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];
    const steps = 5;
    const min = -140;
    const max = 140;

    for (let i = 0; i <= steps; i++) {
      const v = min + (i / steps) * (max - min);
      // X-Z plane at y = 100 (bottom of space)
      const p1 = project3D({ x: v, y: 100, z: min }, rotY, rotX, CX, CY, SCALE, FOV);
      const p2 = project3D({ x: v, y: 100, z: max }, rotY, rotX, CX, CY, SCALE, FOV);
      lines.push({ x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y });

      const p3 = project3D({ x: min, y: 100, z: v }, rotY, rotX, CX, CY, SCALE, FOV);
      const p4 = project3D({ x: max, y: 100, z: v }, rotY, rotX, CX, CY, SCALE, FOV);
      lines.push({ x1: p3.x, y1: p3.y, x2: p4.x, y2: p4.y });
    }

    // Vertical pillars at corners
    const corners = [
      { x: min, z: min },
      { x: max, z: min },
      { x: max, z: max },
      { x: min, z: max },
    ];
    corners.forEach((c) => {
      const bottom = project3D({ x: c.x, y: 100, z: c.z }, rotY, rotX, CX, CY, SCALE, FOV);
      const top = project3D({ x: c.x, y: -100, z: c.z }, rotY, rotX, CX, CY, SCALE, FOV);
      lines.push({ x1: bottom.x, y1: bottom.y, x2: top.x, y2: top.y });
    });

    return lines;
  }, [rotY, rotX]);

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

  const onSphereEnter = useCallback(
    (e: React.MouseEvent, r: Remedy) => {
      setHoveredAbbrev(r.abbrev);
      const rect = containerRef.current?.getBoundingClientRect();
      setTooltip({
        x: e.clientX - (rect?.left ?? 0),
        y: e.clientY - (rect?.top ?? 0),
        remedy: r,
        confidence: getConfidence(r),
      });
    },
    []
  );

  const onSphereLeave = useCallback(() => {
    setHoveredAbbrev(null);
    setTooltip(null);
  }, []);

  return (
    <div className="w-full">
      <div className="flex items-start gap-3 mb-3">
        <span className="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          INTERMEDIATE
        </span>
        <p className="text-xs text-slate-400 italic leading-relaxed">
          This 3D cloud plots remedy candidates as floating spheres in uncertainty space.
          Position (X, Y, Z) maps score, outcome rate, and cycle coverage. Sphere radius
          reflects the remedy score, while opacity reflects confidence — ghostly spheres
          are low-confidence noise, solid spheres are strong signal. Green spheres are
          cycle-confirmed; amber spheres are high-scoring but not yet cycle-confirmed;
          gray spheres sit below the significance threshold. Drag the scene to rotate.
        </p>
      </div>

      <div
        ref={containerRef}
        className={`relative w-full h-96 bg-slate-900 rounded-lg overflow-hidden select-none ${
          dragging ? "cursor-grabbing" : "cursor-grab"
        }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg viewBox="0 0 800 600" className="w-full h-full">
          {/* Floor grid */}
          <g stroke="rgba(148,163,184,0.15)" strokeWidth={1}>
            {gridLines.map((ln, i) => (
              <line key={`g${i}`} x1={ln.x1} y1={ln.y1} x2={ln.x2} y2={ln.y2} />
            ))}
          </g>

          {/* Depth-sorted spheres */}
          {spheres.map((s) => {
            const isHovered = s.abbrev === hoveredAbbrev;
            const remedy = remedies.find((r) => r.abbrev === s.abbrev);
            if (!remedy) return null;

            // Ghostly low-confidence: low opacity, slightly smaller radius
            const baseOpacity = 0.2 + s.confidence * 0.8;
            let opacity = isHovered ? Math.min(1, baseOpacity + 0.2) : baseOpacity;
            const rProj = isHovered ? s.projR * 1.15 : s.projR;

            // Ghost filter: fade to 0 if confidence is below slider threshold
            const isGhost = s.confidence * 100 < ghostFilter;
            if (isGhost) opacity = 0;

            return (
              <g key={s.abbrev}>
                {/* Glow halo for high confidence */}
                {!isGhost && s.confidence > 0.75 && (
                  <circle
                    cx={s.projX}
                    cy={s.projY}
                    r={rProj + 10}
                    fill={s.color}
                    opacity={0.12}
                    style={{ pointerEvents: "none" }}
                  />
                )}
                <circle
                  cx={s.projX}
                  cy={s.projY}
                  r={rProj}
                  fill={s.color}
                  fillOpacity={opacity}
                  stroke={isHovered ? "#ffffff" : s.color}
                  strokeWidth={isHovered ? 2 : 1}
                  strokeOpacity={isHovered ? 1 : 0.6}
                  className="cursor-pointer"
                  style={{
                    transition: "all 0.15s ease",
                    pointerEvents: opacity <= 0 ? "none" : "all",
                  }}
                  onMouseEnter={(e) => onSphereEnter(e, remedy)}
                  onMouseLeave={onSphereLeave}
                  onClick={() => onRemedyClick && onRemedyClick(s.abbrev)}
                />
                {/* Label */}
                <text
                  x={s.projX}
                  y={s.projY - rProj - 6}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={10}
                  fill="#e2e8f0"
                  className="pointer-events-none"
                  style={{
                    textShadow: "0 1px 3px rgba(0,0,0,0.8)",
                    opacity: isGhost ? 0 : isHovered ? 1 : Math.max(0.3, s.confidence),
                  }}
                >
                  {s.abbrev}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute z-10 px-3 py-2 rounded-md bg-slate-800 border border-slate-600 shadow-lg text-xs text-slate-100 pointer-events-none"
            style={{
              left: tooltip.x + 12,
              top: tooltip.y - 12,
            }}
          >
            <div className="font-semibold">{tooltip.remedy.name}</div>
            <div className="text-slate-400">{tooltip.remedy.abbrev}</div>
            <div className="mt-1">
              Score: <span className="text-sky-300">{tooltip.remedy.score.toFixed(1)}</span>
            </div>
            <div>
              Confidence:{" "}
              <span className="text-emerald-300">{(tooltip.confidence * 100).toFixed(0)}%</span>
            </div>
            {tooltip.remedy.cycle_analysis?.meets_threshold && (
              <div className="text-emerald-400 mt-0.5">Cycle confirmed</div>
            )}
            {tooltip.remedy.phantom_risk !== undefined && (
              <div>
                Phantom risk:{" "}
                <span className="text-rose-300">{(tooltip.remedy.phantom_risk * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 mt-2 px-1">
        <button
          onClick={() => setAutoRotatePaused((p) => !p)}
          className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition"
          title={autoRotatePaused ? "Resume rotation" : "Pause rotation"}
        >
          {autoRotatePaused ? (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          )}
          {autoRotatePaused ? "Play" : "Pause"}
        </button>

        <div className="flex items-center gap-2 flex-1">
          <label htmlFor="ghost-filter" className="text-xs text-slate-400 whitespace-nowrap">
            Hide ghosts below:
          </label>
          <input
            id="ghost-filter"
            type="range"
            min={0}
            max={100}
            value={ghostFilter}
            onChange={(e) => setGhostFilter(Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
          <span className="text-xs text-slate-300 w-8 text-right">{ghostFilter}%</span>
        </div>
      </div>
    </div>
  );
}
