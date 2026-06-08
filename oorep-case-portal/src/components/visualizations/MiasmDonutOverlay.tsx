"use client";

import { useMemo } from "react";

/**
 * Miasm Donut Overlay — INTERMEDIATE
 *
 * Donut wedges for psora / sycosis / syphilis / tubercular / cancer.
 * Overlay patient suspected miasm as a target ring.
 */

const MIASMS = [
  { name: "Psora", color: "#f59e0b", weight: 0.25 },
  { name: "Sycosis", color: "#15803d", weight: 0.20 },
  { name: "Syphilis", color: "#be123c", weight: 0.15 },
  { name: "Tubercular", color: "#7c3aed", weight: 0.25 },
  { name: "Cancer", color: "#374151", weight: 0.15 },
];

export default function MiasmDonutOverlay({
  remedyMiasms,
  patientMiasm,
}: {
  remedyMiasms?: Record<string, number>;
  patientMiasm?: string;
}) {
  const data = useMemo(() => {
    return MIASMS.map((m) => ({
      ...m,
      value: remedyMiasms?.[m.name.toLowerCase()] || m.weight,
    }));
  }, [remedyMiasms]);

  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const or = 90;
  const ir = 50;

  let startAngle = -Math.PI / 2;
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs text-slate-500 italic leading-relaxed text-center max-w-md">
        See the miasmatic weighting of a chosen remedy as a donut chart. Each wedge is one miasm (Psora, Sycosis, Syphilis, Tubercular, Cancer) and the wedge size shows how strongly that remedy is associated with that miasm. A dashed target ring highlights the patient's suspected miasm. Helps select a remedy that addresses the active miasmatic layer.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">INTERMEDIATE</span>
        <span className="text-xs text-gray-500">Miasmatic weighting per remedy</span>
      </div>

      <svg width={size} height={size} className="select-none">
        {data.map((d, i) => {
          const angle = (d.value / total) * 2 * Math.PI;
          const endAngle = startAngle + angle;
          const largeArc = angle > Math.PI ? 1 : 0;

          const x1 = cx + or * Math.cos(startAngle);
          const y1 = cy + or * Math.sin(startAngle);
          const x2 = cx + or * Math.cos(endAngle);
          const y2 = cy + or * Math.sin(endAngle);
          const x3 = cx + ir * Math.cos(endAngle);
          const y3 = cy + ir * Math.sin(endAngle);
          const x4 = cx + ir * Math.cos(startAngle);
          const y4 = cy + ir * Math.sin(startAngle);

          const path = `M ${x1} ${y1} A ${or} ${or} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${ir} ${ir} 0 ${largeArc} 0 ${x4} ${y4} Z`;

          const midAngle = startAngle + angle / 2;
          const lx = cx + (or + 14) * Math.cos(midAngle);
          const ly = cy + (or + 14) * Math.sin(midAngle);

          startAngle = endAngle;

          return (
            <g key={i}>
              <path d={path} fill={d.color} fillOpacity={0.85} stroke="#fff" strokeWidth={2} />
              <text x={lx} y={ly} textAnchor="middle" dominantBaseline="central" fontSize={9} fill="#374151" fontWeight={500}>
                {d.name}
              </text>
            </g>
          );
        })}

        {/* Patient miasm target ring */}
        {patientMiasm && (
          <g>
            <circle cx={cx} cy={cy} r={ir - 8} fill="none" stroke="#1e40af" strokeWidth={3} strokeDasharray="4,3" />
            <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" fontSize={10} fill="#1e40af" fontWeight={600}>
              {patientMiasm}
            </text>
          </g>
        )}

        {!patientMiasm && (
          <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" fontSize={9} fill="#9ca3af">
            No patient miasm set
          </text>
        )}
      </svg>
    </div>
  );
}
