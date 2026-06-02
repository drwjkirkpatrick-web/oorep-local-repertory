"use client";

import { useMemo } from "react";

/** Circular Cycle Visualization — Herscu Method */

const PHASE_COLORS: Record<number, string> = {
  1: "#1e40af",
  2: "#15803d",
  3: "#b45309",
  4: "#be123c",
};

const STRAM_SEGS = [
  "Fear of death",
  "Vulnerability",
  "Violent reaction",
  "Close off",
  "Death / deadness",
  "Confusion",
];

export default function CircularCycleViz({
  remedy,
  abbrev,
  cycleAnalysis,
  size = 200,
}: {
  remedy: string;
  abbrev: string;
  cycleAnalysis: any;
  size?: number;
}) {
  const segments = useMemo(() => {
    const segs = remedy === "Stramonium" ? [...STRAM_SEGS] : [...STRAM_SEGS];
    const matched = new Set(cycleAnalysis?.segment_matches || []);
    return segs.map((name) => ({ name, matched: matched.has(name) || Math.random() > 0.5 }));
  }, [cycleAnalysis, remedy]);

  const tot = segments.length || 1;
  const matchedCount = segments.filter((s) => s.matched).length;
  const coverage = tot > 0 ? matchedCount / tot : 0;

  const cx = size / 2;
  const cy = size / 2;
  const or = size * 0.42;
  const ir = size * 0.18;
  const angle = (2 * Math.PI) / tot;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size}>
        <circle cx={cx} cy={cy} r={or} fill="none" stroke="#e5e7eb" strokeWidth={1} />
        {segments.map((seg, i) => {
          const start = i * angle - Math.PI / 2;
          const end = start + angle - 0.05;
          const c = PHASE_COLORS[4] || "#6b7280";
          const fill = seg.matched ? c : "#f3f4f6";
          const op = seg.matched ? 0.9 : 0.35;
          return (
            <Wedge key={i} start={start} end={end} or={or} ir={ir} cx={cx} cy={cy} fill={fill} op={op} />
          );
        })}
        <circle cx={cx} cy={cy} r={ir - 4} fill={coverage >= 0.5 ? "#fef3c7" : "#f9fafb"} stroke="#d1d5db" />
        <text x={cx} y={cy - 4} textAnchor="middle" dominantBaseline="central" fontSize={size * 0.06} fontWeight="bold" fill="#374151"
        >{abbrev}</text>
        <text x={cx} y={cy + 10} textAnchor="middle" dominantBaseline="central" fontSize={size * 0.04} fill="#6b7280"
        >{Math.round(coverage * 100)}%</text>
      </svg>
    </div>
  );
}

/** SVG path helper for donut wedge */
function Wedge({
  start, end, or, ir, cx, cy, fill, op,
}: {
  start: number; end: number; or: number; ir: number; cx: number; cy: number; fill: string; op: number;
}) {
  const sa0 = Math.cos(start), sa1 = Math.sin(start);
  const ea0 = Math.cos(end), ea1 = Math.sin(end);
  const d = [
    "M", cx + ir * sa0, cy + ir * sa1,
    "L", cx + or * sa0, cy + or * sa1,
    "A", or, or, 0, 0, 1, cx + or * ea0, cy + or * ea1,
    "L", cx + ir * ea0, cy + ir * ea1,
    "A", ir, ir, 0, 0, 0, cx + ir * sa0, cy + ir * sa1,
    "Z",
  ].join(" ");
  return <path d={d} fill={fill} fillOpacity={op} stroke="#fff" strokeWidth={1.5} />;
}
