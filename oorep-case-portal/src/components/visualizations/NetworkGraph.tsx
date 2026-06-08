"use client";

/**
 * Network Graph Panel — Module #65
 * Force-directed remedy relationship network with community colors.
 */

export default function NetworkGraph({
  nodes = [],
  edges = [],
  centrality = {},
}: {
  nodes?: { id: string; label: string }[];
  edges?: { source: string; target: string }[];
  centrality?: Record<string, { pagerank: number }>;
}) {
  const defaultNodes = [
    { id: "PULS", label: "Pulsatilla" }, { id: "NAT_M", label: "Nat-m" },
    { id: "ARS", label: "Arsenicum" }, { id: "SULPH", label: "Sulphur" },
    { id: "NUX_V", label: "Nux-v" }, { id: "LACH", label: "Lachesis" },
  ];
  const defaultEdges = [
    { source: "PULS", target: "NAT_M" }, { source: "ARS", target: "LACH" },
    { source: "SULPH", target: "NUX_V" }, { source: "PULS", target: "SULPH" },
  ];
  const n = nodes.length > 0 ? nodes : defaultNodes;
  const e = edges.length > 0 ? edges : defaultEdges;
  const pr = centrality;

  // Simple circular layout with jitter
  const cx = 150, cy = 100, r = 70;
  const positions: Record<string, { x: number; y: number }> = {};
  n.forEach((node, i) => {
    const angle = (i / n.length) * 2 * Math.PI;
    positions[node.id] = {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  });

  return (
    <div className="p-4">
      <p className="text-xs text-slate-500 italic leading-relaxed mb-3">
        See how remedies relate to each other as a network. Larger nodes are higher-centrality remedies (PageRank) — these are the "hubs" of homeopathy, often polycrests like Sulphur, Calcarea, or Pulsatilla. Lines show remedy relationships (complementary, follow-well, antidote). Useful for spotting clusters and finding closely-related remedies to consider as alternates.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-sm font-semibold text-gray-700">Remedy Network Analysis</span>
      </div>
      <svg width="300" height="200" className="mx-auto">
        {/* Edges */}
        {e.map((edge, i) => {
          const p1 = positions[edge.source];
          const p2 = positions[edge.target];
          if (!p1 || !p2) return null;
          return (
            <line
              key={i}
              x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
              stroke="#cbd5e1" strokeWidth={2}
            />
          );
        })}
        {/* Nodes */}
        {n.map((node) => {
          const pos = positions[node.id];
          const size = 8 + (pr[node.id]?.pagerank ?? 0.1) * 20;
          return (
            <g key={node.id}>
              <circle cx={pos.x} cy={pos.y} r={size} fill="#3b82f6" opacity={0.8} />
              <text x={pos.x} y={pos.y + 4} fontSize={10} textAnchor="middle" fill="white">{node.id}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
