"use client";

import React, { useMemo, useState, useCallback, useRef, useEffect } from "react";
import {
  project3D,
  prismFaces,
  depthSort,
  deg,
  Point3D,
} from "@/lib/projection3d";

interface Remedy {
  abbrev: string;
  name: string;
  score: number;
  cycle_analysis?: {
    segment_coverage?: number;
    meets_threshold?: boolean;
  };
  outcome_rate?: number;
  srp_density?: number;
}

interface RemedyLandscapeProps {
  remedies: Remedy[];
  onRemedyClick?: (abbrev: string) => void;
}

const BAR_WIDTH = 30;
const SPACING = 50;
const DEFAULT_ROT_Y = 30;
const DEFAULT_ROT_X = -20;
const CX = 400;
const CY = 320;
const FOV = 900;

function getConfidence(r: Remedy): number {
  let sum = 0;
  let count = 0;
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
  if (r.srp_density !== undefined) {
    sum += r.srp_density;
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

interface FaceItem {
  points: string;
  fill: string;
  stroke: string;
  depth: number;
  remedyAbbrev?: string;
  isNoisePlane?: boolean;
}

interface TerrainLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  depth: number;
}

export default function RemedyLandscape({ remedies, onRemedyClick }: RemedyLandscapeProps) {
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
  const [noiseFloorPercent, setNoiseFloorPercent] = useState(30);
  const [animProgress, setAnimProgress] = useState(0);
  const animStartRef = useRef<number | null>(null);

  const n = remedies.length;
  const maxScore = useMemo(() => Math.max(1, ...remedies.map((r) => r.score)), [remedies]);
  const yScale = useMemo(() => 220 / maxScore, [maxScore]);
  const noiseFloorScore = maxScore * (noiseFloorPercent / 100);
  const noiseFloorY = noiseFloorScore * yScale;

  // Animated bar growth on data load
  useEffect(() => {
    animStartRef.current = null;
    setAnimProgress(0);
    let rafId: number;
    const animate = (ts: number) => {
      if (animStartRef.current === null) animStartRef.current = ts;
      const elapsed = ts - animStartRef.current;
      const t = Math.min(1, elapsed / 800);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setAnimProgress(eased);
      if (t < 1) {
        rafId = requestAnimationFrame(animate);
      }
    };
    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [remedies]);

  const totalWidth = Math.max(200, n * SPACING);
  const xMin = -(totalWidth / 2);
  const xMax = totalWidth / 2;
  const zMin = -80;
  const zMax = 80;

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

  const allFaces: FaceItem[] = useMemo(() => {
    const faces: FaceItem[] = [];

    remedies.forEach((r, i) => {
      const x = (i - (n - 1) / 2) * SPACING;
      const effectiveScore = r.score >= noiseFloorScore ? r.score : r.score * 0.2;
      const h = effectiveScore * yScale * animProgress;
      const confidence = getConfidence(r);
      const d = 20 + confidence * 60;
      const center: Point3D = { x, y: h / 2, z: 0 };
      const color = getColor(r, noiseFloorScore);

      const prism = prismFaces(center, BAR_WIDTH, h, d, rotY, rotX, CX, CY, 1, FOV, color);
      prism.forEach((f) => {
        faces.push({ ...f, remedyAbbrev: r.abbrev });
      });
    });

    const nfCorners = [
      { x: xMin, y: noiseFloorY, z: zMin },
      { x: xMax, y: noiseFloorY, z: zMin },
      { x: xMax, y: noiseFloorY, z: zMax },
      { x: xMin, y: noiseFloorY, z: zMax },
    ];
    const nfProj = nfCorners.map((p) => project3D(p, rotY, rotX, CX, CY, 1, FOV));
    const nfPoints = nfProj.map((p) => `${p.x},${p.y}`).join(" ");
    const nfDepth = nfProj.reduce((s, p) => s + p.depth, 0) / 4;
    faces.push({
      points: nfPoints,
      fill: "rgba(239,68,68,0.10)",
      stroke: "rgba(239,68,68,0.4)",
      depth: nfDepth,
      isNoisePlane: true,
    });

    return depthSort(faces);
  }, [remedies, n, yScale, noiseFloorScore, noiseFloorY, rotY, rotX, xMin, xMax, zMin, zMax, animProgress]);

  const terrainLines: TerrainLine[] = useMemo(() => {
    const lines: TerrainLine[] = [];
    for (let i = 0; i < n - 1; i++) {
      const r1 = remedies[i];
      const r2 = remedies[i + 1];
      const x1 = (i - (n - 1) / 2) * SPACING;
      const x2 = (i + 1 - (n - 1) / 2) * SPACING;

      const effectiveScore1 = r1.score >= noiseFloorScore ? r1.score : r1.score * 0.2;
      const effectiveScore2 = r2.score >= noiseFloorScore ? r2.score : r2.score * 0.2;

      const h1 = effectiveScore1 * yScale * animProgress;
      const h2 = effectiveScore2 * yScale * animProgress;

      const p1 = project3D({ x: x1, y: h1, z: 0 }, rotY, rotX, CX, CY, 1, FOV);
      const p2 = project3D({ x: x2, y: h2, z: 0 }, rotY, rotX, CX, CY, 1, FOV);

      lines.push({
        x1: p1.x,
        y1: p1.y,
        x2: p2.x,
        y2: p2.y,
        depth: (p1.depth + p2.depth) / 2,
      });
    }
    return lines.sort((a, b) => b.depth - a.depth);
  }, [remedies, n, yScale, noiseFloorScore, rotY, rotX, animProgress]);

  const labels = useMemo(() => {
    return remedies.map((r, i) => {
      const x = (i - (n - 1) / 2) * SPACING;
      const effectiveScore = r.score >= noiseFloorScore ? r.score : r.score * 0.2;
      const h = effectiveScore * yScale * animProgress;
      const p = project3D({ x, y: h + 8, z: 0 }, rotY, rotX, CX, CY, 1, FOV);
      return { x: p.x, y: p.y, abbrev: r.abbrev, depth: p.depth };
    });
  }, [remedies, n, yScale, noiseFloorScore, rotY, rotX, animProgress]);

  const gridLines = useMemo(() => {
    const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];
    const stepsX = Math.max(4, n);
    const stepsZ = 4;
    for (let i = 0; i <= stepsX; i++) {
      const x = xMin + (i / stepsX) * (xMax - xMin);
      const p1 = project3D({ x, y: 0, z: zMin }, rotY, rotX, CX, CY, 1, FOV);
      const p2 = project3D({ x, y: 0, z: zMax }, rotY, rotX, CX, CY, 1, FOV);
      lines.push({ x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y });
    }
    for (let i = 0; i <= stepsZ; i++) {
      const z = zMin + (i / stepsZ) * (zMax - zMin);
      const p1 = project3D({ x: xMin, y: 0, z }, rotY, rotX, CX, CY, 1, FOV);
      const p2 = project3D({ x: xMax, y: 0, z }, rotY, rotX, CX, CY, 1, FOV);
      lines.push({ x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y });
    }
    return lines;
  }, [rotY, rotX, xMin, xMax, zMin, zMax, n]);

  const onFaceEnter = useCallback(
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

  const onFaceLeave = useCallback(() => {
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
          This 3D landscape plots remedy candidates as vertical peaks rising from a noise-floor
          plane. Height (Y) is the remedy score; depth (Z) reflects composite confidence from cycle
          coverage, outcome history, and SRP density. Peaks that clear the red threshold plane are
          the most significant candidates. Drag the scene to rotate. Green peaks are
          cycle-confirmed; amber peaks are high-scoring but not yet confirmed by cycle analysis;
          gray peaks sit below the noise floor.
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
        <svg viewBox="0 0 800 500" className="w-full h-full">
          {/* Floor grid */}
          <g stroke="rgba(148,163,184,0.25)" strokeWidth={1}>
            {gridLines.map((ln, i) => (
              <line key={`g${i}`} x1={ln.x1} y1={ln.y1} x2={ln.x2} y2={ln.y2} />
            ))}
          </g>

          {/* Terrain mesh connecting adjacent bar tops */}
          <g stroke="rgba(148,163,184,0.35)" strokeWidth={1.5}>
            {terrainLines.map((ln, i) => (
              <line key={`t${i}`} x1={ln.x1} y1={ln.y1} x2={ln.x2} y2={ln.y2} />
            ))}
          </g>

          {/* All sorted 3D faces (bars + noise plane) */}
          {allFaces.map((f, i) => {
            const isHovered = f.remedyAbbrev && f.remedyAbbrev === hoveredAbbrev;
            const remedy = f.remedyAbbrev
              ? remedies.find((r) => r.abbrev === f.remedyAbbrev)
              : undefined;
            return (
              <polygon
                key={`f${i}`}
                points={f.points}
                fill={f.fill}
                stroke={isHovered ? "#ffffff" : f.stroke}
                strokeWidth={isHovered ? 2 : 1}
                strokeOpacity={isHovered ? 1 : 0.8}
                fillOpacity={isHovered ? 0.9 : f.isNoisePlane ? 0.15 : 0.75}
                className={f.remedyAbbrev ? "cursor-pointer" : "pointer-events-none"}
                onMouseEnter={(e) => {
                  if (remedy) onFaceEnter(e, remedy);
                }}
                onMouseLeave={onFaceLeave}
                onClick={() => {
                  if (f.remedyAbbrev && onRemedyClick) onRemedyClick(f.remedyAbbrev);
                }}
              />
            );
          })}

          {/* Labels above each bar */}
          {labels.map((lb) => (
            <text
              key={lb.abbrev}
              x={lb.x}
              y={lb.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={11}
              fill="#e2e8f0"
              className="pointer-events-none"
              style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}
            >
              {lb.abbrev}
            </text>
          ))}
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
          </div>
        )}
      </div>

      {/* Noise-floor slider */}
      <div className="mt-3 flex items-center gap-3">
        <span className="text-xs text-slate-400">Noise floor</span>
        <input
          type="range"
          min={0}
          max={100}
          value={noiseFloorPercent}
          onChange={(e) => setNoiseFloorPercent(Number(e.target.value))}
          className="w-48 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
        />
        <span className="text-xs text-slate-300 w-12">{noiseFloorPercent}%</span>
      </div>
    </div>
  );
}
