"""
Patient Outcome Prediction — Feature #28

Lightweight Bayesian/Laplace outcome prediction for remedy recommendations.
Based on patient history, symptom pattern, remedy track record, and classical
keynote coverage. No neural networks — fully interpretable and fast.

Usage:
    from oorep.outcome_prediction import OutcomePredictionEngine

    engine = OutcomePredictionEngine(
        db_path="data/feedback.db",
        repertory_json="data/rubric_to_remedies.json",
        materia_medica_json="data/remedy_keynotes.json"
    )

    # Predict outcomes for repertorization results
    results = [                                      # from Repertorization
        {"remedy": "Puls", "score": 28.5, "grade3": 4, "grade2": 2},
        {"remedy": "Ars",  "score": 24.0, "grade3": 3, "grade2": 3},
    ]
    predictions = engine.predict(
        patient_pseudonym="MrsJ2024",
        candidate_remedies=results,
        symptom_set=["anxiety", "restless", "night aggravation"],
    )
    # predictions = [
    #   {"remedy": "Puls", "outcome_likelihood": 0.72, "confidence": "high", ...},
    #   ...
    # ]
"""

import json
import math
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import sqlite3


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

BASE_PRIOR = 0.5          # Uniform prior when no data exists (Laplace smoothing)
LAP_ALPHA = 1.0           # Laplace smoothing count
MIN_SAMPLES_FOR_CONFIDENCE = 5
HIGH_CONF_THRESHOLD = 0.75
MED_CONF_THRESHOLD = 0.50

# Keynote coverage weights (classical keynotes carry more diagnostic weight)
KEYNOTE_WEIGHT_BASE = 0.30
RUBRIC_WEIGHT_BASE = 0.40
HISTORY_WEIGHT_BASE = 0.20
METADATA_WEIGHT_BASE = 0.10

# Grade values for scoring
GRADE_VALUES = {1: 1, 2: 2, 3: 3}


# ──────────────────────────────────────────────────────────────────────────────
# OutcomePredictionEngine
# ──────────────────────────────────────────────────────────────────────────────

