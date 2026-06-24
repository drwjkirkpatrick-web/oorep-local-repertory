"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import ModulePickerSidebar from "@/components/dashboard/ModulePickerSidebar";
import DashboardCanvas from "@/components/dashboard/DashboardCanvas";
import ReportActionBar from "@/components/dashboard/ReportActionBar";
import StickyDashboardHeader from "@/components/dashboard/StickyDashboardHeader";
import CaseEntryPanel, { type CaseFormData } from "@/components/dashboard/CaseEntryPanel";
import CaseListPanel, { type SavedCase } from "@/components/dashboard/CaseListPanel";
import PractitionerSettingsPanel, { type PractitionerSettings } from "@/components/dashboard/PractitionerSettingsPanel";
import QuickLinksPanel, { type QuickLink } from "@/components/dashboard/QuickLinksPanel";
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

  /* ── Practitioner profile / settings / quick links ── */
  const [practitionerProfile, setPractitionerProfile] = useState<{
    id: string;
    name: string;
    email: string;
    clinic: string;
    license_number: string;
    default_potency: string;
    default_repertory_method: string;
    created_at: string;
    updated_at: string;
  } | null>(null);
  const [practitionerSettings, setPractitionerSettings] = useState<PractitionerSettings | null>(null);
  const [quickLinks, setQuickLinks] = useState<QuickLink[]>([]);

  /* ── Tab + edit state ── */
  const [activeTab, setActiveTab] = useState<"case_entry" | "saved_cases" | "profile" | "quick_links">("case_entry");
  const [editingCaseId, setEditingCaseId] = useState<string | undefined>(undefined);
  const [isRunning, setIsRunning] = useState(false);

  // Fetch modules
  useEffect(() => {
    fetch("/api/portal/modules")
      .then((r) => r.json())
      .then((j) => {
        if (j.ok) {
          setModules(j.modules);
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

  // Fetch practitioner profile, settings, quick links on mount
  useEffect(() => {
    fetch("/api/practitioner/profile")
      .then((r) => r.json())
      .then((j) => {
        if (j.ok) setPractitionerProfile(j.profile || null);
      })
      .catch((err) => console.error("[profile]", err));

    fetch("/api/practitioner/settings")
      .then((r) => r.json())
      .then((j) => {
        if (j.ok) {
          const db = j.settings || {};
          // Map DB shape (PractitionerSettingsDoc) to panel shape
          setPractitionerSettings({
            default_enabled_module_ids: db.default_enabled_module_ids,
            show_advanced_panels: db.show_visualizations,
            auto_run_on_save: db.auto_run_on_load,
          });
        }
      })
      .catch((err) => console.error("[settings]", err));

    fetch("/api/practitioner/quicklinks")
      .then((r) => r.json())
      .then((j) => {
        if (j.ok) setQuickLinks(j.links || []);
      })
      .catch((err) => console.error("[quicklinks]", err));
  }, []);

  // Apply default enabled modules from practitioner settings once modules load
  useEffect(() => {
    if (modules.length === 0) return;
    const settingIds = practitionerSettings?.default_enabled_module_ids;
    if (settingIds && settingIds.length > 0) {
      setActiveIds(new Set(settingIds));
    } else {
      setActiveIds(
        new Set(modules.filter((m) => m.defaultEnabled).map((m) => m.id))
      );
    }
  }, [modules, practitionerSettings]);

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

  const handleUpdateCase = useCallback(async (id: string, data: CaseFormData) => {
    const res = await fetch(`/api/practitioner/cases/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const j = await res.json();
    if (j.ok && j.case) {
      setSavedCases((prev) =>
        prev.map((c) => (c.id === id ? j.case : c))
      );
      setEditingCaseId(undefined);
      setActiveTab("saved_cases");
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
      if (editingCaseId === id) setEditingCaseId(undefined);
    }
  }, [activeCaseId, editingCaseId]);

  const handleEditCase = useCallback((c: SavedCase) => {
    setEditingCaseId(c.id);
    setActiveTab("case_entry");
  }, []);

  const handleUpload = useCallback(async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
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

  /* ── Practitioner profile / settings / quick links handlers ── */

  const handleSaveProfile = useCallback(async (profile: typeof practitionerProfile) => {
    if (!profile) return;
    const res = await fetch("/api/practitioner/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    const j = await res.json();
    if (j.ok) setPractitionerProfile(j.profile || profile);
  }, []);

  const handleSaveSettings = useCallback(async (settings: PractitionerSettings) => {
    const res = await fetch("/api/practitioner/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    const j = await res.json();
    if (j.ok) {
      // Map DB shape back to panel shape
      const db = j.settings || {};
      setPractitionerSettings({
        default_enabled_module_ids: db.default_enabled_module_ids,
        show_advanced_panels: db.show_visualizations,
        auto_run_on_save: db.auto_run_on_load,
      });
      // Re-apply default enabled modules if they changed
      const newIds = db.default_enabled_module_ids;
      if (newIds && modules.length > 0) {
        setActiveIds(new Set(newIds));
      }
    }
  }, [modules]);

  const handleAddQuickLink = useCallback(async (link: Omit<QuickLink, "id">) => {
    const res = await fetch("/api/practitioner/quicklinks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(link),
    });
    const j = await res.json();
    if (j.ok && j.link) {
      setQuickLinks((prev) => [...prev, j.link]);
    }
  }, []);

  const handleDeleteQuickLink = useCallback(async (id: string) => {
    const res = await fetch(`/api/practitioner/quicklinks/${id}`, { method: "DELETE" });
    const j = await res.json();
    if (j.ok) {
      setQuickLinks((prev) => prev.filter((l) => l.id !== id));
    }
  }, []);

  const handleExport = useCallback(() => {
    // Build a simple JSON export of current results
    const exportData = {
      exportedAt: new Date().toISOString(),
      activeCaseId,
      caseSymptoms: caseSymptoms.split("\n").filter(Boolean),
      selectedRemedy,
      results: Object.fromEntries(
        Object.entries(results).filter(([, r]) => r.includeInReport)
      ),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `oorep-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [activeCaseId, caseSymptoms, selectedRemedy, results]);

  const handleClearAll = useCallback(() => {
    setResults({});
    setCaseSymptoms("");
    setSelectedRemedy("");
    setActiveCaseId(undefined);
    setEditingCaseId(undefined);
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
    setIsRunning(true);
    const active = modules.filter((m) => activeIds.has(m.id));
    for (const mod of active) {
      await runModule(mod, allOutputs);
    }
    setIsRunning(false);
  };

  const toggleInclude = (id: string) => {
    setResults((prev) => ({
      ...prev,
      [id]: { ...prev[id], includeInReport: !prev[id]?.includeInReport },
    }));
  };

  if (loading) return <div className="p-8 text-gray-500">Loading modules...</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  const editingCase = editingCaseId
    ? savedCases.find((c) => c.id === editingCaseId)
    : undefined;

  const tabButton = (
    tab: typeof activeTab,
    label: string
  ) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`px-4 py-2 text-xs font-medium rounded-t-lg transition ${
        activeTab === tab
          ? "bg-white text-blue-700 border-t border-x border-gray-200"
          : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex h-screen">
      <ModulePickerSidebar
        modules={modules}
        activeIds={activeIds}
        onToggle={toggleModule}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* ── Sticky Header ── */}
        <StickyDashboardHeader
          activeModules={activeIds.size}
          totalModules={modules.length}
          onRunAll={runAll}
          onClearAll={handleClearAll}
          onExport={handleExport}
          isRunning={isRunning}
          patient={
            activeCaseId
              ? {
                  id: activeCaseId,
                  name: savedCases.find((c) => c.id === activeCaseId)?.patient_pseudonym || "Case",
                  constitutionalRemedy: selectedRemedy || undefined,
                }
              : undefined
          }
        />

        {/* ── Tabs ── */}
        <div className="bg-gray-50 border-b border-gray-200 px-4 pt-2 flex gap-1">
          {tabButton("case_entry", "Case Entry")}
          {tabButton("saved_cases", "Saved Cases")}
          {tabButton("profile", "My Profile")}
          {tabButton("quick_links", "Quick Links")}
        </div>

        {/* ── Tab Content ── */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {activeTab === "case_entry" && (
            <div className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Case entry panel */}
                <div className="md:col-span-1">
                  <CaseEntryPanel
                    onSave={handleSaveCase}
                    onUpload={handleUpload}
                    onSymptomsExtracted={handleSymptomsExtracted}
                    savedCount={savedCases.length}
                    editMode={!!editingCaseId}
                    initialData={
                      editingCase
                        ? {
                            patient_pseudonym: editingCase.patient_pseudonym || "",
                            chief_concern: editingCase.chief_concern || "",
                            modalities: editingCase.modalities || "",
                            body: editingCase.body || "",
                          }
                        : undefined
                    }
                    onUpdate={
                      editingCaseId
                        ? (data) => handleUpdateCase(editingCaseId, data)
                        : undefined
                    }
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
                      disabled={isRunning}
                      className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50"
                    >
                      {isRunning ? "Running…" : "Run Active Modules"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Dashboard canvas below the entry area */}
              <div className="mt-4">
                <DashboardCanvas
                  modules={modules.filter((m) => activeIds.has(m.id))}
                  results={results}
                  onToggleInclude={toggleInclude}
                  selectedRemedy={selectedRemedy}
                  caseSymptoms={caseSymptoms}
                />
              </div>

              <ReportActionBar
                modules={modules}
                results={results}
              />
            </div>
          )}

          {activeTab === "saved_cases" && (
            <div className="p-4 max-w-4xl mx-auto">
              {caseListLoading ? (
                <p className="text-xs text-gray-400">Loading saved cases…</p>
              ) : (
                <CaseListPanel
                  cases={savedCases}
                  onLoad={handleLoadCase}
                  onDelete={handleDeleteCase}
                  onEdit={handleEditCase}
                  activeCaseId={activeCaseId}
                />
              )}
            </div>
          )}

          {activeTab === "profile" && (
            <div className="p-4 max-w-4xl mx-auto">
              <div className="bg-white rounded-lg border shadow-sm p-4 mb-4">
                <h2 className="font-semibold text-sm text-gray-800 mb-3">Practitioner Profile</h2>
                {practitionerProfile ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-500">Name</span>
                      <span className="font-medium">{practitionerProfile.name}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-500">Email</span>
                      <span>{practitionerProfile.email}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-500">Clinic</span>
                      <span>{practitionerProfile.clinic}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-500">License</span>
                      <span>{practitionerProfile.license_number}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-500">Default Potency</span>
                      <span>{practitionerProfile.default_potency}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Method</span>
                      <span>{practitionerProfile.default_repertory_method}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 italic">No profile loaded.</p>
                )}
              </div>

              <PractitionerSettingsPanel
                settings={practitionerSettings}
                onSave={handleSaveSettings}
                modules={modules.map((m) => ({ id: m.id, name: m.name }))}
              />
            </div>
          )}

          {activeTab === "quick_links" && (
            <div className="p-4 max-w-2xl mx-auto">
              <QuickLinksPanel
                links={quickLinks}
                onAdd={handleAddQuickLink}
                onDelete={handleDeleteQuickLink}
              />
            </div>
          )}
        </div>
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
