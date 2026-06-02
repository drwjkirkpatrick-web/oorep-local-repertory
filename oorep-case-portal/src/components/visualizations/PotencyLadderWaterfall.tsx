"use client";

/**
 * Potency Ladder Waterfall — INTERMEDIATE
 *
 * Vertical cascading chart showing recommended potency sequence.
 * Each rung labeled with rationale.
 */

export default function PotencyLadderWaterfall({
  ladder,
  context,
}: {
  ladder: string[];
  context: { acute: boolean; mental: boolean; layer_depth: number };
}) {
  const rungs = ladder.map((potency, i) => {
    const rationale = i === 0
      ? context.acute ? "Acute starter — matches physical onset" : "Gentle opening — observe reaction"
      : i === ladder.length - 1
      ? "Deep chronic — constitutional layer"
      : `Progressive step ${i + 1}`;
    return { potency, rationale, active: i === 0 };
  });

  const cellH = 40;
  const width = 320;
  const height = rungs.length * cellH + 60;

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">INTERMEDIATE</span>
        <span className="text-xs text-gray-500">Recommended potency progression</span>
      </div>

      <svg width={width} height={height} className="select-none">
        {rungs.map((rung, i) => {
          const y = 30 + i * cellH;
          const w = 160 - i * 12; // tapering
          const x = (width - w) / 2;
          const color = rung.active ? "#1e40af" : "#9ca3af";
          return (
            <g key={i}>
              {/* Rung block */}
              <rect x={x} y={y} width={w} height={28} rx={4} fill={rung.active ? "#dbeafe" : "#f3f4f6"} stroke={color} strokeWidth={1.5} />
              <text x={width / 2} y={y + 18} textAnchor="middle" fontSize={12} fontWeight={600} fill={color}>
                {rung.potency}
              </text>
              {/* Rationale */}
              <text x={width / 2} y={y + 38} textAnchor="middle" fontSize={9} fill="#6b7280">
                {rung.rationale}
              </text>
              {/* Connector arrow */}
              {i < rungs.length - 1 && (
                <path
                  d={`M ${width / 2} ${y + 28} L ${width / 2} ${y + cellH - 2}`}
                  stroke="#d1d5db"
                  strokeWidth={1.5}
                  strokeDasharray="3,2"
                  markerEnd="url(#arrow)"
                />
              )}
            </g>
          );
        })}

        {/* Arrow marker */}
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#d1d5db" />
          </marker>
        </defs>
      </svg>
    </div>
  );
}
