# OOREP Python Backend Module Report

**Scope:** All Python modules under `/home/walker/projects/oorep-local-repertory/oorep/` (~150 modules)  
**Analysis date:** 2026-06-23  
**Method:** Read `__init__.py`, portal module registry, and first ~30 lines of every `.py` file; mapped internal imports and docstring descriptions.

---

## 1. Executive Summary

The OOREP backend is a large, feature-rich homeopathic repertory system with ~150 modules. The codebase is **broad but shallowly integrated**: most modules are self-contained classes that read from local JSON/SQLite (`data/`) and return dictionaries. The true "glue" is the Next.js frontend (`oorep-case-portal`), which calls modules via API routes. Internal Python-to-Python dependencies are minimal.

### Key Findings
- **Central data spine:** `homeopathic_repertory.py` is the only module imported by many others (~34 references). It owns rubric JSON, remedy JSON, and inverted indexes.
- **Shared database:** A large cohort of modules (analytics, safety, workflow) rely on `data/feedback.db` (via `scripts.remedy_feedback`), but there is no unified ORM or data layer.
- **Intake pipeline (v4.0) is the most integrated subsystem:** 10 modules are explicitly orchestrated by `patient_intake_engine.py`.
- **Statistical tier (v3.6–v3.9) is largely isolated:** ~20 modules compute metrics but rarely consume each other’s outputs.
- **Redundancy/overlap exists** in remedy relationships, miasm tracking, elimination logic, and materia medica search.

---

## 2. Module Inventory by Category

> Categories align with the portal module registry (`src/app/api/portal/modules/route.ts`). Modules not in the portal registry are placed in the most logical bucket.

### 2.1 Differential (Remedy Selection & Analysis)

| Module | Purpose (1 sentence) | Key Internal Dependencies | Downstream Consumers | Integration Gap / Opportunity |
|---|---|---|---|---|
| `homeopathic_repertory` | Core repertory: lexical/vector search, repertorization, rubric↔remedy lookups. | None (root) | ~34 modules import it; portal `/api/admin/repertorize` | Already central spine. |
| `clinical_rubric_mapper` | Normalizes patient-friendly language into repertory query text. | `homeopathic_repertory` | Portal `/api/admin/repertorize` (indirect) | Could feed `word_wrap_search` and `patient_intake_engine`. |
| `master_score_engine` | Composite scoring (Kent + Boenninghausen + SRP + rarity + kingdom). | `homeopathic_repertory`, `srp_detector`, `kingdom_taxonomy` | Portal `/api/admin/repertorize` | Sub-scorers are isolated; could expose sub-score API. |
| `srp_detector` | Flags Strange-Rare-Peculiar symptoms for boosted weighting. | None | `master_score_engine`, portal `/api/admin/srp` | Output should auto-feed `patient_intake_engine` and `adaptive_symptom_sequencer`. |
| `rare_remedy_triangulator` | Surfaces small/rare remedies overlooked by polychrests. | None | Portal (indirect) | Could be triggered automatically when top-3 are all polycrests. |
| `phantom_rubric_analyzer` | Flags low-differentiation rubrics via Gini/entropy. | `homeopathic_repertory` | Portal `/api/admin/phantoms` | Could prune rubrics before `master_score_engine` runs. |
| `rubric_cooccurrence` | Mines remedy pairs and polycrest clusters. | `homeopathic_repertory` | Portal `/api/admin/cooccurrence` | Could inform `remedy_network_analysis` and `differential_diagnosis`. |
| `elimination_analysis` | Shows which rubrics a target remedy does NOT cover. | `homeopathic_repertory` | Portal `/api/admin/elimination` | Overlaps with `elimination_rubrics`; should merge logic. |
| `elimination_rubrics` | Structured AND/OR/NOT elimination engine. | None | Portal `/api/admin/elimination` (planned) | **Redundant with `elimination_analysis`.** Merge opportunity. |
| `potency_guidance` | Classical potency ladder + remedy-specific profiles. | `scripts.remedy_feedback` DB | Portal `/api/admin/potency` | Should be called automatically after repertorization. |
| `acute_chronic_layer` | Tags symptoms as acute/chronic and reweights results. | `homeopathic_repertory` | Portal `/api/admin/layers` | Could auto-tag in `patient_intake_engine`. |
| `differential_diagnosis` | Multi-way differential table: shared vs exclusive rubrics. | None (standalone) | Portal `/api/admin/compare` | Should consume `remedy_comparator` and `kingdom_taxonomy`. |
| `remedy_comparator` | Overlap, divergence, Jaccard across remedies. | `homeopathic_repertory` | Portal `/api/admin/compare` | Currently manual; could auto-trigger after repertorization. |
| `reverse_repertorization` | Given remedy → list all graded rubrics. | None (JSON load) | Portal `/api/admin/reverse_repertorization` | Useful for `materia_medica_search` confirmation. |
| `polarity_analysis` | Heiner Frei systematic symptom confirmation. | None | Portal `/api/admin/polarity` | Could integrate with `discriminant_rubric_selector`. |
| `miasm_timeline` | Visual miasmatic layer history. | SQLite | Portal `/api/admin/miasm_timeline` | **Overlaps with `miasm_tracking`.** |
| `modality_matrix` | Boenninghausen-style symptom-modality grid. | None | Portal `/api/admin/modality_matrix` | Could auto-generate from `modality_extractor` output. |
| `case_analysis_bridge` | Cross-references confusion matrix + co-occurrence lift. | `confusion_matrix_differential`, `symptom_cooccurrence_lift` | Portal (indirect) | Good integration example; should be promoted to first-class API. |

