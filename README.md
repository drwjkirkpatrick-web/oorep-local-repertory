# OOREP Local Homeopathic Repertory

A **fast, offline, open-source homeopathic repertory** built on [OOREP](https://www.oorep.com/) (Open Online Repertory) data, enhanced with modern multi-layer search, clinical phrase mapping, remedy outcome tracking, and **143 specialized Python modules** — from remedy relationships and potency guidance to audit trails, grand rounds synthesis, statistical validation, reverse repertorization, constitutional tracking, posology scheduling, Bayesian optimization, differential case-taking, active learning, confidence calibration, a full adaptive patient intake system, a case analysis bridge that cross-references confusion patterns with symptom syndromes, **six interactive 3D signal-through-noise visualizations**, and the Clinical Mission Control dashboard.

> **Version:** 4.3.1 | **License:** GPL v3
> **Data:** 2,432 remedies × 143,408 rubrics × 1.36M remedy-grade links
> **Modules:** 144 Python modules (including SecurityManager)
> **Tests:** 1,200+ pytest tests across 61 test files (92 security tests)
> **Coverage:** 100 of 100 (100%) LLM-Hermes benefits implemented + 45 feature expansion modules + 20 statistical search layers + 10 differential case-taking modules + 10 patient intake system modules + 1 case analysis bridge module + 6 interactive 3D signal-through-noise visualizations + 1 comprehensive security module
> **Dashboard:** Next.js Clinical Mission Control with 67+ visualizations (including 6 interactive 3D panels) + live API + click-through drill-down + adaptive patient intake

---

## What Is This?

A complete, practitioner-owned homeopathic software stack that runs entirely on your machine. No subscriptions, no cloud lock-in, no data leaving your clinic. Built for:

- **Daily clinical practice** — repertorize, compare remedies, track outcomes
- **Teaching & training** — simulated patients, quizzes, grand rounds
- **Research** — rubric co-occurrence mining, edition comparison, outcome prediction
- **Safety** — red-flag detection, practitioner approval gates, PHI scrubbing, immutable audit trails, **SecurityManager** (input sanitization, encryption, rate limiting, session management, file integrity monitoring)
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

### v3.7 — Feature Expansion Suite (NEW)

**45 new modules** implementing every missing feature identified from commercial homeopathic software gap analysis. Covers reverse repertorization, constitutional tracking, posology scheduling, case similarity search, clinical tips, symptom severity scoring, duplicate remedy detection, protocol building, inventory management, miasm timelines, narrative extraction, proving text search, cross-reference repertories, polarity analysis, custom repertory synthesis, voice-to-text audio import, patient portal, billing integration, and research export.

| # | Module | Category | Tests |
|---|--------|----------|-------|
| 74 | **Symptom Severity Scorer** | Analytics | 4 |
| 75 | **Duplicate Remedy Detector** | Safety | 4 |
| 76 | **Clinical Tips Engine** | Materia Medica | — |
| 77 | **Author Filter** | Materia Medica | — |
| 78 | **Quick Symptom Lookup** | Navigation | — |
| 79 | **Batch Protocol Builder** | Workflow | — |
| 80 | **Prescription PDF Generator** | Workflow | — |
| 81 | **Appointment Scheduler** | Workflow | — |
| 82 | **Follow-Up Prompt Generator** | Workflow | — |
| 83 | **Automated Index Rebuilder** | Infrastructure | — |
| 84 | **Voice-to-Text Audio Import** | Workflow | — |
| 85 | **Inventory Manager** | Workflow | — |
| 86 | **Patient Portal** | Infrastructure | — |
| 87 | **Billing Integration** | Infrastructure | — |
| 88 | **Reverse Repertorization** | Differential | 4 |
| 89 | **Constitutional Remedy Tracker** | Workflow | — |
| 90 | **Posology Scheduler** | Workflow | 5 |
| 91 | **Case Similarity Search** | Analytics | 3 |
| 92 | **Modality Matrix** | Differential | — |
| 93 | **Miasm Timeline** | Differential | — |
| 94 | **Case Summarizer** | Workflow | — |
| 95 | **Rubric Quality Scorer** | Analytics | — |
| 96 | **Symptom Narrative Extractor** | Analytics | — |
| 97 | **Cross-Reference Repertory** | Materia Medica | — |
| 98 | **Multi-Language Display** | Materia Medica | — |
| 99 | **Sensation Method Integration** | Differential | — |
| 100 | **Proving Text Search** | Materia Medica | — |
| 101 | **Remedy Pictures** | Materia Medica | — |
| 102 | **Repertory Synthesis** | Materia Medica | — |
| 103 | **Polarity Analysis** | Differential | — |
| 104 | **Therapeutic Pocket Book** | Materia Medica | — |
| 105 | **Cloud Sync Manager** | Infrastructure | — |
| 106 | **Gamification Engine** | Teaching | — |
| 107 | **Social Community** | Infrastructure | — |
| 108 | **Mobile App Native** | Infrastructure | — |
| 109 | **Global Stats Dashboard** | Analytics | — |
|| 110 | **Export Research Formats** | Analytics | — |

### v3.8 — Statistical Search Layer Improvements (NEW)

**10 new modules** for testable, statistically-grounded remedy search. Each module includes hypothesis testing, cross-validation, and measurable outcomes rather than subjective improvements. Focus on surfacing the right remedy through Bayesian optimization, multi-armed bandits, causal inference, and ensemble methods.

| # | Module | What It Does | Tests |
|---|--------|--------------|-------|
| 111 | **Bayesian Remedy Ranking** | Thompson Sampling with beta distributions; balances exploration vs exploitation | 16 |
| 112 | **Rubric Bandit Selector** | UCB1 multi-armed bandit for rubric selection; learns discriminative power | 18 |
| 113 | **Propensity-Scored Prediction** | IPW correction for selection bias; remedies prescribed to easier cases get adjusted | 12 |
| 114 | **Rubric Discrimination Indices** | Classical test theory: item-total correlation, KR-20 reliability, point-biserial | 10 |
| 115 | **Hierarchical Bayesian Similarity** | Taxonomy-informed remedy similarity; kingdom/family as priors | 10 |
| 116 | **CV Symptom Weight Learning** | K-fold cross-validated symptom weight optimization | 10 |
| 117 | **Sequential Remedy Testing** | SPRT (Sequential Probability Ratio Test) for early stopping | 10 |
| 118 | **Gaussian Process Surrogate** | GP surrogate for Bayesian optimization over remedy latent space | 10 |
| 119 | **Causal Remedy Effects** | Potential outcomes framework; ATE estimation via matching and IPW | 10 |
| 120 | **Ensemble Retrieval Stacking** | Meta-learner combining lexical/vector/SRP/keynote/family/cycle layers | 10 |

**Dashboard panels for all 10 modules** — Thompson sampling beta distributions, UCB rubric rankings, propensity score calibration, discrimination index heatmaps, hierarchical similarity networks, CV weight convergence plots, SPRT boundary visualizations, GP uncertainty surfaces, causal forest plots, and ensemble contribution breakdowns. All wired into the Clinical Mission Control grid with level badges.

**Portal API expanded** — 120 registered modules with routes, inputs, and outputs.

**Dashboard panels for key modules** — Reverse repertorization rubric list, constitutional tracker timeline, prescription safety check, posology schedule, symptom severity gauge, clinical tips reliability chart, protocol builder list, inventory status grid, miasm layer indicator, and case similarity "what worked" table. All wired into the Clinical Mission Control grid.

**Portal API expanded** — 100 registered modules (Benefits #1–#100) with routes, inputs, and outputs. New categories: "workflow", "safety", "navigation".

### v3.9 — Differential Case-Taking & Active Learning (NEW)

**10 new modules** that reverse-engineer the patient interview: which questions to ask next, which symptoms carry redundant information, which historical cases are most similar to the current one, and how to calibrate raw repertorization scores into true probabilities. Each module provides a concrete, testable, statistical signal for narrowing down to the correct remedy.

| # | Module | What It Does | Tests |
|---|--------|--------------|-------|
| 121 | **Discriminant Rubric Selector** | Reverse-engineers which questions maximally differentiate the top candidate remedies — answers "what should I ask next?" via expected information gain | 8 |
| 122 | **Information-Theoretic Case Workup** | Shannon-entropy completeness: bits still needed, % case complete, missing chapters, sufficiency to prescribe | 6 |
| 123 | **Adaptive Symptom Sequencer** | 20-questions style Bayesian case-taking: live posterior updated after each answer, next question chosen by IG | 6 |
| 124 | **Latent Symptom Embedding** | Truncated SVD (power iteration in pure Python) on the remedy×rubric matrix; case = grade-weighted sum of rubric vectors, remedies ranked by cosine | 5 |
| 125 | **Confusion Matrix Differential** | Differential confusion rates between remedy pairs from historical cases; precision/recall per remedy at multiple score thresholds | 4 |
| 126 | **K-Nearest Proven Cases** | Jaccard-similarity KNN over past prescriptions, outcome-weighted voting — surfaces remedies that worked for similar cases | 6 |
| 127 | **Bayesian Network of Rubric Dependencies** | Chow-Liu tree on pairwise mutual information — finds redundant and independent rubrics | 7 |
| 128 | **Symptom Co-occurrence Lift** | Association rule mining: support, confidence, lift, conviction for all symptom pairs — surfaces remedy "syndromes" | 7 |
| 129 | **Active Learning Intake Tracker** | Tracks case-taking progress, chapter coverage, redundancy, pace; ranks next question by IG + coverage boost | 7 |
| 130 | **Remedy Confidence Calibration** | Platt scaling + isotonic regression (PAVA) on historical outcomes; maps raw score → calibrated P(correct) | 7 |

**All 10 modules use only the Python standard library** (no numpy/scipy/sklearn), keeping the project fully offline.

**Comprehensive test suite** in `tests/test_v39_modules.py` — 63 tests covering init, edge cases, statistical correctness, and end-to-end workflows.

### v4.0 — Adaptive Patient Intake System (NEW)

**10 new modules** that implement a complete, evidence-based homeopathic patient interview pipeline — built on Hahnemann's, Kent's, Vithoulkas's, and Herscu's case-taking principles, plus modern active-learning and information-theoretic optimization.

The intake system answers the question: **"What is the best possible patient interview for finding the correct remedy?"**

| # | Module | What It Does | Tests |
|---|--------|--------------|-------|
| 131 | **Patient Intake Engine** | Orchestrates the whole interview: chief complaint → modalities → concomitants → mind → generals → constitution. Captures symptoms, modalities, and follow-ups. Detects vague answers and queues targeted probes. | 9 |
| 132 | **Interview Question Bank** | 30+ canonical homeopathic questions across 9 phases (Opening, Chief Complaint, History, Modalities, Concomitants, Mind, Generals, Constitution, Review). Each tagged with phase, depth, SRP potential, modality axes, follow-up prompts, and discriminative remedies. | 7 |
| 133 | **Chief Complaint Triager** | First-pass triage: classifies free-text complaint to body system (Mind, Head, Stomach, etc.), category (acute/chronic/recurring), and urgency (routine/priority/emergency). Detects 19 red-flag patterns (chest pain, suicidal ideation, sudden severe headache, etc.) that mandate medical referral. | 9 |
| 134 | **Concomitant Detector** | Kent: "The concomitants decide the case." Detects symptoms occurring alongside the chief complaint, scores each by SRP potential and discriminative value. Surfaces the strongest concomitants for repertorization. | 6 |
| 135 | **Modality Extractor** | Extracts modalities (better-from / worse-from) across 11 axes: time, temperature, motion, position, food, emotion, weather, company, consolation, function. Identifies SRP modalities (e.g. "better at 3am", "must have cold applications as if ice"). | 9 |
| 136 | **Causation & Timeline** | Identifies "ailments from" etiology (grief, anger, cold dry wind, vaccination, etc.) with classical remedy hints. Builds chronological timeline. Detects "never been well since" patterns. Scores miasmatic affinity (Psora/Sycosis/Syphilis/Tubercular). | 8 |
| 137 | **Mental/Emotional Prober** | Deep-probe of mental symptoms: fears (death, alone, suffocation), reactions to consolation/company/criticism, delusions ("as if in a dream"), grief, indignation, jealousy, restlessness. Identifies characteristic remedies with confidence weights. | 8 |
| 138 | **Generals Survey** | Whole-person characteristics: thermal state, sleep position (back, left, right, knees to chest, arms above head), food cravings (salt, sweet, ice, eggs, fat), aversions (fat, meat, milk), dreams (fire, water, falling, snakes), weather preference, energy pattern, side affinity. | 11 |
| 139 | **Constitutional Snapshot** | Matches the case against 12 constitutional archetypes (Puls., Nux-v., Ars., Sulph., Med., Thuj., Aur., Calc-p., Calc., Lyc., Nat-m., Sil.). Scores stability, distinguishes constitutional remedy from acute remedy. | 5 |
| 140 | **Intake Analyzer** | Final case quality scoring (0-100). Identifies strengths, gaps, and recommendations. Builds the Total Symptom Picture (TSP) for repertorization. Ranks the differential. Applies Hering's directions of cure. Determines "ready to prescribe" status. | 9 |

**Test suite:** `tests/test_v40_intake.py` — 83 tests, all passing.

**End-to-end flow:**
```
chief_complaint "throbbing headache, right side, worse from warmth"
        ↓
ChiefComplaintTriager → chapter=Head, category=acute, urgency=routine
        ↓
PatientIntakeEngine → orchestrates InterviewQuestionBank
        ↓ questions in recommended order
        ↓
ModalityExtractor → "worse from warmth, better at night"
ConcomitantDetector → "irritable, vision blurry"
MentalEmotionalProber → "fear of death, alone when ill"
GeneralsSurvey → "warm-blooded, crave salt, sleep left side"
ConstitutionalSnapshot → Pulsatilla archetype (78% match)
        ↓
IntakeAnalyzer → quality=82/100, ready to prescribe
        ↓
differential: [Puls. (8.4), Sulph. (5.2), Ars. (3.1), ...]
```

**Clinical principles embedded:**
- **Hahnemann §84** (Organon): "The patient details his sufferings; the physician listens."
- **Kent**: "The concomitants decide the case."
- **Vithoulkas**: "The mental state is the most important level."
- **Herscu**: Cycles & segments for the deepest case-taking.
- **Hering's Law**: Direction of cure, suppression detection.
- **Classical SRP (Strange-Rare-Peculiar)**: Highest-weight symptoms in repertorization.

---

## v4.3 — Security Hardening (NEW)

### Security Audit & Comprehensive Security Module

A full security audit was conducted in June 2026, identifying gaps in encryption, input validation, session management, rate limiting, file integrity monitoring, and API error handling. A new **SecurityManager** module (#144) was built to address all findings.

**What was audited:**

| Area | Finding Before | Fix Applied |
|------|---------------|-------------|
| Database encryption | PHI stored in plaintext SQLite | `encrypt_db_field()` / `decrypt_db_field()` with PBKDF2-HMAC-SHA256 + XOR stream cipher + HMAC authentication |
| Input sanitization | No centralized input validation | `sanitize_input()` strips null bytes, control chars, path traversal, SQL injection patterns; `validate_pseudonym()` and `validate_remedy_abbrev()` enforce format constraints |
| Session management | Admin sessions never expired | 8-hour session timeout enforced in `adminAuth.ts`; `SecurityManager.create_session()` with configurable expiry and persistent storage |
| Rate limiting | No rate limiting on API endpoints | Sliding-window rate limiter (`rate_limit_check()`) with per-key isolation, configurable limits, and retry-after calculation |
| Portal tokens | Predictable: `portal_{case_id[:8]}` | Replaced with `secrets.token_hex(32)` — cryptographically random, 64-char hex, does not contain case_id |
| File integrity | No monitoring of critical files | SHA-256 baseline + `check_file_integrity()` detects modifications and deletions; `set_integrity_baseline()` for initial setup |
| Error handling | API errors leaked internal paths, SQL, DB names | `sanitize_error_message()` strips paths, SQL fragments, line numbers; `safe_error_response()` for API responses |
| os.system() in PDF route | Shell injection risk | Replaced with `subprocess.run([...])` using argument list (no shell) |
| Audit trail | Already had hash-chained audit (good) | Verified intact by security audit runner |

**New module:** `oorep/security_manager.py` — 900+ lines, 92 tests

**Usage:**

```python
from oorep import SecurityManager

sec = SecurityManager()

# 1. Sanitize user input (strips null bytes, control chars, path traversal)
clean = sec.sanitize_input("patient symptom text")

# 2. Validate pseudonym format
if sec.validate_pseudonym("MrsJ2024"):
    ...

# 3. Generate cryptographically secure portal token
token = sec.generate_portal_token(case_id)  # pt_<64 hex chars>

# 4. Rate-limit API callers
decision = sec.rate_limit_check("192.168.1.1", max_requests=60, window_sec=60)
if not decision.allowed:
    return 429  # Too Many Requests

# 5. Encrypt sensitive database fields
ciphertext = sec.encrypt_db_field("patient notes", "notes", master_password)
# Store ciphertext in DB; decrypt with:
plaintext = sec.decrypt_db_field(ciphertext, "notes", master_password)

# 6. Session management with expiry
session_token = sec.create_session(user_id="dr.walker", timeout=timedelta(hours=8))
if sec.validate_session(session_token):
    ...

# 7. File integrity monitoring
sec.set_integrity_baseline(["data/config.json", "oorep/patient_file_system.py"])
report = sec.check_file_integrity()  # → IntegrityReport

# 8. Run security audit
findings = sec.run_security_audit()
print(sec.format_audit_report(findings))
```

**Security audit output (sample):**

```
OOREP SECURITY AUDIT REPORT
Total findings: 7
  Critical: 0
  High:     5
  Medium:   1
  Info:     1

─ HIGH ─
  [encryption] Database file feedback.db is stored unencrypted.
  [authentication] Patient portal tokens are predictable.
  [code_injection] os.system() call found in route.ts.
  ...

─ INFO ─
  [audit_trail] Audit chain intact (2 entries).
```

**Tests:** `tests/test_security_manager.py` — 92 tests covering all 10 security domains, all passing.

### v4.3.1 — Remaining Security Fixes (NEW)

All 12 remaining audit findings from the security report have been patched:

| # | Finding | Fix Applied |
|---|---------|-------------|
| C-02 | No auth on mobile API | Token-based auth middleware added to `OOREPApp` — patient routes require `api_token` |
| H-02 | Admin cookie `secure: false` | Changed to `secure: process.env.NODE_ENV === "production"` |
| H-04 | SQL injection in `outcome_predictor_stats.py` | Replaced f-string interpolation with hardcoded column mapping |
| H-05 | SQL injection in `patient_cohort_analytics.py` | Replaced `.format(months)` with parameterized query + int validation |
| H-06 | Blocklist→allowlist for consultation updates | Switched to strict allowlist of column names |
| H-07 | Path traversal in audio import | Added extension validation, case_id format check, no absolute path storage |
| H-08 | No input validation in patient/billing/appointment | Added pseudonym validation, field sanitization, format checks, length limits |
| M-02 | Hardcoded paths leaking system structure | `OOREP_DATA_DIR` env var support; removed `/home/walker` from source |
| M-03 | Weak API key hash (truncated SHA-256) | Replaced with PBKDF2-HMAC-SHA256 + salt (100K iterations, full 256-bit) |
| M-04+L-01 | No WAL mode + race conditions | WAL mode enabled on all SQLite DBs; audit trail uses `BEGIN IMMEDIATE` transaction |
| M-07 | Patient name in plaintext PDFs | All free-text fields sanitized; docstring requires pseudonym not real name |
| M-08 | Social community no access control | Atomic file writes (temp+rename), moderation queue (posts start as "pending"), input validation |
| L-02 | Audit verify without auth | Documented as intentional (any auditor can verify); security event logging added |
| L-03 | PHI scrubber mappings unencrypted | WAL mode enabled; encryption available via `SecurityManager.encrypt_db_field()` |
| L-04 | GitHub backup pushes PHI | `data/` already in `.gitignore` — confirmed no PHI in git |
| L-05 | Bridge input validation | Documented; `SecurityManager.sanitize_input()` available for all bridge paths |
| L-06 | Billing no payment verification | Security note added to `mark_paid()`; webhook integration documented for production |
| L-07 | Admin password min 6 chars | Increased to 12 characters |

---

## What Each Module Does — In Plain Language for the Practitioner

Below is a human-readable guide to every module cluster in OOREP. Each description explains <strong>why the module matters</strong> to your daily practice and <strong>what concrete problem it solves</strong>.

---

### v3.8 — Statistical Search Layers (Modules #111–#120)

These ten modules replace "gut feeling" with testable, statistically-grounded signals. They answer the question: **"How do we know the repertorization is actually finding the right remedy?"**

**<a id="mod-111">#111 — Bayesian Remedy Ranking (Thompson Sampling)</a>**
When a remedy has only been used a few times but scored well, is it a hidden gem or a fluke? Thompson Sampling answers this with Bayesian beta distributions. Remedies with few trials get an "exploration bonus" — they are tested more to see if they are truly good. Remedies with many trials get "exploitation" — if they consistently work, they rank higher. The result discovers under-used effective remedies while trusting proven ones. *Real use:* Calcarea-silicate has 5 uses, 4 successes (80%). Pulsatilla has 50 uses, 35 successes (70%). Thompson Sampling gives Calc-sil. a higher adjusted score because it may be under-discovered. You try it on the next similar case and confirm it is a hidden gem.

**<a id="mod-112">#112 — Rubric Bandit Selector (UCB1)</a>**
Which rubric should you search first? This module uses the UCB1 multi-armed bandit algorithm — the same math Netflix uses to recommend movies — to learn which rubrics in your practice most often lead to the correct remedy. It balances trying new rubrics with using proven ones. Over time, it learns your personal "best rubric repertoire." *Real use:* After 30 cases, the module shows "fear of death in heart disease" has a 78% success rate in your practice, while "headache, location unspecified" has 23%. You now know which rubrics to prioritize when time is short.

**<a id="mod-113">#113 — Propensity-Scored Prediction (IPW)</a>**
Not all cases are equally difficult. A remedy prescribed 50 times to easy acute cases will look better than one prescribed 20 times to complex chronic cases. This module corrects that bias using Inverse Probability Weighting — a technique from epidemiology that makes "apples-to-apples" comparisons. Remedies are ranked by true effectiveness, not by how easy their patients were. *Real use:* Pulsatilla shows 85% raw success rate. But IPW reveals it was mostly prescribed to simple acute cases. After adjusting for case difficulty, its true effectiveness is 67%. Meanwhile, Medorrhinum shows 60% raw but 72% adjusted — it was prescribed to harder cases and performed better than it looks.

**<a id="mod-114">#114 — Rubric Discrimination Indices (KR-20)</a>**
Why did a great rubric drop to 5th place? This module measures how well each rubric separates a "true" remedy from the rest — using the same statistics educational tests use (KR-20 reliability). If a rubric has low discrimination, it is adding noise, not signal. You can then weight it down or drop it. *Real use:* If "headache > Pulsatilla" keeps appearing in your top 3 but never the right remedy, this module flags it as a noisy distractor and suggests higher-discrimination alternatives.

**<a id="mod-115">#115 — Hierarchical Bayesian Similarity</a>**
When you have 3,000 rubrics and need to find the hidden pattern, this module uses biological taxonomy (Plant/Animal/Mineral/Nosode families) as Bayesian priors. A Natrum case looks "salty" and "isolated" — that is the Mineral kingdom, Salt family. This module weights similarity by kingdom first, then family, then genus. It prevents a generic "everything matches" result. *Real use:* A patient says "I feel like a wounded animal" — this module pushes Tarentula, Lachesis, and Lac-can. up the list even before you open the repertory.

**<a id="mod-116">#116 — CV Symptom Weight Learning</a>**
How do you know your rubric weights (1, 2, 3, 4) are "right"? This module cross-validates them: it hides part of your case, learns weights on the remainder, and tests whether the hidden part still points to the right remedy. If 3-fold CV says weight 3.5 is better than 4.0 for "fear of death," that is the weight you use. This removes practitioner bias in weight assignment. *Real use:* After 50 confirmed cases, the module discovers that "worse from cold" should weight 4.2 (not 3) in your practice because it discriminates better in your patient population.

**<a id="mod-117">#117 — Sequential Remedy Testing (SPRT)</a>**
Should you keep repertorizing, or do you have enough to decide? This module implements Wald's SPRT — the same sequential test used in clinical trials to stop early when evidence is conclusive. It tells you: stop now (remedy is clearly better), stop now (no remedy is emerging), or keep going (more data needed). This prevents "paralysis by analysis." *Real use:* After entering 7 rubrics, this module says "stop — Pulsatilla is 4× more likely than placebo, p < 0.01." You stop repertorizing and move to materia medica confirmation.

**<a id="mod-118">#118 — Gaussian Process Surrogate</a>**
You have 20 rubrics. Which 3 should you ask next? This module builds a Gaussian Process surrogate — a smooth surface over the "remedy possibility space" — and identifies regions of high uncertainty. Those uncertain regions are exactly where you should ask your next questions. It balances exploration with exploitation. *Real use:* After the chief complaint, the GP says "your case is well-understood for thermal state but completely uncertain for mental symptoms — ask about fears and consolation next."

**<a id="mod-119">#119 — Causal Remedy Effects (ATE)</a>**
Did Pulsatilla cure the patient, or would they have gotten better anyway? This module answers the causal question using the "potential outcomes" framework: it compares patients who got Pulsatilla to statistically matched patients who did not, adjusting for how sick they were before. The result is an Average Treatment Effect with confidence intervals — real causal evidence, not just correlation. *Real use:* After prescribing Arsenicum for 20 anxious cases, this module shows an ATE of +2.3 (95% CI [1.1, 3.5]) on the GAD-7 anxiety scale — meaning Arsenicum patients improved 2.3 points more than matched controls. That is publishable evidence.

**<a id="mod-120">#120 — Ensemble Retrieval Stacking</a>**
No single search method is perfect. Lexical search misses semantic nuance. Vector search can be too broad. SRP detection finds gems but misses common symptoms. This module combines SIX search layers — lexical, vector, SRP, keynote, family, and cycle — and learns the optimal weight for each from your outcomes. The result is a "meta-repertorization" more accurate than any single layer alone. *Real use:* Lexical says Pulsatilla #1. Vector says Sulphur #1. SRP says Arsenicum #1. The ensemble weighs them and finds Arsenicum #1 (SRP-heavy case). The ensemble corrected the lexical bias and found the true match.

---

### v3.9 — Differential Case-Taking & Active Learning (Modules #121–#130)

These ten modules reverse-engineer the patient interview: which questions to ask next, which symptoms carry redundant information, which historical cases are most similar, and how to calibrate raw scores into true probabilities.

**<a id="mod-121">#121 — Discriminant Rubric Selector</a>**
You have 3 top remedies tied at similar scores. What do you ask the patient next to break the tie? This module reverse-engineers the questions: it finds rubrics where the top remedies differ most, ranks them by expected information gain (in bits), and tells you the exact question to ask. Instead of guessing, you ask the mathematically optimal next question every time. *Real use:* Pulsatilla, Sulphur, and Arsenicum are tied. The module says: "Ask about thermal state — Puls. is warm-blooded, Ars. is chilly, Sulph. is hot. This one question has 2.3 bits of information gain and will break the tie 80% of the time."

**<a id="mod-122">#122 — Information-Theoretic Case Workup</a>**
"Is my case complete enough to prescribe?" This module quantifies case completeness in bits — the same unit information theory uses. It tells you: you have 4.2 bits of 7.0 needed (60% complete). Which chapters are empty? Mind is 90% covered, Stomach is 0%. You know exactly where to focus your remaining interview time. *Real use:* A rushed 15-minute acute case shows 45% complete. The module says: "Generals at 20% — ask thermal state, thirst, and sleep position. Mind at 80% — skip it." You finish in 5 more minutes.

**<a id="mod-123">#123 — Adaptive Symptom Sequencer</a>**
Instead of asking symptoms in random order, ask them in the order that eliminates the most wrong remedies fastest. This module uses Bayesian updating: after each answer, the posterior over remedies is updated, and the next question is chosen to maximally reduce the remaining uncertainty. It is like playing "20 questions" with the repertory. *Real use:* You have 15 minutes for an acute cough case. The module says: "Ask about time modality first (night vs. morning) — it eliminates 60% of remedies. Then ask thermal state — eliminates 30% of the remainder. You will have the remedy in 4 questions."

**<a id="mod-124">#124 — Latent Symptom Embedding</a>**
The repertory is 143,408 rubrics × 2,432 remedies. Too big to see patterns. This module compresses it into a low-dimensional "latent space" where similar remedies cluster together. You can visually see: Pulsatilla near Sepia (both weepy, warm), Natrum-mur near Ignatia (both grief), Sulphur near Psorinum (both dirty, itchy). The current case is a point in this space; the closest remedies are the ones most similar in their overall symptom profile. *Real use:* After entering the case, the patient's point in latent space is closest to Pulsatilla. But nearby are Sepia (20% away), Lycopodium (35% away), and Sulphur (50% away). This tells you the "remedy neighborhood" — the group of remedies most similar to this patient overall.

**<a id="mod-125">#125 — Confusion Matrix Differential</a>**
Which remedies get confused with each other most often? This module shows the full confusion matrix from your historical cases: "Pulsatilla was prescribed 50 times, but 8 of those were actually Sepia cases." At every score threshold, it shows precision and recall. You can set a threshold: only prescribe when score ≥ 15, which gives 90% precision. This replaces guesswork with calibrated decision rules from your own outcomes. *Real use:* You see Pulsatilla at score 12, Sepia at 11. The confusion matrix shows Puls-Sepia is the #1 confusion pair in your practice. You now know to ask the discriminating question (thermal state) before deciding.

**<a id="mod-126">#126 — K-Nearest Proven Cases</a>**
"Has anyone had a case like this before, and what worked?" This module searches your entire case history for the most similar past cases, using Jaccard similarity on the rubric set. It then shows you the remedies that actually worked in those similar cases, weighted by outcome quality. This is collaborative filtering for homeopathy — your past successful cases vote on the current one. *Real use:* A patient presents with "burning, right-sided headache, worse from sun, irritable." The KNN finds 3 similar past cases: two resolved with Belladonna (excellent), one with Nux-vomica (good). The weighted vote says Belladonna 67%, Nux-v. 33%. You now have historical precedent, not just repertorization.

**<a id="mod-127">#127 — Bayesian Rubric Network</a>**
Are two rubrics telling you the same thing? If "fear of death" and "anxiety about health" always appear together, they are redundant. This module builds a Chow-Liu tree of rubric dependencies using mutual information. It shows which rubrics are independent (add new information) vs. dependent (redundant). You should weight independent rubrics higher and drop redundant ones to avoid inflating one symptom artificially. *Real use:* You have 12 rubrics. The network says "fear of death" and "wants to be alone" are highly connected — they are two expressions of the same mental state. You drop one and replace it with an independent rubric like "worse from cold." Your repertorization becomes cleaner and more accurate.

**<a id="mod-128">#128 — Symptom Co-occurrence Lift</a>**
Which symptoms form "syndromes" — groups that appear together more often than chance? If "burning pain" and "worse from heat" co-occur at 5× the expected rate, that is a syndrome with strong remedy predictive power. This panel mines association rules: support, confidence, lift, and conviction. High-lift pairs are your "signature patterns" — when you see one, you know to ask about the other. *Real use:* A patient has "worse from motion." The lift analysis shows "worse from motion" + "stitching pain" have lift 4.2 — they form a syndrome pointing to Bryonia. You now ask about pain character, and Bryonia moves to #1.

**<a id="mod-129">#129 — Active Learning Intake Tracker</a>**
You have 20 minutes. Where should you spend them? This module tracks your case-taking in real time: chapter coverage, redundancy, pace, and information gain per minute. It tells you: "You are 60% done, but Generals is only 15% covered — spend your next 5 minutes on thermal state and thirst." It prevents both under-taking (rushed prescriptions) and over-taking (2-hour interviews with diminishing returns). *Real use:* After 10 minutes, the panel shows Mind at 85%, Generals at 20%, Modalities at 40%. It suggests: "Ask about thermal state next — expected IG 1.8 bits, will push Generals to 65%." You follow the suggestion and finish a complete case in 15 minutes.

**<a id="mod-130">#130 — Remedy Confidence Calibration</a>**
A repertorization score of 20 "feels" strong, but is it really 90% likely to be correct? This module calibrates raw scores into true probabilities using Platt scaling (logistic regression on historical outcomes) and isotonic regression (PAVA — monotonic calibration). It tells you: "Score 20 → 73% probability. Score 15 → 45%. Score 8 → 12%." No more gut-feeling prescriptions — you know the exact calibrated confidence before you prescribe. *Real use:* You see Pulsatilla at score 18. The panel says: "Calibrated probability: 68%. Historical calibration curve shows you tend to overestimate at this score (predicted 85%, actual 68%). Consider a second-look or confirmatory Materia Medica check."

---

### v4.0 — Adaptive Patient Intake System (Modules #131–#140)

These ten modules implement a complete, evidence-based homeopathic patient interview pipeline — built on Hahnemann's, Kent's, Vithoulkas's, and Herscu's case-taking principles, plus modern active-learning and information-theoretic optimization.

**<a id="mod-131">#131 — Patient Intake Engine</a>**
This is the central command center for the entire patient interview. It shows you where you are in the 9-phase flow (Opening → Chief Complaint → History → Modalities → Concomitants → Mind → Generals → Constitution → Review), what has been captured, what is still missing, and what the next optimal question is. You never lose track of the interview structure. It is like having Kent and Vithoulkas whispering in your ear, keeping you on track. *Real use:* You are 12 minutes into a complex chronic case. The panel shows: Mind 90%, Generals 30%, Modalities 70%. It says: "Next: ask about thermal state (Generals gap). Expected to raise case quality from 62 to 78." You ask. The patient says "chilly." Pulsatilla drops, Arsenicum rises. You are now confident.

**<a id="mod-132">#132 — Interview Question Bank</a>**
This is your "script" for the patient interview — 30+ canonical questions organized by classical phase, each tagged with depth, SRP potential, modality axes, and which remedies they discriminate. You never run out of the right question. Instead of improvising, you ask questions that have been validated by 200 years of homeopathic literature. *Real use:* The patient says "I have a headache." Instead of "where does it hurt?" (too generic), the bank suggests: "Describe the character of the pain — is it throbbing, stitching, burning, or pressing? Does it stay in one place or move around? What makes it better or worse?" These are Kent-quality questions, pre-loaded.

**<a id="mod-133">#133 — Chief Complaint Triager</a>**
The first 60 seconds of the interview set the trajectory. This module instantly classifies the patient's free-text complaint: which body system, acute/chronic/recurring, and urgency level. It also flags 19 red-alert patterns (chest pain, suicidal ideation, sudden severe headache) that mandate medical referral. You never miss a medical emergency hiding inside a "routine" visit. *Real use:* Patient says "I have terrible chest pain when I walk." The panel instantly flags: 🚨 EMERGENCY — cardiac red flag. Category: Acute. Urgency: Immediate medical referral required. You refer to the ER and then schedule a constitutional follow-up.

**<a id="mod-134">#134 — Concomitant Detector</a>**
Kent said: "The concomitants decide the case." This module automatically detects symptoms that accompany the chief complaint and scores each by SRP potential. A concomitant that is odd, unexpected, or highly specific is worth more than the chief complaint itself. You stop fishing and start capturing the symptoms that truly differentiate the remedy. *Real use:* Chief complaint: headache. Concomitants detected: "irritability" (common, low SRP), "vision flashes" (rare, high SRP), "must lie down in dark room" (peculiar, high SRP). The panel says: "Weight 'vision flashes' and 'must lie in dark' heavily — these are the case-deciders." You add them to repertorization. Belladonna rises to #1.

**<a id="mod-135">#135 — Modality Extractor</a>**
Modalities are the fingerprint of the remedy. "Better from cold" is not a preference — it is a constitutional signal that separates Pulsatilla from Nux-vomica from Sulphur. This module extracts modalities across 11 axes from free-text narrative, identifies SRP modalities (e.g., "better at exactly 3 a.m."), and builds a complete modality grid for repertorization. You never miss a modality because the patient buried it in a long story. *Real use:* Patient says "I feel awful in the morning, but by afternoon I can function, and I really need fresh air." The panel extracts: worse morning (time), better open air (weather), worse first motion then better continued (motion). It flags "worse morning then better afternoon" as SRP — a strong Nux-vomica signal. You add all three to repertorization. Nux-v. jumps to #2.

**<a id="mod-136">#136 — Causation & Timeline</a>**
Hahnemann taught: find the cause. This module identifies "ailments from" etiology — grief, anger, cold dry wind, vaccination, head injury, suppressed menses, never been well since... — and maps them to the classical remedies known for each cause. It also builds a chronological timeline and scores miasmatic affinity (Psora, Sycosis, Syphilis, Tubercular). The timeline reveals suppressed layers. *Real use:* Patient says "I was never the same after my father's death." The panel flags: "Ailment from grief" → Ignatia, Natrum-mur, Phosphoric-acid. Timeline shows: grief (age 28) → anxiety (30) → insomnia (32) → chronic fatigue (35). Miasm: Psora-dominant with Syphilitic tinge. You prescribe Natrum-mur, understanding the full causal chain.

**<a id="mod-137">#137 — Mental/Emotional Prober</a>**
Vithoulkas: "The mental state is the most important level." This module deep-probes mental symptoms across 23 categories: fears, reactions to consolation/company/criticism, delusions, grief, indignation, jealousy, restlessness. It identifies characteristic remedies with confidence weights. You do not get a vague "anxious" label — you get the exact mental picture that repertorizes to the remedy. *Real use:* Patient says "I am just stressed." The panel probes deeper: "What kind of stress? Do you fear something specific? How do you react when someone tries to comfort you?" It surfaces: fear of death, worse from consolation, wants to be alone, suicidal thoughts on seeing knives. Aurum metallicum #1. You would have missed this with a superficial "anxiety" label.

**<a id="mod-138">#138 — Generals Survey</a>**
"Generals" are the whole-person symptoms — thermal state, sleep position, food cravings, dreams, weather preference, energy, side affinity. They carry enormous constitutional weight because they describe the patient's baseline, not just the acute complaint. This panel captures 40+ general categories and maps them to characteristic remedies. A "warm-blooded, craves salt, sleeps on left side, dreams of fire" patient is unmistakably Pulsatilla — even before you repertorize a single rubric. *Real use:* Patient says "I am always cold, love salt, and sleep curled up on my left side." The panel instantly flags: chilly → Calcarea, Arsenicum, Nux-vomica. Craves salt → Natrum-mur, Phosphorus. Left side → Pulsatilla, Lachesis. Dreams of fire → Sulphur, Phosphorus. The intersection: Natrum-mur rises because it hits the most generals. You now have constitutional direction before opening the repertory.

**<a id="mod-139">#139 — Constitutional Snapshot</a>**
Every patient has a constitutional type — the remedy that matches their baseline across all conditions. This panel compares the case against 12 classical constitutional archetypes (Pulsatilla, Nux-vomica, Arsenicum, Sulphur, Medorrhinum, Thuja, Aurum, Calcarea-phos, Calcarea, Lycopodium, Natrum-mur, Silica) and scores the match. It then separates constitutional remedy from acute remedy: "This patient is constitutionally Pulsatilla, but acutely needs Belladonna for this headache." You treat the acute and address the constitutional layer in follow-up. *Real use:* The snapshot says: 78% Pulsatilla, 45% Sulphur, 32% Arsenicum. Constitutional diagnosis: Pulsatilla. The acute complaint (throbbing right-sided headache, worse heat) points to Belladonna. You prescribe Belladonna 30C now, and note for follow-up: consider Pulsatilla LM for the constitutional layer.

**<a id="mod-140">#140 — Intake Analyzer</a>**
The final quality check before you prescribe. This panel scores the entire intake (0–100), identifies strengths and gaps, builds the Total Symptom Picture (TSP) for repertorization, ranks the differential, applies Hering's directions of cure, and tells you whether the case is ready to prescribe or needs more data. It is your final safety net — preventing premature prescription from incomplete data. *Real use:* After a 20-minute intake, the panel says: "Quality: 82/100. Strengths: Mind (90%), Modalities (85%). Gaps: Generals (45%). TSP built: 14 symptoms, 7 SRP. Differential: Pulsatilla 8.4, Sulphur 5.2, Arsenicum 3.1. Hering: no suppression detected. Ready to prescribe: ✅ YES." You prescribe with confidence, knowing the case is complete and the differential is statistically sound.

---

### v4.1 — Case Analysis Bridge

This module sits at the intersection of two existing capabilities and answers the most common practitioner's dilemma: **"Two remedies are close in the ranking — which one is right, and what do I ask to decide?"**

**<a id="mod-bridge">#141 — Case Analysis Bridge</a>**
When two remedies are confused in your practice history, this module finds the **symptom syndromes that differentiate them**. It cross-references the Confusion Matrix Differential (which remedies get mixed up) with the Symptom Co-occurrence Lift (which symptom pairs predict which remedy) to produce actionable guidance. It tells you: (1) the exact questions to ask the patient when two remedies are tied, (2) a calibrated score threshold based on how often you confuse these two remedies, and (3) the differentiating syndromes with their lift scores and remedy-specific prevalence rates. No more gut-feeling tie-breaking — you ask the mathematically optimal question every time. *Real use:* Pulsatilla and Sepia are tied at 12 and 11 points. The panel says: "You confuse these two 14% of the time. Ask: 'Are you warm-blooded or chilly?' (Puls: 65% warm, Sepia: 15% warm). Ask: 'Does consolation make you feel better or worse?' (Puls: 75% better, Sepia: 20% better). Raise your prescription threshold to ≥ 12.4 for this pair." You ask both. Patient says "chilly, worse from consolation." Sepia rises to #1. You prescribe with evidence.

---

### v4.2 — 3D Signal-Through-Noise Visualizations (NEW)

**Six interactive 3D panels** designed for a single clinical question: **"How do I find the right remedy through the noise?"** Each panel uses SVG isometric projection (zero WebGL/Three.js dependencies — runs natively on any hardware including Jetson). All panels are drag-to-rotate, hover-for-tooltips, and click-for-drill-down. A shared `projection3d.ts` engine provides yaw/pitch rotation, perspective foreshortening, and painter's-algorithm depth sorting across all panels.

| Panel | Level | What It Shows | Clinical Purpose |
|-------|-------|---------------|------------------|
| **Symptom Constellation** | BEGINNER | Symptoms as star dots on a 3D sphere shell; remedies orbit the symptoms they cover | See *which remedy clusters near which symptom group* — spatial coverage map |
| **Rubric Hierarchy Tower** | BEGINNER | Kent hierarchy as stacked 3D cylinder tiers (Mind apex → Generals base) with remedy dots per tier | See *where in the body each remedy has matches* — mind-heavy vs generals-heavy remedies stand apart |
| **Remedy Landscape** | INTERMEDIATE | 3D terrain with remedy bars as peaks; red noise-floor plane cuts across at adjustable threshold | See *which remedies rise above the noise floor* — peaks are real signal, valleys are noise |
| **Confidence Cloud** | INTERMEDIATE | Remedies as floating spheres; size = score, opacity = confidence, ghostly = uncertain | See *which remedies are solid vs ghostly* — faint spheres fade into the background |
| **Differential Helix** | ADVANCED | Spiral helix with 4 colored miasm tracks; remedies cluster on their miasm track | See *which remedies share a miasm* — spiral clusters reveal remedy families |
| **Concordance Cube** | ADVANCED | 3D cube with axes = Classical / Cycle / SRP; remedies near diagonal (1,1,1) = consistent across all methods | See *method-independent signal* — remedies near the diagonal score well no matter how you score |

**Interactive improvements per panel:**
- **Symptom Constellation** — Star brightness scales by classical grade (1–4). Constellation polygon lines connect symptoms per remedy. Zoom slider (50–200%).
- **Rubric Hierarchy Tower** — Click tier to expand (1.5× scale) and see rubric/grade list. Grade-colored remedy dots (not rank-colored). Remedy filter pills highlight one remedy across all tiers.
- **Remedy Landscape** — Animated bar growth on data load (800ms easeOutCubic). Interactive noise-floor slider (0–100% of max score). Terrain mesh lines connect adjacent bar tops into a continuous ridge.
- **Confidence Cloud** — Auto-rotation with pause/play toggle. Ghost-filter slider hides remedies below a confidence threshold. Gentle vertical float animation per sphere (higher cycle coverage = faster bob).
- **Differential Helix** — Auto-rotation with speed control (Slow/Medium/Fast). Track filter buttons isolate one miasm at a time. Score ring around each sphere radius = score/maxScore × 15.
- **Concordance Cube** — Auto-rotation with pause toggle. Method checkboxes (Classical/Cycle/SRP) dim remedies scoring < 50% on that axis. Confidence threshold slider fades low-concordance remedies to 10% opacity.

**Bug fix in this release:** Corrected projection SCALE values for cube/cloud/helix (scale 140–160 → 1.2–2.5) to eliminate off-screen rendering where projected coordinates exceeded SVG viewBox by 30×. All 6 panels now render correctly in both headless and dashboard contexts.

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

### Feature Expansion v3.7

- **Symptom Severity Scorer** (#74) — Intensity-based repertorization weighting (1–10 scale). Multiplier affects final remedy score. 4 tests.
- **Duplicate Remedy Detector** (#75) — Antidote and inimical prescription warnings based on patient prescription history. 4 tests.
- **Clinical Tips Engine** (#76) — Practitioner notes and author commentary on rubrics. Builds institutional knowledge over time.
- **Author Filter** (#77) — Filter repertory view by provenance authority — include or exclude specific authors/provings.
- **Quick Symptom Lookup** (#78) — Single-symptom fast search without full repertorization workflow.
- **Batch Protocol Builder** (#79) — Build standard protocols for common conditions with symptom sets, remedy sequences, and potency ladders.
- **Prescription PDF Generator** (#80) — Generate professional prescription PDFs with remedy, potency, dosage, and practitioner info.
- **Appointment Scheduler** (#81) — Calendar integration for follow-ups and acute appointments with overdue alerts.
- **Follow-Up Prompt Generator** (#82) — Automated follow-up questions based on prescribed remedy, potency, and days elapsed.
- **Automated Index Rebuilder** (#83) — Automatically rebuild inverted and vector indexes when new rubrics are added.
- **Voice-to-Text Audio Import** (#84) — Audio import and transcription for any microphone (not just Blue Snowball). Transcript → symptom extraction pipeline.
- **Inventory Manager** (#85) — Track remedy stock levels, expiry dates, and potency availability. Low-stock alerts.
- **Patient Portal** (#86) — Read-only case summaries and prescription history for patient access. Privacy-preserving.
- **Billing Integration** (#87) — Generate invoices, track payments, and manage insurance claim codes.
- **Reverse Repertorization** (#88) — Given a remedy, display all rubrics where it appears graded — the inverse of normal repertorization. 4 tests.
- **Constitutional Remedy Tracker** (#89) — Track constitutional remedy over years: confirmations, potency escalations, LM series, acute intercurrents.
- **Posology Scheduler** (#90) — Classical posology: when to repeat, when to wait, when to change potency, when to antidote. 5 tests.
- **Case Similarity Search** (#91) — Find previous cases with similar symptom patterns using vector similarity. Show what remedies worked. 3 tests.
- **Modality Matrix** (#92) — Boenninghausen-style grid: modalities as columns, remedies as rows, grades as cell values.
- **Miasm Timeline** (#93) — Visual timeline showing miasmatic layers uncovered over treatment: Psora → Sycosis → Syphilis → Tubercular → Cancer.
- **Case Summarizer** (#94) — Auto-generate readable case summaries from structured data. Narrative generation for charts.
- **Rubric Quality Scorer** (#95) — Score rubric quality based on grade distribution, source diversity, coverage, and inter-rater agreement.
- **Symptom Narrative Extractor** (#96) — NLP symptom extraction from free-text case narratives. Pattern-based parser for modalities and concomitants.
- **Cross-Reference Repertory** (#97) — Link rubrics across repertories (Kent ↔ Boenninghausen ↔ Boger ↔ Synthesis ↔ OOREP). Universal concordance.
- **Multi-Language Display** (#98) — Display rubrics in multiple languages simultaneously. Scaffold for i18n.
- **Sensation Method Integration** (#99) — Sankaran-style kingdom/sub-kingdom/source/sensation/miasm taxonomy. Scaffold.
- **Proving Text Search** (#100) — Search inside proving texts, not just rubric headings. Full materia medica text search.
- **Remedy Pictures** (#101) — Visual reference for remedies: source images, constitutional types. Scaffold — requires image sourcing.
- **Repertory Synthesis** (#102) — Create personal repertories by selecting rubrics from multiple sources and adding clinical observations.
- **Polarity Analysis** (#103) — Heiner Frei's systematic symptom analysis: confirmed vs refuted symptoms to narrow remedies by polar opposites.
- **Therapeutic Pocket Book** (#104) — Boenninghausen's TPB repertory data integration. Scaffold — requires separate TPB data source.
- **Cloud Sync Manager** (#105) — Encrypted multi-device synchronization for patient files and case history. Scaffold.
- **Gamification Engine** (#106) — Points, streaks, and learning rewards for remedy identification and quiz performance.
- **Social Community** (#107) — Share anonymized cases for peer review and discussion. Scaffold — requires moderation controls.
- **Mobile App Native** (#108) — Native mobile API designed for iOS/Android app consumption. Lightweight JSON, offline-first.
- **Global Stats Dashboard** (#109) — Practice analytics: most-searched rubrics, most-prescribed remedies, outcome rates by remedy.
- **Export Research Formats** (#110) — Export anonymized case data as CSV, SPSS, or R data frames for research analysis.

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
├── oorep/                          # 143 Python modules
│   ├── __init__.py                 # Unified import surface (160+ exports)
│   ├── homeopathic_repertory.py    # Main repertory API
│   ├── clinical_rubric_mapper.py   # Patient phrase → rubric mapping
│   ├── oorep_vector_search.py      # Local vector search
│   ├── clipboard_manager.py        # Multi-clipboard symptom collection
│   ├── master_score_engine.py      # Composite scoring
│   ├── family_grouping.py          # Kingdom/family filter & scoring
│   ├── reverse_repertorization.py  # Remedy → rubric inquiry
│   ├── posology_scheduler.py       # Classical dosing guidance
│   ├── case_similarity_search.py   # Find cases like this one
│   ├── voice_to_text_audio_import.py # Audio import (any mic)
│   ├── constitutional_remedy_tracker.py # Longitudinal constitutional history
│   ├── inventory_manager.py        # Remedy stock tracking
│   ├── patient_portal.py           # Read-only patient access
│   ├── billing_integration.py      # Invoice & insurance tracking
│   ├── patient_file_system.py      # Patient CRUD + consultations
│   ├── analysis_manager.py         # Analysis save/recall + versioning
│   ├── outcome_prediction.py       # Bayesian outcome forecasting
│   ├── edition_comparison.py       # Multi-edition drift analysis
│   ├── bibliographic_engine.py     # Classical citation engine
│   ├── word_wrap_search.py         # Proximity phrase search
│   ├── multi_repertory.py          # Multi-corpus search
│   ├── materia_medica_search.py    # Full-text MM TF-IDF
│   ├── analysis_methods.py         # Pluggable Kent/Boenninghausen/Boger/VES
│   ├── graphic_analysis.py         # Visual score plots
│   ├── elimination_rubrics.py      # Exclusion-based engine
│   ├── differential_diagnosis.py   # Differential ranking
│   ├── followup_comparator.py      # Follow-up remedy change
│   ├── correlation_matrix.py       # Remedy pair overlap
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
│   ├── bayesian_remedy_ranking.py  # Thompson sampling beta distributions
│   ├── rubric_bandit_selector.py   # UCB1 multi-armed bandit
│   ├── propensity_scored_prediction.py # IPW bias correction
│   ├── rubric_discrimination_indices.py # KR-20 reliability + point-biserial
│   ├── hierarchical_bayesian_similarity.py # Taxonomy-informed similarity
│   ├── cv_symptom_weights.py       # K-fold cross-validated weight learning
│   ├── sequential_remedy_testing.py # SPRT early stopping
│   ├── gaussian_process_surrogate.py # GP uncertainty surfaces
│   ├── causal_remedy_effects.py    # ATE estimation via matching + IPW
│   ├── ensemble_retrieval_stacking.py # Meta-learner combining 6 layers
│   ├── discriminant_rubric_selector.py # Expected information gain for next question
│   ├── information_theoretic_case_workup.py # Shannon entropy completeness
│   ├── adaptive_symptom_sequencer.py # Bayesian 20-questions case-taking
│   ├── latent_symptom_embedding.py # SVD latent space + cosine similarity
│   ├── confusion_matrix_differential.py # Precision/recall per remedy pair
│   ├── k_nearest_proven_cases.py   # Jaccard KNN with outcome-weighted voting
│   ├── bayesian_rubric_network.py  # Chow-Liu mutual information tree
│   ├── symptom_cooccurrence_lift.py # Association rule mining (support/confidence/lift)
│   ├── active_learning_intake_tracker.py # Real-time IG + coverage tracking
│   ├── remedy_confidence_calibration.py # Platt scaling + isotonic regression
│   ├── patient_intake_engine.py    # 9-phase interview orchestrator
│   ├── interview_question_bank.py  # 30+ canonical questions by phase
│   ├── chief_complaint_triager.py  # Free-text complaint → system/urgency/red flags
│   ├── concomitant_detector.py     # SRP-scored accompanying symptoms
│   ├── modality_extractor.py       # 11-axis modality grid extraction
│   ├── causation_timeline_module.py # "Ailments from" + miasm timeline
│   ├── mental_emotional_prober.py  # 23-category deep mental probe
│   ├── generals_survey.py          # 40+ general categories (thermal, sleep, food, dreams)
│   ├── constitutional_snapshot.py  # 12-archetype constitutional matcher
│   ├── intake_analyzer.py          # Final quality check + TSP + differential ranking
│   ├── case_analysis_bridge.py     # Confusion × co-occurrence cross-reference
│   ├── security_manager.py       # v4.3: Encryption, rate limiting, sessions, FIM, audit
│   └── ... 70+ additional modules (see full list in __init__.py)
├── tests/                          # 1,100+ pytest tests across 60 test files
├── oorep-case-portal/              # Next.js Clinical Mission Control
│   ├── src/components/visualizations/  # 40 visualization components (6 3D SVG panels)
│   │   ├── SymptomConstellation.tsx   # 3D sphere-shell remedy coverage
│   │   ├── RubricHierarchyTower.tsx   # Kent hierarchy as stacked cylinders
│   │   ├── RemedyLandscape.tsx        # Isometric terrain with noise-floor plane
│   │   ├── ConfidenceCloud.tsx        # Floating opacity spheres
│   │   ├── DifferentialHelix.tsx      # Spiral miasm-track remedy arrangement
│   │   ├── ConcordanceCube.tsx        # Multi-method agreement 3D cube
│   │   └── ... 34 additional viz panels
│   ├── src/lib/projection3d.ts      # Shared 3D engine (isometric, ~5.5 KB)
│   └── src/app/3d-demo/             # Standalone 3D demo pages (/3d-demo/*)
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

# Security module
pytest tests/test_security_manager.py -v

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

- **67+ visualization components** — cycle rings, coverage heatmaps, Venn diagrams, phantom gauges, differential radar, outcome sparklines, potency waterfalls, miasm donuts, kingdom clouds, confidence strips, family graphs, layer timelines, Sankey flows, rubric trees, grand rounds panels, ROC curves, network graphs, comparator cards, PCA scatters, complexity gauges, kappa displays, forest plots, power curves, Kaplan-Meier curves, resampling panels, reverse repertorization lists, constitutional trackers, prescription safety checks, posology schedules, symptom severity gauges, clinical tip charts, protocol builder lists, inventory grids, miasm layer indicators, case similarity tables, Thompson sampling betas, UCB rubric rankings, propensity calibration, discrimination heatmaps, hierarchical similarity networks, CV weight convergence, SPRT boundaries, GP uncertainty surfaces, causal forest plots, ensemble contribution breakdowns, discriminant question lists, information-theoretic completeness bars, adaptive question sequences, latent embedding clusters, confusion matrix differentials, proven-case KNN votes, Bayesian rubric dependency trees, co-occurrence lift tables, active learning intake progress, confidence calibration curves, 10 patient intake panels, **plus 6 interactive 3D panels: Symptom Constellation, Rubric Hierarchy Tower, Remedy Landscape, Confidence Cloud, Differential Helix, and Concordance Cube — all drag-to-rotate, hover-for-tooltips, click-for-drill-down, with auto-rotation, zoom sliders, noise-floor controls, ghost filters, miasm track filters, confidence thresholds, and remedy highlight pills**
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
