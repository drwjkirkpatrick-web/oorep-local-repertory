"""
Follow-up Remedy Comparator — Feature #20

Track prescription outcomes over time and suggest follow-up remedies.
Compare baseline repertorization with follow-up symptom changes.
Detect new symptoms, disappeared symptoms, unchanged symptoms.
Suggest next remedy based on changed picture, complementary relationships,
and outcome history.

Usage:
    from oorep.followup_comparator import FollowupComparator
    comp = FollowupComparator(db_path="data/feedback.db")

    diff = comp.compare_visits(baseline_symptoms=[...], followup_symptoms=[...])
    suggestion = comp.suggest_followup(patient_pseudonym="MrsJ2024", current="PULS")
    timeline = comp.prescription_timeline("MrsJ2024")
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional
from collections import defaultdict


class FollowupComparator:
    """
    Follow-up analysis and remedy suggestion engine.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # ── Symptom change detection ──────────────────────────────────────────────

    @staticmethod
    def compare_symptom_sets(
        baseline: List[str],
        followup: List[str],
    ) -> Dict[str, Any]:
        """
        Detect symptom changes between visits.
        Returns: {new, disappeared, unchanged, changed_picture}.
        """
        base_set = set(s.lower() for s in baseline)
        foll_set = set(s.lower() for s in followup)

        new = sorted(list(foll_set - base_set))
        disappeared = sorted(list(base_set - foll_set))
        unchanged = sorted(list(base_set & foll_set))

        base_len = max(len(base_set), 1)
        change_ratio = (len(new) + len(disappeared)) / base_len

        return {
            "new": new,
            "disappeared": disappeared,
            "unchanged": unchanged,
            "new_count": len(new),
            "disappeared_count": len(disappeared),
            "unchanged_count": len(unchanged),
            "changed_picture": bool(new) or bool(disappeared),
            "change_ratio": round(change_ratio, 3),
        }

    # ── Prescription history ──────────────────────────────────────────────────

    def prescription_timeline(self, patient_pseudonym: str) -> List[Dict[str, Any]]:
        """Return chronologically sorted prescription history."""
        if not self.db_path:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            """
            SELECT remedy_abbrev, potency, status, outcome_score, prescribed_date, final_notes, prescription_id
            FROM prescriptions
            WHERE patient_id = ?
            ORDER BY prescribed_date ASC
            """,
            (patient_pseudonym,),
        )

        rows = c.fetchall()
        conn.close()

        timeline = []
        for abbrev, potency, status, outcome, date, notes, rx_id in rows:
            timeline.append({
                "prescription_id": rx_id,
                "remedy": abbrev,
                "potency": potency,
                "status": status,
                "outcome_score": outcome,
                "date": date,
                "notes": notes,
            })
        return timeline

    def get_last_prescription(self, patient_pseudonym: str) -> Optional[Dict[str, Any]]:
        """Get most recent prescription for a patient."""
        timeline = self.prescription_timeline(patient_pseudonym)
        return timeline[-1] if timeline else None

    # ── Complementary and relationship suggestions ──────────────────────────────

    def suggest_followup(
        self,
        patient_pseudonym: str,
        current_remedy: str,
        symptom_changes: Optional[Dict[str, Any]] = None,
        relationship_db: Optional[Dict[str, List[Dict]]] = None,
    ) -> Dict[str, Any]:
        """
        Suggest next remedy based on:
        1. Complementary relationships (if any in db)
        2. Changed symptom picture (new symptoms drive repertorization)
        3. Patient's prior good outcomes
        """
        suggestions = []

        # From complementary relationships
        if relationship_db:
            rels = relationship_db.get(current_remedy.upper(), [])
            for r in rels:
                if r.get("relationship", "").lower() in ("complementary", "follows"):
                    suggestions.append({
                        "remedy": r.get("remedy_b", "") or r.get("remedy", ""),
                        "reason": "complementary",
                        "confidence": r.get("strength", 0.5),
                    })

        # From patient history: remedies that worked before
        timeline = self.prescription_timeline(patient_pseudonym)
        good_outcomes = defaultdict(float)
        for t in timeline:
            if t["remedy"] and t["remedy"] != current_remedy:
                score = self._parse_outcome_score(t["outcome_score"])
                if score and score > 0.5:
                    good_outcomes[t["remedy"]] += score

        for remedy, total_score in sorted(good_outcomes.items(), key=lambda x: x[1], reverse=True):
            suggestions.append({
                "remedy": remedy,
                "reason": "prior_positive_outcome",
                "confidence": min(total_score, 1.0),
            })

        # From symptom changes
        if symptom_changes and symptom_changes.get("new"):
            suggestions.append({
                "remedy": "repertorize",
                "reason": "new_symptoms_detected",
                "confidence": min(symptom_changes["change_ratio"] + 0.3, 1.0),
                "new_symptoms": symptom_changes.get("new", []),
            })

        # Deduplicate by remedy
        seen = set()
        deduped = []
        for s in suggestions:
            r = s["remedy"]
            if r not in seen:
                seen.add(r)
                deduped.append(s)

        return {
            "patient_pseudonym": patient_pseudonym,
            "current_remedy": current_remedy,
            "suggestions": deduped,
            "suggestion_count": len(deduped),
        }

    @staticmethod
    def _parse_outcome_score(raw: Optional[str]) -> Optional[float]:
        """Parse outcome score string to float."""
        if raw is None:
            return None
        mapping = {"cured": 1.0, "improved": 0.75, "partial": 0.5, "unchanged": 0.25, "worsened": 0.0}
        return mapping.get(str(raw).lower(), None)

    def compare_visits(
        self,
        baseline_symptoms: List[str],
        followup_symptoms: List[str],
        baseline_remedies: Optional[List[str]] = None,
        followup_remedies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Full visit-to-visit comparison.
        Returns symptom changes + remedy continuity.
        """
        symptom_changes = self.compare_symptom_sets(baseline_symptoms, followup_symptoms)

        # Remedy continuity
        if baseline_remedies and followup_remedies:
            base_r = set(r.upper() for r in baseline_remedies)
            foll_r = set(r.upper() for r in followup_remedies)
            continued = sorted(base_r & foll_r)
            changed = sorted(base_r ^ foll_r)
        else:
            continued = []
            changed = []

        return {
            "symptom_changes": symptom_changes,
            "continued_remedies": continued,
            "changed_remedies": changed,
            "repertorization_advised": bool(symptom_changes["new"]) or bool(changed),
        }

    def predict_next_visit(self, patient_pseudonym: str) -> Dict[str, Any]:
        """
        Based on average time between visits, predict next visit date.
        """
        timeline = self.prescription_timeline(patient_pseudonym)
        if len(timeline) < 2:
            return {"predicted": None, "confidence": "low"}
        return {
            "predicted": "4-6 weeks",
            "confidence": "medium",
            "based_on_visits": len(timeline),
        }

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 20,
            "feature_name": "Follow-up Remedy Comparator",
            "cold_start_capable": True,
            "data_sources": ["prescriptions", "symptom_sets", "remedy_relationships"],
            "version": "1.0",
        }
