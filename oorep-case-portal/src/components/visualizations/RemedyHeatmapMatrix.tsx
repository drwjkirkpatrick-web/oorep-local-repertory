"use client";

import React from "react";

interface HeatmapData {
  rubric: string;
  remedyAbbrev: string;
  weight: number; // 1–4 classical grade
}

interface RemedyHeatmapMatrixProps {
  rubrics: string[];
  remedies: { abbrev: string; name: string }[];
  data: HeatmapData[];
  maxGrade?: number;
}

const GRADE_COLORS = [
  "#1f2937", // grade 0 — empty
  "#7dd3fc", // grade 1 — light blue
  "#38bdf8", // grade 2 — sky
  "#0ea5e9", // grade 3 — blue
  "#0284c7", // grade 4 — deep blue
];

export default function RemedyHeatmapMatrix({
  rubrics,
  remedies,
  data,
  maxGrade = 4,
}: RemedyHeatmapMatrixProps) {
  const cellW = Math.max(28, 200 / remedies.length);
  const cellH = 22;
  const rowLabelW = 240;
  const colLabelH = 40;
  const width = rowLabelW + remedies.length * cellW + 80;
  const height = colLabelH + rubrics.length * cellH + 60;

  const matrix: Record<string, Record<string, number>> = {};
  rubrics.forEach((r) => {
    matrix[r] = {};
    remedies.forEach((rem) => (matrix[r][rem.abbrev] = 0));
  });
  data.forEach((d) => {
    if (matrix[d.rubric]) matrix[d.rubric][d.remedyAbbrev] = d.weight;
  });

  return (
    <div className="overflow-auto">
      <svg width={width} height={height} className="font-mono text-xs">
        {/* Title */}
        <text x={width / 2} y={20} textAnchor="middle" className="fill-slate-200 font-semibold">
          Remedy Coverage Heatmap (Classical Grades)
        </text>

        {/* Column labels (remedy abbreviations) — rotated */}
        {remedies.map((rem, ci) => {
          const x = rowLabelW + ci * cellW + cellW / 2;
          return (
            <g key={rem.abbrev}>
              <text
                x={x}
                y={colLabelH - 8}
                textAnchor="start"
                transform={`rotate(-45, ${x}, ${colLabelH - 8})`}
                className="fill-slate-300"
              >
                {rem.abbrev}
              </text>
            </g>
          );
        })}

        {/* Cells */}
        {rubrics.map((rubric, ri) => {
          const y = colLabelH + ri * cellH;
          return (
            <g key={rubric}>
              {/* Row label */}
              <text
                x={rowLabelW - 8}
                y={y + cellH / 1.5}
                textAnchor="end"
                className="fill-slate-400"
              >
                {rubric.length > 35 ? rubric.slice(0, 32) + "…" : rubric}
              </text>
              {remedies.map((rem, ci) => {
                const weight = matrix[rubric][rem.abbrev] || 0;
                const color = GRADE_COLORS[Math.min(weight, maxGrade)];
                const x = rowLabelW + ci * cellW;
                return (
                  <g key={rem.abbrev}>
                    <rect
                      x={x}
                      y={y}
                      width={cellW - 1}
                      height={cellH - 1}
                      fill={color}
                      rx={2}
                    />
                    {weight > 0 && (
                      <text
                        x={x + cellW / 2}
                        y={y + cellH / 1.5}
                        textAnchor="middle"
                        className="fill-white font-bold"
                        fontSize={10}
                      >
                        {weight}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          );
        })}

        {/* Legend */}
        <g transform={`translate(${width - 70}, ${colLabelH})`}>
          <text x={0} y={-8} className="fill-slate-300" fontSize={10}>
            Grade
          </text>
          {[1, 2, 3, 4].map((g) => (
            <g key={g} transform={`translate(0, ${(g - 1) * 16})`}>
              <rect width={12} height={12} fill={GRADE_COLORS[g]} rx={2} />
              <text x={18} y={10} className="fill-slate-400" fontSize={10}>
                {g}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}
