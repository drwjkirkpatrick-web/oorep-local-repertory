"use client";

/**
 * SymptomConstellation — 3D Spatial Remedy Coverage View
 *
 * Symptoms are fixed as white star-like dots on a spherical shell (golden-angle
 * distribution). Remedy spheres float at the centroid of the symptoms they cover,
 * with connecting lines whose opacity reflects match weight. Sphere size maps to
 * remedy score and colour maps to rank (green = 1st, blue = 2nd, amber = 3rd).
 * Drag to rotate, hover for details, click to explore.
 */

import React, { useMemo, useState, useCallback, useRef } from "react";
import {
  project3D,
  sphereProject,
  depthSort,
  deg,
  Point3D,
} from "@/lib/projection3d";

interface Match {
  rubric?: string;
  weight?: number;
  grade?: number;
}

interface Remedy {
  abbrev: string;
  name: string;
  score: number;
  matches?: Match[];
}

interface SymptomConstellationProps {
  remedies: Remedy[];
  onRemedyClick?: (abbrev: string) => void;
  onRubricClick?: (rubric: string) => void;
}

const DEFAULT_ROT_Y = 30;
const DEFAULT_ROT_X = -20;
const CX = 400;
const CY = 300;
const SCALE = 1;
const FOV = 900;
const SHELL_RADIUS = 220;

function fibonacciSphere(n: number, radius: number): Point3D[] {
  if (n <= 0) return [];
  if (n === 1) return [{ x: 0, y: radius, z: 0 }];
  const points: Point3D[] = [];
  const phi = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = 1 - (i / (n - 1)) * 2;
    const theta = phi * i;
    const r = Math.sqrt(1 - y * y) * radius;
    points.push({ x: Math.cos(theta) * r, y: y * radius, z: Math.sin(theta) * r });
  }
  return points;
}

function getRemedyColor(rank: number): string {
  if (rank === 0) return "#22c55e"; // green
  if (rank === 1) return "#3b82f6"; // blue
  if (rank === 2) return "#f59e0b"; // amber
  return "#9ca3af"; // gray
}

