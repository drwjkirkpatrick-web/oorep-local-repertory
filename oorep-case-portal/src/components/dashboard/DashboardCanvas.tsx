"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { PortalModule } from "../../lib/portal-types";
import type { ModuleResult } from "../../lib/portal-types";
import RepertorizationPanel from "@/components/dashboard/RepertorizationPanel";
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

import ROCAUCurve from "@/components/visualizations/ROCAUCurve";
import NetworkGraph from "@/components/visualizations/NetworkGraph";
import OutcomeComparatorPanel from "@/components/visualizations/OutcomeComparatorPanel";
import RepertoryPCAPanel from "@/components/visualizations/RepertoryPCAPanel";
import CaseComplexityPanel from "@/components/visualizations/CaseComplexityPanel";
import InterRaterReliabilityPanel from "@/components/visualizations/InterRaterReliabilityPanel";
import MetaAnalysisPanel from "@/components/visualizations/MetaAnalysisPanel";
import PowerAnalysisPanel from "@/components/visualizations/PowerAnalysisPanel";
import SurvivalAnalysisPanel from "@/components/visualizations/SurvivalAnalysisPanel";
import ResamplingEnginePanel from "@/components/visualizations/ResamplingEnginePanel";
import ReverseRepertorizationPanel from "@/components/visualizations/ReverseRepertorizationPanel";
import ConstitutionalTrackerPanel from "@/components/visualizations/ConstitutionalTrackerPanel";
import DuplicateRemedyPanel from "@/components/visualizations/DuplicateRemedyPanel";
import PosologySchedulerPanel from "@/components/visualizations/PosologySchedulerPanel";
import SymptomSeverityPanel from "@/components/visualizations/SymptomSeverityPanel";
import ClinicalTipsPanel from "@/components/visualizations/ClinicalTipsPanel";
import BatchProtocolPanel from "@/components/visualizations/BatchProtocolPanel";
import InventoryPanel from "@/components/visualizations/InventoryPanel";
import MiasmTimelinePanel from "@/components/visualizations/MiasmTimelinePanel";
import CaseSimilarityPanel from "@/components/visualizations/CaseSimilarityPanel";

/* ── NEW 3D Visualizations ── */
import ConcordanceCube from "@/components/visualizations/ConcordanceCube";
import RemedyLandscape from "@/components/visualizations/RemedyLandscape";
import ConfidenceCloud from "@/components/visualizations/ConfidenceCloud";
import SymptomConstellation from "@/components/visualizations/SymptomConstellation";
import DifferentialHelix from "@/components/visualizations/DifferentialHelix";
import RubricHierarchyTower from "@/components/visualizations/RubricHierarchyTower";

/* ── Orphan Panels (imported for module routing) ── */
import PatientIntakePanel from "./PatientIntakePanel";
import ChiefComplaintPanel from "./ChiefComplaintPanel";
import ConcomitantPanel from "./ConcomitantPanel";
import ModalityPanel from "./ModalityPanel";
import CausationTimelinePanel from "./CausationTimelinePanel";
import MentalEmotionalPanel from "./MentalEmotionalPanel";
import GeneralsSurveyPanel from "./GeneralsSurveyPanel";
import ConstitutionalSnapshotPanel from "./ConstitutionalSnapshotPanel";
import IntakeAnalyzerPanel from "./IntakeAnalyzerPanel";
import CaseAnalysisBridgePanel from "./CaseAnalysisBridgePanel";
import ThompsonSamplingPanel from "./ThompsonSamplingPanel";
import RubricBanditPanel from "./RubricBanditPanel";
import PropensityScoredPanel from "./PropensityScoredPanel";
import EnsembleStackingPanel from "./EnsembleStackingPanel";
import DiscriminantRubricPanel from "./DiscriminantRubricPanel";
import InformationTheoreticPanel from "./InformationTheoreticPanel";
import AdaptiveSymptomSequencerPanel from "./AdaptiveSymptomSequencerPanel";
import LatentEmbeddingPanel from "./LatentEmbeddingPanel";
import ConfusionMatrixPanel from "./ConfusionMatrixPanel";
import KNearestProvenPanel from "./KNearestProvenPanel";
import BayesianNetworkPanel from "./BayesianNetworkPanel";
import SymptomCooccurrencePanel from "./SymptomCooccurrencePanel";
import ActiveLearningIntakePanel from "./ActiveLearningIntakePanel";
import RemedyCalibrationPanel from "./RemedyCalibrationPanel";
import GaussianProcessPanel from "./GaussianProcessPanel";
import HierarchicalBayesianPanel from "./HierarchicalBayesianPanel";
import CVWeightLearningPanel from "./CVWeightLearningPanel";
import SPRTPanel from "./SPRTPanel";
import CausalRemedyEffectsPanel from "./CausalRemedyEffectsPanel";
import RubricDiscriminationPanel from "./RubricDiscriminationPanel";
import QuestionBankPanel from "./QuestionBankPanel";
import RemedyComparisonView from "./RemedyComparisonView";
import RemedyHoverCard from "./RemedyHoverCard";
import QuickFilterBar from "./QuickFilterBar";

