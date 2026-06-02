"use client";

import { useCallback, useState } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  type Node,
  type Edge,
  type Connection,
  type NodeChange,
  type EdgeChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

/**
 * Drag-and-Drop Pipeline Builder
 *
 * Practitioners assemble OOREP modules into reusable clinical protocols.
 * Node graph → sequential API execution on the backend.
 */

const MODULE_NODES: Record<string, { name: string; category: string; color: string }> = {
  repertorize: { name: "Repertorize", category: "differential", color: "#dbeafe" },
  cycles: { name: "Cycles & Segments", category: "differential", color: "#fef3c7" },
  srp_detector: { name: "SRP Detector", category: "differential", color: "#fce7f3" },
  phantom_rubric: { name: "Phantom Analyzer", category: "differential", color: "#f3e8ff" },
  red_flags: { name: "Red Flag Detector", category: "safety", color: "#fee2e2" },
  phi_scrubber: { name: "PHI Scrubber", category: "safety", color: "#ffe4e6" },
  approval_gate: { name: "Approval Gate", category: "safety", color: "#ffedd5" },
  remedy_comparator: { name: "Remedy Comparator", category: "differential", color: "#dbeafe" },
  potency_guidance: { name: "Potency Guidance", category: "differential", color: "#dcfce7" },
  patient_cases: { name: "Case Memory", category: "analytics", color: "#ecfeff" },
  suppression_tracker: { name: "Suppression Tracker", category: "analytics", color: "#ecfeff" },
  remedy_relationships: { name: "Relationships", category: "materia_medica", color: "#fef9c3" },
  kent_vs_boenn: { name: "Kent vs Boenninghausen", category: "materia_medica", color: "#fef9c3" },
};

export default function PipelineBuilderPage() {
  const [nodes, setNodes] = useState<Node[]>([
    {
      id: "start",
      type: "input",
      position: { x: 100, y: 200 },
      data: { label: "🩺  Case Symptoms" },
      style: { background: "#dcfce7", border: "2px solid #16a34a" },
    },
    {
      id: "repertorize",
      position: { x: 350, y: 200 },
      data: { label: "Repertorize" },
      style: { background: MODULE_NODES.repertorize.color, border: "1px solid #93c5fd" },
    },
    {
      id: "cycles",
      position: { x: 600, y: 200 },
      data: { label: "Cycles & Segments" },
      style: { background: MODULE_NODES.cycles.color, border: "1px solid #fcd34d" },
    },
    {
      id: "red_flags",
      position: { x: 600, y: 50 },
      data: { label: "Red Flag Detector" },
      style: { background: MODULE_NODES.red_flags.color, border: "1px solid #fca5a5" },
    },
    {
      id: "end",
      type: "output",
      position: { x: 900, y: 200 },
      data: { label: "📄  Final Report" },
      style: { background: "#e0f2fe", border: "2px solid #0284c7" },
    },
  ]);

  const [edges, setEdges] = useState<Edge[]>([
    { id: "start-rep", source: "start", target: "repertorize", animated: true },
    { id: "rep-cycles", source: "repertorize", target: "cycles", animated: true },
    { id: "start-red", source: "start", target: "red_flags", animated: false },
    { id: "red-cycles", source: "red_flags", target: "cycles", animated: false },
    { id: "cycles-end", source: "cycles", target: "end", animated: true },
  ]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge({ ...connection, animated: true }, eds)),
    []
  );

  const addNode = (moduleId: string) => {
    const mod = MODULE_NODES[moduleId];
    if (!mod) return;
    const newNode: Node = {
      id: `${moduleId}-${nodes.length}`,
      position: {
        x: 300 + Math.random() * 300,
        y: 50 + Math.random() * 350,
      },
      data: { label: mod.name },
      style: { background: mod.color, border: "1px solid #9ca3af" },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const exportPipeline = () => {
    const pipeline = {
      name: `pipeline-${Date.now()}`,
      version: "1.0",
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        animated: e.animated,
      })),
      sequential: nodes
        .filter((n) => MODULE_NODES[n.id])
        .map((n) => n.id),
    };

    const blob = new Blob([JSON.stringify(pipeline, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${pipeline.name}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen">
      {/* Module Palette */}
      <aside className="w-56 bg-white border-r p-4 overflow-y-auto shrink-0">
        <h2 className="font-semibold text-sm mb-3">Pipeline Palette</h2>
        <div className="space-y-2">
          {Object.entries(MODULE_NODES).map(([id, mod]) => (
            <button
              key={id}
              onClick={() => addNode(id)}
              className="w-full text-left text-xs px-3 py-2 rounded-md border hover:bg-gray-50 transition"
              style={{ backgroundColor: mod.color }}
              title={`Add ${mod.name}`}
            >
              {mod.name}
            </button>
          ))}
        </div>

        <div className="mt-6 space-y-2">
          <button
            onClick={exportPipeline}
            className="w-full px-3 py-2 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition"
          >
            Export JSON
          </button>
          <button
            onClick={() => alert("Run pipeline via API endpoint: POST /api/pipeline/execute")}
            className="w-full px-3 py-2 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 transition"
          >
            Run Pipeline
          </button>
        </div>
      </aside>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}
