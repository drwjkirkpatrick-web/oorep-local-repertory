# OOREP Dashboard Panel & Visualization Audit

## Summary
- **Registry modules:** 100 modules defined in `src/app/api/portal/modules/route.ts`
- **Backend Python modules:** ~143 `.py` files in `oorep/`
- **Dashboard panel components:** 45 `.tsx` files in `src/components/dashboard/`
- **Visualization components:** 40 `.tsx` files in `src/components/visualizations/`
- **Custom panels rendered in DashboardCanvas:** 21 (mapped to registry modules)
- **Orphan dashboard panels (exist but unused):** 32
- **Backend modules with no registry entry:** ~60+
- **Registry modules with only generic JSON dump panel:** ~79

---

## 1. Registry Modules with Custom Frontend Panels

These modules have a dedicated visualization component in DashboardCanvas.tsx and receive live data via `results[module_id]`.

| Registry ID | Component | Live Data? | Notes |
|-------------|-----------|------------|-------|
| `repertorize` | `RepertorizationPanel` | Yes | Primary panel; receives `results["repertorize"]` |
| `outcome_predictor_stats` | `ROCAUCurve` | Yes | `results["outcome_predictor_stats"]?.data` |
| `remedy_network_analysis` | `NetworkGraph` | Yes (with mock defaults) | `results["remedy_network_analysis"]?.data`; falls back to hardcoded default nodes/edges |
| `outcome_comparator` | `OutcomeComparatorPanel` | Yes | `results["outcome_comparator"]?.data` |
| `repertory_pca` | `RepertoryPCAPanel` | Yes | `results["repertory_pca"]?.data` |
| `case_complexity` | `CaseComplexityPanel` | Yes | `results["case_complexity"]?.data` |
| `inter_rater_reliability` | `InterRaterReliabilityPanel` | Yes | `results["inter_rater_reliability"]?.data` |
| `meta_analysis` | `MetaAnalysisPanel` | Yes | `results["meta_analysis"]?.data` |
| `power_analysis` | `PowerAnalysisPanel` | Yes | `results["power_analysis"]?.data` |
| `survival_analysis` | `SurvivalAnalysisPanel` | Yes | `results["survival_analysis"]?.data` |
| `resampling_engine` | `ResamplingEnginePanel` | Yes | `results["resampling_engine"]?.data` |
| `reverse_repertorization` | `ReverseRepertorizationPanel` | Yes | `results["reverse_repertorization"]?.data` |
| `constitutional_tracker` | `ConstitutionalTrackerPanel` | Yes | `results["constitutional_tracker"]?.data` |
| `duplicate_remedy_detector` | `DuplicateRemedyPanel` | Yes | `results["duplicate_remedy_detector"]?.data` |
| `posology_scheduler` | `PosologySchedulerPanel` | Yes | `results["posology_scheduler"]?.data` |
| `symptom_severity` | `SymptomSeverityPanel` | Yes | `results["symptom_severity"]?.data` |
| `clinical_tips` | `ClinicalTipsPanel` | Yes | `results["clinical_tips"]?.data` |
| `batch_protocols` | `BatchProtocolPanel` | Yes | `results["batch_protocols"]?.data` |
| `inventory` | `InventoryPanel` | Yes | `results["inventory"]?.data` |
| `miasm_timeline` | `MiasmTimelinePanel` | Yes | `results["miasm_timeline"]?.data` |
| `case_similarity` | `CaseSimilarityPanel` | Yes | `results["case_similarity"]?.data` |

---

## 2. Registry Modules with Generic JSON Dump Panel Only

All other registry modules (~79) are rendered via the generic `ModulePanel` component in DashboardCanvas.tsx. This panel simply displays `JSON.stringify(result.data, null, 2)` with no custom visualization.

**Examples:** `cycles`, `srp_detector`, `phantom_rubric`, `potency_guidance`, `acute_chronic`, `red_flags`, `patient_cases`, `remedy_relationships`, `soap_assembler`, `letter_generator`, `cron_tasks`, `model_router`, `billing`, `patient_portal`, etc.

**Gap:** These modules produce backend data but have no tailored UI; practitioners see raw JSON.

---

## 3. Hardcoded / Mock-Data Visualizations (Not Registry-Driven)

These visualizations are rendered unconditionally inside DashboardCanvas.tsx when `hasRepertorization` is true. They are **not** tied to registry module IDs and many use hardcoded or randomly generated data.

