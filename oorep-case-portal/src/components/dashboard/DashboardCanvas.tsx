"use client";

import { useMemo } from "react";
import type { PortalModule } from "../../lib/portal-types";
import type { ModuleResult } from "../../lib/portal-types";
import CircularCycleViz from "@/components/visualizations/CircularCycleViz";
import RadarChartViz from "@/components/visualizations/RadarChartViz";
import TimelineSankeyViz from "@/components/visualizations/TimelineSankeyViz";

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

  return (
    <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
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

        {/* Visualization panels — always show if we have repertorization data */}
        {repertorizationData.length > 0 && (
          <>
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-sm">
                  Circular Cycle Visualization (Herscu Method)
                </h3>
                <span className="text-xs text-gray-400">{selectedRemedy || "Top remedy"}</span>
              </div>
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

            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-sm">
                  Differential Remedy Radar
                </h3>
              </div>
              <RadarChartViz
                remedies={repertorizationData.slice(0, 6)}
                size={400}
              />
            </div>
          </>
        )}

        {/* Timeline + Sankey for any case data */}
        <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm">
              Repertorization Transparency Flow
            </h3>
          </div>
          <TimelineSankeyViz
            symptoms={["fear of death", "violent outbursts", "wants to be alone"]}
            remedies={repertorizationData.slice(0, 4)}
          />
        </div>
      </div>
    </main>
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
          <h3 className="font-semibold text-sm">{module.name}</h3>
          <span className="text-xs text-gray-400">#{module.benefit}</span>
        </div>
        <label className="flex items-center gap-1 text-xs text-gray-500 cursor-pointer">
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
        {!result && <span className="text-gray-400 italic">Waiting for run...</span>}
        {result?.status === "loading" && <span className="text-blue-500">Running...</span>}
        {result?.status === "error" && (
          <span className="text-red-600">{result.error}</span>
        )}
        {result?.status === "success" && (
          <pre className="text-[10px] whitespace-pre-wrap">{JSON.stringify(result.data, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}