class OutcomePredictionEngine:
    """
    Bayesian outcome prediction for homeopathic remedy selection.

    Combines four signal sources:
      1. **Rubric coverage** — how many rubrics match and their grades
      2. **Keynote coverage** — does the remedy cover the keynote symptoms?
      3. **Patient history** — prior outcomes with same remedy / similar profile
      4. **Remedy metadata** — kingdom/family patterns (optional)

    Ships with Laplace smoothing so it never produces 0.0 or 1.0 probabilities.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        repertory_json: Optional[Path] = None,
        materia_medica_json: Optional[Path] = None,
    ):
        self.db_path = db_path
        self.repertory_json = repertory_json
        self.mm_json = materia_medica_json

        # Caches
        self._history_cache: Dict[str, Dict[str, Any]] = {}
        self._rubric_cache: Optional[Dict[str, Any]] = None
        self._keynote_cache: Optional[Dict[str, Any]] = None

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Safely load a JSON file, returning {} on failure."""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _get_rubric_data(self) -> Dict[str, Any]:
        if self._rubric_cache is None and self.repertory_json:
            self._rubric_cache = self._load_json(Path(self.repertory_json))
        return self._rubric_cache or {}

    def _get_keynote_data(self) -> Dict[str, Any]:
        if self._keynote_cache is None:
            if self.mm_json:
                self._keynote_cache = self._load_json(Path(self.mm_json))
            else:
                self._keynote_cache = {}
        return self._keynote_cache

    # ── Patient history queries ───────────────────────────────────────────────

    def get_patient_history(self, pseudonym: str) -> Dict[str, Any]:
        """
        Return all prescription outcomes for a patient from the database.
        Returns {"prescriptions": [...], "overall_pattern": str}.
        """
        if not self.db_path:
            return {"prescriptions": [], "overall_pattern": "no_db"}

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT remedy_abbrev, potency, outcome_score, prescribed_date,
                   status, final_notes
            FROM prescriptions
            WHERE patient_id = ?
            ORDER BY prescribed_date ASC
            """,
            (pseudonym,),
        )

        rows = cursor.fetchall()
        conn.close()

        prescriptions = []
        for abbrev, potency, outcome, date, status, notes in rows:
            prescriptions.append({
                "remedy": abbrev,
                "potency": potency,
                "outcome_score": self._parse_outcome(outcome),
                "date": date,
                "status": status,
                "notes": notes,
            })

        # Determine overall pattern
        if not prescriptions:
            pattern = "no_history"
        else:
            successes = sum(1 for p in prescriptions if p["outcome_score"] and p["outcome_score"] > 0.5)
            pattern = "mixed" if successes < len(prescriptions) else "generally_positive"

        return {"prescriptions": prescriptions, "overall_pattern": pattern}

    @staticmethod
    def _parse_outcome(raw: Optional[str]) -> Optional[float]:
        """Parse outcome_score from DB (stored as 'improved','worsened','unchanged', or numeric)."""
        if raw is None:
            return None
        mapping = {"cured": 1.0, "improved": 0.75, "partial": 0.5, "unchanged": 0.25, "worsened": 0.0}
        return mapping.get(raw.lower(), None)

    def get_remedy_track_record(self, remedy_abbrev: str) -> Dict[str, Any]:
        """Return historical performance of a remedy across ALL patients."""
        if not self.db_path:
            return {"total_uses": 0, "avg_outcome": None, "success_rate": None}

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT outcome_score, status
            FROM prescriptions
            WHERE remedy_abbrev = ? AND outcome_score IS NOT NULL
            """,
            (remedy_abbrev,),
        )
        outcomes = []
        for row in cursor.fetchall():
            val = self._parse_outcome(row[0])
            if val is not None:
                outcomes.append(val)

        conn.close()

        if not outcomes:
            return {"total_uses": 0, "avg_outcome": None, "success_rate": None}

        avg = sum(outcomes) / len(outcomes)
        successes = sum(1 for v in outcomes if v > 0.5)
        return {
            "total_uses": len(outcomes),
            "avg_outcome": round(avg, 3),
            "success_rate": round(successes / len(outcomes), 3),
        }

    # ── Scoring components ──────────────────────────────────────────────────

    def _rubric_coverage_score(
        self,
        remedy: str,
        symptom_set: List[str],
        rubric_data: Dict[str, Any],
    ) -> float:
        """
        Score based on how many of the query symptoms appear in rubrics that
        contain this remedy. Uses grade-weighted matching.
        """
        if not rubric_data:
            return BASE_PRIOR

        rubric_remedies = rubric_data.get("rubrics", [])
        if not rubric_remedies:
            rubric_remedies = rubric_data.get("rubric_to_remedies", [])

        total_weight = 0.0
        match_weight = 0.0

        for rubric_entry in rubric_remedies:
            if not isinstance(rubric_entry, dict):
                continue
            rubric_text = rubric_entry.get("path", "") + " " + rubric_entry.get("text", "")
            rubric_tokens = set(rubric_text.lower().split())

            # Check if any symptom keyword appears in this rubric
            symptom_hits = sum(1 for s in symptom_set if s.lower() in rubric_text.lower())
            if symptom_hits == 0:
                continue

            # Look for remedy in this rubric's graded entries
            remedies = rubric_entry.get("remedies", [])
            max_grade = 0
            for rem in remedies:
                if rem.get("remedy", "").upper() == remedy.upper():
                    g = rem.get("grade", 1)
                    if g in GRADE_VALUES:
                        max_grade = max(max_grade, GRADE_VALUES[g])

            weight = symptom_hits * (1 + max_grade)  # grade boosts weight
            total_weight += weight
            if max_grade > 0:
                match_weight += weight

        if total_weight == 0:
            return BASE_PRIOR

        # Laplace-smoothed probability
        return (match_weight + LAP_ALPHA) / (total_weight + 2 * LAP_ALPHA)

    def _keynote_coverage_score(
        self,
        remedy: str,
        symptom_set: List[str],
        keynote_data: Dict[str, Any],
    ) -> float:
        """
        Score based on how many query symptoms are classical keynotes for
        this remedy. Uses materia medica keynote data.
        """
        if not keynote_data:
            return BASE_PRIOR

        keynotes = keynote_data.get(remedy.upper(), keynote_data.get(remedy, []))
        if not keynotes:
            return BASE_PRIOR

        keynote_text = " ".join(k if isinstance(k, str) else k.get("symptom", "") for k in keynotes)
        keynote_tokens = set(keynote_text.lower().split())

        matches = 0
        for symptom in symptom_set:
            sym_tok = set(symptom.lower().split())
            if sym_tok & keynote_tokens:
                matches += 1

        n_symptoms = max(len(symptom_set), 1)
        return (matches + LAP_ALPHA) / (n_symptoms + 2 * LAP_ALPHA)

    def _history_score(
        self,
        remedy: str,
        patient_pseudonym: str,
    ) -> float:
        """
        Score based on patient's prior experience with this remedy.
        Returns higher score if patient had positive outcomes with it before.
        """
        history = self.get_patient_history(patient_pseudonym)
        prescriptions = history.get("prescriptions", [])

        remedy_outcomes = [
            p["outcome_score"]
            for p in prescriptions
            if p["remedy"] == remedy and p["outcome_score"] is not None
        ]

        if not remedy_outcomes:
            return BASE_PRIOR  # No prior experience = neutral

        avg = sum(remedy_outcomes) / len(remedy_outcomes)
        return avg

    def _metadata_score(self, remedy: str, taxonomy: Optional[Dict] = None) -> float:
        """
        Optional metadata score (kingdom/family patterns). If no taxonomy data,
        returns neutral. This is a hook for future enrichment.
        """
        if not taxonomy:
            return BASE_PRIOR
        # Placeholder: could weight remedies by family success rates
        return BASE_PRIOR

    # ── Prediction API ────────────────────────────────────────────────────────

    def predict(
        self,
        patient_pseudonym: str,
        candidate_remedies: List[Dict[str, Any]],
        symptom_set: List[str],
        taxonomy: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Predict outcome likelihood for each candidate remedy.

        Parameters
        ----------
        patient_pseudonym: str
            The patient's pseudonym (links to DB history).
        candidate_remedies: List[dict]
            Each dict has at minimum: {"remedy": "Puls", "score": 28.5, ...}
            Typically the top-N from a repertorization.
        symptom_set: List[str]
            Chief complaint + concomitants as symptom strings.
        taxonomy: Optional[dict]
            Optional remedy taxonomy for family-pattern scoring.

        Returns
        -------
        List[dict]: Each with:
            - remedy (str)
            - outcome_likelihood (float, 0-1)
            - confidence (str: "high" | "medium" | "low")
            - components (dict): breakdown of sub-scores
        """
        rubric_data = self._get_rubric_data()
        keynote_data = self._get_keynote_data()

        results = []
        for cand in candidate_remedies:
            remedy = cand.get("remedy", "")
            if not remedy:
                continue

            # Individual component scores
            rubric_p = self._rubric_coverage_score(remedy, symptom_set, rubric_data)
            keynote_p = self._keynote_coverage_score(remedy, symptom_set, keynote_data)
            history_p = self._history_score(remedy, patient_pseudonym)
            meta_p = self._metadata_score(remedy, taxonomy)

            # Weighted combination (normalized to 0-1)
            combined = (
                RUBRIC_WEIGHT_BASE * rubric_p +
                KEYNOTE_WEIGHT_BASE * keynote_p +
                HISTORY_WEIGHT_BASE * history_p +
                METADATA_WEIGHT_BASE * meta_p
            )

            # Clamp to valid probability range
            likelihood = max(0.0, min(1.0, combined))

            # Confidence based on data volume
            track = self.get_remedy_track_record(remedy)
            n_samples = track.get("total_uses", 0)
            if n_samples >= MIN_SAMPLES_FOR_CONFIDENCE:
                conf = "high" if likelihood > HIGH_CONF_THRESHOLD else "medium" if likelihood > MED_CONF_THRESHOLD else "low"
            else:
                conf = "low"  # Insufficient historical data

            results.append({
                "remedy": remedy,
                "outcome_likelihood": round(likelihood, 4),
                "confidence": conf,
                "components": {
                    "rubric_coverage": round(rubric_p, 4),
                    "keynote_coverage": round(keynote_p, 4),
                    "patient_history": round(history_p, 4),
                    "metadata": round(meta_p, 4),
                },
                "track_record": track,
            })

        # Sort by likelihood descending
        results.sort(key=lambda x: x["outcome_likelihood"], reverse=True)
        return results

    # ── Update with outcome (learning) ──────────────────────────────────────────

    def record_outcome(
        self,
        patient_pseudonym: str,
        remedy: str,
        outcome: str,  # 'cured', 'improved', 'partial', 'unchanged', 'worsened'
        notes: str = "",
    ) -> bool:
        """
        Record a new outcome in the database. This updates the Bayesian priors
        for future predictions.

        Returns True on success.
        """
        if not self.db_path:
            return False

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Update via subquery since SQLite doesn't support ORDER BY in UPDATE
        cursor.execute(
            """
            UPDATE prescriptions
            SET outcome_score = ?, final_notes = ?
            WHERE prescription_id = (
                SELECT prescription_id FROM prescriptions
                WHERE patient_id = ? AND remedy_abbrev = ?
                ORDER BY prescribed_date DESC, prescription_id DESC
                LIMIT 1
            )
            """,
            (outcome, notes, patient_pseudonym, remedy),
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        # Invalidate cache
        self._history_cache.pop(patient_pseudonym, None)

        return affected > 0

    def get_feature_overview(self) -> Dict[str, Any]:
        """Return feature metadata for integration."""
        return {
            "feature_id": 28,
            "feature_name": "Patient Outcome Prediction",
            "method": "Bayesian with Laplace smoothing",
            "data_sources": ["prescriptions", "rubric_dataset", "materia_medica_keynotes"],
            "cold_start_capable": True,
            "interpretable": True,
            "version": "1.0",
        }