| Component | Data Source | Live? | Notes |
|-----------|-------------|-------|-------|
| `CircularCycleViz` | `repertorizationData` + `Math.random()` | Partial | Cycle segments default to hardcoded STRAM_SEGS; matching uses `Math.random() > 0.5` fallback |
| `RadarChartViz` | `repertorizationData` | Yes | Live remedy data |
| `RemedyHeatmapMatrix` | `repertorizationData` (via helpers) | Yes | Live rubric/remedy data; helper functions build matrices from matches |
| `ComparativeVennDiagram` | `repertorizationData` | Yes | Uses live `rubricIds` from remedy matches |
| `PhantomRubricRiskGauge` | `phantomData` | Partial | Props default to `0.15`, `3`, `143408` if no live data |
| `PotencyLadderWaterfall` | `potencyData` | Partial | Defaults to hardcoded `["6C", "12C", "30C", "200C"]` if no live data |
| `MiasmDonutOverlay` | Hardcoded `MIASMS` | **No** | Weights are static; `patientMiasm` prop optional |
| `KingdomMorphologyCloud` | Hardcoded `KINGDOM_WORDS` | **No** | Completely static mock word cloud |
| `FamilyConstellationGraph` | Hardcoded `DEMO_FAMILY`, `EDGES` | **No** | Static demo graph with fake relatives |
| `LayerTimelineRibbon` | Hardcoded `EVENTS` | **No** | Static timeline of suppression events |
| `OutcomeTrajectorySparklines` | `repertorizationData` labels + `Math.random()` | **No** | All Y-axis points are `Math.random()` generated |
| `RubricConfidenceStrip` | `repertorizationData` labels + `Math.random()` | **No** | `lexical_score`, `vector_score`, `grade1_density` randomly generated in `buildConfidenceRubrics` |
| `TimelineSankeyViz` | Hardcoded symptoms + `Math.random()` | **No** | Symptoms list is static; link values use `Math.random()` |
| `SymptomConstellation` | `repertorizationData` | Yes | 3D viz using live remedy list |
| `RubricHierarchyTower` | `repertorizationData` | Yes | 3D viz using live remedy list |
| `RemedyLandscape` | `repertorizationData` | Yes | 3D viz using live remedy list |
| `ConfidenceCloud` | `repertorizationData` | Yes | 3D viz using live remedy list |
| `DifferentialHelix` | `repertorizationData` | Yes | 3D viz using live remedy list |
| `ConcordanceCube` | `repertorizationData` | Yes | 3D viz using live remedy list |

---

## 4. Orphan Dashboard Panels (Exist but NOT Rendered in DashboardCanvas)

These 32 components live in `src/components/dashboard/` and are exported from `index.ts`, but **DashboardCanvas.tsx never imports or renders them**. They are effectively dead code.