### 2.2 Navigation (Search, Exploration, Lookup)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `rubric_explorer` | Kent hierarchy parent/child/sibling traversal. | `homeopathic_repertory` | Portal `/api/admin/rubric-explore` | Could be embedded in `quick_symptom_lookup` results. |
| `private_rubrics` | Practitioner-created custom rubrics with merge-to-repertorization. | None (SQLite) | Portal `/api/admin/private-rubrics` | Should feed `homeopathic_repertory` at runtime. |
| `quick_symptom_lookup` | Single-symptom fast search without full repertorization. | None (JSON load) | Portal `/api/admin/quick_lookup` | Could return rubric IDs directly to `clipboard_manager`. |
| `word_wrap_search` | Proximity-aware multi-word phrase search. | `homeopathic_repertory` | None exposed in portal | **Integration gap:** not wired to portal; should replace default search in `homeopathic_repertory`. |
| `keynote_autocomplete` | Trie-based rubric autocomplete with keynote boosting. | None | None exposed in portal | **Integration gap:** could power frontend search bar. |
| `cross_reference_repertory` | Maps rubrics across Kent/Boenninghausen/Boger/Synthesis. | None (JSON load) | Portal `/api/admin/cross_reference` | Could enrich `edition_comparison`. |
| `multi_repertory` | Parallel search across multiple corpora with source tagging. | None | Portal (indirect) | Could be the backend for `cross_reference_repertory`. |
| `oorep_vector_search` | Offline feature-hashing vector search (numpy). | numpy | `homeopathic_repertory` (hybrid mode) | Already consumed by core; no gap. |

