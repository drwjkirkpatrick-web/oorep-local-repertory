"use client";

/**
 * RubricHierarchyTower — 3D Stacked Kent Hierarchy Visualization
 *
 * Shows the Kent repertory hierarchy as a vertical tower of stacked 3D discs.
 * Each cylinder tier represents one hierarchy level (Mind, Head, Eye, …,
 * Generals). Remedy dots sit on the tier surfaces where that remedy has rubric
 * matches. The practitioner can immediately see which remedies cover Mind
 * symptoms, which cover Generals, which are purely physical, etc. — a spatial
 * map of the case’s hierarchical footprint.
 */

import React, { useMemo, useState, useCallback, useRef } from "react";
import { project3D, deg } from "@/lib/projection3d";

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

interface RubricHierarchyTowerProps {
  remedies: Remedy[];
  onRemedyClick?: (abbrev: string) => void;
  onRubricClick?: (rubric: string) => void;
}

const TIER_ORDER = [
  "Generals",
  "Chill",
  "Fever",
  "Perspiration",
  "Sleep",
  "Skin",
  "Dreams",
  "Extremities",
  "Back",
  "Chest",
  "Respiratory",
  "Female",
  "Male",
  "Urinary",
  "Rectum",
  "Abdomen",
  "Stomach",
  "Throat",
  "Mouth",
  "Face",
  "Nose",
  "Ear",
  "Eye",
  "Head",
  "Mind",
];

const TIER_COLOR_BASE = "#64748b";
const TIER_COLOR_MIND = "#f59e0b";
const DEFAULT_DOT_COLOR = "#9ca3af";

const GRADE_COLORS: Record<number, string> = {
  1: "#93C5FD",
  2: "#38BDF8",
  3: "#3B82F6",
  4: "#1E3A8A",
};

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = hex.replace("#", "");
  const bigint = parseInt(
    n.length === 3 ? n.split("").map((c) => c + c).join("") : n,
    16
  );
  return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
}

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

function pseudoRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 10000;
  return x - Math.floor(x);
}

function getTierFromRubric(rubric: string): string | null {
  const rl = rubric.trim().toLowerCase();
  for (const tier of TIER_ORDER) {
    const tl = tier.toLowerCase();
    if (
      rl.startsWith(tl) ||
      rl.startsWith(tl + ";") ||
      rl.startsWith(tl + ",") ||
      rl.startsWith(tl + " ")
    ) {
      return tier;
    }
  }
  for (const tier of TIER_ORDER) {
    if (rl.includes(tier.toLowerCase())) return tier;
  }
  return null;
}

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface Face {
  points: string;
  fill: string;
  stroke: string;
  depth: number;
  tier: string;
}

function cylinderFaces(
  center: Point3D,
  radius: number,
  height: number,
  rotY: number,
  rotX: number,
  cx: number,
  cy: number,
  scale: number,
  fov: number,
  color: string,
  tier: string
): Face[] {
  const segments = 20;
  const hh = height / 2;
  const topRim: Point3D[] = [];
  const bottomRim: Point3D[] = [];
  for (let i = 0; i < segments; i++) {
    const theta = (i / segments) * Math.PI * 2;
    const x = Math.cos(theta) * radius;
    const z = Math.sin(theta) * radius;
    topRim.push({ x: center.x + x, y: center.y - hh, z: center.z + z });
    bottomRim.push({ x: center.x + x, y: center.y + hh, z: center.z + z });
  }

  const projTop = topRim.map((p) => project3D(p, rotY, rotX, cx, cy, scale, fov));
  const projBottom = bottomRim.map((p) => project3D(p, rotY, rotX, cx, cy, scale, fov));

  const rgba = hexToRgb(color);
  const topFill = `rgba(${rgba.r},${rgba.g},${rgba.b},0.9)`;
  const bottomFill = `rgba(${Math.round(rgba.r * 0.55)},${Math.round(rgba.g * 0.55)},${Math.round(rgba.b * 0.55)},0.9)`;
  const sideFill = `rgba(${Math.round(rgba.r * 0.7)},${Math.round(rgba.g * 0.7)},${Math.round(rgba.b * 0.7)},0.95)`;
  const stroke = `rgba(${Math.round(rgba.r * 0.5)},${Math.round(rgba.g * 0.5)},${Math.round(rgba.b * 0.5)},0.6)`;

  const topDepth = projTop.reduce((s, p) => s + p.depth, 0) / segments;
  const bottomDepth = projBottom.reduce((s, p) => s + p.depth, 0) / segments;

  const faces: Face[] = [
    {
      points: projTop.map((p) => `${p.x},${p.y}`).join(" "),
      fill: topFill,
      stroke,
      depth: topDepth,
      tier,
    },
    {
      points: projBottom.map((p) => `${p.x},${p.y}`).join(" "),
      fill: bottomFill,
      stroke,
      depth: bottomDepth,
      tier,
    },
  ];

  for (let i = 0; i < segments; i++) {
    const next = (i + 1) % segments;
    const pts = `${projTop[i].x},${projTop[i].y} ${projTop[next].x},${projTop[next].y} ${projBottom[next].x},${projBottom[next].y} ${projBottom[i].x},${projBottom[i].y}`;
    const depth =
      (projTop[i].depth + projTop[next].depth + projBottom[next].depth + projBottom[i].depth) / 4;
    faces.push({ points: pts, fill: sideFill, stroke, depth, tier });
  }

  return faces.sort((a, b) => b.depth - a.depth);
}

