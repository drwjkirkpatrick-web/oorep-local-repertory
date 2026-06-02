"use client";

import React from "react";

interface SparklinePoint {
  month: number; // relative month
  score: number; // e.g. Herscu -4 to +4
}

interface OutcomeTrajectorySparklinesProps {
  remedies: {
    abbrev: string;
    color: string;
    points: SparklinePoint[];
  }[];
}

export default function OutcomeTrajectorySparklines({ remedies, onRemedyClick }: OutcomeTrajectorySparklinesProps & { onRemedyClick?: (abbrev: string) => void }) {
  const width = 500;
  const height = 260;
  const plotH = 160;
  const padding = { top: 40, left: 40, right: 16, bottom: 36 };
  const plotW = width - padding.left - padding.right;

  const maxScore = 4;
  const minScore = -4;
  const months = Array.from(new Set(remedies.flatMap((r) => r.points.map((p) => p.month))));
  const maxMonth = Math.max(12, ...months);

  const xScale = (m: number) => padding.left + (m / maxMonth) * plotW;
  const yScale = (s: number) =>
    padding.top + plotH - ((s - minScore) / (maxScore - minScore)) * plotH;

  const pathFor = (pts: SparklinePoint[]) =>
    pts
      .sort((a, b) => a.month - b.month)
      .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.month)} ${yScale(p.score)}`)
      .join(" ");

  return (
    <div className="overflow-auto">
      <svg width={width} height={height} className="font-mono text-xs">
        <text x={width / 2} y={22} textAnchor="middle" className="fill-slate-200 font-semibold">
          Historical Outcome Trajectories (Herscu -4 → +4)
        </text>

        {/* Y axis grid */}
        {[-4, -2, 0, 2, 4].map((s) => (
          <g key={s}>
            <line
              x1={padding.left}
              y1={yScale(s)}
              x2={width - padding.right}
              y2={yScale(s)}
              stroke="#334155"
              strokeWidth={0.5}
            />
            <text x={padding.left - 6} y={yScale(s) + 4} textAnchor="end" className="fill-slate-500">
              {s}
            </text>
          </g>
        ))}

        {/* X axis grid */}
        {Array.from({ length: maxMonth + 1 }, (_, m) => m).map((m) => (
          <g key={m}>
            <line
              x1={xScale(m)}
              y1={padding.top}
              x2={xScale(m)}
              y2={padding.top + plotH}
              stroke="#1e293b"
              strokeWidth={0.5}
            />
            <text
              x={xScale(m)}
              y={padding.top + plotH + 14}
              textAnchor="middle"
              className="fill-slate-500"
            >
              M{m}
            </text>
          </g>
        ))}

        {/* Sparklines */}
        {remedies.map((rem) => (
          <g key={rem.abbrev}>
            <path
              d={pathFor(rem.points)}
              fill="none"
              stroke={rem.color}
              strokeWidth={2}
            />
            {/* dots */}
            {rem.points.map((p) => (
              <circle
                key={p.month + rem.abbrev}
                cx={xScale(p.month)}
                cy={yScale(p.score)}
                r={3}
                fill={rem.color}
              />
            ))}
          </g>
        ))}

        {/* Legend */}
        <g transform={`translate(${padding.left}, ${height - 28})`}>
          {remedies.map((rem, idx) => (
            <g
              key={rem.abbrev}
              transform={`translate(${idx * 80}, 0)`}
              style={{ cursor: "pointer" }}
              onClick={() => {
                if (onRemedyClick) onRemedyClick(rem.abbrev);
              }}
            >
              <line x1={0} y1={6} x2={16} y2={6} stroke={rem.color} strokeWidth={2} />
              <text x={22} y={10} className="fill-slate-400" fontSize={10}>
                {rem.abbrev}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}