### 2.3 Analytics (Cases, Cohorts, Patterns)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `patient_case_manager` | Hermes-session Q&A over cases ("What did I prescribe Mrs. J?"). | `scripts.remedy_feedback` | Portal `/api/admin/cases` | Could call `case_summarizer` for narrative answers. |
| `patient_cohort_analytics` | Practice-wide SQL analytics: outcomes, timelines, correlations. | `scripts.remedy_feedback` DB | Portal `/api/admin/cohort` | Should feed `global_stats_dashboard`. |
| `family_constellation` | Family remedy patterns across generations. | `scripts.remedy_feedback` DB | Portal `/api/admin/family` | Could link to `genomic_hypothesis`. |
| `suppression_tracker` | Records suppression events and warns against repeat. | `scripts.remedy_feedback` DB | Portal `/api/admin/suppression` | Should auto-check during `patient_intake_engine`. |
| `case_similarity_search` | Vector similarity to find previous similar cases. | None (JSON load) | Portal `/api/admin/case_similarity` | Could be called by `k_nearest_proven_cases`. |
| `symptom_severity_scorer` | Intensity-based 1–10 weighting for repertorization. | None (JSON) | Portal `/api/admin/severity` | Could feed `master_score_engine` weights. |
| `symptom_narrative_extractor` | NLP-lite extraction of symptoms from free text. | None | Portal `/api/admin/narrative_extract` | **Key integration gap:** should be first step in `voice_to_text_audio_import` pipeline. |
| `case_summarizer` | Auto-generates readable case summaries. | None | Portal `/api/admin/summarize` | Should be called by `patient_portal` and `letter_generator`. |
| `rubric_quality_scorer` | Scores rubric reliability by distribution/diversity. | None (JSON) | Portal `/api/admin/rubric_quality` | Could feed `rubric_gap_analyzer`. |
| `global_stats_dashboard` | Practice-wide analytics overview. | None (aggregates DBs) | Portal `/api/admin/stats` | **Currently isolated.** Should consume `patient_cohort_analytics`, `outcome_comparator`, `remedy_network_analysis`. |
| `export_research_formats` | CSV/JSON anonymized research exports. | None | Portal `/api/admin/export` | Could be triggered by `cron_tasks`. |

### 2.4 Safety (Guardrails, Audit, PHI)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `practitioner_approval_gate` | Enforces `prescriber_ack` before recording prescriptions. | None (SQLite) | Portal `/api/admin/approve` | Should wrap every prescription-writing API automatically. |
| `red_flag_detector` | Critical/urgent symptom detection with referral triggers. | `scripts.remedy_feedback` DB | Portal `/api/admin/red-flags` | Should auto-run in `patient_intake_engine` and `chief_complaint_triager`. |
| `phi_scrubber` | PHI detection + reversible pseudonym mapping. | None (SQLite) | Portal `/api/admin/phi-scrub` | Should be applied by `export_research_formats` and `social_community`. |
| `audit_trail` | SHA-256 hash chain, immutable prescription logs. | None (SQLite) | Portal `/api/admin/audit` | Should be written by `practitioner_approval_gate`, `billing_integration`, `appointment_scheduler`. |
| `duplicate_remedy_detector` | Antidote/inimical prescription warnings. | SQLite | Portal `/api/admin/duplicate_detector` | **Overlaps with `toxicology_layer`.** Merge opportunity. |

