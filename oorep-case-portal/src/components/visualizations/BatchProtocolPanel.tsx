"use client";

export default function BatchProtocolPanel({ result }: { result?: { protocols?: any[] } }) {
  const protocols = result?.protocols || [];
  return (
    <div className="space-y-2 max-h-48 overflow-y-auto">
      <p className="text-xs text-slate-500 italic leading-relaxed">
        Quick access to standard treatment protocols for common conditions — each protocol names the condition, lists the remedy sequence with potencies, and shows how many steps are involved. Useful for experienced practitioners who want a fast starting template they can adapt to the individual case.
      </p>
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
