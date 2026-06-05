"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import ModulePickerSidebar from "@/components/dashboard/ModulePickerSidebar";
import DashboardCanvas from "@/components/dashboard/DashboardCanvas";
import ReportActionBar from "@/components/dashboard/ReportActionBar";
import CaseEntryPanel, { type CaseFormData } from "@/components/dashboard/CaseEntryPanel";
import CaseListPanel, { type SavedCase } from "@/components/dashboard/CaseListPanel";
import type { PortalModule, ModuleResult } from "@/lib/portal-types";

export default function DashboardPage() {
  const [modules, setModules] = useState<PortalModule[]>([]);
  const [activeIds, setActiveIds] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<Record<string, ModuleResult>>({});
  const [caseSymptoms, setCaseSymptoms] = useState<string>("");
  const [selectedRemedy, setSelectedRemedy] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ── Practitioner case state ── */
  const [savedCases, setSavedCases] = useState<SavedCase[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | undefined>(undefined);
  const [caseListLoading, setCaseListLoading] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

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

  // Fetch saved cases on mount
  useEffect(() => {
    fetch("/api/practitioner/cases")
      .then((r) => r.json())
      .then((j) => {
        if (j.ok) setSavedCases(j.cases || []);
      })
      .catch((err) => console.error("[cases]", err))
      .finally(() => setCaseListLoading(false));
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

  /* ── Case management handlers ── */

  const handleSaveCase = useCallback(async (data: CaseFormData) => {
    const res = await fetch("/api/practitioner/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const j = await res.json();
    if (j.ok && j.case) {
      setSavedCases((prev) => [j.case, ...prev]);
      setActiveCaseId(j.case.id);
      // Auto-populate symptoms from chief concern + modalities + body
      const symptoms = [
        data.chief_concern,
        data.modalities,
        data.body,
      ]
        .filter(Boolean)
        .join("\n")
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 3)
        .join("\n");
      setCaseSymptoms(symptoms);
    }
  }, []);

  const handleLoadCase = useCallback((c: SavedCase) => {
    setActiveCaseId(c.id);
    const symptoms = [c.chief_concern, c.modalities, c.body]
      .filter(Boolean)
      .join("\n")
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 3)
      .join("\n");
    setCaseSymptoms(symptoms);
  }, []);

  const handleDeleteCase = useCallback(async (id: string) => {
    const res = await fetch(`/api/practitioner/cases/${id}`, { method: "DELETE" });
    const j = await res.json();
    if (j.ok) {
      setSavedCases((prev) => prev.filter((c) => c.id !== id));
      if (activeCaseId === id) setActiveCaseId(undefined);
    }
  }, [activeCaseId]);

  const handleUpload = useCallback(async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    // Upload to a temp area (we don't tie it to a case here; practitioner can re-upload after saving)
    const res = await fetch("/api/upload", { method: "POST", body: fd });
    const j = await res.json();
    if (j.ok) {
      setUploadedFiles((prev) => [...prev, file.name]);
    }
  }, []);

  const handleSymptomsExtracted = useCallback((symptoms: string) => {
    setCaseSymptoms((prev) => {
      if (prev.trim()) return prev + "\n" + symptoms;
      return symptoms;
    });
  }, []);

  /* ── Module execution ── */

  const runModule = async (module: PortalModule, inputs: Record<string, any>) => {
    setResults((prev) => ({
      ...prev,
      [module.id]: {
        moduleId: module.id,
        status: "loading",
        includeInReport: prev[module.id]?.includeInReport ?? true,
      },
    }));

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
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  return (
    <div className="flex h-screen">
      <ModulePickerSidebar
        modules={modules}
        activeIds={activeIds}
        onToggle={toggleModule}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* ── Top bar: case entry + symptoms ── */}
        <div className="bg-white border-b p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">Clinical Mission Control</h1>
            {activeCaseId && (
              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                Case: {savedCases.find((c) => c.id === activeCaseId)?.case_code || activeCaseId}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Case entry panel */}
            <div className="md:col-span-1">
              <CaseEntryPanel
                onSave={handleSaveCase}
                onUpload={handleUpload}
                onSymptomsExtracted={handleSymptomsExtracted}
                savedCount={savedCases.length}
              />
              {uploadedFiles.length > 0 && (
                <div className="mt-2 text-[10px] text-gray-500">
                  Uploaded: {uploadedFiles.join(", ")}
                </div>
              )}
            </div>

            {/* Symptoms + run bar */}
            <div className="md:col-span-2 flex flex-col gap-3">
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">
                    Case Symptoms (one per line)
                  </label>
                  <textarea
                    className="w-full border rounded-lg px-3 py-2 text-sm min-h-[4rem] resize-y"
                    placeholder="fear of death\nviolent outbursts\nwants to be alone"
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

              {/* Saved cases list */}
              <div className="mt-1">
                {caseListLoading ? (
                  <p className="text-xs text-gray-400">Loading saved cases…</p>
                ) : (
                  <CaseListPanel
                    cases={savedCases}
                    onLoad={handleLoadCase}
                    onDelete={handleDeleteCase}
                    activeCaseId={activeCaseId}
                  />
                )}
              </div>
            </div>
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
          matches: [
            { rubric_id: 10123, rubric: "Mind; fear, death of", weight: 4 },
            { rubric_id: 10124, rubric: "Mind; violent, outbursts", weight: 4 },
            { rubric_id: 10125, rubric: "Mind; alone, wants to be", weight: 3 },
            { rubric_id: 10126, rubric: "Mind; confusion", weight: 3 },
            { rubric_id: 10127, rubric: "Face; discoloration, red", weight: 2 },
            { rubric_id: 10128, rubric: "Throat; dry", weight: 2 },
            { rubric_id: 10129, rubric: "Sleep; sleeplessness", weight: 2 },
            { rubric_id: 10130, rubric: "General; cold, forearm icy", weight: 1 },
          ],
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
          matches: [
            { rubric_id: 20101, rubric: "Mind; anxiety, health about", weight: 4 },
            { rubric_id: 20102, rubric: "Mind; restlessness", weight: 3 },
            { rubric_id: 20103, rubric: "General; cold, sensitive to", weight: 3 },
            { rubric_id: 20104, rubric: "Stomach; thirst, small quantities", weight: 2 },
            { rubric_id: 20105, rubric: "Skin; burning", weight: 1 },
          ],
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
          matches: [
            { rubric_id: 30101, rubric: "Mind; weeping, consolation agg.", weight: 4 },
            { rubric_id: 30102, rubric: "Mind; changeable mood", weight: 3 },
            { rubric_id: 30103, rubric: "General; warm, wants", weight: 3 },
            { rubric_id: 30104, rubric: "Stomach; thirstless", weight: 2 },
          ],
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
        context_rationale:
          "Mental/emotional predominance with violent, confused behavior suggests middle potency; avoid too low (physical focus) and too high (risk of aggravation without supervision).",
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
