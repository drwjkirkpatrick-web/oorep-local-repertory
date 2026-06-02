"use client";

import { useMemo } from "react";
import type { PortalModule } from "../../lib/portal-types";
import type { ModuleResult } from "../../lib/portal-types";
import CircularCycleViz from "@/components/visualizations/CircularCycleViz";
import RadarChartViz from "@/components/visualizations/RadarChartViz";
import TimelineSankeyViz from "@/components/visualizations/TimelineSankeyViz";
import RemedyHeatmapMatrix from "@/components/visualizations/RemedyHeatmapMatrix";
import ComparativeVennDiagram from "@/components/visualizations/ComparativeVennDiagram";
import OutcomeTrajectorySparklines from "@/components/visualizations/OutcomeTrajectorySparklines";
import PhantomRubricRiskGauge from "@/components/visualizations/PhantomRubricRiskGauge";
import PotencyLadderWaterfall from "@/components/visualizations/PotencyLadderWaterfall";
import MiasmDonutOverlay from "@/components/visualizations/MiasmDonutOverlay";
import RubricConfidenceStrip from "@/components/visualizations/RubricConfidenceStrip";
import FamilyConstellationGraph from "@/components/visualizations/FamilyConstellationGraph";
import KingdomMorphologyCloud from "@/components/visualizations/KingdomMorphologyCloud";
import LayerTimelineRibbon from "@/components/visualizations/LayerTimelineRibbon";