### 2.5 Materia Medica (Remedy Knowledge)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `materia_medica` | Full-text proving DB with SQLite backend. | `scripts.remedy_feedback` DB | Portal `/api/admin/materia-medica` | Core reference; widely used implicitly. |
| `materia_medica_search` | TF-IDF indexing + repertorization confirmation layer. | `materia_medica` | Portal (indirect) | Could auto-confirm `homeopathic_repertory` results. |
| `remedy_relationships` | Classical complementary/antidote/inimical tables. | None (SQLite) | Portal `/api/admin/relationships` | **Overlaps with `remedy_relationships_v2`.** |
| `remedy_relationships_v2` | Directed graph, strength scoring, temporal sequencing. | None (SQLite) | Portal (indirect) | Should replace v1 or expose distinct API. |
| `remedy_network_analysis` | Graph centrality, community detection on relationship graph. | `remedy_relationships_v2` (implicit) | Portal `/api/admin/network` | Consumes v2 data; good linkage. |
| `kingdom_taxonomy` | Mineral/Plant/Animal tags + family cross-references. | `scripts.remedy_feedback` DB | Portal `/api/admin/kingdom` | Consumed by `family_grouping`, `master_score_engine`; well-integrated. |
| `botanical_bridge` | WHO Monograph cross-map for botanical remedies. | `scripts.remedy_feedback` DB | Portal `/api/admin/botanical` | Could enrich `materia_medica` search results. |
| `genomic_hypothesis` | SNP → remedy outcome correlation hypotheses. | `scripts.remedy_feedback` DB | Portal `/api/admin/genomic` | Currently niche; could link to `family_constellation`. |
| `clinical_tips_engine` | Practitioner notes on rubrics. | SQLite | Portal `/api/admin/clinical_tips` | Could surface in `rubric_explorer`. |
| `author_filter` | Filter repertory by source authority. | None | Portal `/api/admin/author_filter` | Could be applied to `materia_medica` and `homeopathic_repertory`. |
| `proving_text_search` | Full-text search inside proving texts. | None (JSON) | Portal `/api/admin/proving_search` | Could use `materia_medica_search` engine. |
| `repertory_synthesis` | Build custom repertories from multiple sources. | None (JSON) | Portal `/api/admin/synthesis` | Could ingest `private_rubrics`. |
| `therapeutic_pocket_book` | Scaffold for Boenninghausen TPB data. | None | None | **Scaffold / no data.** Needs TPB corpus or removal. |
| `remedy_pictures` | Visual remedy reference metadata. | None (JSON) | None | **Scaffold / no images.** Low priority. |
| `sensation_method_integration` | Sankaran-style kingdom/source/sensation taxonomy. | None | None | Small seed data; could replace/extend `kingdom_taxonomy`. |

### 2.6 Teaching (Students, Quizzes, Grand Rounds)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `student_training` | Simulated patients + 4-option quizzes. | SQLite | Portal `/api/admin/training` | Could consume `clinical_vignette_quiz` for real-case questions. |
| `clinical_vignette_quiz` | Real-outcome → difficulty-tiered quizzes. | `scripts.remedy_feedback` DB | Portal `/api/admin/vignette-quiz` | Good standalone; could feed `student_training`. |
| `grand_rounds` | Multi-case synthesis + markdown teaching narratives. | SQLite | Portal `/api/admin/grand-rounds` | Could consume `case_summarizer`. |
| `flashcard_srs` | SM-2 spaced repetition for materia medica. | SQLite | Portal `/api/admin/srs` | Could auto-generate cards from `materia_medica`. |
| `gamification_engine` | Points, streaks, leaderboards. | JSON | None | **Isolated.** Could integrate with `flashcard_srs` and `student_training`. |

### 2.7 Workflow (SOAP, Letters, Scheduling, Inventory)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `soap_assembler` | Template-based SOAP from case notes. | None (SQLite) | Portal `/api/admin/soap` | Should consume `patient_file_system` and `case_summarizer`. |
| `letter_generator` | Referral / summary / prescription letters. | None (SQLite) | Portal `/api/admin/letter` | Should consume `case_summarizer` and `soap_assembler`. |
| `prescription_pdf_generator` | Structured prescription data for PDF rendering. | None | Portal `/api/admin/prescription_pdf` | Should be triggered by `practitioner_approval_gate`. |
| `batch_protocol_builder` | Standard protocols for common conditions. | None (JSON) | Portal `/api/admin/protocols` | Could be suggested by `patient_intake_engine` for acute cases. |
| `posology_scheduler` | Classical dosing + repetition guidance. | None | Portal `/api/admin/posology` | Should follow `potency_guidance` in prescription chain. |
| `appointment_scheduler` | Follow-up and acute appointment calendar. | SQLite | Portal `/api/admin/appointments` | Should write to `audit_trail`. |
| `followup_prompt_generator` | Automated follow-up questions by remedy/potency. | None | Portal `/api/admin/followup` | Should be linked to `appointment_scheduler`. |
| `inventory_manager` | Remedy stock and expiry tracking. | SQLite | Portal `/api/admin/inventory` | Could warn in `prescription_pdf_generator`. |
| `case_summarizer` | *(also in Analytics)* | — | — | — |
| `voice_to_text_audio_import` | Audio → transcription → symptom extraction. | None | Portal `/api/admin/voice_import` | **Key gap:** transcription stub; should call `symptom_narrative_extractor`. |
| `automated_index_rebuilder` | Monitors data changes and rebuilds indexes. | None (JSON) | `cron_tasks` | Good linkage; runs via cron. |
| `cloud_sync_manager` | Encrypted multi-device sync scaffold. | None | None | **Scaffold.** Needs cloud backend config. |
| `patient_file_system` | Unified patient→consultation→SOAP→prescription linkage. | None (SQLite) | Portal (indirect) | **Underutilized.** Many modules write their own SQLite tables instead of using this. |
| `clipboard_manager` | Named multi-clipboard for rubric collection. | SQLite | None (indirect via core) | Good internal utility; could expose clipboard API to portal. |