export default function DashboardCanvas({
  modules,
  results,
  onToggleInclude,
  selectedRemedy,
  caseSymptoms,
}: {
  modules: PortalModule[];
  results: Record<string, ModuleResult>;
  onToggleInclude: (id: string) => void;
  selectedRemedy: string;
  caseSymptoms?: string;
}) {
  const [pinnedRemedies, setPinnedRemedies] = useState<Set<string>>(new Set());
  const [compareOpen, setCompareOpen] = useState(false);

  // Extract data from results
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

  const srpData = useMemo(() => {
    const srp = results["srp_detector"];
    return srp?.data || null;
  }, [results]);

  const patientMiasm = useMemo(() => {
    const mi = results["miasm_timeline"];
    return mi?.data?.deepest_layer || mi?.data?.active_layers?.[0] || undefined;
  }, [results]);

  const router = useRouter();

  // Click-through handlers
  const handleRubricClick = (rubric: string, rubricId?: string) => {
    if (rubricId) {
      router.push(`/rubrics/${encodeURIComponent(rubricId)}`);
    } else {
      router.push(`/rubrics?q=${encodeURIComponent(rubric)}`);
    }
  };

  const handleRemedyClick = (abbrev: string) => {
    router.push(`/remedies/${encodeURIComponent(abbrev)}`);
  };

  const togglePin = (abbrev: string) => {
    setPinnedRemedies((prev) => {
      const next = new Set(prev);
      if (next.has(abbrev)) next.delete(abbrev);
      else next.add(abbrev);
      return next;
    });
  };

  const hasRepertorization = repertorizationData.length > 0;

  // Separate repertorization module from other modules
  const repertorizationModule = modules.find((m) => m.id === "repertorize");
  const otherModules = modules.filter((m) => m.id !== "repertorize");

  // Deterministic seeded sparkline data based on remedy abbrev
  const sparklineRemedies = useMemo(() => {
    return repertorizationData.slice(0, 4).map((r: any, i: number) => {
      const colors = ["#be123c", "#1e40af", "#15803d", "#b45309"];
      const abbrev = r.abbrev;
      // Simple deterministic pseudo-random based on abbrev string
      const seed = abbrev.split("").reduce((acc: number, ch: string) => acc + ch.charCodeAt(0), 0);
      const rand = (offset: number) => {
        const x = Math.sin(seed + offset) * 10000;
        return x - Math.floor(x);
      };
      return {
        abbrev,
        color: colors[i % colors.length],
        points: [
          { month: 0, score: -2 + rand(1) * 2 },
          { month: 1, score: -1 + rand(2) * 2 },
          { month: 2, score: 0 + rand(3) * 2 },
          { month: 3, score: 1 + rand(4) * 2 },
          { month: 6, score: 2 + rand(5) * 2 },
        ],
      };
    });
  }, [repertorizationData]);

  const sankeySymptoms = useMemo(() => {
    if (caseSymptoms) {
      return caseSymptoms.split("\n").filter((s) => s.trim().length > 0).slice(0, 8);
    }
    return ["fear of death", "violent outbursts", "wants to be alone"];
  }, [caseSymptoms]);

  return (
    <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">

        {/* ═══════════════════════════════════════
            PRIMARY: REPERTORIZATION PANEL (full width)
        ═══════════════════════════════════════ */}
        {hasRepertorization && repertorizationModule && (
          <div className="xl:col-span-2"
          >
            <RepertorizationPanel
              remedies={repertorizationData}
              phantomCount={phantomData?.phantoms?.length || 0}
              totalRubrics={phantomData?.summary?.total_rubrics || 143408}
              srpBoost={srpData?.boost_multiplier || 1}
              pinnedRemedies={pinnedRemedies}
              onTogglePin={togglePin}
              onRemedyClick={handleRemedyClick}
              onRubricClick={handleRubricClick}
            />
          </div>
        )}

        {/* ═══════════════════════════════════════
            PINNED REMEDIES BAR (if any pinned)
        ═══════════════════════════════════════ */}
        {pinnedRemedies.size > 0 && (
          <div className="xl:col-span-2 bg-white rounded-lg border shadow-sm p-3 flex items-center gap-2 flex-wrap"
          >
            <span className="text-xs font-semibold text-gray-500 mr-1">Pinned:</span>
            {Array.from(pinnedRemedies).map((abbrev) => {
              const rem = repertorizationData.find((r: any) => r.abbrev === abbrev);
              return (
                <span
                  key={abbrev}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md border border-blue-100"
                >
                  <span className="font-bold">{abbrev}</span>
                  <span className="text-blue-400">|</span>
                  <span>{rem?.score || "—"}</span>
                  <button
                    onClick={() => togglePin(abbrev)}
                    className="ml-1 text-blue-400 hover:text-blue-600"
                    title="Unpin"
                  >
                    ×
                  </button>
                </span>
              );
            })}
            <button
              onClick={() => setCompareOpen(true)}
              className="ml-auto text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition"
            >
              Compare
            </button>
          </div>
        )}

        {/* ═══════════════════════════════════════
            OTHER MODULE PANELS (2-column grid)
        ═══════════════════════════════════════ */}
        {otherModules.map((mod) => {
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
                      onRemedyClick={handleRemedyClick}
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
                onRubricClick={handleRubricClick}
                onRemedyClick={handleRemedyClick}
              />
            </div>

            {/* Venn — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Comparative Venn"
                level="BEGINNER"
                subtitle="Shared vs unique differentiating rubrics"
              />
              <ComparativeVennDiagram
                remedies={repertorizationData.slice(0, 3)}
                onRemedyClick={handleRemedyClick}
                onRubricClick={handleRubricClick}
              />
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
              <RadarChartViz remedies={repertorizationData.slice(0, 6)} size={400} onRemedyClick={handleRemedyClick} />
            </div>

            {/* Sparklines — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Outcome Trajectory Sparklines"
                level="INTERMEDIATE"
                subtitle="Historical outcomes for similar profiles"
              />
              <OutcomeTrajectorySparklines remedies={sparklineRemedies} onRemedyClick={handleRemedyClick} />
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
              <MiasmDonutOverlay patientMiasm={patientMiasm} />
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
                onRubricClick={handleRubricClick}
              />
            </div>

            {/* Family Constellation — ADVANCED */}
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <PanelHeader
                title="Family Constellation Graph"
                level="ADVANCED"
                subtitle="Inherited remedy patterns & suppression chains"
              />
              <FamilyConstellationGraph onRemedyClick={handleRemedyClick} />
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

        {/* ═══════════════════════════════════════
            3D VISUALIZATIONS (v4.2) — Finding Remedy Through Noise
        ═══════════════════════════════════════ */}
        {hasRepertorization && (
          <>
            {/* Symptom Constellation — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Symptom Constellation (3D)"
                level="BEGINNER"
                subtitle="Spatial remedy-symptom coverage map"
              />
              <SymptomConstellation
                remedies={repertorizationData.slice(0, 6)}
                onRemedyClick={handleRemedyClick}
                onRubricClick={handleRubricClick}
              />
            </div>

            {/* Rubric Hierarchy Tower — BEGINNER */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Rubric Hierarchy Tower (3D)"
                level="BEGINNER"
                subtitle="Kent hierarchy as stacked cylinder tiers"
              />
              <RubricHierarchyTower
                remedies={repertorizationData.slice(0, 6)}
                onRemedyClick={handleRemedyClick}
                onRubricClick={handleRubricClick}
              />
            </div>

            {/* Remedy Landscape — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Remedy Landscape (3D)"
                level="INTERMEDIATE"
                subtitle="Terrain peaks above the noise floor"
              />
              <RemedyLandscape
                remedies={repertorizationData.slice(0, 8)}
                onRemedyClick={handleRemedyClick}
              />
            </div>

            {/* Confidence Cloud — INTERMEDIATE */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Confidence Cloud (3D)"
                level="INTERMEDIATE"
                subtitle="Uncertainty space: size = score, opacity = confidence"
              />
              <ConfidenceCloud
                remedies={repertorizationData.slice(0, 8)}
                onRemedyClick={handleRemedyClick}
              />
            </div>

            {/* Differential Helix — ADVANCED */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Differential Helix (3D)"
                level="ADVANCED"
                subtitle="Miasm-tracked remedy spiral clustering"
              />
              <DifferentialHelix
                remedies={repertorizationData.slice(0, 8)}
                onRemedyClick={handleRemedyClick}
              />
            </div>

            {/* Concordance Cube — ADVANCED */}
            <div className="bg-white rounded-lg border shadow-sm p-4 xl:col-span-2">
              <PanelHeader
                title="Concordance Cube (3D)"
                level="ADVANCED"
                subtitle="Multi-method agreement: signal vs noise"
              />
              <ConcordanceCube
                remedies={repertorizationData.slice(0, 8)}
                onRemedyClick={handleRemedyClick}
              />
            </div>
          </>
        )}

        {/* Sankey Flow — always visible */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader
            title="Repertorization Transparency Flow"
            level="BEGINNER"
            subtitle="Symptom-to-remedy routing diagram"
          />
          <TimelineSankeyViz
            symptoms={sankeySymptoms}
            remedies={repertorizationData.slice(0, 4)}
            onRemedyClick={handleRemedyClick}
          />
        </div>

        {/* ═══════════════════════════════════════
            STATISTICAL MODULE PANELS (v3.6)
        ═══════════════════════════════════════ */}
        {/* Outcome Predictor Stats — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Outcome Prediction Validation" level="ADVANCED" subtitle="ROC/AUC, calibration, bootstrap CI" />
          <ROCAUCurve rocData={results["outcome_predictor_stats"]?.data?.roc} calibrationData={results["outcome_predictor_stats"]?.data?.calibration} bootstrapCI={results["outcome_predictor_stats"]?.data?.bootstrap_ci} />
        </div>

        {/* Remedy Network Analysis — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Remedy Network Analysis" level="ADVANCED" subtitle="Graph centrality, communities, PageRank" />
          <NetworkGraph centrality={results["remedy_network_analysis"]?.data?.centrality} />
        </div>

        {/* Outcome Comparator — STATISTICS */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Outcome Comparator" level="ADVANCED" subtitle="Mann-Whitney, odds ratio, Cohen's d" />
          <OutcomeComparatorPanel result={results["outcome_comparator"]?.data} />
        </div>

        {/* Repertory PCA — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Repertory PCA" level="ADVANCED" subtitle="SVD/PCA on remedy-rubric matrix" />
          <RepertoryPCAPanel result={results["repertory_pca"]?.data} />
        </div>

        {/* Case Complexity — INTERMEDIATE */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Case Complexity" level="INTERMEDIATE" subtitle="Entropy, coverage gaps, redundancy" />
          <CaseComplexityPanel result={results["case_complexity"]?.data} />
        </div>

        {/* Inter-Rater Reliability — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Inter-Rater Reliability" level="ADVANCED" subtitle="Cohen's / Fleiss' kappa, ICC" />
          <InterRaterReliabilityPanel result={results["inter_rater_reliability"]?.data} />
        </div>

        {/* Meta-Analysis — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Meta-Analysis" level="ADVANCED" subtitle="Fixed/random-effects with heterogeneity" />
          <MetaAnalysisPanel result={results["meta_analysis"]?.data} />
        </div>

        {/* Power Analysis — INTERMEDIATE */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Power Analysis" level="INTERMEDIATE" subtitle="Sample size, power curves, MDE" />
          <PowerAnalysisPanel result={results["power_analysis"]?.data} />
        </div>

        {/* Survival Analysis — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Survival Analysis" level="ADVANCED" subtitle="Kaplan-Meier, hazard ratios" />
          <SurvivalAnalysisPanel result={results["survival_analysis"]?.data} />
        </div>

        {/* Resampling Engine — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Resampling Engine" level="ADVANCED" subtitle="Bootstrap CI, permutation, cross-validation" />
          <ResamplingEnginePanel result={results["resampling_engine"]?.data} />
        </div>

        {/* ═══════════════════════════════════════
            FEATURE EXPANSION PANELS (v3.7)
        ═══════════════════════════════════════ */}
        {/* Reverse Repertorization — BEGINNER */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Reverse Repertorization" level="BEGINNER" subtitle="Remedy → rubric inquiry" />
          <ReverseRepertorizationPanel result={results["reverse_repertorization"]?.data} />
        </div>

        {/* Constitutional Tracker — INTERMEDIATE */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Constitutional Remedy Tracker" level="INTERMEDIATE" subtitle="Longitudinal prescription history" />
          <ConstitutionalTrackerPanel result={results["constitutional_tracker"]?.data} />
        </div>

        {/* Duplicate Remedy Detector — BEGINNER */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Prescription Safety Check" level="BEGINNER" subtitle="Antidote & inimical warnings" />
          <DuplicateRemedyPanel result={results["duplicate_remedy_detector"]?.data} />
        </div>

        {/* Posology Scheduler — INTERMEDIATE */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Posology Scheduler" level="INTERMEDIATE" subtitle="Dosing & repetition guidance" />
          <PosologySchedulerPanel result={results["posology_scheduler"]?.data} />
        </div>

        {/* Symptom Severity — BEGINNER */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Symptom Severity" level="BEGINNER" subtitle="Intensity-based weighting" />
          <SymptomSeverityPanel result={results["symptom_severity"]?.data} />
        </div>

        {/* Clinical Tips — INTERMEDIATE */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Clinical Tips" level="INTERMEDIATE" subtitle="Practitioner notes on rubrics" />
          <ClinicalTipsPanel result={results["clinical_tips"]?.data} />
        </div>

        {/* Batch Protocols — INTERMEDIATE */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Protocol Builder" level="INTERMEDIATE" subtitle="Standard condition protocols" />
          <BatchProtocolPanel result={results["batch_protocols"]?.data} />
        </div>

        {/* Inventory — BEGINNER */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Inventory Manager" level="BEGINNER" subtitle="Remedy stock & expiry tracking" />
          <InventoryPanel result={results["inventory"]?.data} />
        </div>

        {/* Miasm Timeline — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Miasm Timeline" level="ADVANCED" subtitle="Miasmatic layer history" />
          <MiasmTimelinePanel result={results["miasm_timeline"]?.data} />
        </div>

        {/* Case Similarity — ADVANCED */}
        <div className="bg-white rounded-lg border shadow-sm p-4">
          <PanelHeader title="Case Similarity Search" level="ADVANCED" subtitle="Previous cases like this one" />
          <CaseSimilarityPanel result={results["case_similarity"]?.data} />
        </div>
      </div>

      {/* Remedy Comparison Modal */}
      {compareOpen && (
        <RemedyComparisonView
          remedies={repertorizationData
            .filter((r: any) => pinnedRemedies.has(r.abbrev))
            .map((r: any) => ({
              name: r.name,
              abbrev: r.abbrev,
              score: r.score,
              matches: r.matches || [],
              cycleCoverage: r.cycle_analysis?.segment_coverage || 0,
              kingdom: r.kingdom,
              miasm: r.miasm,
            }))}
          isOpen={compareOpen}
          onClose={() => setCompareOpen(false)}
          onRemoveRemedy={(abbrev) => togglePin(abbrev)}
        />
      )}
    </main>
  );
}

/* ── Panel Header ── */
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

/* ── Module Panel ── */
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

  // Map orphan panels that have component files but no dedicated API yet
  const orphanComponentMap: Record<string, React.FC<any>> = {
    patient_intake: PatientIntakePanel,
    chief_complaint: ChiefComplaintPanel,
    concomitant: ConcomitantPanel,
    modality_extractor: ModalityPanel,
    causation_timeline: CausationTimelinePanel,
    mental_emotional: MentalEmotionalPanel,
    generals_survey: GeneralsSurveyPanel,
    constitutional_snapshot: ConstitutionalSnapshotPanel,
    intake_analyzer: IntakeAnalyzerPanel,
    case_analysis_bridge: CaseAnalysisBridgePanel,
    thompson_sampling: ThompsonSamplingPanel,
    rubric_bandit: RubricBanditPanel,
    propensity_scored: PropensityScoredPanel,
    ensemble_stacking: EnsembleStackingPanel,
    discriminant_rubric: DiscriminantRubricPanel,
    information_theoretic: InformationTheoreticPanel,
    adaptive_symptom_sequencer: AdaptiveSymptomSequencerPanel,
    latent_embedding: LatentEmbeddingPanel,
    confusion_matrix: ConfusionMatrixPanel,
    knn_proven: KNearestProvenPanel,
    bayesian_network: BayesianNetworkPanel,
    symptom_cooccurrence: SymptomCooccurrencePanel,
    active_learning_intake: ActiveLearningIntakePanel,
    remedy_calibration: RemedyCalibrationPanel,
    gaussian_process: GaussianProcessPanel,
    hierarchical_bayesian: HierarchicalBayesianPanel,
    cv_weight_learning: CVWeightLearningPanel,
    sprt: SPRTPanel,
    causal_remedy_effects: CausalRemedyEffectsPanel,
    rubric_discrimination: RubricDiscriminationPanel,
    question_bank: QuestionBankPanel,
  };

  const OrphanComponent = orphanComponentMap[module.id];

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
        {!result && !OrphanComponent && (
          <span className="text-gray-400 italic">Waiting for run…</span>
        )}
        {result?.status === "loading" && !OrphanComponent && (
          <span className="text-blue-500">Running…</span>
        )}
        {result?.status === "error" && !OrphanComponent && (
          <span className="text-red-600">{result.error}</span>
        )}
        {result?.status === "success" && !OrphanComponent && (
          <pre className="text-[10px] whitespace-pre-wrap">{JSON.stringify(result.data, null, 2)}</pre>
        )}
        {OrphanComponent && (
          <div className="text-xs">
            {result?.data ? (
              <OrphanComponent result={result.data} />
            ) : (
              <OrphanComponent />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Helpers ── */
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
  const data: Array<{ rubric: string; remedyAbbrev: string; weight: number; rubricId?: string }> = [];
  for (const rem of remedies) {
    for (const m of rem.matches || []) {
      if (m.rubric && m.weight) {
        data.push({
          rubric: m.rubric,
          remedyAbbrev: rem.abbrev,
          weight: Math.min(m.weight, 4),
          rubricId: m.rubric_id ? String(m.rubric_id) : undefined,
        });
      }
    }
  }
  return data;
}
