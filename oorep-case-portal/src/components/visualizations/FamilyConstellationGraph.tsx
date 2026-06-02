"use client";

import { useMemo } from "react";

/**
 * Family Constellation Graph — ADVANCED
 *
 * Force-directed-ish layout of family members with edges weighted by
 * shared remedy patterns, suppression chains, or miasmatic threads.
 */

const DEMO_FAMILY = [
  { id: "self", label: "Patient", remedy: "Stram.", x: 200, y: 120 },
  { id: "mother", label: "Mother", remedy: "Puls.", x: 100, y: 50 },
  { id: "father", label: "Father", remedy: "Nux-v.", x: 300, y: 50 },
  { id: "sib1", label: "Sibling 1", remedy: "Stram.", x: 120, y: 200 },
  { id: "sib2", label: "Sibling 2", remedy: "Calc.", x: 280, y: 200 },
];

const EDGES = [
  { source: "mother", target: "self", weight: 0.8, label: "Puls→Stram" },
  { source: "father", target: "self", weight: 0.4, label: "Nux→Stram" },
  { source: "mother", target: "sib1", weight: 0.9, label: "same remedy" },
  { source: "self", target: "sib1", weight: 0.7, label: "shared Stram" },
  { source: "father", target: "sib2", weight: 0.6, label: "Calc link" },
];

export default function FamilyConstellationGraph() {
  const nodes = useMemo(() => DEMO_FAMILY, []);

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-xs text-gray-500">Inherited remedy patterns & suppression chains</span>
      </div>

      <svg width={400} height={260} className="select-none bg-gray-50 rounded-lg">
        {/* Edges */}
        {EDGES.map((e, i) => {
          const s = nodes.find((n) => n.id === e.source)!;
          const t = nodes.find((n) => n.id === e.target)!;
          const strokeWidth = Math.max(1, e.weight * 4);
          return (
            <g key={i}>
              <line
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke="#d1d5db"
                strokeWidth={strokeWidth}
              />
              {/* Midpoint label */}
              <text
                x={(s.x + t.x) / 2}
                y={(s.y + t.y) / 2 - 4}
                textAnchor="middle"
                fontSize={8}
                fill="#9ca3af"
              >
                {e.label}
              </text>
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((n) => (
          <g key={n.id}>
            <circle cx={n.x} cy={n.y} r={22} fill="#fff" stroke="#374151" strokeWidth={2} />
            <text x={n.x} y={n.y - 4} textAnchor="middle" fontSize={9} fontWeight={600} fill="#374151">
              {n.label}
            </text>
            <text x={n.x} y={n.y + 8} textAnchor="middle" fontSize={8} fill="#6b7280">
              {n.remedy}
            </text>
          </g>
        ))}
      </svg>

      <div className="flex gap-3 mt-2 text-[10px] text-gray-400">
        <div className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-gray-400 inline-block" /> Weak link
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-1 bg-gray-400 inline-block" /> Strong link
        </div>
      </div>
    </div>
  );
}
