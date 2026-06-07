# OOREP Local Homeopathic Repertory

A **fast, offline, open-source homeopathic repertory** built on [OOREP](https://www.oorep.com/) (Open Online Repertory) data, enhanced with modern multi-layer search, clinical phrase mapping, remedy outcome tracking, and **73 specialized Python modules** — from remedy relationships and potency guidance to audit trails, grand rounds synthesis, statistical validation, and the Clinical Mission Control dashboard.

> **Version:** 3.6 | **License:** GPL v3  
> **Data:** 2,432 remedies × 143,408 rubrics × 1.36M remedy-grade links  
> **Modules:** 73 Python modules  
> **Tests:** 746 pytest tests  
> **Coverage:** 59 of 59 (100%) LLM-Hermes benefits implemented + 14 statistical modules  
> **Dashboard:** Next.js Clinical Mission Control with 25 visualizations + live API + click-through drill-down

---

## What Is This?

A complete, practitioner-owned homeopathic software stack that runs entirely on your machine. No subscriptions, no cloud lock-in, no data leaving your clinic. Built for:

- **Daily clinical practice** — repertorize, compare remedies, track outcomes
- **Teaching & training** — simulated patients, quizzes, grand rounds
- **Research** — rubric co-occurrence mining, edition comparison, outcome prediction
- **Safety** — red-flag detection, practitioner approval gates, PHI scrubbing, immutable audit trails
- **Integration** — Hermes Agent voice/Telegram interface + Next.js web portal

---

## Recent Updates (June 2026)

### v3.5 — Complete Package

**All 63 modules now importable from the standard API.** Previously, ~23 newer modules were built but missing from `oorep.__all__`. Every module now exports cleanly via `from oorep import ModuleName`.

**Feature #28: Patient Outcome Prediction** — Bayesian outcome forecasting with Laplace smoothing. Combines rubric coverage, keynote matching, patient history, and remedy track records into an interpretable probability score. 15 tests.

**Feature #29: Comparative Edition Analysis** — Compare rubric definitions, remedy grades, and coverage across repertory editions (Kent 1st vs 2nd, Synthesis vs OOREP). Jaccard similarity, weighted overlap, grade consistency, drift metrics. 22 tests.

**Bibliographic Engine fully implemented** — Was a 31-line stub; now a 650-line citation engine with 13 pre-loaded classical sources (Hahnemann, Kent, Allen, Boenninghausen, Hering, Clarke, Nash, Boger, Herscu, OOREP), SQLite-backed source registration, rubric/remedy citation links, Vancouver/BibTeX/plain formatting, bibliography generation, and footnotes. 25 tests.

**Master Score Engine test speed-up** — Module-scoped fixtures cut test time from >60s to ~10s on Jetson.

### v3.6 — Statistical Validation Suite (NEW)

**10 new pure-Python statistical modules** for clinical outcome validation, remedy comparison, case complexity scoring, and study design. No `scipy`, `pandas`, or `sklearn` dependencies — runs entirely offline on any hardware.

| # | Module | What It Does | Tests |
|---|--------|--------------|-------|
| 64 | **Outcome Predictor Stats** | ROC/AUC curves, calibration analysis (ECE), bootstrap 95% CI on predictions | 14 |
| 65 | **Remedy Network Analysis** | Graph centrality (PageRank, betweenness), community detection (Louvain), shortest path on remedy relationship graph | 13 |
| 66 | **Outcome Comparator** | Mann-Whitney U (pure Python), odds ratio + CI, Cohen's d, Cliff's delta for remedy outcome comparison | 10 |
| 67 | **Repertory PCA** | SVD/PCA on remedy-rubric matrix, 2D/3D projections, explained variance ratios | 10 |
| 68 | **Case Complexity Scorer** | Symptom entropy, coverage ratio, redundancy, specificity → composite 0–1 complexity score | 5 |
| 69 | **Inter-Rater Reliability** | Cohen's kappa, Fleiss' kappa, ICC(3,1) for practitioner agreement measurement | 10 |
| 70 | **Meta-Analysis Engine** | Fixed-effect & random-effects (DerSimonian-Laird), forest plot data, I² heterogeneity | 10 |
| 71 | **Power Analysis** | Sample size per group, achievable power, minimum detectable effect, power curves | 10 |
| 72 | **Survival Analysis** | Kaplan-Meier estimator, median survival time, hazard ratio comparison between remedies | 10 |
| 73 | **Resampling Engine** | Bootstrap CI (1000+ iterations), permutation tests, k-fold cross-validation | 13 |

**Dashboard panels for all 10 modules** — ROC curve, network graph, comparator cards, PCA scatter, complexity gauge, kappa display, forest plot, power curve, Kaplan-Meier curve, and resampling visualization. All wired into the Clinical Mission Control 2-column responsive grid with BEGINNER/INTERMEDIATE/ADVANCED level badges.

---

## Complete Feature List

### Core Repertory Engine

- **Fully Local & Offline** — No API calls, no cloud, no subscriptions. Works in remote clinics.
- **Memory-Safe Data Extraction** — 1.36M remedy-rubric links processed in 150K-link batches.
- **Lightning-Fast Lexical Search** — Token-matched rubric lookup in milliseconds.
- **Local Vector Semantic Search** — Offline 384-dim random-projection vectors (float16). No API keys.
- **Hybrid Retrieval Fusion** — Combines lexical precision + vector semantic reach + token overlap.
- **Clinical Rubric Mapper** — Patient phrase normalization and synonym expansion ("can't sleep after 3am" → sleep/waking/after midnight rubrics).
- **Classical Grade-Only Scoring** — Kent grades (1/2/3) rank remedies. Retrieval confidence never enters the score.
- **Multi-Symptom Repertorization** — Full symptom set → ranked remedy table by classical grade sums.
- **Rare Remedy Triangulation** — Surface unusual simillimums that broad repertories bury.
- **Abbreviation Decoding** — Robust remedy abbreviation resolution.

### Search & Discovery

- **Word-Wrap Proximity Search** — Multi-word phrase matching with adjacency scoring. Configurable window size. 16 tests.
- **Multi-Repertory Search** — Search across multiple corpora simultaneously with source tagging. 10 tests.
- **Materia Medica Full-Text Search** — TF-IDF indexed proving text search. 11 tests.
- **Keynote Autocomplete** — Kent keynote trie-based completion with scoring and history. 12 tests.
- **Rubric Co-occurrence Mining** — Remedy pair mining, polycrest clusters, association rules. 10 tests.
- **Phantom Rubric Detection** — Gini + entropy flags for low-differentiation rubrics. 10 tests.
- **Rubric Gap Analyzer** — Coverage gap detection, rubric quality scoring, new-rubric suggestions. 6 tests.

### Differential Diagnosis & Selection

- **Remedy Comparator** — Multi-remedy overlap, divergence, Jaccard analysis. 8 tests.
- **SRP Detector** — Strange-Rare-Peculiar keyword detection with weighted scoring. 10 tests.
- **Elimination Analyzer** — "What symptom rules out X?" exclusion logic. 10 tests.
- **Differential Diagnosis Engine** — Differential remedy ranking with similarity metrics. 8 tests.
- **Potency Guidance** — Classical potency ladder + remedy-specific profiles. 10 tests.
- **Acute / Chronic Layer Separation** — Layer-tagging and layer-separate repertorization. 10 tests.
- **Follow-up Comparator** — Track remedy changes across consultations. 10 tests.
- **Correlation Matrix** — Remedy pair overlap matrix with clustering. 10 tests.

### Composite & Advanced Scoring

- **Master Score Engine** — Composite repertorization combining Kent, Boenninghausen, SRP, rarity, and kingdom scorers with confidence intervals. 29 tests.
- **Pluggable Analysis Methods** — Switch between Kent, Boenninghausen, Boger, and Vithoulkas Expert System methods. 10 tests.
- **Graphic Analysis** — Visual score plots and charts for repertorization results. 10 tests.
- **Elimination Rubrics UI** — Exclusion-based rubric engine for differential work. 8 tests.
- **Family Grouping** — Filter/group by kingdom (plant/mineral/animal) or family (Solanaceae, Ranunculaceae, etc.). Family-level scoring. 17 tests.
- **Kingdom Taxonomy** — Mineral/Plant/Animal tags with family cross-references. 10 tests.

### Materia Medica & Learning

- **Materia Medica Proving DB** — Full-text proving text lookup with source attribution. 10 tests.
- **Remedy Relationships** — Classical complementary, antidotal, inimical, antidote tables. 10 tests.
- **Remedy Relationships V2** — Graph-based remedy relationship engine. 10 tests.
- **Kent vs. Boenninghausen** — Both methods side-by-side with divergence analysis. 10 tests.
- **Student Training** — Simulated patients, 4-option quizzes, progress tracking. 10 tests.
- **Clinical Vignette Quiz** — Real outcome records → difficulty-tiered teaching quizzes. 10 tests.
- **Grand Rounds** — Multi-case synthesis with common themes and markdown teaching narratives. 10 tests.
- **Flashcard SRS** — SM-2 spaced repetition for materia medica study. 10 tests.

### Patient Memory & Analytics

- **Patient Case Manager** — Hermes-session Q&A: "What did I prescribe Mrs. J. last month?" 10 tests.
- **Patient File System** — Patient CRUD, consultation tracking, chief-complaint timeline, outcome notes. 16 tests.
- **Patient Cohort Analytics** — Outcome rates, remedy timelines, symptom-success correlation. 10 tests.
- **Family Constellation** — Cross-generational remedy pattern linking. 10 tests.
- **Suppression Tracker** — Suppression history alerts with miasm-tracking tags. 10 tests.
- **Miasm Tracking** — Miasm history + suppression chain analysis. 10 tests.

### Analysis Save/Recall & Outcomes

- **Analysis Save/Recall with Versioning** — SQLite-backed snapshots with auto-incrementing versions per consultation. Baseline flagging, side-by-side comparison. 18 tests.
- **Patient Outcome Prediction** — Bayesian forecasting with rubric/keynote/history signals. 15 tests.
- **Edition Comparison** — Multi-edition rubric drift analysis with Jaccard metrics. 22 tests.
- **Remedy Freshness Tracker** — Staleness alerts, review queue, proven-source tracking. 10 tests.

### Safety, Privacy & Audit

- **Practitioner Approval Gate** — `prescriber_ack` safety gate (strict/audit/test modes). 10 tests.
- **Red Flag Detector** — Critical/urgent/advisory symptom detection with referral triggers. 10 tests.
- **PHI Scrubber** — Automated PHI detection + reversible pseudonym mapping. 10 tests.
- **Audit Trail** — SHA-256 hash chain, immutable prescription logs, licensure export. 10 tests.
- **Toxicology Layer** — Drug interaction and proving safety checks. 10 tests.

### Documentation & Workflow

- **SOAP Assembler** — LLM-powered SOAP generation from case notes. 10 tests.
- **Letter Generator** — Referral / summary / prescription letters with homeopathic rationale. 10 tests.
- **Bibliographic Engine** — Classical source registration, citation links, Vancouver/BibTeX/plain formatting, footnotes. 25 tests.
- **Cron Tasks** — Follow-up alerts, vector auto-rebuild, backup scheduling. 10 tests.

### Multi-Agent & Infrastructure

- **Subagent Orchestrator** — Case analysis plans, literature review delegation, second-opinion routing. 10 tests.
- **Model Router** — Local/cloud task routing with performance tracking and fallback chains. 10 tests.
- **Mobile API** — Mobile-responsive API layer with repertorize, search, compare, health routes. 11 tests.

### Specialized Methods

- **Cycles & Segments Engine** — Herscu method: directed cycle graphs, case-to-cycle matching, Boenninghausen generalization, Map of Hierarchy. 7 verified cycles (Stramonium, Vipera, Kali Carb, Conium, Anacardium, Bothrops, Carcinosin) + 598 auto-derived = 605 total. 39 tests.
- **Personality Engine Bridge** — 50-remedy personality system linked to OOREP remedy IDs. 10 tests.
- **Genomic Hypothesis** — SNP → remedy outcome correlation framework. 10 tests.
- **Botanical Bridge** — WHO Monograph cross-map for botanical remedy safety. 10 tests.
- **Rubric Explorer** — Kent hierarchy parent/child/sibling navigation. 10 tests.
- **Private Rubric Manager** — Practitioner-created custom rubrics. 10 tests.

### Statistics & Validation

- **Outcome Predictor Stats** (#64) — ROC/AUC curves, calibration analysis (ECE), bootstrap 95% CI on predictions. Dashboard: ROC curve + calibration plot. 14 tests.
- **Remedy Network Analysis** (#65) — Graph centrality (PageRank, betweenness, closeness), Louvain community detection, shortest path on remedy relationship graph. Dashboard: force-directed network. 13 tests.
- **Outcome Comparator** (#66) — Mann-Whitney U (pure Python), odds ratio + Wilson CI, Cohen's d, Cliff's delta between two remedies. Dashboard: comparator metric cards. 10 tests.
- **Repertory PCA** (#67) — SVD/PCA on remedy-rubric matrix, 2D/3D projections, explained variance. Dashboard: scatter plot. 10 tests.
- **Case Complexity Scorer** (#68) — Symptom entropy, coverage ratio, redundancy, specificity → composite 0–1 score. Dashboard: gauge + component bars. 5 tests.
- **Inter-Rater Reliability** (#69) — Cohen's kappa, Fleiss' kappa, ICC(3,1) for practitioner agreement. Dashboard: kappa + ICC display. 10 tests.
- **Meta-Analysis Engine** (#70) — Fixed-effect & random-effects (DerSimonian-Laird), heterogeneity metrics (Q, τ², I²), forest plot data. Dashboard: pooled rate + heterogeneity cards. 10 tests.
- **Power Analysis** (#71) — Sample size per group, achievable power, minimum detectable effect, power curve generation. Dashboard: power curve SVG. 10 tests.
- **Survival Analysis** (#72) — Kaplan-Meier estimator, median survival time, hazard ratio comparison. Dashboard: survival curve + median line. 10 tests.
- **Resampling Engine** (#73) — Bootstrap CI (1000+ iterations), permutation tests, k-fold cross-validation. Dashboard: CI interval + CV fold bars. 13 tests.

## Quick Start

```bash
# Clone
git clone https://github.com/drwjkirkpatrick-web/oorep-local-repertory.git
cd oorep-local-repertory

# Install
pip install -r requirements.txt

# Download OOREP data (~44MB compressed)
mkdir -p data
cd data
curl -L -o oorep.sql.gz "https://github.com/nondeterministic/oorep/raw/master/oorep.sql.gz"
cd ..

# Extract into JSON
python scripts/extract_oorep.py

# Run tests
pytest tests/ -v

# Use it
python -c "
from oorep import HomeopathicRepertory
rep = HomeopathicRepertory(data_dir='data')
print(rep.get_stats())
"
```

### Clipboard Example

```python
from oorep import ClipboardManager, ClipboardType

cm = ClipboardManager()
cb = cm.create_clipboard("morning_headache", ClipboardType.INCLUSION)
cm.add_rubric(cb.id, rubric_id=12345, rubric_fullpath="Head; pain; morning", remedy_weight=3)

elim = cm.create_clipboard("exclude_mercury", ClipboardType.ELIMINATION)

results = cm.analyze([cb.id, elim.id], top_n=20)
# Returns ranked remedies with classical grade scoring
```

### Master Score Example

```python
from oorep import MasterScoreEngine

engine = MasterScoreEngine()
results = engine.repertorize(
    symptoms=["anxiety", "restlessness", "thirst small quantities"],
    top_n=10,
)
# Each result includes composite score + Kent/Boenninghausen/SRP/rarity/kingdom sub-scores
```

---

## Project Structure

```
oorep-local-repertory/
├── oorep/                          # 63 Python modules
│   ├── __init__.py                 # Unified import surface (78 exports)
│   ├── homeopathic_repertory.py    # Main repertory API
│   ├── clinical_rubric_mapper.py   # Patient phrase → rubric mapping
│   ├── oorep_vector_search.py      # Local vector search
│   ├── clipboard_manager.py        # Multi-clipboard symptom collection
│   ├── master_score_engine.py      # Composite scoring
│   ├── family_grouping.py        # Kingdom/family filter & scoring
│   ├── patient_file_system.py    # Patient CRUD + consultations
│   ├── analysis_manager.py         # Analysis save/recall + versioning
│   ├── outcome_prediction.py       # Bayesian outcome forecasting
│   ├── edition_comparison.py       # Multi-edition drift analysis
│   ├── bibliographic_engine.py     # Classical citation engine
│   ├── word_wrap_search.py         # Proximity phrase search
│   ├── multi_repertory.py          # Multi-corpus search
│   ├── materia_medica_search.py    # Full-text MM TF-IDF
│   ├── analysis_methods.py         # Pluggable Kent/Boenninghausen/Boger/VES
│   ├── graphic_analysis.py         # Visual score plots
│   ├── elimination_rubrics.py     # Exclusion-based engine
│   ├── differential_diagnosis.py    # Differential ranking
│   ├── followup_comparator.py      # Follow-up remedy change
│   ├── correlation_matrix.py        # Remedy pair overlap
│   ├── keynote_autocomplete.py     # Kent keynote completion
│   ├── toxicology_layer.py         # Drug interaction safety
│   ├── miasm_tracking.py           # Miasm history
│   ├── remedy_relationships_v2.py  # Graph-based relations
│   ├── mobile_api.py               # Mobile-responsive API
│   ├── outcome_predictor_stats.py  # ROC/AUC + calibration + bootstrap
│   ├── remedy_network_analysis.py  # Graph centrality + communities
│   ├── outcome_comparator.py       # Mann-Whitney + odds ratio + Cohen's d
│   ├── repertory_pca.py            # SVD/PCA on remedy-rubric matrix
│   ├── case_complexity_scorer.py   # Symptom entropy + coverage gaps
│   ├── inter_rater_reliability.py  # Cohen's/Fleiss' kappa + ICC
│   ├── meta_analysis_engine.py     # Fixed/random-effects meta-analysis
│   ├── power_analysis.py           # Sample size + power curves
│   ├── survival_analysis.py        # Kaplan-Meier + hazard ratios
│   ├── resampling_engine.py        # Bootstrap + permutation + CV
│   └── ...                         # 50+ additional modules
├── tests/                          # 746 pytest tests across 49 test files
├── oorep-case-portal/              # Next.js Clinical Mission Control
├── scripts/                        # Data extraction, builders, runners
├── data/                           # OOREP JSON + indexes (gitignored)
│   └── cycles/                     # Herscu cycle JSON files
└── README.md / LICENSE / pyproject.toml
```

---

## Testing

```bash
# Core modules (fast)
pytest tests/test_clipboard_manager.py tests/test_grade_mode.py -v

# Search modules
pytest tests/test_word_wrap_search.py tests/test_multi_repertory.py -v

# Analysis modules
pytest tests/test_master_score_engine.py tests/test_analysis_methods.py -v

# Patient / file system
pytest tests/test_patient_file_system.py tests/test_analysis_manager.py -v

# Full suite (Jetson ~3-5 minutes with timeouts)
pytest tests/ --timeout=45 -q
```

---

## Clinical Mission Control Dashboard

Next.js practitioner-facing dashboard with:

- **25 visualization components** — cycle rings, coverage heatmaps, Venn diagrams, phantom gauges, differential radar, outcome sparklines, potency waterfalls, miasm donuts, kingdom clouds, confidence strips, family graphs, layer timelines, Sankey flows, rubric trees, grand rounds panels, **ROC curves, network graphs, comparator cards, PCA scatters, complexity gauges, kappa displays, forest plots, power curves, Kaplan-Meier curves, resampling panels**
- **Live API data layer** — pulls from OOREP backend via Next.js routes
- **Click-through drill-down** — every remedy/rubric clickable to detail pages
- **Pipeline builder** — drag-and-drop module nodes for reusable SOPs

---

## Clinical Disclaimer

This software is for **educational and reference purposes** and is **not intended to diagnose, treat, cure, or prevent any disease**. It supports licensed practitioners in clinical reasoning, not replaces it. Always use professional judgment. Ensure active malpractice insurance and compliance with your jurisdiction's regulations.

**Practitioner override is mandatory** — all remedy recommendations require explicit `prescriber_ack` before being recorded.

---

## Attribution

### Cycles & Segments Method
Software encoding of Dr. Paul Herscu and Dr. Amy Rothenberg's clinical method (NESH). Built-in cycles: Stramonium, Vipera, Kali Carbonicum, Conium Maculatum, Anacardium, Bothrops Lanceolatus, Carcinosin. See *Stramonium: With an Introduction to Analysis Using Cycles and Segments* (NESH Press, 1996).

### OOREP Data
Open Online Repertory by Andreas Bauer, licensed under GPL v3.

---

## License

GPL v3 — same as upstream OOREP. See [LICENSE](LICENSE).

---

*Built with care for the homeopathic community. Open source, open data, open minds.*