### 2.8 Infrastructure (Routing, Sync, Cron, Portal)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `subagent_orchestrator` | Returns task plans/checklists (no actual spawning). | None | Portal `/api/admin/orchestrate` | **Mostly scaffold.** Could dispatch to `analysis_manager`, `model_router`. |
| `model_router` | Routes tasks to local Jetson vs cloud LLM. | SQLite | Portal `/api/admin/model-route` | Could be used by `voice_to_text_audio_import` and `symptom_narrative_extractor`. |
| `mobile_api` | Lightweight route descriptors for FastAPI/Flask. | None | None | API scaffolding; should be consumed by a FastAPI wrapper. |
| `mobile_app_native` | Compact JSON for native mobile apps. | `homeopathic_repertory` | None | Could be merged into `mobile_api`. |
| `cron_tasks` | Follow-up alerts, vector auto-rebuild, GitHub backup. | None | Crontab | Well-linked to `automated_index_rebuilder`. |
| `patient_portal` | Read-only case summaries for patients. | None | Portal `/api/admin/patient_portal` | Should consume `patient_file_system` and `case_summarizer`. |
| `billing_integration` | Invoice + insurance tracking. | SQLite | Portal `/api/admin/billing` | Should write to `audit_trail`. |
| `social_community` | Anonymized case sharing scaffold. | None | None | **Scaffold.** Needs moderation/privacy layer. |
| `p1_bridge_integration` | NL command routing for Word-Wrap/Multi-Repertory/MM Search. | None | None | **Empty scaffold (TODO).** |

### 2.9 Statistics (v3.6–v3.9 Statistical Modules)

