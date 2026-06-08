"use client";

export default function ResamplingEnginePanel({ result }: { result?: { ci_lower?: number; ci_upper?: number; point_estimate?: number; p_value?: number; significant?: boolean; k?: number; fold_scores?: number[]; mean_score?: number } }) {
  const hasCI = result?.ci_lower !== undefined;
  const hasCV = result?.fold_scores !== undefined;
  return (
    <div className="p-4">
      <p className="text-xs text-slate-500 italic leading-relaxed mb-3">
        See how stable and reproducible a statistical estimate really is, by running the same calculation thousands of times on resampled data. The bootstrap confidence interval shows the range of plausible values; a permutation p-value tests whether an observed effect is likely real or could have arisen by chance. Cross-validation scores show how well the model generalizes to new data.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Resampling Engine</span>
      </div>
      {hasCI && (
        <div className="bg-gray-50 rounded-lg p-3 mb-3">
          <div className="text-xs text-gray-500 mb-1">Bootstrap 95% CI</div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-blue-600">{result?.ci_lower?.toFixed(3)}</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2 relative">
              <div className="absolute left-0 right-0 top-0 bottom-0 bg-blue-400 rounded-full" style={{ marginLeft: "10%", marginRight: "10%" }} />
            </div>
            <span className="text-sm font-bold text-blue-600">{result?.ci_upper?.toFixed(3)}</span>
          </div>
          <div className="text-xs text-gray-400 mt-1">Point estimate: {result?.point_estimate?.toFixed(3)}</div>
        </div>
      )}
      {result?.p_value !== undefined && (
        <div className="bg-gray-50 rounded-lg p-3 mb-3 text-center">
          <div className="text-xs text-gray-500">Permutation p-value</div>
          <div className="text-xl font-bold" style={{ color: result?.significant ? "#059669" : "#6b7280" }}>
            {result?.p_value?.toFixed(4)}
          </div>
          <div className="text-xs text-gray-400">{result?.significant ? "✓ Significant" : "Not significant"}</div>
        </div>
      )}
      {hasCV && (
        <div className="bg-white border rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-600 mb-2">Cross-Validation ({result?.k}-fold)</div>
          <div className="flex gap-1">
            {result?.fold_scores?.map((s, i) => (
              <div key={i} className="flex-1 bg-blue-50 rounded p-1 text-center">
                <div className="text-xs text-gray-500">Fold {i+1}</div>
                <div className="text-sm font-bold text-blue-600">{s?.toFixed(3)}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-400 mt-2 text-center">Mean: {result?.mean_score?.toFixed(3)}</div>
        </div>
      )}
    </div>
  );
}
