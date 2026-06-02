"use client";

/**
 * Rubric Confidence Interval Strip — ADVANCED
 *
 * Horizontal bars per rubric with error bars showing lexical-vs-vector
 * variance and grade-1 density.
 */

export default function RubricConfidenceStrip({
  rubrics,
  onRubricClick,
}: {
  rubrics: {
    rubric_id: number;
    rubric: string;
    weight: number;
    lexical_score?: number;
    vector_score?: number;
    grade1_density?: number;
  }[];
  onRubricClick?: (rubric: string, rubricId?: string) => void;
}) {
  const maxW = 240;
  const barH = 14;
  const gap = 4;
  const height = rubrics.length * (barH + gap) + 20;

  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-xs text-gray-500">Confidence per rubric — narrow = reliable</span>
      </div>

      <svg width={maxW + 80} height={height} className="select-none">
        {rubrics.slice(0, 12).map((r, i) => {
          const y = 10 + i * (barH + gap);
          const confidence = r.lexical_score !== undefined && r.vector_score !== undefined
            ? 1 - Math.abs((r.lexical_score - r.vector_score))
            : 0.6;
          const barW = Math.max(confidence * maxW, 4);
          const err = ((1 - confidence) * maxW) / 2;

          const isReliable = confidence > 0.75 && (r.grade1_density || 0) < 0.3;

          return (
            <g
              key={r.rubric_id}
              onClick={() => {
                if (onRubricClick) onRubricClick(r.rubric, String(r.rubric_id));
              }}
              style={{ cursor: "pointer" }}
            >
              {/* Label */}
              <text x={0} y={y + barH / 2 + 3} fontSize={8} fill="#374151" fontWeight={500}>
                {r.rubric?.slice(0, 22) || `Rubric ${r.rubric_id}`}…
              </text>

              {/* Bar */}
              <rect
                x={90}
                y={y}
                width={barW}
                height={barH}
                rx={3}
                fill={isReliable ? "#16a34a" : "#f59e0b"}
                fillOpacity={0.85}
              />

              {/* Error caps */}
              <line x1={90 + barW + err} y1={y} x2={90 + barW + err} y2={y + barH} stroke="#9ca3af" strokeWidth={1} />
              <line x1={90 + barW - err} y1={y} x2={90 + barW - err} y2={y + barH} stroke="#9ca3af" strokeWidth={1} />
              <line x1={90 + barW - err} y1={y + barH / 2} x2={90 + barW + err} y2={y + barH / 2} stroke="#9ca3af" strokeWidth={1} />

              {/* Confidence % */}
              <text x={90 + barW + err + 4} y={y + barH / 2 + 3} fontSize={8} fill="#6b7280">
                {Math.round(confidence * 100)}%
              </text>
            </g>
          );
        })}
      </svg>

      <div className="flex gap-3 mt-1 text-[10px] text-gray-400">
        <div className="flex items-center gap-1">
          <span className="w-3 h-2 rounded-sm bg-green-600 inline-block" /> High confidence
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-2 rounded-sm bg-amber-500 inline-block" /> Moderate
        </div>
        <div className="flex items-center gap-1">
          <span className="w-8 h-0.5 bg-gray-400 inline-block" /> Error range
        </div>
      </div>
    </div>
  );
}
