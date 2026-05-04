# OOREP Local Homeopathic Repertory

A **fast, offline, open-source homeopathic repertory** built on [OOREP](https://www.oorep.com/) (Open Online Repertory) data, enhanced with modern multi-layer search, clinical phrase mapping, and remedy outcome tracking.

> **Version:** 1.6 | **License:** GPL v3 | **Data:** 2,432 remedies × 143,408 rubrics × 1.36M remedy-grade links

---

## Why Build Your Own Repertory?

- **No subscriptions** — free forever, your data stays yours
- **No cloud dependency** — works offline, even in remote clinic settings
- **No vendor lock-in** — add custom rubrics, remedies, or repertory sources freely
- **Clinical time-savers** — intelligent search layers surface the simillimum in seconds, not minutes
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

# Use it
python -c "
from oorep import HomeopathicRepertory
rep = HomeopathicRepertory(data_dir='data')
print(rep.get_stats())
"
```

---

## Core Features

### 1. Fully Local & Offline
No API calls, no cloud servers, no subscription gates. Your repertory lives on your machine.

### 2. Memory-Safe Data Extraction
The 1.36M remedy-rubric links are processed in **batched streaming passes** (150K links per batch) to avoid the memory exhaustion that would crash a naive single-pass load. Rubrics stream at 20K per batch. Small systems handle it fine.

### 3. Lightning-Fast Lexical Search
Instant token-matched rubric lookup. Type `"thirst small sips"` and see Kent rubrics in milliseconds.

### 4. Local Vector Semantic Search
Offline random-projection vectors (384-dim, float16) let you search by **meaning**, not just exact words. No API keys. No fees.

### 5. Hybrid Retrieval Fusion
Combines lexical precision + vector semantic reach + token overlap into one ranked candidate list.

### 6. Clinical Rubric Mapper
Patient says `"can't sleep after 3am"` → system expands to sleep/sleeplessness/waking/after midnight. You review before scoring.

### 7. Classical Grade-Only Scoring
Retrieval finds rubrics; **Kent grades rank remedies**. Semantic similarity never distorts classical repertory arithmetic. Pure methodology.

### 8. Multi-Symptom Repertorization
Enter a full symptom set, get a ranked remedy table scored by summing classical grades across matched rubrics.

### 9. Rare Remedy Triangulation
Cross-reference confirmed rubrics against lesser-known remedies. Surface the unusual simillimum broad repertories bury.

### 10. Remedy Outcome Tracking
Log prescriptions and follow-ups (cured, improved, unchanged, worsened) in SQLite. Build your own evidence base.

### 11. LLM-Powered SOAP Case Intake ⭐
Paste a full SOAP note and a **large language model reads it like a senior clinician**—parsing Subjective narrative into structured symptoms, filtering normal vitals and exam boilerplate, and preserving the *contextual meaning* of each complaint. The LLM understands temporality, concomitance, and modalities in natural language, then maps them to the precise rubric language the repertory speaks.

### 12. Intelligent Fuzzy Rubric Matching ⭐
**The real magic is here.** After the LLM extracts symptoms, it performs *intelligent fuzzy matching* against 143,408 rubrics—finding semantically close equivalents even when wording differs. "Pressure behind eyes worse in warm room" maps to "Head, pain, pressing, warm room agg." The LLM preserves clinical context, handles negations, and resolves ambiguous phrasing so the **right rubric is never missed because the patient used different words**.

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

### Clinical Rubric Mapper (Practitioner Review)

```python
from oorep import HomeopathicRepertory, ClinicalRubricMapper

rep = HomeopathicRepertory(data_dir="data")
mapper = ClinicalRubricMapper(rep)

# Normalize patient language
candidates = mapper.suggest_candidates(
    "can't sleep after 3am",
    limit=5,
    retrieval="hybrid"
)

# Candidates arrive as "pending" — you review before scoring
for c in candidates:
    print(f"[{c['review_status']}] {c['rubric']}")

# Accept confirmed rubrics and repertorize
results = mapper.repertorize_accepted_rubrics(candidates, top_n=10)
```

### Build Vector Index (One-time Setup)

```python
rep = HomeopathicRepertory(data_dir="data")
rep.build_vector_index(source=None, dim=384, dtype="float16")
# Produces data/indexes/oorep_vector_index.npz
```

### Outcome Tracking

```python
from scripts.remedy_feedback import RemedyFeedbackSystem

feedback = RemedyFeedbackSystem()

# Record a prescription
prescription = feedback.record_prescription(
    patient_id="anon-123",
    remedy="Arsenicum Album",
    rubrics_treated=["thirst small quantities", "anxiety health"],
    potency="30C",
    dosing="twice daily"
)

# Follow-up after 4 weeks
feedback.record_followup(
    prescription_id=prescription.id,
    outcome="improved",
    symptom_changes={"thirst": 2, "anxiety": 3}  # severity 1-5 scale
)
```

---

## Project Structure

```
oorep-local-repertory/
├── oorep/                          # Core Python package
│   ├── __init__.py
│   ├── homeopathic_repertory.py    # Main repertory API
│   ├── clinical_rubric_mapper.py   # Patient phrase → rubric mapping
│   ├── oorep_vector_search.py      # Local vector search
│   └── rare_remedy_triangulator.py # Unusual remedy discovery
├── scripts/
│   ├── extract_oorep.py            # Extract OOREP SQL → JSON
│   └── remedy_feedback.py          # Prescription outcome tracking
├── tests/
│   ├── conftest.py
│   ├── test_clinical_rubric_mapper.py
│   └── test_hybrid_repertory.py
├── examples/
│   └── basic_usage.py              # Copy-paste starter code
├── data/                           # Extracted OOREP JSON (gitignored)
│   ├── remedies.json
│   ├── rubrics.json
│   ├── rubric_search_index.json
│   ├── rubric_to_remedies.json
│   └── indexes/                    # Generated vector artifacts
├── README.md
├── LICENSE
├── requirements.txt
└── pyproject.toml
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
- ~120MB disk for extracted JSON data
- ~2MB for vector index (384-dim float16)

---

## Testing

```bash
pip install pytest
pytest tests/ -v
```

Tests cover:
- Clinical rubric mapper normalization and practitioner review flow
- Hybrid retrieval with classical grade-only scoring
- Remedy deduplication and edge cases

---

## Clinical Disclaimer

This software is for **educational and reference purposes** and is **not intended to diagnose, treat, cure, or prevent any disease**. It is designed to support licensed practitioners in their clinical reasoning, not replace it. Always use professional judgment. Ensure you carry active malpractice insurance and comply with your jurisdiction's telehealth and prescribing regulations.

---

## License

GPL v3 — same as upstream OOREP. See [LICENSE](LICENSE).

---

## Related Projects

- **Upstream OOREP:** https://github.com/nondeterministic/oorep
- **OOREP Case Portal (Next.js):** Practitioner-facing web frontend with Stripe payments and PDF generation
- **Hermes Agent Integration:** Voice case intake, Telegram status checks, Mission Control dashboard

---

*Built with care for the homeopathic community. Open source, open data, open minds.*