| Module | Purpose | Dependencies | Consumers | Gap / Opportunity |
|---|---|---|---|---|
| `outcome_predictor_stats` | ROC/AUC, calibration, bootstrap CI on predictions. | `scripts.remedy_feedback` DB | Portal `/api/admin/outcome-stats` | Validates `outcome_prediction`; good pair. |
| `remedy_network_analysis` | Graph centrality, PageRank on remedy graph. | None (JSON) | Portal `/api/admin/network` | Consumes `remedy_relationships_v2` data. |
| `outcome_comparator` | Mann-Whitney U, odds ratio, Cohen's d between remedies. | SQLite | Portal `/api/admin/compare-outcomes` | Could be called by `patient_cohort_analytics`. |
| `repertory_pca` | SVD/PCA on remedy-rubric matrix (pure Python). | None | Portal `/api/admin/pca` | Could feed `graphic_analysis` for 2D/3D projections. |
| `case_complexity_scorer` | Symptom entropy, coverage gaps, composite complexity. | None | Portal `/api/admin/complexity` | Could pre-filter cases before `meta_analysis_engine`. |
| `inter_rater_reliability` | Cohen's kappa, Fleiss' kappa, ICC. | None | Portal `/api/admin/irr` | Could validate `practitioner_approval_gate` agreement data. |
| `meta_analysis_engine` | Fixed/random-effects meta-analysis with heterogeneity. | None | Portal `/api/admin/meta` | Could consume `outcome_comparator` results. |
| `power_analysis` | Sample size + power curves for studies. | None | Portal `/api/admin/power` | Standalone; no gap. |
| `survival_analysis` | Kaplan-Meier + hazard ratios for time-to-improvement. | SQLite | Portal `/api/admin/survival` | Could consume `patient_cohort_analytics` timelines. |
| `resampling_engine` | Bootstrap CI, permutation tests, k-fold CV. | None | Portal `/api/admin/resample` | Could validate all statistical modules. |
| `bayesian_remedy_ranking` | Thompson Sampling with beta distributions. | SQLite | None (indirect) | Could feed `master_score_engine` as a sub-scorer. |
| `rubric_bandit_selector` | UCB1 for discriminative rubric selection. | SQLite | None (indirect) | Could replace static rubric selection in repertorization. |
| `propensity_scored_prediction` | IPW to correct selection bias in outcomes. | SQLite | None (indirect) | Could adjust `outcome_prediction` scores. |
| `rubric_discrimination_indices` | Item-total correlation, KR-20 reliability. | None | None (indirect) | Could feed `rubric_quality_scorer`. |
| `hierarchical_bayesian_similarity` | Taxonomy-prior remedy similarity. | None | None (indirect) | Could replace `correlation_matrix` for neighbor lookups. |
| `cv_symptom_weights` | k-fold CV symptom weight learning. | None | None (indirect) | Could auto-tune `master_score_engine` weights. |
| `sequential_remedy_testing` | SPRT early stopping for remedy selection. | None | None (indirect) | Could stop repertorization early in large cases. |
| `gaussian_process_surrogate` | Bayesian optimization over remedy latent space. | None | None (indirect) | Could guide `adaptive_symptom_sequencer`. |
| `causal_remedy_effects` | Propensity matching + IPW for causal ATE. | None | None (indirect) | Could validate `outcome_comparator`. |
| `ensemble_retrieval_stacking` | Meta-learner combining lexical/vector/SRP/keynote layers. | None | None (indirect) | Could replace `homeopathic_repertory` hybrid search. |
| `discriminant_rubric_selector` | Reverse-engineers patient questions to break remedy ties. | `_v39_index`, `homeopathic_repertory` | None (indirect) | **Well-integrated internally.** Should be exposed in portal. |
| `information_theoretic_case_workup` | Bits-needed, case completeness, entropy reduction. | None | `patient_intake_engine` | Good internal integration. |
| `adaptive_symptom_sequencer` | Dynamic follow-up question ordering by info gain. | None | `patient_intake_engine` | Good internal integration. |
| `latent_symptom_embedding` | Truncated SVD on remedy-rubric matrix (pure Python). | `_v39_index` | None (indirect) | Could feed `case_similarity_search`. |
| `confusion_matrix_differential` | Confusion matrix of remedy mistaken identity. | `_v39_index` | `case_analysis_bridge` | Good internal integration. |
| `k_nearest_proven_cases` | k-NN historical cases weighted by outcomes. | None | None (indirect) | Could be called by `patient_case_manager`. |
| `bayesian_rubric_network` | Chow-Liu tree of rubric dependencies. | None | None (indirect) | Could guide `rubric_bandit_selector`. |
| `symptom_cooccurrence_lift` | Association rule mining (lift, confidence, support). | None | `case_analysis_bridge` | Good internal integration. |
| `active_learning_intake_tracker` | Tracks asked vs unasked symptoms by info gain. | None | `patient_intake_engine` | Good internal integration. |
| `remedy_confidence_calibration` | Platt scaling / isotonic regression on raw scores. | None | None (indirect) | Should calibrate `master_score_engine` outputs. |
| `_v39_index` | Shared index builder for statistical modules. | `homeopathic_repertory` | `discriminant_rubric_selector`, `latent_symptom_embedding`, `confusion_matrix_differential` | Good shared utility. |
| `correlation_matrix` | Pre-computed Jaccard/cosine remedy similarity. | None (JSON) | `master_score_engine` (indirect) | Could be replaced by `hierarchical_bayesian_similarity`. |

