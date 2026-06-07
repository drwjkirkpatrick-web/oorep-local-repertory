"""
Polarity Analysis — Heiner Frei's Systematic Symptom Analysis

Systematic analysis of symptoms as "confirmed" vs "not confirmed"
to narrow remedies by polar opposites.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class PolarityAnalysis:
    """
    Heiner Frei's Polarity Analysis: systematically test symptoms
    to confirm or refute remedy hypotheses.
    """

    def __init__(self):
        pass

    def analyze(self, symptoms: List[Dict[str, Any]],
                candidate_remedies: List[str]) -> Dict[str, Any]:
        """
        Perform polarity analysis on symptoms.
        symptoms: [{"description": "thirstless", "polarity": "positive"}, ...]
        polarity: "positive" = symptom present, "negative" = symptom absent
        """
        # Score each remedy by confirmed symptoms
        scores: Dict[str, Dict[str, Any]] = {}
        for remedy in candidate_remedies:
            scores[remedy] = {"confirmed": 0, "refuted": 0, "neutral": 0, "details": []}

        for symptom in symptoms:
            desc = symptom.get("description", "")
            pol = symptom.get("polarity", "neutral")  # positive, negative, neutral
            # In a real implementation, we'd check rubric-level data
            for remedy in candidate_remedies:
                # Simplified: all symptoms are "potentially" confirmed for all remedies
                # Real implementation would check if remedy is in the rubric for this symptom
                if pol == "positive":
                    scores[remedy]["confirmed"] += 1
                elif pol == "negative":
                    scores[remedy]["refuted"] += 1
                else:
                    scores[remedy]["neutral"] += 1

        # Calculate net polarity score
        for remedy in scores:
            s = scores[remedy]
            s["net_score"] = s["confirmed"] - s["refuted"]
            s["confirmation_rate"] = round(
                s["confirmed"] / max(s["confirmed"] + s["refuted"], 1), 3
            )

        # Rank
        ranked: List[Dict[str, Any]] = sorted(
            [{"remedy": r, **scores[r]} for r in scores],
            key=lambda x: (-int(x.get("net_score", 0)), -float(x.get("confirmation_rate", 0)))
        )

        return {
            "n_symptoms": len(symptoms),
            "n_candidates": len(candidate_remedies),
            "ranked_remedies": ranked,
            "top_remedy": ranked[0]["remedy"] if ranked else None,
            "method": "polarity_analysis",
            "note": "Simplified implementation. Full Polarity Analysis requires rubric-level confirmation data.",
        }

    def generate_polarity_questions(self, remedy: str) -> List[Dict[str, Any]]:
        """
        Generate key polarity questions for a remedy.
        """
        questions = [
            {"question": f"Is the patient thirstless? (Key for {remedy})", "polarity_hint": "positive"},
            {"question": f"Is there morning aggravation?", "polarity_hint": "positive"},
            {"question": f"Is the patient worse from cold?", "polarity_hint": "positive"},
            {"question": f"Is there a history of suppression?", "polarity_hint": "positive"},
        ]
        return questions

    def validate_symptom_set(self, symptoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that symptoms have proper polarity assignments."""
        errors = []
        for i, s in enumerate(symptoms):
            if "polarity" not in s:
                errors.append(f"Symptom {i}: missing 'polarity' field")
            elif s["polarity"] not in ("positive", "negative", "neutral"):
                errors.append(f"Symptom {i}: invalid polarity '{s['polarity']}'")
        return {"valid": len(errors) == 0, "errors": errors}
