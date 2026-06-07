"use client";

export default function BatchProtocolPanel({ result }: { result?: { protocols?: any[] } }) {
  const protocols = result?.protocols || [];
  return (
    <div className="space-y-2 max-h-48 overflow-y-auto">
      {protocols.slice(0, 5).map((p: any) => (
        <div key={p.id} className="border-l-4 border-violet-400 pl-3 py-1">
          <div className="text-sm font-medium text-slate-700">{p.name}</div>
          <div className="text-xs text-slate-500">{p.condition} • {p.steps?.length || 0} steps</div>
        </div>
      ))}
      {protocols.length === 0 && <div className="text-sm text-slate-400 italic">No protocols defined</div>}
    </div>
  );
}
