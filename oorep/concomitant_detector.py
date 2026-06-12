"""
Concomitant Detector (Module #134)

Detects symptoms that occur *together with* the chief complaint. In
classical homeopathy, a striking concomitant is often more characteristic
of the simillimum than the chief complaint itself (Kent: "The concomitants
decide the case").

This module:
  1. Identifies symptoms mentioned alongside the chief complaint in
     the patient's narrative
  2. Scores each concomitant by how SRP-like (Strange-Rare-Peculiar) it is
  3. Ranks them by discriminative value for the running differential
  4. Surfaces which concomitant questions to ask next

Usage:
    from oorep.concomitant_detector import ConcomitantDetector
    detector = ConcomitantDetector()
    analysis = detector.analyze(
        chief_complaint_text="throbbing headache on the right side",
        narrative="when the headache comes I get very irritable and I want to be alone, my vision goes blurry",
    )
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


# Concomitant symptom patterns grouped by body system
CONCOMITANT_LEXICON: Dict[str, List[str]] = {
    "Mental": [
        "irritable", "irritability", "angry", "rage", "weep", "crying", "sad",
        "anxious", "anxiety", "restless", "calm", "withdrawn", "desire to be alone",
        "wants company", "consolation", "fear", "panic", "confused", "drowsy",
        "stupor", "delirium", "delirious", "lethargic", "apathetic",
    ],
    "Gastric": [
        "nausea", "nauseous", "vomit", "vomiting", "queasy", "loss of appetite",
        "no appetite", "no thirst", "thirsty", "thirst for", "aversion to food",
        "belching", "indigestion", "heartburn", "abdominal pain",
    ],
    "Chill/Fever": [
        "chill", "chills", "shiver", "shivering", "hot", "fever", "feverish",
        "sweat", "sweating", "perspiration", "cold", "freezing",
    ],
    "Visual": [
        "blurry vision", "vision blurred", "spots", "dazzling", "light sensitive",
        "photophobia", "darkness better", "light better", "dim", "dimness",
    ],
    "Sleep": [
        "drowsy", "sleepy", "insomnia", "sleepless", "waking", "yawn",
    ],
    "Sensorimotor": [
        "numbness", "tingling", "tremor", "trembling", "weakness", "paralysis",
        "spasm", "cramp", "twitching",
    ],
}

# Concomitant patterns (when-then) in patient narrative
CONCOMITANT_TRIGGERS = [
    r"when\s+(?:i|patient|the)\s+(?:get|gots|has|have)\s+(?:the|this|my)\s+([\w\s,]+?)(?:,|\.|;|and|then|i)",
    r"alongside\s+(?:the|this|my)\s+([\w\s,]+?)(?:,|\.|;|and)",
    r"with\s+(?:the|this|my)\s+([\w\s,]+?)(?:,|\.|;|and)",
    r"at\s+the\s+same\s+time\s+(?:as|i\s+have|i\s+get)\s+([\w\s,]+?)(?:,|\.|;|and)",
    r"during\s+(?:the|this|my)\s+([\w\s,]+?)(?:,|\.|;|and)",
    r"after(?:wards)?\s+(?:the|this|my)\s+([\w\s,]+?)(?:,|\.|;|and|i\s+(?:feel|get|have))",
]


@dataclass
class ConcomitantSymptom:
    text: str                              # The symptom text
    system: str                            # Mental, Gastric, Chill/Fever, etc.
    srp_score: float                       # 0-1: how SRP-like
    occurrence_count: int                  # How many times mentioned
    in_chief_context: bool                 # Mentioned specifically alongside chief


@dataclass
class ConcomitantAnalysis:
    chief_complaint: str
    narrative: str
    concomitants: List[ConcomitantSymptom]
    strongest_concomitant: Optional[ConcomitantSymptom]
    srp_signals: List[str]                 # Detected SRP-style markers
    discriminative_axes: List[str]         # "Mental", "Gastric", etc.
    summary: str


class ConcomitantDetector:
    """
    Detects and ranks concomitant symptoms from a patient narrative.
    """

    def __init__(self):
        # Pre-compile lexicon
        self._lexicon: Dict[str, List[re.Pattern]] = {
            system: [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in terms]
            for system, terms in CONCOMITANT_LEXICON.items()
        }
        self._srp_markers = re.compile(
            r"\b(strange|weird|peculiar|unusual|uncommon|rare|only|exactly|as\s+if|"
            r"like\s+a|never\s+had|no\s+one\s+else|every\s+time)\b",
            re.IGNORECASE,
        )

    def analyze(
        self,
        chief_complaint_text: str,
        narrative: str,
    ) -> ConcomitantAnalysis:
        """
        Analyze a patient narrative for concomitant symptoms.
        """
        if not narrative:
            return ConcomitantAnalysis(
                chief_complaint=chief_complaint_text,
                narrative="",
                concomitants=[],
                strongest_concomitant=None,
                srp_signals=[],
                discriminative_axes=[],
                summary="Empty narrative.",
            )

        # Find all concomitant mentions by system
        detections: Dict[str, List[Tuple[str, int, bool]]] = defaultdict(list)
        # detections[system] = [(text, count, in_chief_context)]
        for system, patterns in self._lexicon.items():
            for pat in patterns:
                for m in pat.finditer(narrative):
                    text = m.group(0).lower()
                    in_chief = self._is_in_chief_context(m.start(), narrative)
                    detections[system].append((text, 1, in_chief))

        # Aggregate per system
        by_text: Dict[str, Dict[str, Any]] = {}
        for system, items in detections.items():
            for text, _, in_chief in items:
                key = text
                if key not in by_text:
                    by_text[key] = {
                        "system": system,
                        "text": text,
                        "count": 0,
                        "in_chief": False,
                    }
                by_text[key]["count"] += 1
                by_text[key]["in_chief"] = by_text[key]["in_chief"] or in_chief

        # Score each
        concomitants: List[ConcomitantSymptom] = []
        for key, info in by_text.items():
            srp = self._compute_srp_score(info["text"], narrative)
            concomitants.append(ConcomitantSymptom(
                text=info["text"],
                system=info["system"],
                srp_score=srp,
                occurrence_count=info["count"],
                in_chief_context=info["in_chief"],
            ))

        # Sort by (srp_score desc, in_chief_context desc, count desc)
        concomitants.sort(key=lambda c: (c.srp_score, c.in_chief_context, c.occurrence_count), reverse=True)

        strongest = concomitants[0] if concomitants else None
        srp_signals = list(set(m.group(0).lower() for m in self._srp_markers.finditer(narrative)))
        discriminative_axes = list(dict.fromkeys(c.system for c in concomitants[:5]))

        summary = self._build_summary(chief_complaint_text, concomitants, srp_signals, discriminative_axes)

        return ConcomitantAnalysis(
            chief_complaint=chief_complaint_text,
            narrative=narrative,
            concomitants=concomitants,
            strongest_concomitant=strongest,
            srp_signals=srp_signals,
            discriminative_axes=discriminative_axes,
            summary=summary,
        )

    def suggest_concomitant_questions(
        self,
        analysis: ConcomitantAnalysis,
        max_questions: int = 3,
    ) -> List[str]:
        """Suggest follow-up questions to elicit more SRP-like concomitants."""
        suggestions: List[str] = []
        # If user has only mental concomitants, ask about physical
        systems_seen = set(c.system for c in analysis.concomitants)
        if "Mental" in systems_seen and "Gastric" not in systems_seen:
            suggestions.append("When the [chief] comes, do you notice any stomach symptoms, nausea, or appetite changes?")
        if "Chill/Fever" not in systems_seen and "Visual" not in systems_seen:
            suggestions.append("Any temperature changes or vision issues when the [chief] is at its worst?")
        if not analysis.srp_signals:
            suggestions.append("Is there anything strange, unusual, or peculiar that happens at the same time?")
        return suggestions[:max_questions]

    def _is_in_chief_context(self, position: int, narrative: str) -> bool:
        """Check if the symptom mention is in a 'when/with' clause to the chief."""
        # Look at the preceding 80 chars
        start = max(0, position - 80)
        preceding = narrative[start:position].lower()
        triggers = ["when", "with", "alongside", "during", "at the same time", "after"]
        return any(t in preceding for t in triggers)

    def _compute_srp_score(self, text: str, narrative: str) -> float:
        """Compute the SRP score for a single concomitant mention."""
        score = 0.3  # base
        # Check for SRP markers near this mention
        idx = narrative.lower().find(text)
        if idx >= 0:
            window = narrative[max(0, idx - 60):idx + len(text) + 30].lower()
            srp_count = len(self._srp_markers.findall(window))
            score += min(0.5, srp_count * 0.15)
        # In chief context boosts score
        if self._is_in_chief_context(idx if idx >= 0 else 0, narrative):
            score += 0.2
        return min(1.0, score)

    def _build_summary(
        self,
        chief: str,
        concomitants: List[ConcomitantSymptom],
        srp_signals: List[str],
        axes: List[str],
    ) -> str:
        if not concomitants:
            return f"No concomitants detected for '{chief}'."
        lines = [
            f"Detected {len(concomitants)} concomitant symptom(s) for '{chief}':"
        ]
        for c in concomitants[:5]:
            tag = " [in chief context]" if c.in_chief_context else ""
            lines.append(f"  - {c.text} ({c.system}, SRP={c.srp_score:.2f}, n={c.occurrence_count}){tag}")
        if srp_signals:
            lines.append(f"SRP markers: {', '.join(srp_signals)}")
        if axes:
            lines.append(f"Discriminative axes: {', '.join(axes)}")
        return "\n".join(lines)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_concomitants(
    chief: str,
    narrative: str,
) -> ConcomitantAnalysis:
    """Quick helper: detect concomitants in a patient narrative."""
    return ConcomitantDetector().analyze(chief, narrative)
