# oorep-hermes-bridge

Hermes skill: Natural-language bridge to the local OOREP homeopathic repertory.

## What it does

Transforms conversational queries ("repertorize dry cough, hoarseness") into
OOREP API calls. Handles repertorization, remedy comparison, rare remedy
triangulation, rubric search, remedy lookup, and patient case memory.

## How Hermes loads it

Hermes auto-discovers skills from `~/.hermes/skills/<category>/<skill-name>/`.
This copy is mirrored from the skill directory for version control:

```
~/.hermes/skills/clinic/oorep-hermes-bridge/
```

## Commands supported

| Command | Example |
|---------|---------|
| Repertorize | `repertorize dry cough evening, throat pressing` |
| Compare | `compare Bromum and Hepar sulph` |
| Rare remedy | `rare remedy for hoarse voice, croup` |
| Profile | `profile for Arsenicum album` |
| Patient | `patient MrsJ2024` |
| Summary | `summary for MrsJ2024` |
| Timeline | `timeline MrsJ2024` |
| Pattern | `pattern MrsJ2024` |
| Suppression | `suppression MrsJ2024` |
| Search rubric | `search rubric throat pit` |
| Abbrev lookup | `what remedy is Brom?` |

## Patient case memory

When a patient command matches a pseudonym, it queries `data/feedback.db` for:
- Past prescriptions and outcomes
- Chronological timeline of visits
- Recurring rubric patterns (constitutional signals)
- Suppression history tracking

All patient data uses pseudonymized IDs only — no PHI stored.

## Files

- `scripts/oorep_bridge.py` — Main bridge logic, command parser, formatters
- `scripts/case_memory.py` — SQLite case persistence + timeline/pattern/suppression
- `scripts/test_bridge.py` — 12 integration tests covering all command types

## Run tests

```bash
python scripts/test_bridge.py
```

## Guardrails

- **Practitioner approval required**: Prescriptions stored with
  `prescriber_ack=False` by default; must be approved before becoming active.
- **PHI minimization**: Pseudonymized patient IDs only.
- **Red-flag awareness**: System does not replace clinical judgment.
