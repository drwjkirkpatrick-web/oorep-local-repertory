"use client";

export default function MiasmTimelinePanel({ result }: { result?: { active_layers?: string[]; deepest_layer?: string } }) {
  const layers = result?.active_layers || [];
  const order = ["psora", "sycosis", "syphilis", "tubercular", "cancer"];
  const colors: Record<string, string> = { psora: "bg-yellow-300", sycosis: "bg-green-400", syphilis: "bg-purple-400", tubercular: "bg-orange-400", cancer: "bg-red-500" };
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-slate-700">Active Layers</div>
      <div className="flex gap-1">
        {order.map((layer) => (
          <div key={layer} className={`flex-1 h-6 rounded text-center text-xs leading-6 text-white ${layers.includes(layer) ? (colors[layer] || "bg-slate-300") : "bg-slate-100 text-slate-300"}`}>
            {layer}
          </div>
        ))}
      </div>
      {result?.deepest_layer && <div className="text-xs text-slate-500">Deepest: <span className="font-medium text-slate-700">{result.deepest_layer}</span></div>}
    </div>
  );
}
