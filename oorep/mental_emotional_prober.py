"""
Mental/Emotional Prober (Module #137)

Deep-probe module for mental and emotional symptoms. In homeopathy, the
mental state is considered the deepest and most characteristic level
(Vithoulkas). This module:

  1. Probes classical mental symptoms with high discriminative value
  2. Captures fears, anxieties, irritabilities, delusions, dreams
  3. Identifies characteristic reactions (to consolation, contradiction, etc.)
  4. Surfaces the most discriminative mental questions for the case

Usage:
    from oorep.mental_emotional_prober import MentalEmotionalProber
    prober = MentalEmotionalProber()
    profile = prober.profile("I feel anxious in crowds, I want to be alone")
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


# Mental symptom lexicon with discriminative remedies
MENTAL_LEXICON: Dict[str, Dict[str, Any]] = {
    "fear_death": {
        "patterns": [r"\bfear\s+(?:of\s+)?death\b", r"\bafraid\s+(?:of|i'?m\s+gonna|i'?ll)\s+die\b"],
        "remedies": ["Acon.", "Ars.", "Calc.", "Phos.", "Stram.", "Cact."],
        "weight": 4,
    },
    "fear_alone": {
        "patterns": [r"\bfear\s+(?:of\s+being\s+)?alone\b", r"\bcan'?t\s+be\s+alone\b", r"\bneed\s+company\b"],
        "remedies": ["Ars.", "Phos.", "Stram.", "Puls.", "Kali-c."],
        "weight": 4,
    },
    "fear_dark": {
        "patterns": [r"\bfear\s+(?:of\s+)?(?:the\s+)?dark\b", r"\bafraid\s+of\s+the\s+dark\b"],
        "remedies": ["Stram.", "Acon.", "Phos.", "Caust.", "Med."],
        "weight": 3,
    },
    "fear_crowd": {
        "patterns": [r"\bfear\s+(?:of\s+)?crowd", r"\bafraid\s+(?:of|in)\s+crowds\b", r"\banxious\s+in\s+crowds\b"],
        "remedies": ["Acon.", "Arg-n.", "Puls.", "Gels."],
        "weight": 3,
    },
    "fear_suffocation": {
        "patterns": [r"\bfear\s+(?:of\s+)?(?:suffoc|chok|smother)", r"\bafraid\s+(?:i'?ll|of)\s+(?:suffoc|chok|smother)"],
        "remedies": ["Acon.", "Ars.", "Lach.", "Phos.", "Spong."],
        "weight": 4,
    },
    "irritability": {
        "patterns": [r"\b(?:irritab|angry|rage|easily\s+angered)\b"],
        "remedies": ["Nux-v.", "Cham.", "Hep.", "Staph.", "Bry."],
        "weight": 3,
    },
    "weeping": {
        "patterns": [r"\bweep(ing)?\b", r"\bcry(ing)?\b", r"\btear(s|ful|y)\b"],
        "remedies": ["Puls.", "Nat-m.", "Ign.", "Lyc.", "Sep."],
        "weight": 2,
    },
    "consolation_amel": {
        "patterns": [r"\bconsolation\s+(?:helps?|ameliorat|better)\b", r"\b(?:feel|feel\s+better)\s+when\s+(?:others\s+)?comfort"],
        "remedies": ["Puls."],
        "weight": 4,
    },
    "consolation_agg": {
        "patterns": [r"\bconsolation\s+(?:aggravat|worse|annoy)", r"\bdon'?t\s+(?:want|like)\s+(?:to\s+be\s+)?comfort"],
        "remedies": ["Nat-m.", "Sep.", "Sil.", "Lyc."],
        "weight": 4,
    },
    "company_amel": {
        "patterns": [r"\b(?:better|prefer|want)\s+company\b", r"\bdon'?t\s+(?:want|like)\s+to\s+be\s+alone\b"],
        "remedies": ["Puls.", "Stram.", "Kali-c.", "Phos."],
        "weight": 3,
    },
    "company_agg": {
        "patterns": [r"\b(?:worse|prefer)\s+(?:to\s+be\s+)?alone\b", r"\bdesire\s+to\s+be\s+alone\b", r"\bavoids?\s+company\b"],
        "remedies": ["Ars.", "Bry.", "Nux-v.", "Nat-m.", "Ign."],
        "weight": 3,
    },
    "indignation": {
        "patterns": [r"\bindign(at|ation)\b", r"\b(?:insulted|humiliated|disrespected)\b"],
        "remedies": ["Staph.", "Coloc.", "Aur.", "Pall."],
        "weight": 4,
    },
    "jealousy": {
        "patterns": [r"\bjealous(y)?\b", r"\benvious\b"],
        "remedies": ["Hyos.", "Lach.", "Apis.", "Stram.", "Puls."],
        "weight": 3,
    },
    "grief": {
        "patterns": [r"\bgrief\b", r"\bsad(ness)?\b", r"\bmourn(ing)?\b", r"\bbereave(d|ment)\b"],
        "remedies": ["Ign.", "Nat-m.", "Puls.", "Phos-ac.", "Caust."],
        "weight": 3,
    },
    "anxiety_health": {
        "patterns": [r"\banxi(ety|ous)\s+(?:about\s+)?health\b", r"\bhypochondria", r"\bworried\s+about\s+(?:my\s+)?health\b"],
        "remedies": ["Ars.", "Phos.", "Calc.", "Nux-v."],
        "weight": 4,
    },
    "anxiety_general": {
        "patterns": [r"\banxi(ety|ous)\b", r"\bworri(ed|ing)\b", r"\bnervous\b", r"\bapprehens(ion|ive)\b"],
        "remedies": ["Ars.", "Acon.", "Calc.", "Lyco.", "Phos."],
        "weight": 2,
    },
    "restlessness": {
        "patterns": [r"\brestless(ness)?\b", r"\bcan'?t\s+(?:sit|sit\s+still|rest)\b", r"\b(?:keep\s+moving|fidgety)\b"],
        "remedies": ["Ars.", "Acon.", "Rhus-t.", "Med.", "Tub."],
        "weight": 3,
    },
    "apathy": {
        "patterns": [r"\bapath(etic|y)\b", r"\bdon'?t\s+care\b", r"\bindifferent\b"],
        "remedies": ["Phos-ac.", "Sep.", "Mur-ac.", "Carb-v."],
        "weight": 3,
    },
    "fastidious": {
        "patterns": [r"\bfastidi(ous|um)\b", r"\bneat\s+freak\b", r"\borderly\b", r"\bperfectionist\b"],
        "remedies": ["Ars.", "Nux-v.", "Plat."],
        "weight": 3,
    },
    "domineering": {
        "patterns": [r"\bdomin(eer|ating)\b", r"\bbossy\b", r"\bcommanding\b", r"\btyrannical\b"],
        "remedies": ["Lyc.", "Plat.", "Verat.", "Hep."],
        "weight": 3,
    },
    "sensitive_criticism": {
        "patterns": [r"\b(?:sensitiv|oversensitiv|easily\s+offended)\s+(?:to\s+)?critic"],
        "remedies": ["Aur.", "Staph.", "Pall.", "Lyc.", "Nux-v."],
        "weight": 4,
    },
    "delusions": {
        "patterns": [r"\bdelusion(s)?\b", r"\b(?:imagines?|thinks?)\s+(?:that|he|she)\b", r"\bas\s+if\s+(?:being|someone|some\s+thing)\b"],
        "remedies": ["Stram.", "Hyos.", "Lach.", "Anac.", "Med."],
        "weight": 4,
    },
    "confusion": {
        "patterns": [r"\bconfus(ed|ion)\b", r"\b(?:dazed|disorient|brain\s+fog)\b"],
        "remedies": ["Acon.", "Bell.", "Gels.", "Nux-m.", "Phos-ac."],
        "weight": 3,
    },
}


@dataclass
class MentalSymptom:
    symptom_type: str                    # e.g. "fear_death"
    text: str
    weight: int                          # Repertory weight (1-4)
    discriminative_remedies: List[str]
    srp_score: float


@dataclass
class MentalEmotionalProfile:
    symptoms_detected: List[MentalSymptom]
    characteristic_remedies: List[str]   # Weighted by # of symptoms matching
    fear_spectrum: Dict[str, float]      # Fear subtypes and intensities
    company_response: Optional[str]      # "amelioration" / "aggravation" / "neutral"
    consolation_response: Optional[str]
    srp_signals: List[str]
    emotional_grade: int                 # 0-4 weighted average
    summary: str


class MentalEmotionalProber:
    """Probes and analyzes mental/emotional symptoms."""

    def __init__(self):
        # Pre-compile patterns
        self._lexicon: Dict[str, Dict[str, Any]] = {}
        for key, info in MENTAL_LEXICON.items():
            self._lexicon[key] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in info["patterns"]],
                "remedies": info["remedies"],
                "weight": info["weight"],
            }
        self._srp_markers = re.compile(
            r"\b(strange|weird|peculiar|unusual|uncommon|as\s+if|like\s+a|never|always|only)\b",
            re.IGNORECASE,
        )

    def profile(self, narrative: str) -> MentalEmotionalProfile:
        """Build a complete mental/emotional profile from a narrative."""
        if not narrative:
            return MentalEmotionalProfile(
                symptoms_detected=[],
                characteristic_remedies=[],
                fear_spectrum={},
                company_response=None,
                consolation_response=None,
                srp_signals=[],
                emotional_grade=0,
                summary="Empty narrative.",
            )

        detected: List[MentalSymptom] = []
        for key, info in self._lexicon.items():
            for pat in info["patterns"]:
                m = pat.search(narrative)
                if m:
                    srp = self._score_srp(m.group(0), narrative)
                    detected.append(MentalSymptom(
                        symptom_type=key,
                        text=m.group(0),
                        weight=info["weight"],
                        discriminative_remedies=list(info["remedies"]),
                        srp_score=srp,
                    ))
                    break  # One match per symptom type

        # Deduplicate by symptom_type (keep highest weight)
        seen = {}
        for s in detected:
            if s.symptom_type not in seen or s.weight > seen[s.symptom_type].weight:
                seen[s.symptom_type] = s
        detected = list(seen.values())

        # Sort by weight desc
        detected.sort(key=lambda s: (s.weight, s.srp_score), reverse=True)

        # Aggregate remedies by total weight
        remedy_weights: Dict[str, int] = defaultdict(int)
        for s in detected:
            for r in s.discriminative_remedies:
                remedy_weights[r] += s.weight
        characteristic = sorted(remedy_weights, key=lambda r: -remedy_weights[r])[:10]

        # Fear spectrum
        fear_spectrum: Dict[str, float] = {}
        for s in detected:
            if s.symptom_type.startswith("fear_"):
                fear_spectrum[s.symptom_type] = s.weight

        # Company response
        company_response = None
        if any(s.symptom_type == "company_amel" for s in detected):
            company_response = "amelioration"
        elif any(s.symptom_type == "company_agg" for s in detected):
            company_response = "aggravation"

        # Consolation response
        consolation_response = None
        if any(s.symptom_type == "consolation_amel" for s in detected):
            consolation_response = "amelioration"
        elif any(s.symptom_type == "consolation_agg" for s in detected):
            consolation_response = "aggravation"

        # SRP signals
        srp_signals = list(set(m.group(0).lower() for m in self._srp_markers.finditer(narrative)))

        # Emotional grade
        if detected:
            emotional_grade = max(s.weight for s in detected)
        else:
            emotional_grade = 0

        summary = self._build_summary(detected, characteristic, fear_spectrum, company_response, consolation_response)

        return MentalEmotionalProfile(
            symptoms_detected=detected,
            characteristic_remedies=characteristic,
            fear_spectrum=fear_spectrum,
            company_response=company_response,
            consolation_response=consolation_response,
            srp_signals=srp_signals,
            emotional_grade=emotional_grade,
            summary=summary,
        )

    def suggest_mental_questions(
        self,
        profile: MentalEmotionalProfile,
        max_questions: int = 5,
    ) -> List[str]:
        """Suggest follow-up mental questions to fill gaps."""
        suggestions: List[str] = []
        detected_types = {s.symptom_type for s in profile.symptoms_detected}

        if "fear_death" not in detected_types:
            suggestions.append("Do you have any specific fears, like fear of death or of being alone?")
        if "company_amel" not in detected_types and "company_agg" not in detected_types:
            suggestions.append("When you're not feeling well, do you prefer to be alone or with company?")
        if "consolation_amel" not in detected_types and "consolation_agg" not in detected_types:
            suggestions.append("When others try to comfort you, does it help or make things worse?")
        if not any(t.startswith("fear_") for t in detected_types):
            suggestions.append("Are there any fears that stand out? Health anxiety? Fear of suffocation?")
        if "sensitive_criticism" not in detected_types:
            suggestions.append("How do you react when someone criticizes you?")
        if not profile.srp_signals:
            suggestions.append("Is there anything strange, unusual, or peculiar that you notice about your mental state?")
        if "delusions" not in detected_types and "confusion" not in detected_types:
            suggestions.append("How is your memory and concentration? Any 'as if' sensations, like being in a dream?")

        return suggestions[:max_questions]

    def _score_srp(self, text: str, narrative: str) -> float:
        score = 0.3
        idx = narrative.lower().find(text.lower())
        if idx >= 0:
            window = narrative[max(0, idx - 50):idx + len(text) + 30].lower()
            score += min(0.5, len(self._srp_markers.findall(window)) * 0.15)
        return min(1.0, score)

    def _build_summary(
        self,
        symptoms: List[MentalSymptom],
        remedies: List[str],
        fears: Dict[str, float],
        company: Optional[str],
        consolation: Optional[str],
    ) -> str:
        lines = [
            f"Detected {len(symptoms)} mental symptom(s).",
        ]
        if remedies:
            lines.append(f"Top characteristic remedies: {', '.join(remedies[:5])}")
        if fears:
            lines.append(f"Fears: {', '.join(f'{k} (weight {int(v)})' for k, v in fears.items())}")
        if company:
            lines.append(f"Company response: {company}")
        if consolation:
            lines.append(f"Consolation response: {consolation}")
        return "\n".join(lines)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_mental_profile(narrative: str) -> MentalEmotionalProfile:
    """Quick helper to profile mental/emotional symptoms."""
    return MentalEmotionalProber().profile(narrative)
