"use client";

import React from "react";

interface TimelineEvent {
  id: string;
  label: string;
  startMonth: number; // relative months from case start
  endMonth: number;
  layer: "acute" | "chronic" | "constitutional" | "suppression";
  remedy?: string;
  color?: string;
}

interface LayerTimelineProps {
  events: TimelineEvent[];
  currentMonth?: number;
}

const LAYER_COLORS: Record<string, string> = {
  acute: "#38bdf8",
  chronic: "#a78bfa",
  constitutional: "#34d399",
  suppression: "#f87171",
};

const LAYER_ORDER = ["suppression", "acute", "chronic", "constitutional"];

export default function LayerTimeline({ events, currentMonth }: LayerTimelineProps) {
  const monthW = 40;
  const trackH = 28;
  const padding = { top: 50, left: 160, right: 40, bottom: 40 };

  const maxMonth = Math.max(12, ...events.map((e) => e.endMonth), currentMonth || 0);
  const width = padding.left + maxMonth * monthW + padding.right;
  const height = padding.top + LAYER_ORDER.length * (trackH + 8) + padding.bottom;

  return (
    <div className="overflow-auto">
      <p className="text-xs text-slate-500 italic leading-relaxed mb-2 max-w-md">
        See a chronic case as a layered timeline: physical suppressions, acute episodes, chronic layer emergence, and constitutional remedy actions plotted on horizontal tracks across months. A vertical "NOW" marker shows where the patient is in treatment. Helps spot the relationship between suppressions and emerging symptoms, and decide when to act or wait.
      </p>
      <svg width={width} height={height} className="font-mono text-xs">
        {/* Title */}
        <text x={width / 2} y={28} textAnchor="middle" className="fill-slate-200 font-semibold">
          Layer Timeline — Chronic Case History
        </text>

        {/* Month grid lines */}
        {Array.from({ length: maxMonth + 1 }, (_, m) => {
          const x = padding.left + m * monthW;
          return (
            <g key={m}>
              <line x1={x} y1={padding.top} x2={x} y2={height - padding.bottom} stroke="#334155" strokeWidth={0.5} />
              <text x={x} y={padding.top - 8} textAnchor="middle" className="fill-slate-500">
                M{m}
              </text>
            </g>
          );
        })}

        {/* Tracks */}
        {LAYER_ORDER.map((layer, li) => {
          const y = padding.top + li * (trackH + 8);
          return (
            <g key={layer}>
              <rect x={0} y={y} width={padding.left - 8} height={trackH} fill="#0f172a" rx={4} />
              <text
                x={padding.left - 16}
                y={y + trackH / 1.5}
                textAnchor="end"
                className="fill-slate-300 font-semibold"
                fontSize={11}
              >
                {layer.charAt(0).toUpperCase() + layer.slice(1)}
              </text>
            </g>
          );
        })}

        {/* Events */}
        {events.map((evt) => {
          const li = LAYER_ORDER.indexOf(evt.layer);
          if (li < 0) return null;
          const y = padding.top + li * (trackH + 8);
          const x = padding.left + evt.startMonth * monthW;
          const w = Math.max((evt.endMonth - evt.startMonth) * monthW, monthW * 0.8);
          return (
            <g key={evt.id}>
              <rect
                x={x}
                y={y + 2}
                width={w}
                height={trackH - 4}
                fill={evt.color || LAYER_COLORS[evt.layer] || "#64748b"}
                opacity={0.85}
                rx={4}
              />
              <text
                x={x + w / 2}
                y={y + trackH / 1.5}
                textAnchor="middle"
                className="fill-slate-900 font-semibold"
                fontSize={10}
              >
                {evt.remedy || evt.label}
              </text>
            </g>
          );
        })}

        {/* Current pointer */}
        {currentMonth !== undefined && (
          <g>
            <line
              x1={padding.left + currentMonth * monthW}
              y1={padding.top - 12}
              x2={padding.left + currentMonth * monthW}
              y2={height - padding.bottom}
              stroke="#fbbf24"
              strokeWidth={2}
              strokeDasharray="4 2"
            />
            <text
              x={padding.left + currentMonth * monthW}
              y={padding.top - 16}
              textAnchor="middle"
              className="fill-amber-400 font-bold"
              fontSize={10}
            >
              NOW
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
