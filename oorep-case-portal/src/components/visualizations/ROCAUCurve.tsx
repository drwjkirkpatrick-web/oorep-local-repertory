"use client";

/**
 * ROC/AUC Curve Panel — Statistical Module #64
 *
 * Displays ROC curve with AUC score, calibration plot, and bootstrap CI.
 */

export default function ROCAUCurve({
  rocData,
  calibrationData,
  bootstrapCI,
}: {
  rocData?: { auc: number; points: { fpr: number; tpr: number }[]; optimal_threshold?: number };
  calibrationData?: { reliability_diagram: { predicted: number; observed: number; count: number }[]; expected_calibration_error: number };
  bootstrapCI?: { mean_auc: number; ci_95: [number, number]; std_auc: number };
}) {
  const auc = rocData?.auc ?? 0.75;
  const points = rocData?.points ?? [];
  const ece = calibrationData?.expected_calibration_error ?? 0.08;
  const ci = bootstrapCI?.ci_95 ?? [0.65, 0.85];

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Outcome Prediction Validation</span>
      </div>

      {/* AUC Score */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-600">{auc.toFixed(3)}</div>
          <div className="text-xs text-gray-500">AUC</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">{ece.toFixed(3)}</div>
          <div className="text-xs text-gray-500">ECE</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">[{ci[0].toFixed(2)}, {ci[1].toFixed(2)}]</div>
          <div className="text-xs text-gray-500">95% CI</div>
        </div>
      </div>

      {/* ROC Curve */}
      <div className="bg-white border rounded-lg p-3">
        <div className="text-xs font-semibold text-gray-600 mb-2">ROC Curve</div>
        <svg width="280" height="200" className="mx-auto">
          {/* Grid */}
          {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
            <g key={tick}>
              <line x1={40 + tick * 200} y1={20} x2={40 + tick * 200} y2={180} stroke="#e5e7eb" strokeWidth={1} />
              <line x1={40} y1={180 - tick * 160} x2={240} y2={180 - tick * 160} stroke="#e5e7eb" strokeWidth={1} />
            </g>
          ))}
          {/* Diagonal */}
          <line x1={40} y1={180} x2={240} y2={20} stroke="#9ca3af" strokeWidth={1} strokeDasharray="4 4" />
          {/* ROC path */}
          {points.length > 0 && (
            <path
              d={`M ${40 + points[0].fpr * 200} ${180 - points[0].tpr * 160} ` +
                points.slice(1).map(p => `L ${40 + p.fpr * 200} ${180 - p.tpr * 160}`).join(" ")}
              fill="none"
              stroke="#7c3aed"
              strokeWidth={2}
            />
          )}
          {/* Axes */}
          <line x1={40} y1={180} x2={240} y2={180} stroke="#374151" strokeWidth={2} />
          <line x1={40} y1={20} x2={40} y2={180} stroke="#374151" strokeWidth={2} />
          <text x={140} y={198} fontSize={10} textAnchor="middle" fill="#6b7280">False Positive Rate</text>
          <text x={20} y={100} fontSize={10} textAnchor="middle" fill="#6b7280" transform="rotate(-90, 20, 100)">True Positive Rate</text>
        </svg>
      </div>

      {/* Calibration */}
      <div className="bg-white border rounded-lg p-3">
        <div className="text-xs font-semibold text-gray-600 mb-2">Calibration (Predicted vs Observed)</div>
        <svg width="280" height="160" className="mx-auto">
          <line x1={40} y1={140} x2={260} y2={140} stroke="#374151" strokeWidth={2} />
          <line x1={40} y1={20} x2={40} y2={140} stroke="#374151" strokeWidth={2} />
          <line x1={40} y1={140} x2={260} y2={20} stroke="#9ca3af" strokeWidth={1} strokeDasharray="4 4" />
          {calibrationData?.reliability_diagram.map((bin, i) => {
            const x = 40 + bin.predicted * 200;
            const y1 = 140;
            const y2 = 140 - bin.observed * 120;
            return (
              <g key={i}>
                <line x1={x} y1={y1} x2={x} y2={y2} stroke="#3b82f6" strokeWidth={8} />
                <circle cx={x} cy={y2} r={4} fill="#1d4ed8" />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