export default function RubricHierarchyTower({
  remedies,
  onRemedyClick,
  onRubricClick,
}: RubricHierarchyTowerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotY, setRotY] = useState(deg(25));
  const [rotX, setRotX] = useState(deg(-20));
  const [dragging, setDragging] = useState(false);
  const [lastPos, setLastPos] = useState<{ x: number; y: number } | null>(null);
  const [hoveredTier, setHoveredTier] = useState<string | null>(null);
  const [hoveredDot, setHoveredDot] = useState<{
    abbrev: string;
    name: string;
    rubric: string;
    grade?: number;
    x: number;
    y: number;
  } | null>(null);
  const [expandedTier, setExpandedTier] = useState<string | null>(null);
  const [expandedPos, setExpandedPos] = useState<{ x: number; y: number } | null>(null);
  const [selectedRemedy, setSelectedRemedy] = useState<string | null>(null);

  const CX = 400;
  const CY = 320;
  const SCALE = 1.4;
  const FOV = 900;

  const tierData = useMemo(() => {
    const map = new Map<
      string,
      {
        count: number;
        remedies: Map<
          string,
          {
            abbrev: string;
            name: string;
            score: number;
            rubrics: { rubric: string; grade?: number }[];
          }
        >;
      }
    >();

    for (const remedy of remedies) {
      for (const match of remedy.matches || []) {
        if (!match.rubric) continue;
        const tier = getTierFromRubric(match.rubric);
        if (!tier) continue;
        if (!map.has(tier)) {
          map.set(tier, { count: 0, remedies: new Map() });
        }
        const t = map.get(tier)!;
        t.count += 1;
        if (!t.remedies.has(remedy.abbrev)) {
          t.remedies.set(remedy.abbrev, {
            abbrev: remedy.abbrev,
            name: remedy.name,
            score: remedy.score,
            rubrics: [],
          });
        }
        t.remedies.get(remedy.abbrev)!.rubrics.push({
          rubric: match.rubric,
          grade: match.grade,
        });
      }
    }
    return map;
  }, [remedies]);

  const visibleTiers = useMemo(() => {
    return TIER_ORDER.filter((t) => tierData.has(t));
  }, [tierData]);

  const { tierGeoms, allFaces, dots, tierProjections } = useMemo(() => {
    const geoms: {
      tier: string;
      center: Point3D;
      radius: number;
      height: number;
      count: number;
      firstRubric: string;
    }[] = [];

    let currentY = 140;
    for (const tier of visibleTiers) {
      const data = tierData.get(tier)!;
      const count = data.count;
      const radius = (80 + count * 10) / 2;
      const height = Math.max(6, Math.min(count * 3, 40));
      const centerY = currentY - height / 2;
      currentY -= height + 4;

      const firstRemedy = Array.from(data.remedies.values())[0];
      const firstRubric = firstRemedy?.rubrics[0]?.rubric || "";

      geoms.push({
        tier,
        center: { x: 0, y: centerY, z: 0 },
        radius,
        height,
        count,
        firstRubric,
      });
    }

    let faces: Face[] = [];
    for (const g of geoms) {
      const color = g.tier === "Mind" ? TIER_COLOR_MIND : TIER_COLOR_BASE;
      const f = cylinderFaces(
        g.center,
        g.radius,
        g.height,
        rotY,
        rotX,
        CX,
        CY,
        SCALE,
        FOV,
        color,
        g.tier
      );
      faces = faces.concat(f);
    }
    faces.sort((a, b) => b.depth - a.depth);

    const dotList: {
      abbrev: string;
      name: string;
      color: string;
      rubric: string;
      grade?: number;
      x: number;
      y: number;
      r: number;
      depth: number;
      tier: string;
    }[] = [];

    for (const g of geoms) {
      const data = tierData.get(g.tier)!;
      for (const r of Array.from(data.remedies.values())) {
        const seed1 = hashString(r.abbrev + g.tier);
        const seed2 = hashString(g.tier + r.abbrev);
        const rr = Math.sqrt(pseudoRandom(seed1)) * (g.radius * 0.78);
        const theta = pseudoRandom(seed2) * Math.PI * 2;
        const dx = rr * Math.cos(theta);
        const dz = rr * Math.sin(theta);
        const py = g.center.y - g.height / 2;
        const proj = project3D(
          { x: dx, y: py, z: dz },
          rotY,
          rotX,
          CX,
          CY,
          SCALE,
          FOV
        );
        const maxGrade = r.rubrics.reduce((m, rub) => Math.max(m, rub.grade || 0), 0);
        const gradeColor = GRADE_COLORS[maxGrade] || DEFAULT_DOT_COLOR;
        dotList.push({
          abbrev: r.abbrev,
          name: r.name,
          color: gradeColor,
          rubric: r.rubrics[0].rubric,
          grade: r.rubrics[0].grade,
          x: proj.x,
          y: proj.y,
          r: 3.5 + (r.score / Math.max(1, ...remedies.map((x) => x.score))) * 3,
          depth: proj.depth,
          tier: g.tier,
        });
      }
    }
    dotList.sort((a, b) => b.depth - a.depth);

    const projMap: Record<string, { x: number; y: number; depth: number }> = {};
    for (const g of geoms) {
      projMap[g.tier] = project3D(g.center, rotY, rotX, CX, CY, SCALE, FOV);
    }

    return { tierGeoms: geoms, allFaces: faces, dots: dotList, tierProjections: projMap };
  }, [visibleTiers, tierData, rotY, rotX, remedies]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setDragging(true);
    setLastPos({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (dragging && lastPos) {
        const dx = e.clientX - lastPos.x;
        const dy = e.clientY - lastPos.y;
        setRotY((prev) => prev + dx * 0.008);
        setRotX((prev) => {
          const next = prev - dy * 0.008;
          const min = deg(-50);
          const max = deg(10);
          return Math.max(min, Math.min(max, next));
        });
        setLastPos({ x: e.clientX, y: e.clientY });
      }
      if (hoveredDot) {
        const rect = containerRef.current?.getBoundingClientRect();
        if (rect) {
          setHoveredDot((d) =>
            d
              ? {
                  ...d,
                  x: e.clientX - rect.left,
                  y: e.clientY - rect.top,
                }
              : null
          );
        }
      }
    },
    [dragging, lastPos, hoveredDot]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(false);
    setLastPos(null);
  }, []);

  const hoveredTierInfo = tierGeoms.find((g) => g.tier === hoveredTier);

  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">
            Rubric Hierarchy Tower
          </h3>
          <p className="mt-1 max-w-xl text-sm text-slate-500">
            The Kent hierarchy shown as a stacked tower. Each disc is a
            repertory chapter — Mind at the apex, Generals at the base. Remedy
            dots sit on the tiers where that remedy has matching rubrics. Hover
            a tier to see how many symptoms fall at that level; hover a dot to
            see the remedy and rubric. Drag to rotate the view.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
          BEGINNER
        </span>
      </div>

      <div className="mb-3 flex flex-wrap gap-3">
        {["Mind", "Head", "Generals"].map((t) => (
          <div key={t} className="flex items-center gap-1.5 text-xs text-slate-500">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{
                backgroundColor: t === "Mind" ? TIER_COLOR_MIND : TIER_COLOR_BASE,
              }}
            />
            {t} tier
          </div>
        ))}
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: GRADE_COLORS[1] }} />
          Grade 1
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: GRADE_COLORS[2] }} />
          Grade 2
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: GRADE_COLORS[3] }} />
          Grade 3
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: GRADE_COLORS[4] }} />
          Grade 4
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-400" />
          No grade
        </div>
      </div>

      <div
        ref={containerRef}
        className={`relative select-none overflow-hidden rounded-lg border border-slate-200 bg-slate-50 ${
          dragging ? "cursor-grabbing" : "cursor-grab"
        }`}
        style={{ width: "100%", height: 520 }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg width="100%" height="100%" viewBox={`0 0 ${CX * 2} ${CY * 2}`}>
          {allFaces.map((f, i) => {
            const proj = tierProjections[f.tier];
            const isExpanded = expandedTier === f.tier;
            return (
              <polygon
                key={`face-${i}`}
                points={f.points}
                fill={f.fill}
                stroke={f.stroke}
                strokeWidth={1}
                onMouseEnter={() => setHoveredTier(f.tier)}
                onMouseLeave={() => setHoveredTier(null)}
                onClick={(e) => {
                  const g = tierGeoms.find((tg) => tg.tier === f.tier);
                  if (g?.firstRubric && onRubricClick) onRubricClick(g.firstRubric);
                  const rect = containerRef.current?.getBoundingClientRect();
                  if (rect) {
                    setExpandedPos({
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                    });
                  }
                  setExpandedTier((prev) => (prev === f.tier ? null : f.tier));
                }}
                style={{
                  transformBox: "view-box",
                  transformOrigin: `${(proj.x / (CX * 2)) * 100}% ${(proj.y / (CY * 2)) * 100}%`,
                  transform: isExpanded ? "scale(1.5)" : "scale(1)",
                  transition: dragging ? "none" : "transform 300ms ease",
                  cursor: onRubricClick ? "pointer" : "default",
                }}
              />
            );
          })}

          {tierGeoms.map((g) => {
            const proj = tierProjections[g.tier];
            const isExpanded = expandedTier === g.tier;
            return (
              <text
                key={`label-${g.tier}`}
                x={proj.x}
                y={proj.y - 6}
                textAnchor="middle"
                fontSize={11}
                fontWeight={600}
                fill={g.tier === "Mind" ? "#92400e" : "#334155"}
                style={{
                  pointerEvents: "none",
                  opacity: 0.85,
                  transformBox: "view-box",
                  transformOrigin: `${(proj.x / (CX * 2)) * 100}% ${(proj.y / (CY * 2)) * 100}%`,
                  transform: isExpanded ? "scale(1.5)" : "scale(1)",
                  transition: dragging ? "none" : "transform 300ms ease",
                }}
              >
                {g.tier}
              </text>
            );
          })}

          {dots.map((d) => {
            const proj = tierProjections[d.tier];
            const isExpanded = expandedTier === d.tier;
            const isHighlighted = selectedRemedy === d.abbrev;
            const isDimmed = selectedRemedy && !isHighlighted;
            return (
              <g
                key={`${d.tier}-${d.abbrev}`}
                onMouseEnter={(e) => {
                  const rect = containerRef.current?.getBoundingClientRect();
                  if (rect) {
                    setHoveredDot({
                      abbrev: d.abbrev,
                      name: d.name,
                      rubric: d.rubric,
                      grade: d.grade,
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                    });
                  }
                }}
                onMouseLeave={() => setHoveredDot(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  onRemedyClick?.(d.abbrev);
                }}
                style={{
                  transformBox: "view-box",
                  transformOrigin: `${(proj.x / (CX * 2)) * 100}% ${(proj.y / (CY * 2)) * 100}%`,
                  transform: isExpanded ? "scale(1.5)" : "scale(1)",
                  transition: dragging ? "none" : "transform 300ms ease",
                  cursor: onRemedyClick ? "pointer" : "default",
                }}
              >
                <circle
                  cx={d.x}
                  cy={d.y}
                  r={d.r + 1.5}
                  fill={d.color}
                  opacity={isDimmed ? 0.15 : 0.2}
                  style={{ pointerEvents: "none" }}
                />
                <circle
                  cx={d.x}
                  cy={d.y}
                  r={d.r}
                  fill={d.color}
                  stroke="#ffffff"
                  strokeWidth={isHighlighted ? 2.5 : 1.5}
                  style={{
                    pointerEvents: "none",
                    filter: isHighlighted
                      ? "drop-shadow(0 0 4px rgba(255,255,255,0.9))"
                      : "none",
                  }}
                />
              </g>
            );
          })}
        </svg>

        {hoveredTierInfo && (
          <div
            className="pointer-events-none absolute z-10 rounded-md border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-lg"
            style={{ left: 12, top: 12 }}
          >
            <div className="font-semibold text-slate-800">{hoveredTierInfo.tier}</div>
            <div className="mt-0.5 text-slate-500">
              {hoveredTierInfo.count} rubric match
              {hoveredTierInfo.count !== 1 ? "es" : ""}
            </div>
            <div className="mt-0.5 text-slate-400">
              {tierData.get(hoveredTierInfo.tier)!.remedies.size} remedy
              {tierData.get(hoveredTierInfo.tier)!.remedies.size !== 1 ? "ies" : "y"}
            </div>
          </div>
        )}

        {hoveredDot && (
          <div
            className="pointer-events-none absolute z-10 rounded-md border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-lg"
            style={{
              left: Math.min(
                hoveredDot.x + 14,
                (containerRef.current?.clientWidth || 800) - 200
              ),
              top: Math.max(hoveredDot.y - 10, 8),
            }}
          >
            <div className="font-semibold text-slate-800">
              {hoveredDot.name} ({hoveredDot.abbrev})
            </div>
            <div className="mt-0.5 max-w-[180px] truncate text-slate-500">
              {hoveredDot.rubric}
            </div>
            {typeof hoveredDot.grade === "number" && (
              <div className="mt-0.5 text-slate-400">Grade {hoveredDot.grade}</div>
            )}
          </div>
        )}

        {expandedTier && expandedPos && (
          <div
            className="absolute z-20 rounded-md border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-lg"
            style={{
              left: Math.min(
                expandedPos.x + 14,
                (containerRef.current?.clientWidth || 800) - 260
              ),
              top: Math.max(expandedPos.y - 10, 8),
              maxWidth: 260,
            }}
          >
            <div className="mb-1 font-semibold text-slate-800">{expandedTier}</div>
            <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
              {(() => {
                const data = tierData.get(expandedTier);
                if (!data) return null;
                const items = Array.from(data.remedies.values()).flatMap((r) =>
                  r.rubrics.map((rub) => ({ ...rub, abbrev: r.abbrev, name: r.name }))
                );
                return items.map((item, i) => (
                  <div key={i} className="flex items-start gap-2 text-slate-600">
                    <span className="shrink-0 font-medium text-slate-800">{item.abbrev}</span>
                    <span className="truncate" title={item.rubric}>{item.rubric}</span>
                    {item.grade ? (
                      <span className="shrink-0 text-slate-400">G{item.grade}</span>
                    ) : null}
                  </div>
                ));
              })()}
            </div>
          </div>
        )}

        <div className="pointer-events-none absolute bottom-2 right-2 text-[10px] text-slate-400">
          Drag to rotate
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {remedies.map((r) => (
          <button
            key={r.abbrev}
            onClick={() =>
              setSelectedRemedy((prev) => (prev === r.abbrev ? null : r.abbrev))
            }
            className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
              selectedRemedy === r.abbrev
                ? "bg-slate-800 text-white shadow-md ring-2 ring-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {r.abbrev}
          </button>
        ))}
      </div>
    </div>
  );
}