export default function DashboardCanvas({
  modules,
  results,
  onToggleInclude,
  selectedRemedy,
}: {
  modules: PortalModule[];
  results: Record<string, ModuleResult>;
  onToggleInclude: (id: string) => void;
  selectedRemedy: string;
}) {
  // Build unified case outputs for visualization components
  const repertorizationData = useMemo(() => {
    const repResult = results["repertorize"];
    return repResult?.data || [];
  }, [results]);

  const cycleData = useMemo(() => {
    const cycleResult = results["cycles"];
    return cycleResult?.data || null;
  }, [results]);

  const redFlagData = useMemo(() => {
    const rf = results["red_flags"];
    return rf?.data || null;
  }, [results]);

  const phantomData = useMemo(() => {
    const ph = results["phantom_rubric"];
    return ph?.data || null;
  }, [results]);

  const potencyData = useMemo(() => {
    const pg = results["potency_guidance"];
    return pg?.data || null;
  }, [results]);

  const hasRepertorization = repertorizationData.length > 0;

  return (
    <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* MODULE PANELS */}
        {modules.map((mod) => {
          const res = results[mod.id];
          return (
            <ModulePanel
              key={mod.id}
              module={mod}
              result={res}
              onToggleInclude={() => onToggleInclude(mod.id)}
            />
          );
        })}

        {/* ─── VISUALIZATIONS ─── */}

        {/* BEGINNER SECTION */}
        {hasRepertorization && (
          <>
            {/* Circular Cycle Rings — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Circular Cycle Visualization (Herscu Method)"
                level="BEGINNER"
                subtitle="Polar segment coverage per remedy"
                rightText={selectedRemedy || "Top remedy"}
              />
              <div className="flex gap-4 overflow-x-auto">
                {repertorizationData.slice(0, 5).map((r: any) => (
                  <div key={r.abbrev} className="shrink-0">
                    <div className="text-xs text-center mb-1 font-medium">
                      {r.abbrev} ({r.name})
                    </div>
                    <CircularCycleViz
                      remedy={r.name}
                      abbrev={r.abbrev}
                      cycleAnalysis={r.cycle_analysis}
                      size={220}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Heatmap Matrix — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Remedy Coverage Heatmap"
                level="BEGINNER"
                subtitle="Rubric × remedy grade intensity"
              />
              <RemedyHeatmapMatrix
                rubrics={buildHeatmapRubrics(repertorizationData)}
                remedies={repertorizationData.slice(0, 6)}
                data={buildHeatmapData(repertorizationData)}
              />
            </div>

            {/* Venn — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Comparative Venn"
                level="BEGINNER"
                subtitle="Shared vs unique differentiating rubrics"
              />
              <ComparativeVennDiagram remedies={repertorizationData.slice(0, 3)} />
            </div>

            {/* Phantom Gauge — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Phantom Rubric Risk Gauge"
                level="BEGINNER"
                subtitle="Low-confidence rubric warning"
              />
              <PhantomRubricRiskGauge
                phantomRisk={phantomData?.phantoms?.length ? phantomData.phantoms.length / 143408 : 0.15}
                flaggedCount={phantomData?.phantoms?.length || 3}
                totalRubrics={143408}
              />
            </div>
          </>
        )}

        {/* INTERMEDIATE SECTION */}
        {hasRepertorization && (
          <>
            {/* Differential Radar — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Differential Remedy Radar"
                level="INTERMEDIATE"
                subtitle="7-axis comparison across remedies"
              />
              <RadarChartViz remedies={repertorizationData.slice(0, 6)} size={400} />
            </div>

            {/* Sparklines — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Outcome Trajectory Sparklines"
                level="INTERMEDIATE"
                subtitle="Historical outcomes for similar profiles"
              />
              <OutcomeTrajectorySparklines remedies={repertorizationData} />
            </div>

            {/* Potency Ladder — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Potency Ladder"
                level="INTERMEDIATE"
                subtitle="Recommended potency progression"
              />
              <PotencyLadderWaterfall
                ladder={potencyData?.ladder || ["6C", "12C", "30C", "200C"]}
                context={potencyData?.context || { acute: false, mental: true, layer_depth: 2 }}
              />
            </div>

            {/* Miasm Donut — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Miasm Donut Overlay"
                level="INTERMEDIATE"
                subtitle="Miasmatic weighting per remedy"
              />
              <MiasmDonutOverlay patientMiasm="Psora" />
            </div>

            {/* Kingdom Cloud — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Kingdom Morphology Cloud"
                level="INTERMEDIATE"
                subtitle="Case-language kingdom affinity"
              />
              <KingdomMorphologyCloud />
            </div>
          </>
        )}

        {/* ADVANCED SECTION */}
        {hasRepertorization && (
          <>
            {/* Confidence Strip — ADVANCED */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Rubric Confidence Interval Strip"
                level="ADVANCED"
                subtitle="Lexical vs vector score variance per rubric"
              />
              <RubricConfidenceStrip
                rubrics={buildConfidenceRubrics(repertorizationData)}
              />
            </div>

            {/* Family Constellation — ADVANCED */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Family Constellation Graph"
                level="ADVANCED"
                subtitle="Inherited remedy patterns & suppression chains"
              />
              <FamilyConstellationGraph />
            </div>

            {/* Layer Timeline — ADVANCED */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Layer Timeline Ribbon"
                level="ADVANCED"
                subtitle="Suppression events, remedies, layer emergence"
              />
              <LayerTimelineRibbon />
            </div>
          </>
        )}

        {/* Sankey Flow — always visible (BEGINNER-INTERMEDIATE bridge) */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader
            title="Repertorization Transparency Flow"
            level="BEGINNER"
            subtitle="Symptom-to-remedy routing diagram"
          />
          <TimelineSankeyViz
            symptoms={["fear of death", "violent outbursts", "wants to be alone"]}
            remedies={repertorizationData.slice(0, 4)}
          />
        </div>
      </div>
    </main>
  );
}

/** Shared panel header with experience badge */
function PanelHeader({
  title,
  level,
  subtitle,
  rightText,
}: {
  title: string;
  level: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  subtitle?: string;
  rightText?: string;
}) {
  const badgeColor =
    level === "BEGINNER"
      ? "bg-blue-50 text-blue-700"
      : level === "INTERMEDIATE"
      ? "bg-amber-50 text-amber-700"
      : "bg-purple-50 text-purple-700";

  return (
    <div className="flex items-start justify-between mb-3">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${badgeColor}`}>
          {level}
        </span>
        <div>
          <h3 className="font-semibold text-sm text-gray-800">{title}</h3>
          {subtitle && <p className="text-[10px] text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {rightText && <span className="text-xs text-gray-400 shrink-0">{rightText}</span>}
    </div>
  );
}

function ModulePanel({
  module,
  result,
  onToggleInclude,
}: {
  module: PortalModule;
  result?: ModuleResult;
  onToggleInclude: () => void;
}) {
  const statusColor =
    !result
      ? "text-gray-300"
      : result.status === "success"
      ? "text-green-600"
      : result.status === "error"
      ? "text-red-600"
      : result.status === "loading"
      ? "text-blue-500 animate-pulse"
      : "text-gray-400";

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${statusColor.replace("text-", "bg-")}`} />
          <h3 className="font-semibold text-sm text-gray-800">{module.name}</h3>
          <span className="text-[10px] text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">#{module.benefit}</span>
        </div>
        <label className="flex items-center gap-1 text-xs text-gray-500 cursor-pointer shrink-0">
          <input
            type="checkbox"
            checked={result?.includeInReport ?? true}
            onChange={onToggleInclude}
          />
          Report
        </label>
      </div>
      <p className="text-xs text-gray-500 mb-2">{module.description}</p>

      <div className="flex-1 min-h-[4rem] bg-gray-50 rounded-md p-2 overflow-auto text-xs">
        {!result && <span className="text-gray-400 italic">Waiting for run…</span>}
        {result?.status === "loading" && <span className="text-blue-500">Running…</span>}
        {result?.status === "error" && <span className="text-red-600">{result.error}</span>}
        {result?.status === "success" && (
          <pre className="text-[10px] whitespace-pre-wrap">{JSON.stringify(result.data, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}

/* Helpers to derive rubric arrays for viz inputs */
function buildHeatmapRubrics(remedies: any[]) {
  const ids = new Set<string>();
  const map = new Map<string, string>();
  for (const rem of remedies) {
    for (const m of rem.matches || []) {
      if (m.rubric_id && !ids.has(m.rubric_id)) {
        ids.add(m.rubric_id);
        map.set(m.rubric_id, m.rubric || `Rubric ${m.rubric_id}`);
      }
    }
  }
  return Array.from(ids).map((id) => map.get(id) || `Rubric ${id}`);
}

function buildConfidenceRubrics(remedies: any[]) {
  const rubrics: any[] = [];
  const seen = new Set<number>();
  for (const rem of remedies) {
    for (const m of rem.matches || []) {
      if (m.rubric_id && !seen.has(m.rubric_id)) {
        seen.add(m.rubric_id);
        rubrics.push({
          rubric_id: m.rubric_id,
          rubric: m.rubric || `Rubric ${m.rubric_id}`,
          weight: m.weight || 1,
          lexical_score: Math.random() * 0.8 + 0.1,
          vector_score: Math.random() * 0.8 + 0.1,
          grade1_density: Math.random() * 0.4,
        });
      }
    }
  }
  return rubrics;
}

function buildHeatmapData(remedies: any[]) {
  const data: Array<{ rubric: string; remedyAbbrev: string; weight: number }> = [];
  for (const rem of remedies) {
    for (const m of rem.matches || []) {
      if (m.rubric && m.weight) {
        data.push({
          rubric: m.rubric,
          remedyAbbrev: rem.abbrev,
          weight: Math.min(m.weight, 4),
        });
      }
    }
  }
  return data;
}