export default function SymptomConstellation({
  remedies,
  onRemedyClick,
  onRubricClick,
}: SymptomConstellationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotY, setRotY] = useState(deg(DEFAULT_ROT_Y));
  const [rotX, setRotX] = useState(deg(DEFAULT_ROT_X));
  const [zoom, setZoom] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [lastPos, setLastPos] = useState<{ x: number; y: number } | null>(null);
  const [hoveredAbbrev, setHoveredAbbrev] = useState<string | null>(null);
  const [hoveredRubric, setHoveredRubric] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    content: React.ReactNode;
  } | null>(null);

  /* ── unique symptoms on sphere shell ── */
  const { symptomMap, symptomGradeMap, maxWeight } = useMemo(() => {
    const map = new Map<string, Point3D>();
    const gradeMap = new Map<string, number>();
    let maxW = 1;

    const uniqueRubrics = Array.from(
      new Set(
        remedies.flatMap((r) =>
          r.matches?.map((m) => m.rubric ?? "Unknown") ?? []
        )
      )
    );

    remedies.forEach((r) => {
      r.matches?.forEach((m) => {
        const w = m.weight ?? 1;
        if (w > maxW) maxW = w;
        const g = m.grade ?? 1;
        const rubric = m.rubric ?? "Unknown";
        const existing = gradeMap.get(rubric);
        if (existing === undefined || g > existing) {
          gradeMap.set(rubric, g);
        }
      });
    });

    const positions = fibonacciSphere(uniqueRubrics.length, SHELL_RADIUS);
    uniqueRubrics.forEach((rubric, i) => {
      map.set(rubric, positions[i]);
    });

    return { symptomMap: map, symptomGradeMap: gradeMap, maxWeight: maxW };
  }, [remedies]);

  const maxScore = useMemo(
    () => Math.max(1, ...remedies.map((r) => r.score)),
    [remedies]
  );

  const sortedRemedies = useMemo(
    () => [...remedies].sort((a, b) => b.score - a.score),
    [remedies]
  );

  /* ── remedy spheres ── */
  const remedyItems = useMemo(() => {
    return sortedRemedies.map((r, idx) => {
      const color = getRemedyColor(idx);
      const matchRubrics =
        r.matches?.map((m) => m.rubric ?? "Unknown") ?? [];
      const matchedPositions = matchRubrics
        .map((rub) => symptomMap.get(rub))
        .filter((p): p is Point3D => !!p);

      let center: Point3D = { x: 0, y: 0, z: 0 };
      if (matchedPositions.length > 0) {
        center = {
          x:
            matchedPositions.reduce((s, p) => s + p.x, 0) /
            matchedPositions.length,
          y:
            matchedPositions.reduce((s, p) => s + p.y, 0) /
            matchedPositions.length,
          z:
            matchedPositions.reduce((s, p) => s + p.z, 0) /
            matchedPositions.length,
        };
      }

      const radius = (r.score / maxScore) * 15;
      const proj = sphereProject(center, radius, rotY, rotX, CX, CY, SCALE * zoom, FOV);

      return {
        abbrev: r.abbrev,
        name: r.name,
        score: r.score,
        matchCount: matchRubrics.length,
        matches: r.matches ?? [],
        color,
        proj,
      };
    });
  }, [sortedRemedies, symptomMap, maxScore, rotY, rotX, zoom]);

  /* ── symptom dots ── */
  const symptomItems = useMemo(() => {
    const items: {
      id: string;
      rubric: string;
      proj: { x: number; y: number; r: number; depth: number };
      grade: number;
      opacity: number;
    }[] = [];
    symptomMap.forEach((pos, rubric) => {
      const grade = symptomGradeMap.get(rubric) ?? 1;
      const baseR = 2;
      const r = baseR + (grade - 1) * 1.5;
      const opacity = 0.3 + (grade / 4) * 0.7;
      const proj = sphereProject(pos, r, rotY, rotX, CX, CY, SCALE * zoom, FOV);
      items.push({ id: `symptom-${rubric}`, rubric, proj, grade, opacity });
    });
    return items;
  }, [symptomMap, symptomGradeMap, rotY, rotX, zoom]);

  /* ── connecting lines (remedy center to symptom) ── */
  const lineItems = useMemo(() => {
    const items: {
      id: string;
      x1: number;
      y1: number;
      x2: number;
      y2: number;
      opacity: number;
      depth: number;
    }[] = [];

    remedyItems.forEach((rem) => {
      rem.matches.forEach((m) => {
        const rubric = m.rubric ?? "Unknown";
        const sp = symptomMap.get(rubric);
        if (!sp) return;
        const sProj = project3D(sp, rotY, rotX, CX, CY, SCALE * zoom, FOV);
        const weight = m.weight ?? 1;
        const opacity = maxWeight > 0 ? weight / maxWeight : 1;
        const depth = (rem.proj.depth + sProj.depth) / 2;
        items.push({
          id: `line-${rem.abbrev}-${rubric}`,
          x1: rem.proj.x,
          y1: rem.proj.y,
          x2: sProj.x,
          y2: sProj.y,
          opacity,
          depth,
        });
      });
    });

    return items;
  }, [remedyItems, symptomMap, maxWeight, rotY, rotX, zoom]);

  /* ── constellation polygon lines per remedy ── */
  const constellationItems = useMemo(() => {
    const items: {
      id: string;
      x1: number;
      y1: number;
      x2: number;
      y2: number;
      color: string;
      depth: number;
    }[] = [];

    sortedRemedies.forEach((r, idx) => {
      const color = getRemedyColor(idx);
      const matchRubrics = r.matches?.map((m) => m.rubric ?? "Unknown") ?? [];
      const matchedPositions = matchRubrics
        .map((rub) => symptomMap.get(rub))
        .filter((p): p is Point3D => !!p);

      if (matchedPositions.length < 2) return;

      if (matchedPositions.length === 2) {
        const p1 = matchedPositions[0];
        const p2 = matchedPositions[1];
        const proj1 = project3D(p1, rotY, rotX, CX, CY, SCALE * zoom, FOV);
        const proj2 = project3D(p2, rotY, rotX, CX, CY, SCALE * zoom, FOV);
        items.push({
          id: `constellation-${r.abbrev}-0`,
          x1: proj1.x,
          y1: proj1.y,
          x2: proj2.x,
          y2: proj2.y,
          color,
          depth: (proj1.depth + proj2.depth) / 2,
        });
        return;
      }

      for (let i = 0; i < matchedPositions.length; i++) {
        const p1 = matchedPositions[i];
        const p2 = matchedPositions[(i + 1) % matchedPositions.length];
        const proj1 = project3D(p1, rotY, rotX, CX, CY, SCALE * zoom, FOV);
        const proj2 = project3D(p2, rotY, rotX, CX, CY, SCALE * zoom, FOV);
        items.push({
          id: `constellation-${r.abbrev}-${i}`,
          x1: proj1.x,
          y1: proj1.y,
          x2: proj2.x,
          y2: proj2.y,
          color,
          depth: (proj1.depth + proj2.depth) / 2,
        });
      }
    });

    return items;
  }, [sortedRemedies, symptomMap, rotY, rotX, zoom]);

  /* ── depth-sorted spheres & dots ── */
  type SphereItem =
    | {
        kind: "remedy";
        id: string;
        abbrev: string;
        name: string;
        score: number;
        matchCount: number;
        x: number;
        y: number;
        r: number;
        color: string;
        depth: number;
      }
    | {
        kind: "symptom";
        id: string;
        rubric: string;
        x: number;
        y: number;
        r: number;
        depth: number;
        grade: number;
        opacity: number;
      };

  const sortedSpheres = useMemo(() => {
    const list: SphereItem[] = [];
    remedyItems.forEach((r) =>
      list.push({
        kind: "remedy",
        id: `remedy-${r.abbrev}`,
        abbrev: r.abbrev,
        name: r.name,
        score: r.score,
        matchCount: r.matchCount,
        x: r.proj.x,
        y: r.proj.y,
        r: r.proj.r,
        color: r.color,
        depth: r.proj.depth,
      })
    );
    symptomItems.forEach((s) =>
      list.push({
        kind: "symptom",
        id: s.id,
        rubric: s.rubric,
        x: s.proj.x,
        y: s.proj.y,
        r: s.proj.r,
        depth: s.proj.depth,
        grade: s.grade,
        opacity: s.opacity,
      })
    );
    return depthSort(list);
  }, [remedyItems, symptomItems]);

  /* ── drag handlers ── */
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

  if (symptomMap.size === 0) {
    return (
      <div className="w-full">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-start gap-3">
            <span className="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              BEGINNER
            </span>
            <p className="text-xs text-slate-400 italic leading-relaxed">
              Symptoms appear as white star dots on a spherical shell. Remedy spheres
              sit at the centroid of the symptoms they cover, with line brightness
              showing match weight and sphere size showing overall score. Green marks
              the top remedy, blue the runner-up, and amber the third. Drag to rotate
              the view. Hover any sphere or dot for details; click to open.
            </p>
          </div>
        </div>
        <div className="w-full h-96 bg-slate-900 rounded-lg flex items-center justify-center text-slate-400 text-sm">
          No symptom matches to visualize.
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* ── header ── */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3">
          <span className="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            BEGINNER
          </span>
          <p className="text-xs text-slate-400 italic leading-relaxed">
            Symptoms appear as white star dots on a spherical shell. Remedy spheres
            sit at the centroid of the symptoms they cover, with line brightness
            showing match weight and sphere size showing overall score. Green marks
            the top remedy, blue the runner-up, and amber the third. Drag to rotate
            the view. Hover any sphere or dot for details; click to open.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400">Zoom</span>
          <input
            type="range"
            min={0.5}
            max={2}
            step={0.01}
            value={zoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            className="w-24 accent-slate-400"
          />
          <span className="text-xs text-slate-400 w-8 text-right">
            {Math.round(zoom * 100)}%
          </span>
        </div>
      </div>

      {/* ── canvas ── */}
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
          {/* faint shell reference */}
          <circle
            cx={CX}
            cy={CY}
            r={SHELL_RADIUS * 0.5 * zoom}
            fill="none"
            stroke="rgba(148,163,184,0.06)"
            strokeWidth={1}
          />

          {/* lines first (behind spheres) */}
          <g strokeLinecap="round">
            {lineItems.map((ln) => (
              <line
                key={ln.id}
                x1={ln.x1}
                y1={ln.y1}
                x2={ln.x2}
                y2={ln.y2}
                stroke="rgba(255,255,255,0.35)"
                strokeOpacity={ln.opacity}
                strokeWidth={1}
                style={{ pointerEvents: "none" }}
              />
            ))}
            {constellationItems.map((ln) => (
              <line
                key={ln.id}
                x1={ln.x1}
                y1={ln.y1}
                x2={ln.x2}
                y2={ln.y2}
                stroke={ln.color}
                strokeOpacity={0.3}
                strokeWidth={1}
                style={{ pointerEvents: "none" }}
              />
            ))}
          </g>

          {/* depth-sorted spheres & dots */}
          <g>
            {sortedSpheres.map((item) => {
              if (item.kind === "remedy") {
                const isHovered = item.abbrev === hoveredAbbrev;
                return (
                  <g key={item.id}>
                    {/* glow halo */}
                    {isHovered && (
                      <circle
                        cx={item.x}
                        cy={item.y}
                        r={item.r + 10}
                        fill={item.color}
                        opacity={0.12}
                        style={{ pointerEvents: "none" }}
                      />
                    )}
                    <circle
                      cx={item.x}
                      cy={item.y}
                      r={isHovered ? item.r * 1.15 : item.r}
                      fill={item.color}
                      fillOpacity={0.85}
                      stroke={isHovered ? "#ffffff" : item.color}
                      strokeWidth={isHovered ? 2 : 1}
                      strokeOpacity={isHovered ? 1 : 0.6}
                      className="cursor-pointer"
                      style={{ transition: "all 0.15s ease" }}
                      onMouseEnter={(e) => {
                        setHoveredAbbrev(item.abbrev);
                        const rect =
                          containerRef.current?.getBoundingClientRect();
                        setTooltip({
                          x: e.clientX - (rect?.left ?? 0),
                          y: e.clientY - (rect?.top ?? 0),
                          content: (
                            <div>
                              <div className="font-semibold">{item.name}</div>
                              <div className="text-slate-400">
                                {item.abbrev}
                              </div>
                              <div className="mt-1">
                                Score:{" "}
                                <span className="text-sky-300">
                                  {item.score.toFixed(1)}
                                </span>
                              </div>
                              <div>
                                Matches:{" "}
                                <span className="text-emerald-300">
                                  {item.matchCount}
                                </span>
                              </div>
                            </div>
                          ),
                        });
                      }}
                      onMouseLeave={() => {
                        setHoveredAbbrev(null);
                        setTooltip(null);
                      }}
                      onClick={() =>
                        onRemedyClick && onRemedyClick(item.abbrev)
                      }
                    />
                    {/* label */}
                    <text
                      x={item.x}
                      y={item.y - item.r - 6}
                      textAnchor="middle"
                      dominantBaseline="central"
                      fontSize={10}
                      fill="#e2e8f0"
                      className="pointer-events-none"
                      style={{
                        textShadow: "0 1px 3px rgba(0,0,0,0.8)",
                        opacity: isHovered ? 1 : 0.7,
                      }}
                    >
                      {item.abbrev}
                    </text>
                  </g>
                );
              }

              // symptom dot
              const isHovered = item.rubric === hoveredRubric;
              return (
                <g key={item.id}>
                  <circle
                    cx={item.x}
                    cy={item.y}
                    r={isHovered ? item.r * 1.3 : item.r}
                    fill="#ffffff"
                    fillOpacity={isHovered ? 1 : item.opacity}
                    stroke={isHovered ? "#ffffff" : "rgba(255,255,255,0.4)"}
                    strokeWidth={isHovered ? 2 : 0}
                    className="cursor-pointer"
                    style={{ transition: "all 0.15s ease" }}
                    onMouseEnter={(e) => {
                      setHoveredRubric(item.rubric);
                      const rect =
                        containerRef.current?.getBoundingClientRect();
                      setTooltip({
                        x: e.clientX - (rect?.left ?? 0),
                        y: e.clientY - (rect?.top ?? 0),
                        content: (
                          <div>
                            <div className="font-semibold">{item.rubric}</div>
                            <div className="text-slate-400 text-[10px] mt-0.5">
                              Grade:{" "}
                              <span className="text-amber-300">
                                {item.grade}
                              </span>
                            </div>
                          </div>
                        ),
                      });
                    }}
                    onMouseLeave={() => {
                      setHoveredRubric(null);
                      setTooltip(null);
                    }}
                    onClick={() =>
                      onRubricClick && onRubricClick(item.rubric)
                    }
                  />
                </g>
              );
            })}
          </g>
        </svg>

        {/* tooltip */}
        {tooltip && (
          <div
            className="absolute z-10 px-3 py-2 rounded-md bg-slate-800 border border-slate-600 shadow-lg text-xs text-slate-100 pointer-events-none"
            style={{
              left: tooltip.x + 12,
              top: tooltip.y - 12,
            }}
          >
            {tooltip.content}
          </div>
        )}
      </div>
    </div>
  );
}