---

## 3. Data Flow Map

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA LAYER                            │
│  JSON: rubric_remedies_full.json, remedies.json, indexes/    │
│  SQLite: feedback.db (many modules), inventory.db, etc.      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
    │ homeopathic_    │ │ scripts  │ │ patient_file_    │
    │ repertory       │ │ remedy_  │ │ system           │
    │ (central spine) │ │ feedback │ │ (underutilized)  │
    └────────┬────────┘ └────┬─────┘ └────────┬─────────┘
             │               │                │
    ┌────────▼────────┐      │                │
    │ Search & Score  │      │                │
    │ - word_wrap_search│      │                │
    │ - oorep_vector_ │      │                │
    │   search        │      │                │
    │ - master_score_ │      │                │
    │   engine        │      │                │
    └────────┬────────┘      │                │
             │               │                │
    ┌────────▼────────┐      │                │
    │ Differential    │      │                │
    │ - srp_detector  │      │                │
    │ - elimination_  │      │                │
    │   analysis      │      │                │
    │ - phantom_rubric│      │                │
    │ - discriminant_ │      │                │
    │   rubric_selector│     │                │
    └────────┬────────┘      │                │
             │               │                │
    ┌────────▼────────────────┼────────────────▼──────┐
    │   PATIENT INTAKE PIPELINE (v4.0)               │
    │  patient_intake_engine ──► chief_complaint_    │
    │        │                    triager              │
    │        ├────────────────► interview_question_   │
    │        │                    bank                  │
    │        ├────────────────► adaptive_symptom_      │
    │        │                    sequencer              │
    │        ├────────────────► active_learning_      │
    │        │                    intake_tracker         │
    │        ├────────────────► modality_extractor      │
    │        ├────────────────► mental_emotional_       │
    │        │                    prober                 │
    │        ├────────────────► generals_survey        │
    │        ├────────────────► constitutional_snapshot │
    │        ├────────────────► causation_timeline      │
    │        └────────────────► concomitant_detector    │
    │                          intake_analyzer          │
    └──────────────────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │ Safety & Workflow │
    │ - red_flag_detector│
    │ - practitioner_   │
    │   approval_gate   │
    │ - phi_scrubber    │
    │ - audit_trail     │
    │ - soap_assembler  │
    │ - letter_generator│
    │ - prescription_  │
    │   pdf_generator   │
    └───────────────────┘
             │
    ┌────────▼────────┐
    │ Analytics & MM  │
    │ - patient_case_ │
    │   manager       │
    │ - patient_cohort│
    │   _analytics     │
    │ - materia_medica│
    │   _search        │
    │ - outcome_      │
    │   prediction     │
    └───────────────────┘
             │
    ┌────────▼────────┐
    │ Statistics Tier │
    │ (largely isolated)│
    │ - bayesian_...   │
    │ - survival_...   │
    │ - meta_analysis_ │
    │   engine         │
    └───────────────────┘
