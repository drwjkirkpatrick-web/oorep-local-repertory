"use client";

import { useMemo } from "react";

/**
 * Layer Timeline (Gantt / Stacked Ribbon) — ADVANCED
 *
 * Chronic cases as a horizontal timeline: suppression events, acute episodes,
 * past remedies, and constitutional layers stacked vertically.
 */

const EVENTS = [
  { year: 2018, label: "Suppression: antibiotics x3", layer: "physical", type: "suppression" },
  { year: 2019.5, label: "Acute: high fever → Belladonna", layer: "acute", type: "acute" },
  { year: 2020, label: "Chronic layer emerges", layer: "chronic", type: "layer" },
  { year: 2021, label: "Remedy: Sulphur 200C", layer: "constitutional", type: "remedy" },
  { year: 2022.5, label: "Suppression: steroid cream", layer: "physical", type: "suppression" },
  { year: 2023, label: "Current presentation", layer: "acute", type: "layer" },
];

const LAYER_COLORS: Record<string, string> = {
  physical: "#ef4444",
  acute: "#f59e0b",
  chronic: "#7c3aed",
  constitutional: "#15803d",
};

const LAYER_Y: Record<string, number> = {
  physical: 20,
  acute: 55,
  chronic: 90,
  constitutional: 125,
};

export default function LayerTimelineRibbon() {
  const data = useMemo(() => EVENTS, []);

  const minYear = Math.min(...data.map((d) => d.year));
  const maxYear = Math.max(...data.map((d) => d.year));
  const span = maxYear - minYear || 1;

  const width = 480;
  const padding = { left: 40, right: 20 };
  const chartW = width - padding.left - padding.right;

  const xFor = (year: number) => padding.left + ((year - minYear) / span) * chartW;

  return (
    <div className="flex flex-col">
      <p className="text-xs text-slate-500 italic leading-relaxed mb-2 max-w-md">
        See how suppressions, acute episodes, chronic layer emergence, and constitutional remedy actions are distributed over multiple years. Each dot is a case event, placed on a horizontal year axis and a vertical layer track. Color-coded by layer type, the view makes it easy to see whether a patient is improving, stuck, or cycling through old layers as treatment progresses.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-xs text-gray-500">Suppression, remedies, and layer emergence over time</span>
      </div>

      <svg width={width} height={170} className="select-none">
        {/* Year axis */}
        <line x1={padding.left} y1={155} x2={width - padding.right} y2={155} stroke="#e5e7eb" strokeWidth={1} />
        {Array.from({ length: Math.ceil(span) + 1 }, (_, i) => {
          const year = Math.floor(minYear) + i;
          const x = xFor(year);
          return (
            <g key={year}>
              <line x1={x} y1={150} x2={x} y2={155} stroke="#9ca3af" strokeWidth={1} />
              <text x={x} y={165} textAnchor="middle" fontSize={9} fill="#6b7280">{year}</text>
            </g>
          );
        })}

        {/* Events */}
        {data.map((e, i) => {
          const x = xFor(e.year);
          const y = LAYER_Y[e.layer] || 80;
          const color = LAYER_COLORS[e.layer] || "#6b7280";
          return (
            <g key={i}>
              <circle cx={x} cy={y} r={6} fill={color} stroke="#fff" strokeWidth={2} />
              <text x={x + 10} y={y + 3} fontSize={9} fill="#374151" fontWeight={500}>
                {e.label}
              </text>
            </g>
          );
        })}

        {/* Layer labels */}
        {Object.entries(LAYER_Y).map(([layer, y]) => (
          <text key={layer} x={padding.left - 8} y={y + 3} textAnchor="end" fontSize={9} fill={LAYER_COLORS[layer]} fontWeight={600}>
            {layer.charAt(0).toUpperCase() + layer.slice(1)}
          </text>
        ))}
      </svg>

      <div className="flex gap-3 mt-1 text-[10px] text-gray-400">
        {Object.entries(LAYER_COLORS).map(([layer, color]) => (
          <div key={layer} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: color }} />
            {layer.charAt(0).toUpperCase() + layer.slice(1)}
          </div>
        ))}
      </div>
    </div>
  );
}
