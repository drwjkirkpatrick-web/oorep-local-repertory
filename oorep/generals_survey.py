"""
Generals Survey (Module #138)

Surveys the "generals" — the whole-person characteristics that pervade
the case. Generals are high-weight differentiators (most are graded 3-4
in the repertory) and they paint the constitutional picture.

Classic "generals" include:
  - Sleep (position, dreams, hours, patterns)
  - Appetite (hunger, thirst, cravings, aversions)
  - Thermal state (warm-blooded vs cold)
  - Weather preferences (dry vs damp, cold vs hot)
  - Sweat (when, where, smell)
  - Energy patterns (morning vs evening)
  - Food cravings/aversions (salt, sweet, fat, eggs, etc.)
  - Side affinity (left, right, both)

Usage:
    from oorep.generals_survey import GeneralsSurvey
    survey = GeneralsSurvey()
    profile = survey.profile("I sleep on my left side, crave salt, hate warm weather")
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


# Generals lexicon: each general is a category with patterns and discriminative remedies
GENERALS_LEXICON: Dict[str, Dict[str, Any]] = {
    "thermal_warm_blooded": {
        "patterns": [
            r"\b(?:warm[\s-]blooded|hot[\s-]blooded|love\s+cool|dislike\s+warmth|"
            r"worse\s+(?:from\s+)?(?:heat|warmth)|better\s+(?:from\s+)?(?:cool|cold|open\s+air))",
            r"\boverheats?\b",
        ],
        "remedies": ["Puls.", "Sulph.", "Lyc.", "Med.", "Calc-p.", "Verat."],
        "weight": 4,
    },
    "thermal_cold_blooded": {
        "patterns": [
            r"\b(?:cold[\s-]blooded|chilly|always\s+cold|"
            r"worse\s+(?:from\s+)?(?:cold|cool)|better\s+(?:from\s+)?(?:warmth|warm))",
            r"\bcold\s+natured\b",
        ],
        "remedies": ["Ars.", "Calc.", "Sil.", "Hep.", "Puls.", "Nux-v."],
        "weight": 4,
    },
    "sleep_position_back": {
        "patterns": [r"\bsleep(?:s|ing)?\s+(?:on\s+)?(?:the\s+)?back\b"],
        "remedies": ["Ars.", "Nux-v.", "Puls.", "Rhus-t."],
        "weight": 3,
    },
    "sleep_position_left_side": {
        "patterns": [r"\bsleep(?:s|ing)?\s+(?:on\s+)?(?:the\s+)?left\s+side\b"],
        "remedies": ["Phos.", "Nat-m.", "Lyc.", "Spong."],
        "weight": 3,
    },
    "sleep_position_right_side": {
        "patterns": [r"\bsleep(?:s|ing)?\s+(?:on\s+)?(?:the\s+)?right\s+side\b"],
        "remedies": ["Calc.", "Ars.", "Nux-v."],
        "weight": 3,
    },
    "sleep_position_knees": {
        "patterns": [r"\b(?:knees?\s+(?:to|2)\s+chest|knees?\s+up|curled\s+up)\b"],
        "remedies": ["Med.", "Coloc.", "Mag-p.", "Stann."],
        "weight": 4,
    },
    "sleep_arms_above_head": {
        "patterns": [r"\b(?:arms?\s+above\s+head|arms?\s+over\s+head)\b"],
        "remedies": ["Ars.", "Phos.", "Puls."],
        "weight": 4,
    },
    "dreams_fire": {
        "patterns": [r"\b(?:dreams?\s+(?:of|about)\s+)?fire\b"],
        "remedies": ["Ars.", "Phos.", "Lach.", "Hep."],
        "weight": 3,
    },
    "dreams_water": {
        "patterns": [r"\b(?:dreams?\s+(?:of|about)\s+)?water\b"],
        "remedies": ["Phos.", "Ars.", "Med.", "Lach."],
        "weight": 3,
    },
    "dreams_falling": {
        "patterns": [r"\b(?:dreams?\s+(?:of|about)\s+)?fall(ing)?\b"],
        "remedies": ["Thuj.", "Calc.", "Lyc."],
        "weight": 3,
    },
    "dreams_snakes": {
        "patterns": [r"\b(?:dreams?\s+(?:of|about)\s+)?snakes?\b"],
        "remedies": ["Lach.", "Arg-n."],
        "weight": 3,
    },
    "dreams_animals": {
        "patterns": [r"\b(?:dreams?\s+(?:of|about)\s+)?animals?\b"],
        "remedies": ["Puls.", "Stram."],
        "weight": 2,
    },
    "dreams_death": {
        "patterns": [r"\b(?:dreams?\s+(?:of|about)\s+)?dead\s+(?:people|person)\b"],
        "remedies": ["Ars.", "Phos.", "Lach."],
        "weight": 3,
    },
    "appetite_good": {
        "patterns": [r"\b(?:good|ravenous|excessive|big)\s+appetite\b"],
        "remedies": ["Petr.", "Calc.", "Lyc.", "Iod."],
        "weight": 2,
    },
    "appetite_poor": {
        "patterns": [r"\b(?:poor|no|low|diminished|lost)\s+appetite\b"],
        "remedies": ["Ars.", "Puls.", "Calc.", "Sil."],
        "weight": 2,
    },
    "thirst_large": {
        "patterns": [r"\b(?:large|great|much|excessive|drinks\s+(?:a\s+lot|plenty))\s+thirst\b"],
        "remedies": ["Ars.", "Bry.", "Verat.", "Nat-m.", "Phos."],
        "weight": 3,
    },
    "thirst_small": {
        "patterns": [r"\b(?:small\s+quantit|drinks?\s+(?:little|sips)|sips?\s+(?:water|often))\b"],
        "remedies": ["Ars.", "Puls.", "Chin.", "Ant-t."],
        "weight": 4,
    },
    "thirstless": {
        "patterns": [r"\bthirstless\b", r"\bno\s+thirst\b"],
        "remedies": ["Puls.", "Apis.", "Gels.", "Nux-m."],
        "weight": 3,
    },
    "craving_salt": {
        "patterns": [r"\b(?:craves?|cravings?|loves?|desire[s]?)\s+salt\b"],
        "remedies": ["Phos.", "Nat-m.", "Calc.", "Ars.", "Lyc."],
        "weight": 4,
    },
    "craving_sweet": {
        "patterns": [r"\b(?:craves?|loves?|desire[s]?)\s+(?:sweet|sugar|chocolate)\b"],
        "remedies": ["Lyc.", "Calc.", "Sulph.", "Arg-n."],
        "weight": 3,
    },
    "craving_ice": {
        "patterns": [r"\b(?:craves?|loves?|desire[s]?)\s+ice\b"],
        "remedies": ["Calc-p.", "Phos.", "Verat."],
        "weight": 4,
    },
    "craving_eggs": {
        "patterns": [r"\b(?:craves?|loves?|desire[s]?)\s+eggs?\b"],
        "remedies": ["Calc-p.", "Calc."],
        "weight": 4,
    },
    "craving_fat": {
        "patterns": [r"\b(?:craves?|loves?|desire[s]?)\s+(?:fat|butter|bacon)\b"],
        "remedies": ["Calc-p.", "Sulph.", "Nux-v."],
        "weight": 3,
    },
    "aversion_fat": {
        "patterns": [r"\b(?:avoids?|aversion\s+to|dislikes?|hates?)\s+fat\b"],
        "remedies": ["Puls.", "Hep.", "Carb-v.", "Cycl."],
        "weight": 3,
    },
    "aversion_meat": {
        "patterns": [r"\b(?:avoids?|aversion\s+to|dislikes?|hates?)\s+meat\b"],
        "remedies": ["Puls.", "Carb-v.", "Graph.", "Mur-ac."],
        "weight": 3,
    },
    "aversion_milk": {
        "patterns": [r"\b(?:avoids?|aversion\s+to|dislikes?|hates?)\s+milk\b"],
        "remedies": ["Puls.", "Lac-c.", "Calc.", "Nat-c."],
        "weight": 3,
    },
    "perspiration_easy": {
        "patterns": [r"\b(?:sweat(?:s|ing)?\s+(?:easily|a\s+lot|profusely)|profuse\s+sweat)\b"],
        "remedies": ["Calc.", "Sil.", "Sulph.", "Puls.", "Merc."],
        "weight": 3,
    },
    "perspiration_forehead": {
        "patterns": [r"\bforehead\s+sweat\b"],
        "remedies": ["Verat.", "Calc.", "Nux-v."],
        "weight": 3,
    },
    "weather_dry": {
        "patterns": [r"\b(?:better|worse|feels?\s+better)\s+(?:in\s+)?dry\s+(?:weather|air|climate)\b"],
        "remedies": ["Rhus-t.", "Hep.", "Caust."],
        "weight": 3,
    },
    "weather_damp": {
        "patterns": [r"\b(?:better|worse|feels?\s+better)\s+(?:in\s+)?damp\s+(?:weather|air)\b"],
        "remedies": ["Med.", "Dulc.", "Rhus-t.", "Nux-m."],
        "weight": 3,
    },
    "weather_storm": {
        "patterns": [r"\b(?:worse|feels?\s+worse)\s+(?:before|at|during)\s+(?:a\s+)?storm\b"],
        "remedies": ["Phos.", "Rhod.", "Med.", "Petr."],
        "weight": 4,
    },
    "weather_seashore": {
        "patterns": [r"\b(?:better|worse|feels?\s+better)\s+(?:at|near)\s+(?:the\s+)?seashore\b"],
        "remedies": ["Med.", "Nat-m.", "Sep."],
        "weight": 4,
    },
    "weather_mountains": {
        "patterns": [r"\b(?:better|worse|feels?\s+better)\s+(?:in\s+)?(?:mountains|high\s+altitudes?)\b"],
        "remedies": ["Phos.", "Verat.", "Calc."],
        "weight": 4,
    },
    "energy_morning": {
        "patterns": [r"\b(?:better|worse)\s+(?:in\s+)?the\s+morning\b", r"\bmorning\s+person\b"],
        "remedies": ["Sulph.", "Nux-v.", "Bry."],
        "weight": 3,
    },
    "energy_evening": {
        "patterns": [r"\b(?:better|worse)\s+(?:in\s+the\s+)?evening\b", r"\bevening\s+person\b"],
        "remedies": ["Puls.", "Lyco."],
        "weight": 3,
    },
    "side_left": {
        "patterns": [r"\b(?:left[\s-]sided|on\s+the\s+left|worse\s+left)\b"],
        "remedies": ["Lach.", "Lyco.", "Sulph.", "Phos."],
        "weight": 2,
    },
    "side_right": {
        "patterns": [r"\b(?:right[\s-]sided|on\s+the\s+right|worse\s+right)\b"],
        "remedies": ["Calc.", "Nux-v.", "Bell."],
        "weight": 2,
    },
}


@dataclass
class GeneralSymptom:
    general_type: str
    text: str
    weight: int
    discriminative_remedies: List[str]
    rubric_phrase: str


@dataclass
class GeneralsProfile:
    symptoms: List[GeneralSymptom]
    thermal_state: Optional[str]            # "warm" or "cold"
    sleep_position: Optional[str]           # "back", "left", "right", "knees", "arms_above"
    food_cravings: List[str]                # list of cravings
    food_aversions: List[str]               # list of aversions
    weather_preference: Optional[str]       # "dry", "damp", etc.
    energy_pattern: Optional[str]           # "morning" or "evening"
    dream_themes: List[str]
    side_affinity: Optional[str]            # "left" or "right"
    characteristic_remedies: List[str]
    coverage_completeness: float            # 0-1
    summary: str


class GeneralsSurvey:
    """Surveys the case for generals."""

    def __init__(self):
        self._lexicon: Dict[str, Dict[str, Any]] = {}
        for key, info in GENERALS_LEXICON.items():
            self._lexicon[key] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in info["patterns"]],
                "remedies": info["remedies"],
                "weight": info["weight"],
            }

    def profile(self, narrative: str) -> GeneralsProfile:
        """Build a complete generals profile from a narrative."""
        if not narrative:
            return GeneralsProfile(
                symptoms=[],
                thermal_state=None,
                sleep_position=None,
                food_cravings=[],
                food_aversions=[],
                weather_preference=None,
                energy_pattern=None,
                dream_themes=[],
                side_affinity=None,
                characteristic_remedies=[],
                coverage_completeness=0.0,
                summary="Empty narrative.",
            )

        detected: List[GeneralSymptom] = []
        for key, info in self._lexicon.items():
            for pat in info["patterns"]:
                m = pat.search(narrative)
                if m:
                    detected.append(GeneralSymptom(
                        general_type=key,
                        text=m.group(0),
                        weight=info["weight"],
                        discriminative_remedies=list(info["remedies"]),
                        rubric_phrase=self._to_rubric(key, m.group(0)),
                    ))
                    break

        # Group by category
        thermal_state = "warm" if any(s.general_type == "thermal_warm_blooded" for s in detected) else (
            "cold" if any(s.general_type == "thermal_cold_blooded" for s in detected) else None
        )
        sleep_position = next(
            (s.general_type.replace("sleep_position_", "") for s in detected
             if s.general_type.startswith("sleep_position_")),
            None,
        )
        food_cravings = [s.general_type.replace("craving_", "") for s in detected
                         if s.general_type.startswith("craving_")]
        food_aversions = [s.general_type.replace("aversion_", "") for s in detected
                          if s.general_type.startswith("aversion_")]
        dream_themes = []
        for s in detected:
            if s.general_type.startswith("dreams_"):
                theme = s.general_type.replace("dreams_", "")
                if theme != "animals":  # animals is generic
                    dream_themes.append(theme)
        weather_preference = next(
            (s.general_type.replace("weather_", "") for s in detected
             if s.general_type.startswith("weather_")),
            None,
        )
        energy_pattern = next(
            (s.general_type.replace("energy_", "") for s in detected
             if s.general_type.startswith("energy_")),
            None,
        )
        side_affinity = next(
            (s.general_type.replace("side_", "") for s in detected
             if s.general_type.startswith("side_")),
            None,
        )

        # Aggregate remedies
        remedy_weights: Dict[str, int] = defaultdict(int)
        for s in detected:
            for r in s.discriminative_remedies:
                remedy_weights[r] += s.weight
        characteristic = sorted(remedy_weights, key=lambda r: -remedy_weights[r])[:10]

        # Coverage (how many categories covered)
        categories = [
            thermal_state, sleep_position, food_cravings, food_aversions,
            dream_themes, weather_preference, energy_pattern, side_affinity,
        ]
        non_empty = sum(1 for c in categories if c)
        coverage = non_empty / len(categories)

        summary = self._build_summary(
            thermal_state, sleep_position, food_cravings, food_aversions,
            dream_themes, weather_preference, energy_pattern, side_affinity,
            characteristic, coverage,
        )

        return GeneralsProfile(
            symptoms=detected,
            thermal_state=thermal_state,
            sleep_position=sleep_position,
            food_cravings=food_cravings,
            food_aversions=food_aversions,
            weather_preference=weather_preference,
            energy_pattern=energy_pattern,
            dream_themes=dream_themes,
            side_affinity=side_affinity,
            characteristic_remedies=characteristic,
            coverage_completeness=coverage,
            summary=summary,
        )

    def suggest_general_questions(
        self,
        profile: GeneralsProfile,
        max_questions: int = 5,
    ) -> List[str]:
        """Suggest follow-up generals questions to fill gaps."""
        suggestions: List[str] = []
        if not profile.thermal_state:
            suggestions.append("Are you more comfortable in warmth or coolness? Do you tend to overheat or feel cold?")
        if not profile.sleep_position:
            suggestions.append("What position do you typically sleep in? On your back, side, curled up?")
        if not profile.food_cravings:
            suggestions.append("Any specific food cravings — salt, sweet, fat, ice, eggs?")
        if not profile.food_aversions:
            suggestions.append("Any foods you really dislike or that disagree with you?")
        if not profile.dream_themes:
            suggestions.append("Do you remember your dreams? Any vivid or recurring themes?")
        if not profile.weather_preference:
            suggestions.append("How does weather affect you — better in dry or damp? Hot or cold?")
        if not profile.energy_pattern:
            suggestions.append("When is your energy best — morning or evening?")
        if not profile.side_affinity:
            suggestions.append("Do you have a side preference — left or right?")
        return suggestions[:max_questions]

    def _to_rubric(self, key: str, value: str) -> str:
        """Convert to repertory-style phrase."""
        # E.g. "thermal_warm_blooded" → "warm-blooded"
        parts = key.split("_")
        return " ".join(parts)

    def _build_summary(
        self,
        thermal, sleep_pos, cravings, aversions, dreams, weather, energy,
        side, remedies, coverage,
    ) -> str:
        lines = [f"Generals coverage: {coverage:.0%}."]
        if thermal:
            lines.append(f"Thermal: {thermal}-blooded")
        if sleep_pos:
            lines.append(f"Sleep position: {sleep_pos}")
        if cravings:
            lines.append(f"Cravings: {', '.join(cravings)}")
        if aversions:
            lines.append(f"Aversions: {', '.join(aversions)}")
        if dreams:
            lines.append(f"Dreams: {', '.join(dreams)}")
        if weather:
            lines.append(f"Weather: {weather}")
        if energy:
            lines.append(f"Energy: {energy}")
        if side:
            lines.append(f"Side: {side}")
        if remedies:
            lines.append(f"Top remedies: {', '.join(remedies[:5])}")
        return "\n".join(lines)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_generals(narrative: str) -> GeneralsProfile:
    """Quick helper: profile the generals from a narrative."""
    return GeneralsSurvey().profile(narrative)