```

---

## 4. Redundancy & Overlap

| Modules | Nature of Overlap | Recommendation |
|---|---|---|
| `remedy_relationships` vs `remedy_relationships_v2` | Both model complementary/antidote/inimical data. v2 adds graph strengths and temporal sequencing. | Deprecate v1; migrate portal to v2 (`RemedyGraphEngine`). |
| `miasm_tracking` vs `miasm_timeline` | Both track miasmatic layers. `miasm_tracking` classifies; `miasm_timeline` visualizes history. | Merge into a single `MiasmManager` with classification + timeline. |
| `elimination_analysis` vs `elimination_rubrics` | Both implement exclusion logic. `elimination_rubrics` adds AND/OR/NOT structured criteria. | Consolidate into `elimination_rubrics` and have `elimination_analysis` call it. |
| `toxicology_layer` vs `duplicate_remedy_detector` | Both check antidote/inimical pairs. | Merge; `toxicology_layer` is broader (contraindications too); absorb duplicate detector. |
| `materia_medica` vs `materia_medica_search` | `materia_medica_search` is an indexing/search layer on top of `materia_medica`. | Keep separate but ensure `materia_medica_search` is the exclusive search API; hide raw `materia_medica` from portal. |
| `outcome_prediction` vs `outcome_predictor_stats` vs `outcome_comparator` | Prediction, validation, and pairwise comparison are distinct but adjacent. | Create an `outcomes` sub-package to share DB connection and schemas. |
| `mobile_api` vs `mobile_app_native` | Both define API layers for mobile. | Merge into one module; `mobile_app_native` can be a formatter class inside `mobile_api`. |
| `global_stats_dashboard` vs `patient_cohort_analytics` | Both compute practice-wide stats. | Have `global_stats_dashboard` call `patient_cohort_analytics` methods instead of reimplementing queries. |
| `correlation_matrix` vs `hierarchical_bayesian_similarity` | Both compute remedy similarity. | Retain `hierarchical_bayesian_similarity` (more principled) and deprecate `correlation_matrix`. |
| `p1_bridge_integration` vs `word_wrap_search` / `multi_repertory` | `p1_bridge_integration` is a TODO scaffold meant to wrap the other two. | Implement or delete; if kept, make it a thin router calling the real modules. |

---

## 5. Top Integration Opportunities

1. **Voice-to-Intake Pipeline**  
   `voice_to_text_audio_import` → `symptom_narrative_extractor` → `patient_intake_engine` → `red_flag_detector`. Currently all stubs or disconnected.

2. **Statistical Tier → Master Score**  
   `bayesian_remedy_ranking`, `cv_symptom_weights`, `remedy_confidence_calibration`, and `ensemble_retrieval_stacking` should be sub-scorers inside `master_score_engine`.

3. **Analytics Dashboard Consolidation**  
   `global_stats_dashboard` should consume outputs from `patient_cohort_analytics`, `outcome_comparator`, `remedy_network_analysis`, and `survival_analysis` instead of re-querying raw DBs.

4. **Safety Auto-Wrapping**  
   `red_flag_detector` and `practitioner_approval_gate` should be middleware (decorators or FastAPI dependencies) around every prescription-related API route.

5. **Materia Medica Confirmation Loop**  
   After `homeopathic_repertory` repertorization, automatically call `materia_medica_search.confirm_repertorization()` to highlight proving-text evidence.

6. **Patient File System Adoption**  
   Many modules (`appointment_scheduler`, `billing_integration`, `constitutional_remedy_tracker`) write their own SQLite tables. Unify them under `patient_file_system` schemas.

7. **Portal Exposure for v3.9 Statistical Modules**  
   `discriminant_rubric_selector`, `information_theoretic_case_workup`, `adaptive_symptom_sequencer`, and `active_learning_intake_tracker` are well-integrated internally but have **no portal routes**. Add API endpoints so the frontend can use the "differential question engine."

---

## 6. File Created

- `/home/walker/projects/oorep-local-repertory/oorep-backend-module-report.md`

---

## 7. Issues Encountered

- **No `requirements.txt` or `pyproject.toml` at root** — dependencies (numpy, sqlite3, etc.) are implied but not pinned.
- **Many modules are JSON/SQLite stubs** — `therapeutic_pocket_book`, `remedy_pictures`, `social_community`, `p1_bridge_integration`, `cloud_sync_manager` have minimal or no real data backends.
- **Import inconsistency** — Some modules use `from .homeopathic_repertory import ...` with try/except fallback to `from homeopathic_repertory import ...`; others use `from oorep.module import ...`. Standardizing to absolute `from oorep.module` would improve reliability.
- **No `tests/` directory visible** in the scanned `oorep/` package; the `__init__.py` mentions `tests/` but none were found alongside the modules.
