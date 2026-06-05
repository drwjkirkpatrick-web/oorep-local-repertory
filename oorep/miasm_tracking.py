"""
Miasm Tracking Integration — Feature #24

Classical miasm classification (Psora, Sycosis, Syphilis, Tubercular, Cancer)
linked to remedies, rubrics, and patient cases.
Track miasm progression over time. Suggest anti-miasmatic remedies.

Usage:
    from oorep.miasm_tracker import MiasmTracker
    tracker = MiasmTracker()

    m = tracker.classify_patient(symptoms=["slow recovery", "overproduction"])
    suggestions = tracker.suggest_remedies(miasm="sycosis", top_n=5)
    progression = tracker.track_over_time(patient_id="MrsJ2024", history=[...])
"""

from typing import Any, Dict, List, Optional
from collections import defaultdict
import sqlite3


# Classical miasm rubric mappings (simplified)
MIASM_RUBRIC_HINTS: Dict[str, List[str]] = {
    "psora": [
        "itching", "dry eruptions", "scratching ameliorates", "suppressed eruptions",
        "skin dry", "slow recovery", "chronic weakness", "sensitivity to cold",
    ],
    "sycosis": [
        "warts", "fungous excrescences", "overproduction", "excess mucus",
        "condylomata", "hysteria", "rheumatic pains", "fixed ideas",
    ],
    "syphilis": [
        "destruction", "ulceration", "bone pains", "night aggravation",
        "malformation", "deformities", "suppuration", "offensive discharges",
    ],
    "tubercular": [
        "emaciation", "night sweats", "hemorrhage", "desire for travel",
        "morning aggravation", "alternating states", "lymphatic enlargement",
    ],
    "cancer": [
        "indurations", "hard glands", "burning pains", "fetid odor",
        "slowly progressing", "cachexia", "fear of cancer", "old scars pain",
    ],
}

ANTI_MIASMATIC_REMEDIES: Dict[str, List[str]] = {
    "psora": ["SULPH", "PSOR", "GRAPH", "ARS"],
    "sycosis": ["MED", "THUJ", "NAT-S", "CAUST"],
    "syphilis": ["AUR", "SYPH", "MERC", "HEP"],
    "tubercular": ["TUB", "BAC", "PSOR", "SIL"],
    "cancer": ["CON", "SCIRR", "ARS-I", "CARB-AN"],
}


class MiasmTracker:
    """
    Miasm classification and tracking engine.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def classify_symptoms(self, symptoms: List[str]) -> Dict[str, float]:
        """
        Score each miasm by keyword overlap with symptoms.
        Returns {miasm: likelihood} (not normalized).
        """
        scored: Dict[str, float] = defaultdict(float)
        for miasm, hints in MIASM_RUBRIC_HINTS.items():
            for sym in symptoms:
                sym_lc = sym.lower()
                for hint in hints:
                    if hint in sym_lc or sym_lc in hint:
                        scored[miasm] += 1.0
        return dict(scored)

    def classify_patient(
        self,
        symptoms: List[str],
        known_miasm: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full miasm classification of a patient's symptom picture.
        """
        scores = self.classify_symptoms(symptoms)
        total = sum(scores.values()) or 1

        sorted_scores = sorted(
            [{"miasm": k, "score": v, "percentage": round(v / total * 100, 1)} for k, v in scores.items()],
            key=lambda x: x["score"],
            reverse=True,
        )

        top = sorted_scores[0] if sorted_scores else {"miasm": "unknown", "score": 0}

        return {
            "primary": top["miasm"],
            "primary_score": top["score"],
            "primary_percentage": top.get("percentage", 0),
            "all_scores": sorted_scores,
            "known_miasm": known_miasm,
            "symptoms_analyzed": len(symptoms),
        }

    def suggest_remedies(self, miasm: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Return anti-miasmatic remedies for a given miasm."""
        remedies = ANTI_MIASMATIC_REMEDIES.get(miasm.lower(), [])
        return [{"remedy": r, "miasm": miasm} for r in remedies[:top_n]]

    def track_over_time(
        self,
        patient_id: str,
        history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Track miasm progression over consultations.
        history: [{date, symptoms: [...], known_miasm}, ...].
        Returns list of per-visit classifications with delta.
        """
        timeline = []
        prev = None
        for entry in history:
            date = entry.get("date", "")
            symptoms = entry.get("symptoms", [])
            known = entry.get("known_miasm")

            classification = self.classify_patient(symptoms, known)

            delta = {}
            if prev:
                prev_prim = prev.get("primary", "")
                curr_prim = classification.get("primary", "")
                if prev_prim != curr_prim:
                    delta["shift"] = f"{prev_prim} -> {curr_prim}"
                delta["score_change"] = round(
                    classification.get("primary_score", 0) - prev.get("primary_score", 0), 2
                )

            timeline.append({
                "date": date,
                "classification": classification,
                "delta": delta,
            })
            prev = classification

        return timeline

    def remedy_miasm_affinity(self, remedy: str) -> List[str]:
        """Which miasms does a remedy typically address?"""
        rem_upper = remedy.upper().replace(".", "")
        matches = []
        for miasm, remedies in ANTI_MIASMATIC_REMEDIES.items():
            if rem_upper in [r.upper().replace(".", "") for r in remedies]:
                matches.append(miasm)
        return matches

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 24,
            "feature_name": "Miasm Tracking Integration",
            "miasms": list(MIASM_RUBRIC_HINTS.keys()),
            "anti_miasmatic_count": sum(len(v) for v in ANTI_MIASMATIC_REMEDIES.values()),
            "cold_start_capable": True,
            "version": "1.0",
        }
