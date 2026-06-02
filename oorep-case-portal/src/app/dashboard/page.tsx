"use client";

import { useEffect, useMemo, useState } from "react";
import ModulePickerSidebar from "@/components/dashboard/ModulePickerSidebar";
import DashboardCanvas from "@/components/dashboard/DashboardCanvas";
import ReportActionBar from "@/components/dashboard/ReportActionBar";
import type { PortalModule, ModuleResult } from "@/lib/portal-types";

export default function DashboardPage() {
  const [modules, setModules] = useState<PortalModule[]>([]);
  const [activeIds, setActiveIds] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<Record<string, ModuleResult>>({});
  const [caseSymptoms, setCaseSymptoms] = useState<string>("");  const [selectedRemedy, setSelectedRemedy] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch modules
  useEffect(() => {
    fetch("/api/portal/modules")
      .then((r) => r.json())
      .then((j) => {
        if (j.ok) {
          setModules(j.modules);
          setActiveIds(
            new Set(j.modules.filter((m: PortalModule) => m.defaultEnabled).map((m: PortalModule) => m.id))
          );
        } else {
          setError("Failed to load modules");
        }
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load modules");
        setLoading(false);
      });
  }, []);

  const toggleModule = (id: string) => {
    setActiveIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const allOutputs = useMemo(() => {
    const out: Record<string, any> = {};
    for (const [id, res] of Object.entries(results)) {
      if (res.status === "success" && res.data) {
        out[id] = res.data;
      }
    }
    return out;
  }, [results]);

  // Run a single module via its API route
  const runModule = async (module: PortalModule, inputs: Record<string, any>) => {
    // Stub: mark loading
    setResults((prev) => ({
      ...prev,
      [module.id]: {
        moduleId: module.id,
        status: "loading",
        includeInReport: prev[module.id]?.includeInReport ?? true,
      },
    }));

    // For now, simulate an API call with mock data.
    // In production, each module will POST to its route.
    try {
      const res = await fetch(module.route, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...inputs, symptoms: caseSymptoms.split("\n").filter(Boolean) }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setResults((prev) => ({
        ...prev,
        [module.id]: {
          moduleId: module.id,
          status: "success",
          data: data.result || data,
          includeInReport: prev[module.id]?.includeInReport ?? true,
        },
      }));
    } catch (err: any) {
      // Fallback: if API route isn't built yet, inject mock data for visual demo
      const mock = getMockData(module.id, caseSymptoms, selectedRemedy);
      if (mock) {
        setResults((prev) => ({
          ...prev,
          [module.id]: {
            moduleId: module.id,
            status: "success",
            data: mock,
            includeInReport: prev[module.id]?.includeInReport ?? true,
          },
        }));
      } else {
        setResults((prev) => ({
          ...prev,
          [module.id]: {
            moduleId: module.id,
            status: "error",
            error: err.message || "Failed",
            includeInReport: prev[module.id]?.includeInReport ?? true,
          },
        }));
      }
    }
  };

  // Run all active modules sequentially
  const runAll = async () => {
    const active = modules.filter((m) => activeIds.has(m.id));
    for (const mod of active) {
      await runModule(mod, allOutputs);
    }
  };

  const toggleInclude = (id: string) => {
    setResults((prev) => ({
      ...prev,
      [id]: { ...prev[id], includeInReport: !prev[id]?.includeInReport },
    }));
  };

  if (loading) return <div className="p-8 text-gray-500">Loading modules...</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;  return (
    <div className="flex h-screen">
      <ModulePickerSidebar
        modules={modules}
        activeIds={activeIds}
        onToggle={toggleModule}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="bg-white border-b p-4 flex flex-col gap-3">
          <h1 className="text-xl font-bold">Clinical Mission Control</h1>          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">Case Symptoms (one per line)</label>
              <textarea
                className="w-full border rounded-lg px-3 py-2 text-sm min-h-[3rem] resize-y"
                placeholder="fear of death&#10;violent outbursts&#10;wants to be alone"
                value={caseSymptoms}
                onChange={(e) => setCaseSymptoms(e.target.value)}
              />
            </div>
            <div className="w-48">
              <label className="block text-xs text-gray-500 mb-1">Selected Remedy</label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="e.g. Stramonium"
                value={selectedRemedy}
                onChange={(e) => setSelectedRemedy(e.target.value)}
              />
            </div>
            <button
              onClick={runAll}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
            >
              Run Active Modules
            </button>
          </div>
        </div>

        <DashboardCanvas
          modules={modules.filter((m) => activeIds.has(m.id))}
          results={results}
          onToggleInclude={toggleInclude}
          selectedRemedy={selectedRemedy}
        />

        <ReportActionBar
          modules={modules}
          results={results}
        />
      </div>
    </div>
  );
}

function getMockData(
  moduleId: string,
  symptoms: string,
  remedy: string
): any | null {
  switch (moduleId) {
    case "repertorize":
      return [
        {
          abbrev: "Stram.",
          name: "Stramonium",
          score: 47,
          match_count: 8,
          cycle_analysis: {
            remedy_cycle: "Stramonium",
            segment_matches: [
              "Fear of death or injury",
              "Vulnerability and clinginess",
              "Violent overreaction",
              "Desire to close off / shut down",
            ],
            segments_matched_count: 4,
            total_segments: 6,
            segment_coverage: 0.667,
            coverage: 0.156,
            generalized_hits: ["violence", "fear", "rage"],
            cycle_sentence:
              "Driven by confusion, fears, and vulnerability, Stramonium is engaged in an ongoing and violent battle...",
            map_of_hierarchy_phase: 4,
            meets_threshold: true,
          },
        },
        {
          abbrev: "Ars.",
          name: "Arsenicum Album",
          score: 32,
          match_count: 5,
          cycle_analysis: {
            remedy_cycle: null,
            segment_matches: [],
            segments_matched_count: 0,
            total_segments: 0,
            segment_coverage: 0,
            coverage: 0,
            generalized_hits: [],
            cycle_sentence: null,
            map_of_hierarchy_phase: null,
            meets_threshold: false,
          },
        },
        {
          abbrev: "Puls.",
          name: "Pulsatilla",
          score: 28,
          match_count: 4,
          cycle_analysis: {
            remedy_cycle: "Pulsatilla Pratensis",
            segment_matches: [],
            segments_matched_count: 0,
            total_segments: 6,
            segment_coverage: 0,
            coverage: 0,
            generalized_hits: [],
            cycle_sentence:
              "Driven by limb expression, Pulsatilla Pratensis manifests a dynamic cycle through mind and general condition...",
            map_of_hierarchy_phase: null,
            meets_threshold: false,
          },
        },
      ];
    case "cycles":
      return {
        remedy: remedy || "Stramonium",
        matched_segments: [
          "Fear of death or injury",
          "Vulnerability and clinginess",
          "Violent overreaction",
        ],
        missing_segments: ["Death and deadness", "Confusion over dual state"],
        segment_coverage: 0.5,
        coverage: 0.21,
        meets_threshold: true,
        essence:
          "Driven by confusion, fears, and vulnerability, Stramonium is engaged in an ongoing and violent battle...",
        map_of_hierarchy_phase: 4,
      };
    case "srp_detector":
      return {
        srp_flag: true,
        severity: "high",
        pattern_type: "paradoxical_modality",
        boost_multiplier: 2.0,
        flagged_rubrics: [
          {
            fullpath: "Mind; weeping, inconsolable, consolation agg.",
            flag: "paradoxical_symptom",
          },
        ],
      };
    case "phantom_rubric":
      return {
        phantoms: [
          {
            rubric_id: 99999,
            fullpath: "Mind; anxiety (concentrated)",
            gini: 0.91,
            hhi: 0.33,
            status: "concentrated",
          },
        ],
        summary: { total_rubrics: 143408, flagged: 1, safe: 143407 },
      };
    case "potency_guidance":
      return {
        remedy: remedy || "Stramonium",
        potency_suggestion: "30C",
        confidence: "medium",
        ladder: ["6C", "12C", "30C", "200C"],
        context_rationale: "Mental/emotional predominance with violent, confused behavior suggests middle potency; avoid too low (physical focus) and too high (risk of aggravation without supervision).",
      };
    case "red_flags":
      return {
        status: "advisory",
        flags: [
          {
            severity: "advisory",
            description: "Violent outbursts reported — consider safety planning",
            referral_recommended: false,
          },
        ],
        referral_recommended: false,
      };
    case "remedy_relationships":
      return {
        remedy: remedy || "Stram.",
        complementary: ["Puls.", "Calc."],
        antidotes: ["Hyos."],
        inimical: ["Bell."],
      };
    case "approval_gate":
      return {
        status: "pending_ack",
        message:
          "This recommendation requires practitioner review and prescriber_ack before recording.",
        recommendation: {
          remedy: remedy || "Stramonium",
          potency: "30C",
          rationale: "Classical score 47, cycle coverage 66.7%, SRP boost ×2, no red flags.",
        },
      };
    case "phi_scrubber":
      return {
        scrubbed: symptoms.replace(/\w+\s+\w+/g, "[REDACTED]"),
        pseudonyms: { "John Doe": "patient-alpha" },
      };
    default:
      return { message: `Mock result for ${moduleId}` };
  }
}
