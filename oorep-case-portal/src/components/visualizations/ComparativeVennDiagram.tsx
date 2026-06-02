"use client";

import React from "react";

interface VennDatum {
  label: string;
  color: string;
  // All rubric IDs belonging to this remedy
  rubricIds: string[];
}

interface ComparativeVennDiagramProps {
  remedies: VennDatum[];
  // Typically top 2–3 remedies; beyond 3 becomes illegible
}

function ellipsePath(cx: number, cy: number, rx: number, ry: number): string {
  return `M ${cx - rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx + rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx - rx} ${cy} Z`;
}

export default function ComparativeVennDiagram({ remedies }: ComparativeVennDiagramProps) {
  const width = 420;
  const height = 260;
  const show = remedies.slice(0, 3);

  // Compute intersections
  const intersections: Record<string, string[]> = {};
  const keys: string[] = [];
  for (let i = 0; i < show.length; i++) {
    for (let j = i + 1; j < show.length; j++) {
      const k = `${i}∩${j}`;
      keys.push(k);
      intersections[k] = show[i].rubricIds.filter((id) => show[j].rubricIds.includes(id));
    }
    if (show.length >= 3) {
      const k = "0∩1∩2";
      keys.push(k);
      intersections[k] = show[0].rubricIds.filter(
        (id) => show[1].rubricIds.includes(id) && show[2].rubricIds.includes(id)
      );
    }
  }

  // Unique-only rubrics per remedy
  const unique: Record<number, string[]> = {};
  show.forEach((rem, idx) => {
    const others = show.filter((_, i) => i !== idx).flatMap((r) => r.rubricIds);
    unique[idx] = rem.rubricIds.filter((id) => !others.includes(id));
  });

  // Positions for 2 or 3 circles
  const centers =
    show.length === 2
      ? [
          { x: 140, y: 130 },
          { x: 280, y: 130 },
        ]
      : [
          { x: 150, y: 110 },
          { x: 270, y: 110 },
          { x: 210, y: 180 },
        ];

  const rx = 80;
  const ry = 60;

  return (
    <div className="overflow-auto">
      <svg width={width} height={height} className="font-mono text-xs">
        <text x={width / 2} y={22} textAnchor="middle" className="fill-slate-200 font-semibold">
          Differentiating Venn — Shared vs Unique Rubrics
        </text>

        {/* Circles */}
        {show.map((rem, idx) => (
          <g key={rem.label}>
            <path
              d={ellipsePath(centers[idx].x, centers[idx].y, rx, ry)}
              fill={rem.color}
              fillOpacity={0.25}
              stroke={rem.color}
              strokeWidth={2}
            />
            {/* Label at center */}
            <text
              x={centers[idx].x}
              y={centers[idx].y - 6}
              textAnchor="middle"
              className="fill-slate-100 font-bold"
              fontSize={12}
            >
              {rem.label}
            </text>
            {/* Unique count in lobe */}
            <text
              x={centers[idx].x}
              y={centers[idx].y + 8}
              textAnchor="middle"
              className="fill-slate-300"
              fontSize={10}
            >
              {unique[idx]?.length || 0} unique
            </text>
          </g>
        ))}

        {/* Intersection counts */}
        {show.length === 2 && (
          <g>
            <text
              x={(centers[0].x + centers[1].x) / 2}
              y={centers[0].y + 4}
              textAnchor="middle"
              className="fill-slate-100 font-semibold"
              fontSize={11}
            >
              {intersections["0∩1"]?.length || 0} shared
            </text>
          </g>
        )}
        {show.length >= 3 && (
          <>
            {["0∩1", "1∩2", "0∩2"].map((pair) => (
              <text
                key={pair}
                // rough midpoint of each pair
                x={210}
                y={130}
                textAnchor="middle"
                className="fill-slate-100 font-semibold"
                fontSize={9}
              >
                {intersections[pair]?.length || 0}
              </text>
            ))}
            <text
              x={210}
              y={155}
              textAnchor="middle"
              className="fill-emerald-300 font-bold"
              fontSize={10}
            >
              {intersections["0∩1∩2"]?.length || 0} all shared
            </text>
          </>
        )}

        {/* Legend */}
        <g transform={`translate(8, ${height - 40})`}>
          {show.map((rem, idx) => (
            <g key={rem.label} transform={`translate(0, ${idx * 14})`}>
              <rect width={10} height={10} fill={rem.color} opacity={0.6} rx={2} />
              <text x={16} y={9} className="fill-slate-400" fontSize={10}>
                {rem.label}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}
