"use client";

/**
 * ConcordanceCube — 3D Multi-Method Agreement Visualization
 *
 * Shows remedies as glowing spheres inside a 3D cube. Each axis is a
 * different scoring methodology (classical, cycle, SRP, outcome).
 * Remedies near the main diagonal (1,1,1) score consistently across ALL
 * methods → high confidence signal. Remedies scattered far from diagonal
 * are method-dependent noise. The practitioner can rotate the cube,
 * hover to see concordance metrics, and click to select a remedy.
 */

import React, { useMemo, useState, useCallback, useEffect, useRef } from "react";
import { project3D, sphereProject, cubeFaces, deg } from "@/lib/projection3d";

interface Remedy {
  abbrev: string;
  name: string;
  score: number;
  cycle_analysis?: {
    segment_coverage?: number;
    meets_threshold?: boolean;
  };
  srp_density?: number;
  outcome_rate?: number;
}

interface ConcordanceCubeProps {
  remedies: Remedy[];
  onRemedyClick?: (abbrev: string) => void;
}

const AXIS_COLORS = {
  classical: "#3b82f6", // blue
  cycle:     "#16a34a", // green
  srp:       "#be123c", // crimson
  outcome:   "#f59e0b", // amber
};

type ActiveMethods = { classical: boolean; cycle: boolean; srp: boolean };

