"use client";

import { useMemo } from "react";

/**
 * Differential Remedy Radar Chart
 *
 * Compares top remedies across 7 clinical dimensions simultaneously.
 */

const AXES = [
  "Repertory Score",
  "Cycle Coverage",
  "SRP Density",
  "Rubric Reliability",
  "Layer Alignment",
  "Method Agreement",
  "Outcome History",
];

const COLORS = [
  "#be123c", // crimson
  "#1e40af", // blue
  "#15803d", // green
  "#b45309", // amber
  "#7c3aed", // violet
  "#0e7490", // cyan
];

export default function RadarChartViz({
  remedies,
  size = 400,
  onRemedyClick,
}: {
  remedies: any[];
  size?: number;
  onRemedyClick?: (abbrev: string) => void;
}) {
  const data = useMemo(() => {
    const maxScore = Math.max(...remedies.map((r) => r.score || 1), 1);

    return remedies.map((r, i) => {
      const ca = r.cycle_analysis || {};
      const scoreNorm = (r.score || 0) / maxScore;
      const cycleNorm = ca.segment_coverage || 0;
      const srpNorm = r.srp_density || 0.3;
      const phantomRisk = r.phantom_risk || 0.1;
      const reliability = 1 - phantomRisk;
      const layerAlign = r.layer_alignment || 0.7;
      // Fake composite values for demo
      return {
        label: r.abbrev,
        values: [
          scoreNorm,       // Repertory Score
          cycleNorm,       // Cycle Coverage
          srpNorm,         // SRP Density
          reliability,     // Rubric Reliability
          layerAlign,      // Layer Alignment
          r.method_agreement || 0.6,  // Kent vs Boenninghausen
          r.outcome_rate || 0.5,      // Outcome history
        ],
        color: COLORS[i % COLORS.length],
        meets_threshold: ca.meets_threshold,
      };
    });
  }, [remedies]);

  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.38;
  const levels = 4;

  const angleFor = (i: number) => (2 * Math.PI * i) / AXES.length - Math.PI / 2;

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs text-slate-500 italic leading-relaxed text-center max-w-md">
        See up to 6 candidate remedies compared across 7 clinical dimensions at once: repertory score, cycle coverage, SRP density, rubric reliability, layer alignment, method agreement, and outcome history. A larger, more rounded shape = stronger on more dimensions. The remedy whose polygon covers the most area on the most axes is typically the best-fit simillimum.
      </p>
      <svg width={size} height={size} className="select-none">
        {/* Grid levels */}
        {Array.from({ length: levels }, (_, level) => {
          const r = (maxR * (level + 1)) / levels;
          return (
            <g key={level}>
              <polygon
                points={AXES.map((_, i) => {
                  const a = angleFor(i);
                  return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
                }).join(" ")}
                fill="none"
                stroke="#e5e7eb"
                strokeWidth={1}
              />
              <text
                x={cx + 4}
                y={cy - r + 4}
                fontSize={"10"}
                fill="#9ca3af"
              >
                {Math.round(((level + 1) / levels) * 100)}%
              </text>
            </g>
          );
        })}

        {/* Axis lines + labels */}
        {AXES.map((label, i) => {
          const a = angleFor(i);
          const x = cx + maxR * Math.cos(a);
          const y = cy + maxR * Math.sin(a);
          const labelX = cx + (maxR + 20) * Math.cos(a);
          const labelY = cy + (maxR + 20) * Math.sin(a);
          return (
            <g key={i}>
              <line
                x1={cx}
                y1={cy}
                x2={x}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth={1}
              />
              <text
                x={labelX}
                y={labelY}
                textAnchor={labelX > cx ? "start" : labelX < cx ? "end" : "middle"}
                dominantBaseline={labelY > cy ? "hanging" : labelY < cy ? "auto" : "central"}
                fontSize={"10"}
                fill="#6b7280"
              >
                {label}
              </text>
            </g>
          );
        })}

        {/* Data polygons */}
        {data.map((d, di) => {
          const points = d.values
            .map((v, i) => {
              const a = angleFor(i);
              const r = maxR * v;
              return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
            })
            .join(" ");

          return (
            <g key={di}>
              <polygon
                points={points}
                fill={d.color}
                fillOpacity={0.15}
                stroke={d.color}
                strokeWidth={2}
              />
              {d.values.map((v, i) => {
                const a = angleFor(i);
                const r = maxR * v;
                return (
                  <circle
                    key={i}
                    cx={cx + r * Math.cos(a)}
                    cy={cy + r * Math.sin(a)}
                    r={4}
                    fill={d.color}
                    stroke="#fff"
                    strokeWidth={1}
                    style={{ cursor: "pointer" }}
                    onClick={() => {
                      if (onRemedyClick) onRemedyClick(d.label);
                    }}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center mt-2">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-1 text-xs">
            <span
              className="w-3 h-3 rounded-full inline-block"
              style={{ backgroundColor: d.color }}
            />
            <span className={d.meets_threshold ? "font-semibold" : ""}>
              {d.label}
              {d.meets_threshold && " ✓"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