| Component File | Backend Module | In Registry | Notes |
|----------------|----------------|-------------|-------|
| `SymptomCooccurrencePanel.tsx` | `symptom_cooccurrence_lift.py` | Yes (`rubric_cooccurrence`) | Exists but unused |
| `RemedyComparisonView.tsx` | `remedy_comparator.py` | Yes (`remedy_comparator`) | Exists but unused |
| `CaseAnalysisBridgePanel.tsx` | `case_analysis_bridge.py` | **No** | No registry entry; orphan panel |
| `ThompsonSamplingPanel.tsx` | `bayesian_remedy_ranking.py`? | **No** | No registry entry; orphan panel |
| `EnsembleStackingPanel.tsx` | `ensemble_retrieval_stacking.py` | **No** | No registry entry; orphan panel |
| `PropensityScoredPanel.tsx` | `propensity_scored_prediction.py` | **No** | No registry entry; orphan panel |
| `RubricBanditPanel.tsx` | `rubric_bandit_selector.py` | **No** | No registry entry; orphan panel |
| `ConstitutionalSnapshotPanel.tsx` | `constitutional_snapshot.py` | **No** | No registry entry; orphan panel |
| `GeneralsSurveyPanel.tsx` | `generals_survey.py` | **No** | No registry entry; orphan panel |
| `MentalEmotionalPanel.tsx` | `mental_emotional_prober.py` | **No** | No registry entry; orphan panel |
| `IntakeAnalyzerPanel.tsx` | `intake_analyzer.py` | **No** | No registry entry; orphan panel |
| `ConcomitantPanel.tsx` | `concomitant_detector.py` | **No** | No registry entry; orphan panel |
| `CausationTimelinePanel.tsx` | `causation_timeline_module.py` | **No** | No registry entry; orphan panel |
| `ChiefComplaintPanel.tsx` | `chief_complaint_triager.py` | **No** | No registry entry; orphan panel |
| `QuestionBankPanel.tsx` | `interview_question_bank.py` | **No** | No registry entry; orphan panel |
| `PatientIntakePanel.tsx` | `patient_intake_engine.py` | **No** | No registry entry; orphan panel |
| `ModalityPanel.tsx` | `modality_extractor.py` | **No** | No registry entry; orphan panel |
| `BayesianNetworkPanel.tsx` | `bayesian_rubric_network.py` | **No** | No registry entry; orphan panel |
| `RemedyCalibrationPanel.tsx` | `remedy_confidence_calibration.py` | **No** | No registry entry; orphan panel |
| `ConfusionMatrixPanel.tsx` | `confusion_matrix_differential.py` | **No** | No registry entry; orphan panel |
| `KNearestProvenPanel.tsx` | `k_nearest_proven_cases.py` | **No** | No registry entry; orphan panel |
| `ActiveLearningIntakePanel.tsx` | `active_learning_intake_tracker.py` | **No** | No registry entry; orphan panel |
| `LatentEmbeddingPanel.tsx` | `latent_symptom_embedding.py` | **No** | No registry entry; orphan panel |
| `AdaptiveSymptomSequencerPanel.tsx` | `adaptive_symptom_sequencer.py` | **No** | No registry entry; orphan panel |
| `InformationTheoreticPanel.tsx` | `information_theoretic_case_workup.py` | **No** | No registry entry; orphan panel |
| `DiscriminantRubricPanel.tsx` | `discriminant_rubric_selector.py` | **No** | No registry entry; orphan panel |
| `CausalRemedyEffectsPanel.tsx` | `causal_remedy_effects.py` | **No** | No registry entry; orphan panel |
| `GaussianProcessPanel.tsx` | `gaussian_process_surrogate.py` | **No** | No registry entry; orphan panel |
| `SPRTPanel.tsx` | `sequential_remedy_testing.py` | **No** | No registry entry; orphan panel |
| `CVWeightLearningPanel.tsx` | `cv_symptom_weights.py` | **No** | No registry entry; orphan panel |
| `HierarchicalBayesianPanel.tsx` | `hierarchical_bayesian_similarity.py` | **No** | No registry entry; orphan panel |
| `RubricDiscriminationPanel.tsx` | `rubric_discrimination_indices.py` | **No** | No registry entry; orphan panel |

---

## 5. Backend Python Modules with NO Registry Entry

These ~60+ backend modules exist in `oorep/` but are **not exposed** in the portal module registry, so the frontend has no way to invoke them.

