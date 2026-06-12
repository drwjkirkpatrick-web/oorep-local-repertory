"""
Modality Extractor (Module #135)

Extracts modalities (what makes a symptom better or worse) from patient
narrative. Modalities are the highest-weighted differentiators in
repertorization (most modalities are graded 3-4 in the repertory).

Modalities are organized into 7 classical axes:
  1. TIME — time of day, day of week, season
  2. TEMPERATURE — heat vs cold, weather
  3. MOTION — rest vs motion, position changes
  4. POSITION — sitting, lying, side preference
  5. FOOD/DRINK — eating, drinking, specific foods
  6. EMOTION — emotional triggers
  7. FUNCTION — activity, sleep, sex, etc.

For each modality captured, this module:
  - Identifies the axis
  - Identifies the direction (amelioration/aggravation)
  - Extracts the specific value (e.g. "evening", "warmth", "lying down")
  - Ranks modalities by SRP potential and discriminative power

Usage:
    from oorep.modality_extractor import ModalityExtractor
    extractor = ModalityExtractor()
    grid = extractor.extract("worse at night, better from warmth, worse lying on left side")
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class ModalityAxis(Enum):
    TIME = "time"
    TEMPERATURE = "temperature"
    MOTION = "motion"
    POSITION = "position"
    FOOD = "food"
    EMOTION = "emotion"
    FUNCTION = "function"
    WEATHER = "weather"
    COMPANY = "company"
    CONSOLATION = "consolation"
    GENERAL = "general"


class ModalityDirection(Enum):
    AMELIORATION = "amelioration"   # Better from
    AGGRAVATION = "aggravation"     # Worse from


@dataclass
class CapturedModality:
    """A single extracted modality."""
    axis: ModalityAxis
    direction: ModalityDirection
    value: str
    raw_text: str                       # The original phrase
    confidence: float
    srp_score: float                    # Peculiarity score
    discriminative_remedies: List[str] = field(default_factory=list)
    rubric_phrase: str = ""             # e.g. "worse lying on left side"


@dataclass
class ModalityGrid:
    """A complete modality grid for a case."""
    modalities: List[CapturedModality]
    axes_covered: Set[ModalityAxis]
    axes_missing: Set[ModalityAxis]
    completeness: float                 # 0-1
    srp_modalities: List[CapturedModality]
    summary: str


# Patterns for each axis
AXIS_PATTERNS: Dict[ModalityAxis, List[str]] = {
    ModalityAxis.TIME: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:in\s+the\s+)?(?:morning|afternoon|evening|night|day|dawn|dusk))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?:at|around|after|before)\s+(?P<val>\d{1,2}\s*(?:am|pm|o'clock|hours?))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>spring|summer|fall|autumn|winter|january|february|march|april|may|june|july|august|september|october|november|december)",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>before|during|after|with)\s+(?:menses|period|menstruation)",
    ],
    ModalityAxis.TEMPERATURE: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>from\s+(?:heat|warmth|cold|cool|air|room))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>in\s+(?:warm|hot|cold|cool)\s+(?:weather|room|air))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:warm|hot|cold|cool)\s+(?:applications?|baths?|drinks?|food))",
    ],
    ModalityAxis.MOTION: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>from\s+motion|with\s+motion|while\s+moving|when\s+moving|when\s+(?:walking|running|active))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>from\s+rest|with\s+rest|while\s+resting|when\s+(?:resting|lying\s+still))",
    ],
    ModalityAxis.POSITION: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>lying|lying\s+down|sitting|standing|leaning|stooping|bending)",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>lying\s+on\s+(?:the\s+)?(?:left|right|back|side))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:head|body)\s+(?:up|down|high|low|elevated))",
    ],
    ModalityAxis.FOOD: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:from|by|with|after)\s+(?:eating|drinking|eating\s+[\w\s]+|drinking\s+[\w\s]+))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:coffee|tea|wine|alcohol|salt|sweet|meat|fat|milk|bread|water|ice))",
    ],
    ModalityAxis.EMOTION: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>from\s+(?:emotion|excitement|anger|grief|fear|joy|stress))",
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>after\s+(?:crying|anger|emotional\s+upset))",
    ],
    ModalityAxis.COMPANY: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>alone|from\s+company|with\s+company|with\s+others|in\s+crowds)",
    ],
    ModalityAxis.CONSOLATION: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>from\s+consolation|with\s+consolation|with\s+sympathy|with\s+comfort)",
    ],
    ModalityAxis.WEATHER: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:storm|rain|snow|wind|damp|dry|fog|humidity|cloudy|clear|thunder))",
    ],
    ModalityAxis.FUNCTION: [
        r"(?P<dir>better|worse|ameliorat\w*|aggravat\w*)\s+(?P<val>(?:sleeping|eating|urinating|defecating|coughing|sneezing|yawning|breathing))",
    ],
}

# Discriminative remedies for each axis
AXIS_DISCRIMINATIVE: Dict[ModalityAxis, List[str]] = {
    ModalityAxis.TIME: ["Ars.", "Nux-v.", "Puls.", "Sulph.", "Lyc.", "Phos."],
    ModalityAxis.TEMPERATURE: ["Puls.", "Sulph.", "Ars.", "Calc.", "Sil.", "Hep."],
    ModalityAxis.MOTION: ["Rhus-t.", "Bry.", "Puls.", "Ars.", "Calc-p."],
    ModalityAxis.POSITION: ["Ars.", "Phos.", "Spong.", "Sulph."],
    ModalityAxis.FOOD: ["Phos.", "Calc.", "Lyc.", "Puls.", "Verat.", "Hep."],
    ModalityAxis.EMOTION: ["Ign.", "Nat-m.", "Puls.", "Staph.", "Aur."],
    ModalityAxis.COMPANY: ["Puls.", "Ars.", "Stram.", "Bry.", "Nux-v."],
    ModalityAxis.CONSOLATION: ["Puls.", "Nat-m.", "Sep.", "Sil."],
    ModalityAxis.WEATHER: ["Rhus-t.", "Med.", "Dulc.", "Nux-m.", "Ars."],
    ModalityAxis.FUNCTION: ["Caust.", "Phos.", "Sulph.", "Puls."],
    ModalityAxis.GENERAL: [],
}

# SRP markers (peculiar modalities are higher weight)
SRP_PECULIAR_TERMS = [
    "only when", "specifically", "exactly", "always", "never", "as if",
    "must", "have to", "compelled", "peculiar", "strange", "weird",
    "unusual", "uncommon", "rare", "inability to",
]

DIRECTION_MAP = {
    "better": ModalityDirection.AMELIORATION,
    "ameliorat": ModalityDirection.AMELIORATION,
    "worse": ModalityDirection.AGGRAVATION,
    "aggravat": ModalityDirection.AGGRAVATION,
}


class ModalityExtractor:
    """Extracts modalities from patient narrative."""

    def __init__(self):
        self._patterns: Dict[ModalityAxis, List[re.Pattern]] = {
            axis: [re.compile(p, re.IGNORECASE) for p in patterns]
            for axis, patterns in AXIS_PATTERNS.items()
        }
        self._srp_markers = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in SRP_PECULIAR_TERMS) + r")\b",
            re.IGNORECASE,
        )

    def extract(self, narrative: str) -> ModalityGrid:
        """Extract all modalities from a free-text narrative."""
        if not narrative:
            return ModalityGrid(
                modalities=[],
                axes_covered=set(),
                axes_missing=set(ModalityAxis),
                completeness=0.0,
                srp_modalities=[],
                summary="Empty narrative.",
            )

        modalities: List[CapturedModality] = []
        for axis, patterns in self._patterns.items():
            for pat in patterns:
                for m in pat.finditer(narrative):
                    direction_str = m.group("dir").lower()
                    value = m.group("val").strip()
                    direction = self._infer_direction(direction_str)
                    raw = m.group(0)
                    srp = self._score_srp(raw, value, narrative)
                    modalities.append(CapturedModality(
                        axis=axis,
                        direction=direction,
                        value=value,
                        raw_text=raw,
                        confidence=0.7,
                        srp_score=srp,
                        discriminative_remedies=list(AXIS_DISCRIMINATIVE.get(axis, [])),
                        rubric_phrase=self._to_rubric_phrase(direction, value),
                    ))

        # Deduplicate (same axis+direction+value)
        seen = set()
        unique = []
        for m in modalities:
            key = (m.axis, m.direction, m.value.lower())
            if key not in seen:
                seen.add(key)
                unique.append(m)

        # Sort by SRP score desc
        unique.sort(key=lambda m: (m.srp_score, m.confidence), reverse=True)

        axes_covered = set(m.axis for m in unique)
        all_axes = set(ModalityAxis)
        axes_missing = all_axes - axes_covered
        completeness = len(axes_covered) / len(all_axes) if all_axes else 0.0
        srp_mods = [m for m in unique if m.srp_score > 0.5]
        summary = self._build_summary(unique, completeness, srp_mods)

        return ModalityGrid(
            modalities=unique,
            axes_covered=axes_covered,
            axes_missing=axes_missing,
            completeness=completeness,
            srp_modalities=srp_mods,
            summary=summary,
        )

    def to_repertory_modalities(
        self,
        grid: ModalityGrid,
    ) -> Dict[str, List[str]]:
        """Convert a modality grid into repertory-style phrases."""
        amel = []
        agg = []
        for m in grid.modalities:
            phrase = m.rubric_phrase
            if m.direction == ModalityDirection.AMELIORATION:
                amel.append(phrase)
            else:
                agg.append(phrase)
        return {"ameliorations": amel, "aggravations": agg}

    def _infer_direction(self, text: str) -> ModalityDirection:
        text = text.lower()
        for k, v in DIRECTION_MAP.items():
            if k in text:
                return v
        return ModalityDirection.AGGRAVATION  # default

    def _score_srp(self, raw_text: str, value: str, narrative: str) -> float:
        """Score modality SRP-ness."""
        score = 0.2
        for marker in SRP_PECULIAR_TERMS:
            if marker in raw_text.lower():
                score += 0.15
        # Specific time values are more SRP
        import re
        if re.search(r"\d+\s*(am|pm)", value):
            score += 0.2
        # Specific body parts
        if any(p in value for p in ["left", "right", "knee", "back", "side"]):
            score += 0.1
        return min(1.0, score)

    def _to_rubric_phrase(self, direction: ModalityDirection, value: str) -> str:
        """Convert to repertory-style phrase."""
        if direction == ModalityDirection.AMELIORATION:
            return f"amelioration from {value}"
        return f"aggravation from {value}"

    def _build_summary(
        self,
        modalities: List[CapturedModality],
        completeness: float,
        srp_mods: List[CapturedModality],
    ) -> str:
        lines = [
            f"Extracted {len(modalities)} modalities covering {completeness:.0%} of axes."
        ]
        if srp_mods:
            lines.append(f"SRP modalities: {', '.join(m.rubric_phrase for m in srp_mods[:3])}")
        if modalities:
            amel = [m for m in modalities if m.direction == ModalityDirection.AMELIORATION]
            agg = [m for m in modalities if m.direction == ModalityDirection.AGGRAVATION]
            if amel:
                lines.append(f"Better from: {', '.join(m.value for m in amel[:3])}")
            if agg:
                lines.append(f"Worse from: {', '.join(m.value for m in agg[:3])}")
        return "\n".join(lines)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_modalities(narrative: str) -> ModalityGrid:
    """Quick helper: extract modalities from narrative text."""
    return ModalityExtractor().extract(narrative)
