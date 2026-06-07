"""
Follow-Up Prompt Generator — Automated Case Follow-Up Questions

Based on prescribed remedy and potency, suggest follow-up timing
and specific questions to ask the patient.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class FollowUpPromptGenerator:
    """
    Generate context-aware follow-up prompts based on remedy,
    potency, and case type.
    """

    # Remedy-specific follow-up patterns
    REMEDY_PATTERNS: Dict[str, Dict[str, Any]] = {
        "PULS": {"ask": ["Has the thirstlessness changed?", "Any change in mood/weeping?", "Better in open air?"], "timing_days": 7},
        "SULPH": {"ask": ["Any burning sensations?", "Appetite changes?", "Morning diarrhea?"], "timing_days": 14},
        "NUX-V": {"ask": ["Sleep quality?", "Irritability level?", "Digestive symptoms?"], "timing_days": 7},
        "LYC": {"ask": ["Confidence level?", "Digestive bloating?", "Right-sided symptoms?"], "timing_days": 14},
        "ARS": {"ask": ["Anxiety level?", "Restlessness?", "Thirst for small sips?"], "timing_days": 7},
        "BELL": {"ask": ["Heat/redness changes?", "Pain intensity?", "Sudden onset symptoms?"], "timing_days": 3},
        "ACON": {"ask": ["Fear/anxiety changes?", "Cold/chill symptoms?", "Sudden onset?"], "timing_days": 3},
        "SIL": {"ask": ["Suppuration tendencies?", "Coldness?", "Confidence?"], "timing_days": 21},
    }

    POTENCY_TIMING = {
        "6C": 3, "12C": 7, "30C": 7, "200C": 14, "1M": 21, "10M": 30, "50M": 45, "CM": 60,
        "LM1": 7, "LM2": 7, "LM3": 14, "LM6": 21, "LM18": 30, "LM30": 45,
    }

    def __init__(self):
        pass

    def generate(self, remedy: str, potency: str,
                 case_type: str = "chronic",
                 previous_remedy: str = "") -> Dict[str, Any]:
        """
        Generate follow-up prompt for a case.
        """
        # Base timing from potency
        base_days = self.POTENCY_TIMING.get(potency, 14)

        # Remedy-specific questions
        remedy_data = self.REMEDY_PATTERNS.get(remedy, {})
        questions = remedy_data.get("ask", [
            "How are you feeling overall?",
            "Any changes in your main complaint?",
            "Any new symptoms since the remedy?",
        ])
        remedy_timing = remedy_data.get("timing_days", base_days)

        # Adjust timing
        suggested_days = min(remedy_timing, base_days) if case_type == "acute" else max(remedy_timing, base_days)

        # Anticipation guidance
        anticipation = self._anticipation_guidance(remedy, case_type)

        return {
            "remedy": remedy,
            "potency": potency,
            "case_type": case_type,
            "suggested_follow_up_days": suggested_days,
            "questions_to_ask": questions,
            "anticipation": anticipation,
            "red_flags": self._red_flags(),
            "template": self._format_template(remedy, potency, questions, suggested_days),
        }

    def _anticipation_guidance(self, remedy: str, case_type: str) -> str:
        if case_type == "acute":
            return "Acute cases: expect change within hours to 1-2 days. If no change after 48h, consider remedy review."
        guides = {
            "SULPH": "May see initial aggravation of skin symptoms. Do not suppress.",
            "SIL": "Suppressed conditions may reappear. This is a positive sign.",
            "PULS": "Emotional sensitivity may shift before physical symptoms.",
            "LYC": "Confidence and digestive symptoms often improve first.",
            "NUX-V": "Sleep may improve before other symptoms.",
        }
        return guides.get(remedy, "Constitutional cases: allow 4-6 weeks before full assessment.")

    def _red_flags(self) -> List[str]:
        return [
            "Severe or worsening symptoms after remedy",
            "New symptoms not part of original picture (proving)",
            "No change after 3 doses in acute / 4 weeks in chronic",
            "Patient reports feeling 'never been worse'",
        ]

    def _format_template(self, remedy: str, potency: str,
                         questions: List[str], days: int) -> str:
        lines = [
            f"FOLLOW-UP: {remedy} {potency}",
            f"Schedule: {days} days from prescription",
            "",
            "Questions to ask:",
        ]
        for i, q in enumerate(questions, 1):
            lines.append(f"  {i}. {q}")
        lines += ["", "Red flags — seek immediate review if any occur:"]
        for rf in self._red_flags():
            lines.append(f"  • {rf}")
        return "\n".join(lines)

    def list_remedy_patterns(self) -> List[str]:
        return list(self.REMEDY_PATTERNS.keys())