| Python Module | Likely Purpose |
|---------------|----------------|
| `case_analysis_bridge.py` | Case analysis bridge |
| `intake_analyzer.py` | Intake analysis |
| `constitutional_snapshot.py` | Constitutional snapshot |
| `generals_survey.py` | Generals survey |
| `mental_emotional_prober.py` | Mental/emotional probing |
| `causation_timeline_module.py` | Causation timeline |
| `modality_extractor.py` | Modality extraction |
| `concomitant_detector.py` | Concomitant detection |
| `patient_intake_engine.py` | Patient intake engine |
| `chief_complaint_triager.py` | Chief complaint triage |
| `interview_question_bank.py` | Interview question bank |
| `confusion_matrix_differential.py` | Confusion matrix differential |
| `adaptive_symptom_sequencer.py` | Adaptive symptom sequencing |
| `information_theoretic_case_workup.py` | Info-theoretic case workup |
| `discriminant_rubric_selector.py` | Discriminant rubric selection |
| `remedy_confidence_calibration.py` | Remedy confidence calibration |
| `active_learning_intake_tracker.py` | Active learning intake tracking |
| `symptom_cooccurrence_lift.py` | Symptom co-occurrence lift |
| `bayesian_rubric_network.py` | Bayesian rubric network |
| `k_nearest_proven_cases.py` | K-nearest proven cases |
| `latent_symptom_embedding.py` | Latent symptom embeddings |
| `ensemble_retrieval_stacking.py` | Ensemble retrieval stacking |
| `causal_remedy_effects.py` | Causal remedy effects |
| `gaussian_process_surrogate.py` | Gaussian process surrogate |
| `sequential_remedy_testing.py` | SPRT / sequential testing |
| `cv_symptom_weights.py` | CV symptom weight learning |
| `hierarchical_bayesian_similarity.py` | Hierarchical Bayesian similarity |
| `rubric_discrimination_indices.py` | Rubric discrimination indices |
| `propensity_scored_prediction.py` | Propensity-scored prediction |
| `rubric_bandit_selector.py` | Rubric bandit selection |
| `bayesian_remedy_ranking.py` | Bayesian remedy ranking |
| `bibliographic_engine.py` | Bibliographic engine |
| `remedy_relationships_v2.py` | Remedy relationships v2 |
| `materia_medica_search.py` | Materia medica search |
| `followup_comparator.py` | Follow-up comparator |
| `mobile_api.py` | Mobile API |
| `miasm_tracking.py` | Miasm tracking |
| `toxicology_layer.py` | Toxicology layer |
| `keynote_autocomplete.py` | Keynote autocomplete |
| `differential_diagnosis.py` | Differential diagnosis |
| `elimination_rubrics.py` | Elimination rubrics |
| `multi_repertory.py` | Multi-repertory support |
| `correlation_matrix.py` | Correlation matrix |
| `graphic_analysis.py` | Graphic analysis |
| `analysis_methods.py` | Analysis methods |
| `edition_comparison.py` | Edition comparison |
| `outcome_prediction.py` | Outcome prediction |
| `p1_bridge_integration.py` | P1 bridge integration |
| `homeopathic_repertory.py` | Homeopathic repertory core |
| `word_wrap_search.py` | Word-wrap search |
| `family_grouping.py` | Family grouping |
| `master_score_engine.py` | Master score engine |
| `analysis_manager.py` | Analysis manager |
| `patient_file_system.py` | Patient file system |
| `clipboard_manager.py` | Clipboard manager |
| `rare_remedy_triangulator.py` | Rare remedy triangulator |
| `clinical_rubric_mapper.py` | Clinical rubric mapper |
| `oorep_vector_search.py` | Vector search |
| `sensation_method_integration.py` | Sensation method integration |
| `multi_language_display.py` | Multi-language display |
| `therapeutic_pocket_book.py` | Therapeutic pocket book |
| `remedy_pictures.py` | Remedy pictures |
| `gamification_engine.py` | Gamification engine |
| `mobile_app_native.py` | Mobile app native |
| `social_community.py` | Social community |
| `cloud_sync_manager.py` | Cloud sync manager |
| `automated_index_rebuilder.py` | Automated index rebuilder |

---

## 6. Key Panel Gaps Identified

1. **32 orphan dashboard panels** exist in `src/components/dashboard/` with corresponding backend Python modules, but **none** are imported or rendered in `DashboardCanvas.tsx`. Many of these panels also lack registry entries.

2. **~79 registry modules** only get a generic JSON dump panel (`ModulePanel`). They have no custom visualization, making the dashboard experience poor for practitioners.

3. **~60+ backend Python modules** have no registry entry at all, meaning they are completely inaccessible from the frontend.

4. **Mock data issues:**
   - `KingdomMorphologyCloud`, `FamilyConstellationGraph`, `LayerTimelineRibbon` are **entirely hardcoded** with static demo data.
   - `OutcomeTrajectorySparklines` and `RubricConfidenceStrip` generate Y-values and scores using `Math.random()` at render time, producing different visuals on every refresh.
   - `TimelineSankeyViz` uses a hardcoded symptom list and random link strengths.
   - `CircularCycleViz` falls back to `Math.random() > 0.5` for segment matching when live `cycle_analysis` is absent.

5. **Missing API routes:** The registry defines routes like `/api/admin/cycles`, `/api/admin/srp`, etc., but only `/api/admin/repertorize`, `/api/admin/auth`, `/api/admin/pdf`, `/api/admin/cases` routes exist in the codebase. Most registry module routes have **no implemented API handler**.

---

*Audit generated by examining `DashboardCanvas.tsx`, `src/app/api/portal/modules/route.ts`, `src/components/dashboard/*.tsx`, `src/components/visualizations/*.tsx`, and the `oorep/` Python package.*
