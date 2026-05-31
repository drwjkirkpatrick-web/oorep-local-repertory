# OOREP Local Homeopathic Repertory

A **fast, offline, open-source homeopathic repertory** built on [OOREP](https://www.oorep.com/) (Open Online Repertory) data, enhanced with modern multi-layer search, clinical phrase mapping, remedy outcome tracking, and **38 specialized modules** — from remedy relationships and potency guidance to audit trails and grand rounds synthesis.

> **Version:** 3.0 | **License:** GPL v3 | **Data:** 2,432 remedies × 143,408 rubrics × 1.36M remedy-grade links | **Modules:** 38 Python modules | **Tests:** 222 passing | **Coverage:** **58 of 58 (100%)** LLM-Hermes benefits implemented

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

## New in V2.0: Advanced Practitioner Modules (24 Modules)

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
├── oorep/                          # Core Python package (38 modules)
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
│   └── remedy_feedback.py        # Prescription outcome tracking
├── tests/                        # 222 pytest tests
│   ├── conftest.py
│   ├── test_clinical_rubric_mapper.py
│   ├── test_hybrid_repertory.py
│   ├── test_new_benefits.py      # Phase 1-2 module tests
│   ├── test_batch_a.py           # Phase 3 batch A
│   ├── test_batch_b.py           # Phase 3 batch B
│   ├── test_batch_c.py           # Phase 3 batch C
│   ├── test_batch_d.py           # Phase 4 batch D
│   └── test_batch_e.py           # Phase 5 batch E (final benefits)
├── examples/
│   └── basic_usage.py            # Copy-paste starter code
├── data/                         # Extracted OOREP JSON (gitignored)
│   ├── remedies.json
│   ├── rubrics.json
│   ├── rubric_search_index.json
│   ├── rubric_to_remedies.json
│   └── indexes/                  # Generated vector artifacts
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
└── OOREP_Gap_Analysis.md        # Full 58-benefit gap audit + build phases
```

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

Full suite: **186 tests** covering all 32 modules.

---

## Gap Analysis & Roadmap

See `OOREP_Gap_Analysis.md` for the complete 58-benefit audit with build phases.

**Coverage summary:**
- **58 of 58 benefits** implemented (**100%**)
- **38 Python modules** built
- **222/222 tests** passing

**Phase 5 Complete:** Materia medica proving texts, kingdom taxonomy (75-remedy seed), botanical bridge (WHO Monograph), genomic SNP hypothesis (14-SNP seed), flashcard spaced repetition, and cron automation (follow-up alerts, vector auto-rebuild, GitHub backup) are all built and tested.

All remaining items are seeded with PD-compatible classical data and ready for expansion with your own corpus.

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
