"use client";

/**
 * Phantom Rubric Risk Gauge — BEGINNER
 *
 * Speedometer showing concentration of "phantom rubrics" (rubrics with
 * few remedy links that can skew results). Flags low-confidence analyses.
 */

export default function PhantomRubricRiskGauge({
  phantomRisk = 0.15,
  flaggedCount = 3,
  totalRubrics = 143408,
}: {
  phantomRisk?: number;
  flaggedCount?: number;
  totalRubrics?: number;
}) {
  const pct = Math.min(Math.max(phantomRisk * 100, 0), 100);
  const angle = -135 + (pct / 100) * 270; // –135° to +135°

  const cx = 160;
  const cy = 110;
  const r = 80;

  const status = pct < 15 ? "safe" : pct < 35 ? "caution" : "risk";
  const statusColor = { safe: "#16a34a", caution: "#f59e0b", risk: "#dc2626" }[status];

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">BEGINNER</span>
        <span className="text-xs text-gray-500">Low-confidence rubric warning</span>
      </div>

      <svg width={320} height={140} className="select-none">
        {/* Arc background */}
        <path
          d={`M ${cx + r * Math.cos((-135 * Math.PI) / 180)} ${cy + r * Math.sin((-135 * Math.PI) / 180)} A ${r} ${r} 0 1 1 ${cx + r * Math.cos((135 * Math.PI) / 180)} ${cy + r * Math.sin((135 * Math.PI) / 180)}`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={12}
          strokeLinecap="round"
        />

        {/* Colored arc */}
        <path
          d={`M ${cx + r * Math.cos((-135 * Math.PI) / 180)} ${cy + r * Math.sin((-135 * Math.PI) / 180)} A ${r} ${r} 0 ${pct > 50 ? 1 : 0} 1 ${cx + r * Math.cos((angle * Math.PI) / 180)} ${cy + r * Math.sin((angle * Math.PI) / 180)}`}
          fill="none"
          stroke={statusColor}
          strokeWidth={12}
          strokeLinecap="round"
        />

        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={cx + (r - 10) * Math.cos((angle * Math.PI) / 180)}
          y2={cy + (r - 10) * Math.sin((angle * Math.PI) / 180)}
          stroke="#374151"
          strokeWidth={3}
          strokeLinecap="round"
        />
        <circle cx={cx} cy={cy} r={6} fill="#374151" />

        {/* Labels */}
        <text x={cx - r - 10} y={cy + 15} fontSize={10} fill="#9ca3af">Safe</text>
        <text x={cx - 10} y={cy - r + 5} fontSize={10} fill="#9ca3af">Caution</text>
        <text x={cx + r - 5} y={cy + 15} fontSize={10} fill="#9ca3af">Risk</text>
      </svg>

      <div className="text-center -mt-2">
        <div className="text-2xl font-bold" style={{ color: statusColor }}>
          {pct.toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500">
          {flaggedCount} phantom rubrics flagged of {totalRubrics.toLocaleString()}
        </div>
      </div>
    </div>
  );
}
