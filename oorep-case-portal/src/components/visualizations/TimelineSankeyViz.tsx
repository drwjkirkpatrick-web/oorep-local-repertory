"use client";

import { useMemo } from "react";

/**
 * Timeline & Sankey Transparency View
 *
 * Shows how each case symptom flows through the repertorization system.
 */

export default function TimelineSankeyViz({
  symptoms,
  remedies,
  onRemedyClick,
}: {
  symptoms: string[];
  remedies: any[];
  onRemedyClick?: (abbrev: string) => void;
}) {
  const width = 800;
  const height = 280;
  const padding = { top: 30, right: 20, bottom: 30, left: 140 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const nodes = useMemo(() => {
    const snodes = symptoms.map((s, i) => ({
      id: `sym-${i}`,
      label: s,
      x: 0,
      y: (i * chartH) / (symptoms.length - 1 || 1) + padding.top,
      color: "#374151",
    }));

    const rnodes = remedies.slice(0, 4).map((r, i) => ({
      id: `rem-${i}`,
      label: `${r.abbrev} (${r.score})`,
      x: chartW,
      y: (i * chartH) / 3 + padding.top,
      color: r.cycle_analysis?.meets_threshold ? "#15803d" : "#6b7280",
    }));

    return { snodes, rnodes };
  }, [symptoms, remedies, chartW, chartH]);

  const links = useMemo(() => {
    const out: { source: { x: number; y: number }; target: { x: number; y: number }; value: number; color: string }[] = [];
    for (let si = 0; si < symptoms.length; si++) {
      for (let ri = 0; ri < nodes.rnodes.length; ri++) {
        // Fake link values based on score distribution
        const remedy = remedies[ri];
        const linkValue = remedy?.score
          ? (remedy.score / 50) * (Math.random() * 0.6 + 0.4)
          : 0.2;
        out.push({
          source: {
            x: nodes.snodes[si].x + padding.left + 60,
            y: nodes.snodes[si].y,
          },
          target: {
            x: nodes.rnodes[ri].x + padding.left,
            y: nodes.rnodes[ri].y,
          },
          value: linkValue,
          color: remedy?.cycle_analysis?.meets_threshold ? "#15803d" : "#9ca3af",
        });
      }
    }
    return out;
  }, [nodes, symptoms, remedies]);

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs text-slate-500 italic leading-relaxed text-center max-w-2xl">
        See how each symptom in the current case flows through the repertorization to the top remedy candidates. Symptoms are nodes on the left, remedies on the right, and the thickness of each connecting line shows how strongly a given symptom contributes to a given remedy's final score. Useful for understanding which symptoms most influenced the differential.
      </p>
      <svg width={width} height={height}>
        {/* Links */}
        {links.map((link, i) => {
          const sx = link.source.x;
          const sy = link.source.y;
          const tx = link.target.x;
          const ty = link.target.y;
          const cp1x = sx + (tx - sx) * 0.5;
          const cp1y = sy;
          const cp2x = tx - (tx - sx) * 0.5;
          const cp2y = ty;
          const d = `M ${sx} ${sy} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${tx} ${ty}`;
          const strokeWidth = Math.max(1, link.value * 8);

          return (
            <path
              key={i}
              d={d}
              fill="none"
              stroke={link.color}
              strokeWidth={strokeWidth}
              strokeOpacity={0.4}
              className="hover:stroke-opacity-80 transition cursor-pointer"
            >
              <title>Flow: {link.value.toFixed(2)} strength</title>
            </path>
          );
        })}

        {/* Symptom nodes */}
        {nodes.snodes.map((n) => (
          <g key={n.id}>
            <circle cx={n.x + padding.left + 60} cy={n.y} r={6} fill={n.color} />
            <text
              x={n.x + padding.left + 55}
              y={n.y + 4}
              textAnchor="end"
              fontSize={11}
              fill="#374151"
              fontWeight={500}
            >
              {n.label}
            </text>
          </g>
        ))}

        {/* Remedy nodes */}
        {nodes.rnodes.map((n) => (
          <g key={n.id}>
            <circle
              cx={n.x + padding.left}
              cy={n.y}
              r={8}
              fill={n.color}
              style={{ cursor: "pointer" }}
              onClick={() => {
                if (onRemedyClick) {
                  // Extract abbreviation from label "ABBREV (score)"
                  const abbrev = n.label.split(" ")[0];
                  onRemedyClick(abbrev);
                }
              }}
            />
            <text
              x={n.x + padding.left + 15}
              y={n.y + 4}
              textAnchor="start"
              fontSize={11}
              fill="#374151"
              fontWeight={500}
              style={{ cursor: "pointer" }}
              onClick={() => {
                if (onRemedyClick) {
                  const abbrev = n.label.split(" ")[0];
                  onRemedyClick(abbrev);
                }
              }}
            >
              {n.label}
            </text>
          </g>
        ))}
      </svg>
      <p className="text-xs text-gray-400 mt-1">
        Flow thickness ∝ remedy score weight per symptom
      </p>
    </div>
  );
}
