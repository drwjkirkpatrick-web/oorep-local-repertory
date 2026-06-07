"use client";

export default function RepertoryPCAPanel({ result }: { result?: { components?: any[]; explained_variance?: number[]; projection_2d?: any[] } }) {
  const proj = result?.projection_2d ?? [];
  const ev = result?.explained_variance ?? [];
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Repertory PCA</span>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-3">
        {ev.slice(0, 3).map((v, i) => (
          <div key={i} className="bg-gray-50 rounded-lg p-2 text-center">
            <div className="text-lg font-bold text-blue-600">{v?.toFixed(2) ?? "—"}</div>
            <div className="text-xs text-gray-500">PC{i+1} variance</div>
          </div>
        ))}
      </div>
      <div className="bg-white border rounded-lg p-3">
        <div className="text-xs font-semibold text-gray-600 mb-2">2D Projection</div>
        <svg width="260" height="180" className="mx-auto">
          <line x1="30" y1="150" x2="240" y2="150" stroke="#374151" strokeWidth={2} />
          <line x1="30" y1="20" x2="30" y2="150" stroke="#374151" strokeWidth={2} />
          <text x="135" y="170" fontSize={10} textAnchor="middle" fill="#6b7280">PC1</text>
          <text x="15" y="85" fontSize={10} textAnchor="middle" fill="#6b7280" transform="rotate(-90, 15, 85)">PC2</text>
          {proj.map((p, i) => {
            const x = 30 + (p?.[0] ?? 0) * 100 + 100;
            const y = 150 - (p?.[1] ?? 0) * 60 - 60;
            return <circle key={i} cx={x} cy={y} r={4} fill="#3b82f6" opacity={0.7} />;
          })}
        </svg>
      </div>
    </div>
  );
}
