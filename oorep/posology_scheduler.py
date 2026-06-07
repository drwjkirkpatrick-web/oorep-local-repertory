"""
Posology Scheduler — Classical Dosing & Repetition Guidance

Classical posology: when to repeat, when to wait, when to change potency,
when to antidote. Based on Hahnemann's Organon principles.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class PosologyScheduler:
    """
    Provide classical posology guidance for homeopathic prescribing.
    Includes potency selection, repetition timing, and LM potency series.
    """

    # Classical potency ladder
    CENTESIMAL_SCALE = ["6C", "12C", "30C", "200C", "1M", "10M", "50M", "CM"]
    LM_SCALE = ["LM1", "LM2", "LM3", "LM6", "LM12", "LM18", "LM24", "LM30"]

    # Classical posology rules
    REPETITION_RULES: Dict[str, Dict[str, Any]] = {
        "acute": {
            "30C": {"repeat": "every 2-4 hours", "stop_on": "improvement", "max_repetitions": 6},
            "200C": {"repeat": "twice daily", "stop_on": "improvement", "max_repetitions": 3},
        },
        "chronic": {
            "30C": {"repeat": "once weekly", "stop_on": "clear change", "assess_after": "4 weeks"},
            "200C": {"repeat": "once every 2 weeks", "stop_on": "clear change", "assess_after": "6 weeks"},
            "1M": {"repeat": "once monthly", "stop_on": "clear change", "assess_after": "8 weeks"},
        },
        "LM": {
            "LM1": {"repeat": "once daily in water", "stop_on": "aggravation or plateau", "assess_after": "2 weeks"},
            "LM3": {"repeat": "once daily in water", "stop_on": "aggravation or plateau", "assess_after": "2 weeks"},
        },
    }

    def __init__(self):
        pass

    def recommend(self, case_type: str, sensitivity: str = "average",
                    previous_potency: str = "", outcome: str = "") -> Dict[str, Any]:
        """
        Recommend potency and repetition schedule.
        sensitivity: low, average, high (determines starting potency)
        """
        if case_type == "acute":
            return self._acute_recommendation(sensitivity)
        elif case_type == "chronic":
            return self._chronic_recommendation(sensitivity, previous_potency, outcome)
        elif case_type == "LM_series":
            return self._lm_recommendation(previous_potency)
        else:
            return {"error": "Unknown case type"}

    def _acute_recommendation(self, sensitivity: str) -> Dict[str, Any]:
        potency = "30C" if sensitivity == "average" else "12C" if sensitivity == "high" else "200C"
        rules = self.REPETITION_RULES["acute"].get(potency, {})
        return {
            "case_type": "acute",
            "recommended_potency": potency,
            "repetition": rules.get("repeat", "every 4 hours"),
            "stop_criteria": rules.get("stop_on", "improvement"),
            "max_doses": rules.get("max_repetitions", 6),
            "next_step": "If no improvement after max doses, review remedy selection.",
        }

    def _chronic_recommendation(self, sensitivity: str, previous: str,
                                outcome: str) -> Dict[str, Any]:
        # Determine next potency
        if not previous:
            potency = "30C" if sensitivity == "average" else "12C" if sensitivity == "high" else "200C"
        else:
            potency = self._next_potency(previous, outcome)

        rules = self.REPETITION_RULES["chronic"].get(potency, {})
        return {
            "case_type": "chronic",
            "recommended_potency": potency,
            "repetition": rules.get("repeat", "once weekly"),
            "stop_criteria": rules.get("stop_on", "clear change"),
            "assess_after": rules.get("assess_after", "4 weeks"),
            "previous_potency": previous,
            "outcome_basis": outcome,
        }

    def _lm_recommendation(self, current_lm: str) -> Dict[str, Any]:
        if not current_lm:
            return {"recommended_potency": "LM1", "repeat": "once daily in 4oz water"}
        next_lm = self._next_lm(current_lm)
        return {
            "case_type": "LM_series",
            "current_lm": current_lm,
            "recommended_potency": next_lm,
            "repeat": "once daily in 4oz water",
            "notes": "Increase potency when improvement plateaus for 2+ weeks.",
        }

    def _next_potency(self, current: str, outcome: str) -> str:
        idx = self.CENTESIMAL_SCALE.index(current) if current in self.CENTESIMAL_SCALE else 2
        if outcome == "aggravation":
            return self.CENTESIMAL_SCALE[max(0, idx - 1)]
        elif outcome == "no_change":
            return self.CENTESIMAL_SCALE[min(len(self.CENTESIMAL_SCALE) - 1, idx + 1)]
        else:
            return self.CENTESIMAL_SCALE[min(len(self.CENTESIMAL_SCALE) - 1, idx + 1)]

    def _next_lm(self, current: str) -> str:
        idx = self.LM_SCALE.index(current) if current in self.LM_SCALE else 0
        return self.LM_SCALE[min(len(self.LM_SCALE) - 1, idx + 1)]

    def potency_ladder(self, scale: str = "centesimal") -> List[str]:
        return self.CENTESIMAL_SCALE if scale == "centesimal" else self.LM_SCALE

    def validate_prescription(self, remedy: str, potency: str,
                               case_type: str) -> Dict[str, Any]:
        """Validate a prescription against classical rules."""
        errors = []
        warnings = []

        if potency not in self.CENTESIMAL_SCALE and potency not in self.LM_SCALE:
            errors.append(f"Unknown potency: {potency}")

        if case_type == "acute" and potency in ["1M", "10M", "50M", "CM"]:
            warnings.append("High potencies in acute cases are unusual. Verify remedy certainty.")

        if case_type == "chronic" and potency in ["6C", "12C"]:
            warnings.append("Low potencies in chronic cases may be insufficient. Consider 30C or higher.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
