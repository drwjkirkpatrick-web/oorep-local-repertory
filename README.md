# OOREP Local Homeopathic Repertory

A **fast, offline, open-source homeopathic repertory** built on [OOREP](https://www.oorep.com/) (Open Online Repertory) data, enhanced with modern multi-layer search, clinical phrase mapping, remedy outcome tracking, and **41 specialized modules** — from remedy relationships and potency guidance to audit trails, grand rounds synthesis, and the Clinical Mission Control dashboard.

> **Version:** 3.4 | **License:** GPL v3 | **Data:** 2,432 remedies × 143,408 rubrics × 1.36M remedy-grade links | **Modules:** 41 Python modules + Clinical Mission Control (Next.js dashboard with 15 visualization components + live API data + click-through drill-down) | **Tests:** 271 passing (Python) + portal smoke tests | **Coverage:** **59 of 59 (100%)** LLM-Hermes benefits implemented

---

## Why Build Your Own Repertory?

- **No subscriptions** — free forever, your data stays yours
- **No cloud dependency** — works offline, even in remote clinic settings
- **No vendor lock-in** — add custom rubrics, remedies, or repertory sources freely
- **Clinical time-savers** — intelligent search layers surface the simillimum in seconds, not minutes
- **Practice intelligence** — track outcomes, family patterns, suppression history, build your own evidence base
- **Safety by design** — red-flag detection, practitioner approval gates, PHI scrubbing, immutable audit trails
- **Teaching + training** — simulated patients, clinical vignette quizzes, grand rounds synthesis
- **Practitioner-owned** — built for integration into your existing workflow (Hermes Agent, Next.js portal, or plain Python)

---

## Quick Start

```bash
# Clone
git clone https://github.com/drwjkirkpatrick-web/oorep-local-repertory.git
cd oorep-local-repertory

# Install dependencies
pip install -r requirements.txt

# Download OOREP data (~44MB compressed)
mkdir -p data
cd data
curl -L -o oorep.sql.gz "https://github.com/nondeterministic/oorep/raw/master/oorep.sql.gz"
cd ..

# Extract into JSON
python scripts/extract_oorep.py

# Run the full test suite
pytest tests/ -v

# Use it
python -c "
from oorep import HomeopathicRepertory
rep = HomeopathicRepertory(data_dir='data')
print(rep.get_stats())
"
```

---

## Core Features (V1.x → Still Here)

### 1. Fully Local & Offline
No API calls, no cloud servers, no subscription gates. Your repertory lives on your machine.

### 2. Memory-Safe Data Extraction
The 1.36M remedy-rubric links are processed in **batched streaming passes** (150K links per batch) to avoid memory exhaustion. Small systems handle it fine.

### 3. Lightning-Fast Lexical Search
Instant token-matched rubric lookup. Type `"thirst small sips"` and see Kent rubrics in milliseconds.

### 4. Local Vector Semantic Search
Offline random-projection vectors (384-dim, float16) let you search by **meaning**, not just exact words. No API keys. No fees.

### 5. Hybrid Retrieval Fusion
Combines lexical precision + vector semantic reach + token overlap into one ranked candidate list.

### 6. Clinical Rubric Mapper
Patient says `"can't sleep after 3am"` → system expands to sleep/sleeplessness/waking/after midnight. You review before scoring.

### 7. Classical Grade-Only Scoring
Retrieval finds rubrics; **Kent grades rank remedies**. Semantic similarity never distorts classical repertory arithmetic.

### 8. Multi-Symptom Repertorization
Enter a full symptom set, get a ranked remedy table scored by summing classical grades across matched rubrics.

### 9. Rare Remedy Triangulation
Cross-reference confirmed rubrics against lesser-known remedies. Surface the unusual simillimum broad repertories bury.

### 10. Remedy Outcome Tracking
Log prescriptions and follow-ups (cured, improved, unchanged, worsened) in SQLite. Build your own evidence base.

### 11. LLM-Powered SOAP Case Intake
Paste a full SOAP note and a large language model parses the Subjective narrative into structured symptoms, filtering normal vitals and exam boilerplate, and preserving contextual meaning.

### 12. Intelligent Fuzzy Rubric Matching
After the LLM extracts symptoms, it performs intelligent fuzzy matching against 143,408 rubrics — finding semantically close equivalents even when wording differs.

---

## New in V2.0: Advanced Practitioner Modules (29 Modules + 12 Core = 41 Total)

### Differential Diagnosis & Selection

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `RemedyComparator` | #3 | Multi-remedy overlap, divergence, Jaccard analysis |
| `SRPDetector` | #13 | Strange-Rare-Peculiar keyword detection with weighted scoring |
| `PhantomRubricAnalyzer` | #27 | Gini coefficient + entropy flags for low-differentiation rubrics |
| `RubricCooccurrenceEngine` | #24 | Mine remedy pairs, polycrest clusters, association rules |
| `EliminationAnalyzer` | #15 | "What symptom rules out X?" exclusion logic |
| `PotencyGuidance` | #16 | Classical potency ladder + remedy-specific profiles |
| `AcuteChronicLayer` | #17 | Tag acute vs. chronic symptoms, layer-separate repertorization |

### Repertory Navigation & Customization

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `RubricExplorer` | #2 | Kent hierarchy parent/child navigation, sibling traversal |
| `PrivateRubricManager` | #41 | Practitioner-created custom rubrics with merge-to-repertorization |

### Patient Memory & Analytics

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `PatientCaseManager` | #7–11 | Hermes-session Q&A: "What did I prescribe Mrs. J. last month?" |
| `PatientCohortAnalytics` | #26 | Outcome rates, remedy timelines, symptom-success correlation |
| `FamilyConstellation` | #10 | Family remedy patterns, cross-generational linking |
| `SuppressionTracker` | #11 | Suppression history alerts and miasm-tracking tags |

### Safety, Privacy & Audit

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `PractitionerApprovalGate` | #50 | `prescriber_ack` safety gate (strict/audit/test modes) |
| `RedFlagDetector` | #51 | Critical/urgent/advisory symptom detection with referral triggers |
| `PHIScrubber` | #49 | Automated PHI detection + reversible pseudonym mapping |
| `AuditTrail` | #32, #53 | SHA-256 hash chain, immutable prescription logs, licensure export |

### Materia Medica & Learning

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `RemedyRelationships` | #4, #19–21 | Complementary, antidotal, inimical, antidote classical tables |
| `KentVsBoenninghausen` | #46 | Both methods side-by-side, divergence analysis, auto-recommendation |
| `PersonalityEngineBridge` | #47, #56 | Link 50-remedy personality system to OOREP remedy IDs |
| `CyclesAndSegmentsEngine` | #59 | Herscu cycle/segment remedy analysis: directed graphs, case matching, Boenninghausen generalization, Map of Hierarchy — now **integrated into every repertorization** as `cycle_analysis` with configurable segment/coverage thresholds |

### Teaching & Training

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `StudentTraining` | #38 | Simulated patients, 4-option quizzes, progress tracking |
| `ClinicalVignetteQuiz` | #45 | Real outcome records → difficulty-tiered teaching quizzes |
| `GrandRounds` | #48 | Multi-case synthesis, common themes, markdown teaching narratives |

### Documentation & Workflow

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `SOAPAssembler` | #31 | Template-based SOAP generation from case notes |
| `LetterGenerator` | #34 | Referral / summary / prescription letters with homeopathic rationale |
| `RemedyFreshnessTracker` | #39 | Staleness alerts, review queue, proven-source tracking |
| `RubricGapAnalyzer` | #40 | Coverage gap detection, rubric quality scoring, new-rubric suggestions |

### Multi-Agent & Infrastructure

| Module | Benefit | What It Does |
|--------|---------|-------------|
| `SubagentOrchestrator` | #35–37 | Case analysis plan templates, literature review delegation, second-opinion routing |
| `ModelRouter` | #57 | Local/cloud task routing, performance tracking, fallback chains |

---

## Usage Examples

### Basic Repertorization

```python
from oorep import HomeopathicRepertory

rep = HomeopathicRepertory(data_dir="data")

# Single symptom lookup
results = rep.search_rubrics("headache morning", limit=10)

# Multi-symptom repertorization (uses Clinical Mapper by default)
results = rep.repertorize([
    "head pain morning",
    "thirst small quantities",
    "anxiety health"
], top_n=20)

# Results are ranked by classical Kent grade sums
for r in results[:5]:
    print(f"{r['abbrev']:12} {r['name']:25} score={r['score']} matches={r['match_count']}")
```

### Multi-Remedy Comparison (Benefit #3)

```python
from oorep import RemedyComparator

cmp = RemedyComparator(rep)

# Overlap, exclusive rubrics, and Jaccard similarity
result = cmp.compare("Puls.", "Ars.")
print(result["overlap"])
print(result["exclusive_a"])

# Pairwise comparison across a remedy list
pairwise = cmp.pairwise_compare(["Puls.", "Ars.", "Nux-v."])
```

### SRP Detection (Benefit #13)

```python
from oorep import SRPDetector

srp = SRPDetector()
case_rubrics = [
    {"rubric_id": "1", "fullpath": "Mind; anxiety, health, about"},
    {"rubric_id": "2", "fullpath": "Mind; weeping, inconsolable, consolation agg."},
]

flagged = srp.analyze(case_rubrics)
# Returns: SRP flag, severity, pattern type, boost multiplier
# Weeping with consolation aggravation → paradoxical modality → 2× boost
```

### Phantom Rubric Analysis (Benefit #27)

```python
from oorep import PhantomRubricAnalyzer

pha = PhantomRubricAnalyzer(rep)

# Find rubrics where top 3 remedies dominate >90% of grade mass
phantoms = pha.find_phantoms()
# Gini >0.85 or HHI >0.30 flagged as "concentrated"
```

### Co-occurrence Mining (Benefit #24)

```python
from oorep import RubricCooccurrenceEngine

cooc = RubricCooccurrenceEngine(rep)

# Top remedy pairs by Jaccard overlap
pairs = cooc.top_pairs(min_cooccurrence=50, limit=20)

# Which remedies cluster with Pulsatilla?
cluster = cooc.cluster_for_remedy("Puls.", min_cooccurrence=30)
```

### Patient Case Memory (Benefit #7–11)

```python
from oorep import PatientCaseManager

mgr = PatientCaseManager()

# During a session — query your own practice database
mgr.ask_hermes("What did I prescribe Mrs. J. last month?")
# → {"answer_text": "Mrs. J. was prescribed Pulsatilla 30C on 2025-03-15..."}

mgr.ask_hermes("Which of my patients have taken Arsenicum?")
# → {"answer_text": "3 patients: Mrs. J. (2025-01), ...", "patients": [...]}
```

### Practitioner Approval Gate (Benefit #50)

```python
from oorep import PractitionerApprovalGate

gate = PractitionerApprovalGate(mode="strict", db_path="./gate.db")
recommendation = {"remedy": "Arsenicum Album", "potency": "30C", "rationale": "..."}

outcome = gate.evaluate(recommendation, context={})
# If approved: status="approved", recommendation preserved
# If denied: status="denied", recommendation cleared

# Audit log is immutable — every gate decision logged with SHA-256 chain
```

### Red-Flag Detection (Benefit #51)

```python
from oorep import RedFlagDetector

rfd = RedFlagDetector()

report = rfd.analyze_patient_symptoms([
    {"description": "chest pain radiating to left arm"},
    {"description": "shortness of breath on exertion"},
])

# → {"status": "critical", "flags": [...], "referral_recommended": True}
```

### Kent vs. Boenninghausen (Benefit #46)

```python
from oorep import KentVsBoenninghausen

kvb = KentVsBoenninghausen(rep)

result = kvb.analyze_case(rubrics=["Mind; anxiety", "Head; pain, morning"], symptoms=["anxiety", "headache"])

# → {"kent_method": {...}, "boenninghausen_method": {...}, "auto_recommendation": "kent", "divergence_analysis": [...]}
```

### Remedy Relationships (Benefit #4, #19–21)

```python
from oorep import RemedyRelationships

rel = RemedyRelationships(db_path="./relationships.db")
rel.load_classical_data()

# Classical relationships
rel.get_relationships("Puls.")        # → complementary, antidotal, inimical
rel.check_compatibility("Puls.", "Nux-v.")  # → status + classical reference
rel.find_antidotes("Ars.")           # → ["Nux-v.", "Camph.", ...]
```

### Cycles & Segments (Benefit #59)

```python
from oorep import CyclesAndSegmentsEngine

engine = CyclesAndSegmentsEngine()

# Retrieve a remedy's full cycle
stram = engine.get_cycle("Stramonium")
print(stram.sentence)          # One-sentence essence
print(stram.transition_pairs()) # Directed segment flow

# Match patient symptoms to the cycle
case = ["fear of death", "violent outbursts", "wants to be alone"]
match = engine.match_case_to_cycle(case, stram)
print(match["coverage"])       # 0.0–1.0 symptom coverage
print(match["matched_segments"])

# Rank all registered cycles against a case
suggestions = engine.suggest_cycles_for_case(case, limit=5)

# Apply Boenninghausen-style generalization
gen = engine.generalize_symptom("fear of death",
                                 stram.segment_by_name("Fear of death or injury"))

# View pediatric Map of Hierarchy
hierarchy = engine.get_map_of_hierarchy()
```

**Built-in cycles** (verified from Herscu publications):
- **Stramonium** (6 segments, phase 4) — canonical prototype
- **Vipera** (5 segments, phase 4) — NEJH Vol 7 #1
- **Kali Carbonicum** (6 segments, phase 3) — NEJH Vol 5 #2
- **Conium Maculatum** (5 segments, phase 4) — NEJH Vol 6 #1
- **Anacardium** (5 segments, phase 3) — NEJH Vol 5 #3
- **Bothrops Lanceolatus** (5 segments, phase 4) — NEJH Vol 8 #2
- **Carcinosin** (6 segments, phase 2) — NEJH Vol 5 #4

**Builder tool:**
```bash
python scripts/build_cycle.py --interactive    # Build a new cycle
python scripts/build_cycle.py --validate-all   # Check all JSON files
python scripts/build_cycle.py --list           # Show all cycles
```

### Cycles & Segments — Automatic in Every Repertorization

Since v3.0+, `HomeopathicRepertory.repertorize()` automatically enriches each top remedy with cycle/segment analysis when `with_cycles=True` (the default).  Every result dict gains a `cycle_analysis` key:

```python
from oorep import HomeopathicRepertory

rep = HomeopathicRepertory(data_dir="data")

results = rep.repertorize(
    ["fear of death", "violent outbursts", "wants to be alone"],
    top_n=10,
    with_cycles=True,          # default
    cycle_min_segments=2,      # ≥2 segments must match
    cycle_min_coverage=0.20,   # ≥20% of the cycle's segments
)

for r in results:
    ca = r["cycle_analysis"]
    print(f"{r['abbrev']}  score={r['score']}  cycle={ca['remedy_cycle']}  "
          f"segments={ca['segments_matched_count']}/{ca['total_segments']}  "
          f"meets_threshold={ca['meets_threshold']}")
    if ca["meets_threshold"]:
        print("  → Segment matches:", ", ".join(ca["segment_matches"]))
        print("  → Essence:", ca["cycle_sentence"])
```

**Threshold logic:** A remedy is flagged `meets_threshold=True` only when:
1. It has a registered cycle (7 verified + 598 auto-derived = **605 total**), **and**
2. The case symptoms hit at least `cycle_min_segments` distinct segments (default **2**), **and**
3. The segment coverage ratio is at least `cycle_min_coverage` (default **20%**).

This lets classical grade scoring (Kent arithmetic) remain primary, while Cycles & Segments provides a **second-opinion structural filter** — surfacing remedies whose dynamic pattern genuinely matches the case, not just individual rubric grades.

### Student Training — Simulated Patients (Benefit #38)

```python
from oorep import StudentTraining

st = StudentTraining(db_path="./training.db")

# Generate a simulated case
case = st.generate_simulated_patient()
# → {"case_id": "...", "correct_remedy": "Arsenicum", "rubrics": [...], "chief_complaint": "..."}

# Build a quiz from it
quiz = st.generate_quiz([case])
# → 4-option multiple choice with rationale, explanation, weak-area tracking

# Evaluate the answer
result = st.evaluate_answer(case["case_id"], "Arsenicum")
# → {"correct": True, "explanation": "...", "suggested_rubrics": [...]}
```

### Grand Rounds (Benefit #48)

```python
from oorep import GrandRounds

gr = GrandRounds()

# Synthesize cases from your practice database
cases = gr.synthesize_cases(patient_ids=["A", "B", "C"], date_range=("2025-01-01", "2025-06-01"))

# Extract common themes
themes = gr.find_common_themes(cases)

# Generate teaching narrative
narrative = gr.generate_teaching_narrative(cases)
# → Markdown grand rounds summary with top remedies, rubric clusters, outcome distribution
```

### Audit Trail (Benefit #32, #53)

```python
from oorep import AuditTrail

audit = AuditTrail(db_path="./audit.db")
audit.initialize()

# Log every prescription with immutable hash chain
entry = audit.log_prescription_recorded(
    record_id="rx-001",
    record_type="prescription",
    practitioner_id="dr-kirkpatrick",
    patient_pseudonym="patient-alpha",
    action="recorded",
    details={"remedy": "Pulsatilla", "potency": "30C"},
)

# Verify chain integrity
integrity = audit.verify_chain()
# → {"total_records": N, "broken_at": None, "status": "valid"}

# Export for licensure review
report = audit.export_for_review(practitioner_id="dr-kirkpatrick")
```

---

## Project Structure

```
oorep-local-repertory/
├── oorep/                          # Core Python package (41 modules)
│   ├── __init__.py                 # Unified import surface
│   ├── homeopathic_repertory.py    # Main repertory API
│   ├── clinical_rubric_mapper.py   # Patient phrase → rubric mapping
│   ├── oorep_vector_search.py      # Local vector search
│   ├── rare_remedy_triangulator.py # Unusual remedy discovery
│   ├── remedy_comparator.py        # Multi-remedy comparison (#3)
│   ├── srp_detector.py           # SRP keyword scoring (#13)
│   ├── phantom_rubric_analyzer.py # Differentiation analysis (#27)
│   ├── rubric_cooccurrence.py     # Remedy pair mining (#24)
│   ├── rubric_explorer.py         # Kent hierarchy navigation (#2)
│   ├── private_rubrics.py         # Custom practitioner rubrics (#41)
│   ├── patient_case_manager.py    # Hermes session case Q&A (#7-11)
│   ├── patient_cohort_analytics.py # SQL outcome analytics (#26)
│   ├── family_constellation.py    # Family remedy patterns (#10)
│   ├── suppression_tracker.py     # Suppression history (#11)
│   ├── practitioner_approval_gate.py # Safety gate (#50)
│   ├── red_flag_detector.py       # Critical symptom gate (#51)
│   ├── phi_scrubber.py           # PHI detection + pseudonyms (#49)
│   ├── audit_trail.py            # Immutable audit chain (#32, #53)
│   ├── remedy_relationships.py    # Classical comp/antidotal DB (#4, #19-21)
│   ├── elimination_analysis.py    # Exclusion logic (#15)
│   ├── potency_guidance.py        # Potency ladder (#16)
│   ├── acute_chronic_layer.py    # Layer separation (#17)
│   ├── kent_vs_boenninghausen.py  # Method comparison (#46)
│   ├── personality_engine_bridge.py # Personality ↔ OOREP bridge (#47, #56)
│   ├── cycles_and_segments.py       # Herscu cycle/segment analysis (#59)
│   ├── student_training.py        # Simulated patients + quizzes (#38)
│   ├── clinical_vignette_quiz.py  # Real outcome quiz generator (#45)
│   ├── grand_rounds.py            # Multi-case synthesis (#48)
│   ├── soap_assembler.py          # SOAP generation (#31)
│   ├── letter_generator.py        # Document generation (#34)
│   ├── remedy_freshness_tracker.py # Staleness alerts (#39)
│   ├── rubric_gap_analyzer.py    # Gap detection (#40)
│   ├── subagent_orchestrator.py  # Case analysis plans (#35-37)
│   ├── model_router.py           # Local/cloud routing (#57)
│   ├── materia_medica.py         # Full-text proving DB (#18, #21)
│   ├── kingdom_taxonomy.py       # Mineral/Plant/Animal tags (#22)
│   ├── botanical_bridge.py       # WHO Monograph cross-map (#28)
│   ├── genomic_hypothesis.py     # SNP → remedy outcomes (#29)
│   ├── flashcard_srs.py          # SM-2 spaced repetition (#44)
│   └── cron_tasks.py             # Follow-ups, rebuild, backup (#33, #42, #43)
├── scripts/
│   ├── extract_oorep.py          # Extract OOREP SQL → JSON
│   ├── remedy_feedback.py        # Prescription outcome tracking
│   └── build_cycle.py            # Cycle & Segment builder / validator
├── tests/                        # 271 pytest tests
│   ├── conftest.py
│   ├── test_clinical_rubric_mapper.py
│   ├── test_hybrid_repertory.py
│   ├── test_new_benefits.py      # Phase 1-2 module tests
│   ├── test_batch_a.py           # Phase 3 batch A
│   ├── test_batch_b.py           # Phase 3 batch B
│   ├── test_batch_c.py           # Phase 3 batch C
│   ├── test_batch_d.py           # Phase 4 batch D
│   └── test_batch_e.py           # Phase 5 batch E (final benefits)
│   └── test_cycles_and_segments.py  # Herscu cycle/segment module (#59)
│   └── test_cycles_in_repertorization.py  # Cycle enrichment inside repertorize()
├── examples/
│   └── basic_usage.py            # Copy-paste starter code
├── data/                         # Extracted OOREP JSON (gitignored)
│   ├── cycles/                   # Herscu Cycles & Segments JSON files
│   │   ├── vipera.json
│   │   ├── kali_carbonicum.json
│   │   ├── conium_maculatum.json
│   │   ├── anacardium.json
│   │   ├── bothrops_lanceolatus.json
│   │   └── carcinosin.json
│   ├── remedies.json
│   ├── rubrics.json
│   ├── rubric_search_index.json
│   ├── rubric_to_remedies.json
│   └── indexes/                  # Generated vector artifacts
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
└── OOREP_Gap_Analysis.md        # Full 59-benefit gap audit + build phases
```

---

## Attribution

### Cycles & Segments Method
The **Cycles & Segments** analysis module in this project is a software encoding of the clinical method developed by **Dr. Paul Herscu** and **Dr. Amy Rothenberg**, co-founders and leaders of the **New England School of Homeopathy (NESH)**. The method — that disease is a unit composed of recurring dynamic segments through which the vital force expresses itself — was articulated by Dr. Herscu in *Stramonium: With an Introduction to Analysis Using Cycles and Segments* (NESH Press, 1996) and in the *New England Journal of Homeopathy* (cycles of Vipera, Kali carbonicum, Conium maculatum, Anacardium, Bothrops lanceolatus, and Carcinosin).

All verified cycle descriptions, segment names, and one-sentence remedy essences in the built-in canonical cycles are derived from these published works. The software implementation is independent and does not substitute for study of the original texts or NESH curriculum.

- **NESH:** https://nesh.com
- **Herscu, P.** (1996). *Stramonium: With an Introduction to Analysis Using Cycles and Segments.* NESH Press. ISBN 978-0965400404.

### OOREP Data
This project uses the **OOREP (Open Online Repertory)** database by Andreas Bauer, licensed under GPL v3.

---

## Data Source

This project uses the **OOREP (Open Online Repertory)** database by Andreas Bauer, licensed under GPL v3.

| Repertory | Language | Rows |
|-----------|----------|------|
| Kent (kent-de) | German | 74,785 rubrics |
| Repertorium Publicum | English/Generic | 68,623 rubrics |
| **Total** | | **143,408 rubrics** |

**Download:** `curl -L -o oorep.sql.gz https://github.com/nondeterministic/oorep/raw/master/oorep.sql.gz`

---

## Requirements

- Python 3.10+
- `numpy` (for vector search)
- `pytest` (for test suite)
- ~120MB disk for extracted JSON data
- ~2MB for vector index (384-dim float16)

---

## Testing

```bash
pip install pytest
pytest tests/ -v
```

Full suite: **271 tests** covering all 41 modules.

---

## Gap Analysis & Roadmap

See `OOREP_Gap_Analysis.md` for the complete 58-benefit audit with build phases.

**Coverage summary:**
- **59 of 59 benefits** implemented (**100%**)
- **40 Python modules** built
- **271/271 tests** passing

**Phase 5 Complete:** Materia medica proving texts, kingdom taxonomy (75-remedy seed), botanical bridge (WHO Monograph), genomic SNP hypothesis (14-SNP seed), flashcard spaced repetition, cron automation (follow-up alerts, vector auto-rebuild, GitHub backup), and **Cycles & Segments enrichment in every repertorization** are all built and tested.

All remaining items are seeded with PD-compatible classical data and ready for expansion with your own corpus.

---

## 59 Benefits — Ordered List (1–59)

All 59 Hermes-Agent-identified benefits for clinical repertory software are now implemented.

### V1 Core (Benefits 1–12)
1. **Fully Local & Offline** — No API calls, no subscriptions, no cloud lock-in
2. **Rubric Hierarchy Navigation** — Kent parent/child/sibling traversal with `RubricExplorer`
3. **Remedy Comparator** — Multi-remedy overlap, divergence, and Jaccard similarity analysis
4. **Remedy Relationships** — Classical complementary, antidotal, inimical, antidote tables
5. **Lexical + Hybrid Search** — Token-matched rubric lookup + vector semantic reach + overlap fusion
6. **Abbreviation Decoding** — Robust remedy abbreviation resolution with collision handling
7. **Patient Case Memory** — SQLite-backed case tracking with Hermes-session Q&A queries
8. **Clinical Rubric Mapper** — Patient phrase normalization and synonym expansion to Kent rubrics
9. **Multi-Symptom Repertorization** — Classical grade-based scoring across matched rubrics
10. **Family Constellation** — Cross-generational remedy pattern linking and inherited suppression chains
11. **Suppression Tracker** — Suppression history alerts with miasm-tracking tags
12. **Memory-Safe Data Extraction** — Batched streaming (150K links/batch) for small-system compatibility

### V2 Differential & Analysis (Benefits 13–28)
13. **SRP Detector** — Strange-Rare-Peculiar keyword detection with weighted scoring
14. **Keynote Triangulation** — Scarcity + pattern-based unusual remedy surfacing
15. **Elimination Analyzer** — "What symptom rules out X?" exclusion logic
16. **Potency Guidance** — Classical potency ladder with remedy-specific profiles
17. **Acute / Chronic Layer Separation** — Layer-tagging and layer-separate repertorization
18. **Materia Medica Proving DB** — Full-text proving text lookup with source attribution
19. **Remedy Relationships Tutoring** — Classical relationship explanations with source references
20. **Source Material Tracing** — Proving and author attribution in data schema
21. **Comparative Materia Medica** — Side-by-side remedy proving text comparison
22. **Kingdom Taxonomy** — Mineral / Plant / Animal tags with family cross-references
23. **Clinical Tip Extraction** — Outcome-note NLP mining for success-pattern discovery
24. **Rubric Co-occurrence Engine** — Remedy pair mining, polycrest clusters, association rules
25. **Severity-Weighted Trending** — Time-series analysis of rubric importance across cases
26. **Patient Cohort Analytics** — Outcome rates, remedy timelines, symptom-success correlation
27. **Phantom Rubric Analyzer** — Gini + entropy flags for low-differentiation rubrics
28. **Botanical Bridge** — WHO Monograph cross-map for botanical remedy safety data

### V3 Advanced Modules (Benefits 29–53)
29. **Genomic Hypothesis** — SNP → remedy outcome correlation mining
30. **Voice-to-Rubric Intake** — Blue Snowball STT → rubric mapper pipeline
31. **SOAP Assembler** — LLM-powered SOAP generation from conversational case notes
32. **Audit Trail** — SHA-256 hash chain, immutable prescription logs
33. **Cron Tasks** — Follow-up alerts, vector auto-rebuild, GitHub backup scheduling
34. **Letter Generator** — Referral / summary / prescription letters with homeopathic rationale
35. **Subagent Orchestrator** — Case analysis plan templates and literature-review delegation
36. **Literature-Review Agent** — PubMed / homeopathic journal monitoring delegation
37. **Case-Supervision Agent** — Second-opinion re-repertorization routing
38. **Student Training** — Simulated patients, 4-option quizzes, progress tracking
39. **Remedy Freshness Tracker** — Staleness alerts, review queue, proven-source tracking
40. **Rubric Gap Analyzer** — Coverage gap detection, rubric quality scoring, new-rubric suggestions
41. **Private Rubric Manager** — Practitioner-created custom rubrics with merge-to-repertorization
42. **Vector Index Rebalancing** — Automated vector index rebuild on data updates
43. **Backup & Sync Verification** — Encrypted SQLite + JSON snapshots with integrity checks
44. **Flashcard SRS** — SM-2 spaced repetition for materia medica study
45. **Clinical Vignette Quiz** — Real outcome records → difficulty-tiered teaching quizzes
46. **Kent vs. Boenninghausen** — Both methods side-by-side with divergence analysis
47. **Personality Engine Bridge** — 50-remedy personality system linked to OOREP remedy IDs
48. **Grand Rounds** — Multi-case synthesis with common themes and markdown teaching narratives
49. **PHI Scrubber** — Automated PHI detection + reversible pseudonym mapping
50. **Practitioner Approval Gate** — `prescriber_ack` safety gate (strict/audit/test modes)
51. **Red Flag Detector** — Critical / urgent / advisory symptom detection with referral triggers
52. **Contraindicated Remedy Alerts** — Remedy-family reaction history tracking
53. **Licensure Export** — Audit-grade immutable logs formatted for regulatory review

### V4 Cycles, Dashboard & Visual Intelligence (Benefits 54–59)
54. **Offline Resilience** — Full core functionality without network connectivity
55. **Skill Accumulation** — OOREP-specific Hermes workflow skills auto-generated from usage
56. **Personality-Aware Reasoning** — Remedy narrative matched to patient persona via 50-remedy system
57. **Model Router** — Local/cloud task routing with performance tracking and fallback chains
58. **Cross-Reference Repertory Editions** — Multi-edition comparison framework (extensible)
59. **Cycles & Segments Engine** — Herscu method: directed cycle graphs, case-to-cycle matching, Boenninghausen generalization, Map of Hierarchy — now with **15 dashboard visualizations, live API data layer, and click-through drill-down**

---

## Clinical Mission Control Dashboard (v3.4)

The Next.js **OORep Case Portal** ships with a practitioner-facing **Clinical Mission Control Dashboard** — a unified cockpit for the OOREP module suite.

### Dashboard Routes
- **`/dashboard`** — Module picker sidebar + responsive canvas + live data panels + report action bar
- **`/dashboard/pipeline`** — Visual pipeline builder (React-Flow node graph) for reusable SOPs

### Live API Data Layer
All visualizations now pull from live OOREP backend data via Next.js API routes:
- `GET /api/rubrics/[id]` — Rubric metadata + top 50 remedies by classical grade
- `GET /api/rubrics?q=query` — Lexical rubric search (top 20 matches)
- `GET /api/remedies/[abbrev]` — Remedy profile with classification metadata
- `POST /api/admin/repertorize` — Classical grade-ranked remedy list with automatic `cycle_analysis` enrichment

### Dashboard Architecture
- **Module Discovery API** (`/api/portal/modules`) — Serves all 41 module definitions with metadata, routes, and I/O contracts
- **Module Picker Sidebar** — Organized by 8 clinical categories; draggable toggles; search by benefit number or name
- **Dashboard Canvas** — Responsive grid of visualization panels; each panel shows status, JSON preview, and "Include in final report" checkbox
- **Run Active Modules** — Executes enabled modules sequentially via their API routes
- **Report Action Bar** — Exports a Markdown report with included module outputs + PDF generation

### 15 Visualization Components (v3.4)

| # | Visualization | Level | What It Shows | Click-Through |
|---|-------------|-------|---------------|---------------|
| 1 | **Circular Cycle Rings** | BEGINNER | Polar donut per top remedy: angular segments = cycle phases; fill brightness = segment match intensity; center dot = threshold met | Remedy detail |
| 2 | **Remedy Coverage Heatmap** | BEGINNER | Rubric × remedy grade intensity matrix; color = Kent grade (1–4); tooltip shows full path | Rubric detail + Remedy detail |
| 3 | **Comparative Venn Diagram** | BEGINNER | Shared vs unique differentiating rubrics across top-3 remedies; overlap count labels | Remedy detail + Rubric detail |
| 4 | **Phantom Rubric Risk Gauge** | BEGINNER | Speedometer: concentration of low-confidence rubrics; needle position = phantom fraction | — |
| 5 | **Differential Remedy Radar** | INTERMEDIATE | 7-axis spider chart: Repertory Score, Cycle Coverage, SRP Density, Rubric Reliability, Layer Alignment, Method Agreement, Outcome History | Remedy detail |
| 6 | **Outcome Trajectory Sparklines** | INTERMEDIATE | Herscu-score temporal lines per remedy (-4 to +4); month-by-month outcomes; overlapping trajectories | Remedy detail (legend) |
| 7 | **Potency Ladder Waterfall** | INTERMEDIATE | Vertical cascading potency rungs (6C → 200C); tapering blocks; rationale per step | — |
| 8 | **Miasm Donut Overlay** | INTERMEDIATE | Psora / Sycosis / Syphilis / Tubercular / Cancer wedge weights; dashed patient-miasm target ring | — |
| 9 | **Kingdom Morphology Cloud** | INTERMEDIATE | Tag-cloud of Plant / Mineral / Animal case-language affinity; font size = word frequency | — |
| 10 | **Rubric Confidence Interval Strip** | ADVANCED | Horizontal bars per rubric: green = reliable (confidence >0.75 + low grade-1 density), amber = moderate; error caps show lexical-vs-vector variance | Rubric detail |
| 11 | **Family Constellation Graph** | ADVANCED | Force-directed nodes: patient + family members with remedy labels; edge thickness = shared pattern weight | Remedy detail (node) |
| 12 | **Layer Timeline Ribbon** | ADVANCED | Gantt-style suppression / acute / constitutional event timeline; color-coded layers (red=physical, amber=acute, purple=chronic, green=constitutional) | — |
| 13 | **Repertorization Sankey Flow** | BEGINNER–INTERMEDIATE | Symptom nodes → remedy nodes with curved Bézier paths; thickness ∝ score weight per symptom; green paths = cycle threshold met | Remedy detail |
| 14 | **Rubric Explorer Tree** | INTERMEDIATE | Kent hierarchy parent/child navigation with sibling traversal | — |
| 15 | **Grand Rounds Synthesis Panel** | ADVANCED | Multi-case markdown narrative with top remedies, rubric clusters, outcome distribution | — |

### New in v3.4: Click-Through Drill-Down
Every visualization that displays a **remedy abbreviation** or **rubric ID** is now clickable:
- **Remedy click** → `/remedies/[abbrev]` (profile + classification)
- **Rubric click** → `/rubrics/[id]` (metadata + top 50 remedy grade table)

11 of 15 components support live click-through navigation. The remaining 4 (Phantom Gauge, Potency Ladder, Miasm Donut, Layer Timeline) operate at aggregate/abstraction levels with no discrete remedy/rubric to route to.

### Pipeline Builder
Drag-and-drop module nodes from the palette onto a canvas. Connect inputs → outputs with animated edges. Export protocol as JSON. Designed for creating reusable "Acute Quick" or "Chronic Deep" SOPs.

---

## Clinical Disclaimer

This software is for **educational and reference purposes** and is **not intended to diagnose, treat, cure, or prevent any disease**. It is designed to support licensed practitioners in their clinical reasoning, not replace it. Always use professional judgment. Ensure you carry active malpractice insurance and comply with your jurisdiction's telehealth and prescribing regulations.

**Practitioner override is mandatory** — all remedy recommendations require explicit `prescriber_ack` before being recorded. The `PractitionerApprovalGate` enforces this by design.

---

## License

GPL v3 — same as upstream OOREP. See [LICENSE](LICENSE).

---

## Related Projects

- **Upstream OOREP:** https://github.com/nondeterministic/oorep
- **OOREP Case Portal (Next.js):** Practitioner-facing web frontend with Stripe payments and PDF generation
- **Hermes Agent Integration:** Voice case intake, Telegram status checks, Mission Control dashboard, naturopathic remedy personality system

---

*Built with care for the homeopathic community. Open source, open data, open minds.*