export default function ConcordanceCube({ remedies, onRemedyClick }: ConcordanceCubeProps) {
  // ── 3D camera state ──
  const [rotY, setRotY] = useState(deg(25));
  const [rotX, setRotX] = useState(deg(-20));
  const [dragging, setDragging] = useState(false);
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState<string | null>(null);

  const [autoRotate, setAutoRotate] = useState(true);
  const [activeMethods, setActiveMethods] = useState<ActiveMethods>({ classical: true, cycle: true, srp: true });
  const [threshold, setThreshold] = useState(0);

  const draggingRef = useRef(false);
  const autoRotateRef = useRef(true);

  useEffect(() => { draggingRef.current = dragging; }, [dragging]);
  useEffect(() => { autoRotateRef.current = autoRotate; }, [autoRotate]);

  // ── Auto-rotation animation ──
  useEffect(() => {
    let animId: number;
    const tick = () => {
      if (autoRotateRef.current && !draggingRef.current) {
        setRotY((prev) => prev + 0.3 * (Math.PI / 180));
      }
      animId = requestAnimationFrame(tick);
    };
    animId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animId);
  }, []);

  const size = 420;
  const cx = size / 2;
  const cy = size / 2;
  const scale = 1.2;

  // ── Normalize remedy coords to 0-1 per axis ──
  const data = useMemo(() => {
    const maxScore = Math.max(...remedies.map((r) => r.score || 0), 1);
    return remedies.slice(0, 8).map((r) => {
      const classical = (r.score || 0) / maxScore;
      const cycle     = r.cycle_analysis?.segment_coverage || 0;
      const srp       = r.srp_density || (r.score > 30 ? 0.6 : 0.2);
      const outcome   = r.outcome_rate || 0.5;

      // Concordance = Euclidean distance from perfect (1,1,1,1) in 4D projected to 3D
      // We use classical, cycle, srp as 3D axes; outcome as sphere color intensity
      const concordance = Math.sqrt(
        (1 - classical) ** 2 + (1 - cycle) ** 2 + (1 - srp) ** 2
      ) / Math.sqrt(3); // 0 = perfect, 1 = worst

      const confidence = 1 - concordance; // 0-1, higher = better

      return {
        abbrev: r.abbrev,
        name: r.name,
        x: classical * 200 - 100,     // map 0-1 → -100 to 100 cube space
        y: -(cycle * 200 - 100),      // invert Y so up is better
        z: srp * 200 - 100,
        classical,
        cycle,
        srp,
        outcome,
        concordance,
        confidence,
        radius: 6 + confidence * 10,    // bigger sphere = more confident
        color: outcome > 0.6 ? "#16a34a" : outcome > 0.4 ? "#f59e0b" : "#ef4444",
        meetsThreshold: r.cycle_analysis?.meets_threshold || false,
      };
    });
  }, [remedies]);

  // ── Mouse drag handlers for rotation ──
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    draggingRef.current = true;
    setDragging(true);
    setLastMouse({ x: e.clientX, y: e.clientY });
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging) return;
    const dx = e.clientX - lastMouse.x;
    const dy = e.clientY - lastMouse.y;
    setRotY((prev) => prev + dx * 0.01);
    setRotX((prev) => Math.max(-Math.PI / 2, Math.min(Math.PI / 2, prev + dy * 0.01)));
    setLastMouse({ x: e.clientX, y: e.clientY });
  }, [dragging, lastMouse]);

  const onMouseUp = useCallback(() => {
    draggingRef.current = false;
    setDragging(false);
  }, []);

  // ── Render ──
  const cube = cubeFaces({ x: 0, y: 0, z: 0 }, 200, rotY, rotX, cx, cy, scale);

  // Axis labels at cube corners
  const axisLabels = [
    { label: "Classical", pos: { x: 120, y: 0, z: 0 }, color: AXIS_COLORS.classical },
    { label: "Cycle",     pos: { x: 0, y: -120, z: 0 }, color: AXIS_COLORS.cycle },
    { label: "SRP",       pos: { x: 0, y: 0, z: 120 }, color: AXIS_COLORS.srp },
  ];

  const projectedLabels = axisLabels.map((a) => ({
    ...a,
    proj: project3D(a.pos, rotY, rotX, cx, cy, scale),
  }));

  // Diagonal line (perfect concordance axis) projected
  const diagStart = project3D({ x: -100, y: 100, z: -100 }, rotY, rotX, cx, cy, scale);
  const diagEnd   = project3D({ x: 100, y: -100, z: 100 }, rotY, rotX, cx, cy, scale);

  // Projected remedy spheres
  const spheres = data.map((d) => ({
    ...d,
    proj: sphereProject({ x: d.x, y: d.y, z: d.z }, d.radius, rotY, rotX, cx, cy, scale),
  }));

  const hoveredData = data.find((d) => d.abbrev === hovered);

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs text-slate-500 italic leading-relaxed text-center max-w-md mb-2">
        See which remedies score consistently across ALL methods. Each axis is a different scoring methodology (classical, cycle, SRP). Remedies clustered along the diagonal (1,1,1) are high-confidence signal — they rank well no matter how you score. Remedies scattered far from the diagonal are method-dependent noise. Drag to rotate the cube.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">ADVANCED</span>
        <span className="text-xs text-gray-500">Multi-method concordance in 3D</span>
      </div>

      <svg
        width={size}
        height={size}
        className={`select-none ${dragging ? "cursor-grabbing" : "cursor-grab"}`}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        {/* Background */}
        <rect width={size} height={size} fill="#f8fafc" rx={8} />

        {/* Cube wireframe faces (painter sorted) */}
        {cube.map((f, i) => (
          <polygon
            key={i}
            points={f.points}
            fill={f.fill}
            stroke={f.stroke}
            strokeWidth={1}
            strokeDasharray="4 2"
          />
        ))}

        {/* Diagonal concordance axis */}
        <line
          x1={diagStart.x}
          y1={diagStart.y}
          x2={diagEnd.x}
          y2={diagEnd.y}
          stroke="#94a3b8"
          strokeWidth={2}
          strokeDasharray="6 3"
          opacity={0.6}
        />
        <text
          x={(diagStart.x + diagEnd.x) / 2 + 10}
          y={(diagStart.y + diagEnd.y) / 2}
          fontSize={10}
          fill="#94a3b8"
          fontStyle="italic"
        >
          Perfect concordance
        </text>

        {/* Axis labels */}
        {projectedLabels.map((a, i) => {
          const isActive = activeMethods[a.label.toLowerCase() as keyof ActiveMethods];
          return (
            <g key={i} opacity={isActive ? 1 : 0.3}>
              <circle cx={a.proj.x} cy={a.proj.y} r={4} fill={a.color} />
              <text
                x={a.proj.x + 8}
                y={a.proj.y + 4}
                fontSize={11}
                fill={a.color}
                fontWeight={600}
              >
                {a.label}
              </text>
            </g>
          );
        })}

        {/* Remedy spheres (depth-sorted for occlusion) */}
        {[...spheres]
          .sort((a, b) => b.proj.depth - a.proj.depth)
          .map((s) => {
            const isMethodHidden =
              (!activeMethods.classical && s.classical < 0.5) ||
              (!activeMethods.cycle && s.cycle < 0.5) ||
              (!activeMethods.srp && s.srp < 0.5);
            if (isMethodHidden) return null;
            const passesThreshold = Math.round(s.confidence * 100) >= threshold;
            const opacity = passesThreshold ? (hovered === s.abbrev ? 1 : 0.85) : 0.1;
            return (
              <g key={s.abbrev}>
                {/* Glow halo for high confidence */}
                {s.confidence > 0.7 && passesThreshold && (
                  <circle
                    cx={s.proj.x}
                    cy={s.proj.y}
                    r={s.proj.r + 8}
                    fill={s.color}
                    opacity={0.15}
                    style={{ pointerEvents: "none" }}
                  />
                )}
                <circle
                  cx={s.proj.x}
                  cy={s.proj.y}
                  r={s.proj.r}
                  fill={s.color}
                  opacity={opacity}
                  stroke={hovered === s.abbrev ? "#1e293b" : "#fff"}
                  strokeWidth={hovered === s.abbrev ? 2 : 1}
                  style={{ cursor: "pointer", transition: "all 0.15s" }}
                  onMouseEnter={() => setHovered(s.abbrev)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => onRemedyClick && onRemedyClick(s.abbrev)}
                >
                  <title>
                    {s.name} ({s.abbrev}){"\n"}
                    Confidence: {Math.round(s.confidence * 100)}%{"\n"}
                    Classical: {Math.round(s.classical * 100)}%{"\n"}
                    Cycle: {Math.round(s.cycle * 100)}%{"\n"}
                    SRP: {Math.round(s.srp * 100)}%{"\n"}
                    Outcome: {Math.round(s.outcome * 100)}%
                  </title>
                </circle>
                {/* Label */}
                <text
                  x={s.proj.x}
                  y={s.proj.y - s.proj.r - 4}
                  textAnchor="middle"
                  fontSize={10}
                  fill={s.color}
                  fontWeight={600}
                  opacity={opacity < 0.5 ? 0.3 : 1}
                  style={{ pointerEvents: "none" }}
                >
                  {s.abbrev}
                </text>
              </g>
            );
          })}
      </svg>

      {/* ── Auto-rotation toggle ── */}
      <div className="flex items-center gap-3 mt-2">
        <button
          onClick={() => setAutoRotate((prev) => !prev)}
          className="text-xs px-2 py-0.5 rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700"
        >
          {autoRotate ? "⏸ Pause rotation" : "▶ Resume rotation"}
        </button>
      </div>

      {/* ── Method toggle checkboxes ── */}
      <div className="flex gap-3 mt-2 flex-wrap justify-center">
        {([
          { key: "classical", label: "Classical" },
          { key: "cycle", label: "Cycle" },
          { key: "srp", label: "SRP" },
        ] as const).map((m) => (
          <label key={m.key} className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={activeMethods[m.key]}
              onChange={() =>
                setActiveMethods((prev) => ({ ...prev, [m.key]: !prev[m.key] }))
              }
              className="w-3 h-3 accent-slate-600"
            />
            {m.label}
          </label>
        ))}
      </div>

      {/* ── Confidence threshold slider ── */}
      <div className="flex items-center gap-2 mt-2">
        <span className="text-xs text-gray-500">Confidence threshold</span>
        <input
          type="range"
          min={0}
          max={100}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          className="w-32 h-1 accent-slate-600"
        />
        <span className="text-xs text-gray-600 w-8 text-right">{threshold}%</span>
      </div>

      {/* ── Hover detail card ── */}
      {hoveredData && (
        <div className="mt-3 p-3 bg-white border rounded-lg shadow-sm max-w-xs text-center">
          <div className="text-sm font-bold text-gray-800">
            {hoveredData.name} ({hoveredData.abbrev})
          </div>
          <div className="mt-1 flex items-center justify-center gap-2">
            <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              Concordance {Math.round(hoveredData.confidence * 100)}%
            </span>
            {hoveredData.meetsThreshold && (
              <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-700">
                ✓ Cycle match
              </span>
            )}
          </div>
          <div className="mt-2 grid grid-cols-3 gap-1 text-[10px]">
            <div className="text-blue-600">Classical {Math.round(hoveredData.classical * 100)}%</div>
            <div className="text-green-600">Cycle {Math.round(hoveredData.cycle * 100)}%</div>
            <div className="text-red-600">SRP {Math.round(hoveredData.srp * 100)}%</div>
          </div>
        </div>
      )}

      {/* ── Legend ── */}
      <div className="flex gap-3 mt-2 flex-wrap justify-center">
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-3 h-3 rounded-full bg-green-500 inline-block"></span> High outcome
        </div>
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span> Medium
        </div>
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> Low outcome
        </div>
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-3 h-3 rounded-full border-2 border-slate-300 inline-block"></span> Size = confidence
        </div>
      </div>
    </div>
  );
}
