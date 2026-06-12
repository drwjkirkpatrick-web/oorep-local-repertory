"""
Causation & Timeline Module (Module #136)

Captures the etiology (cause) and chronological timeline of a case.
In homeopathy, causation is often the most specific indicator of the
simillimum (e.g. "ailments from grief" → Ignatia, "ailments from anger"
→ Staphysagria, "ailments from cold dry wind" → Aconite).

This module:
  1. Identifies the etiologic moment (when did this start? what triggered it?)
  2. Builds a chronological timeline of symptoms, treatments, and events
  3. Identifies suppression patterns (symptom disappears but new one emerges)
  4. Detects miasmatic patterns (Psora, Sycosis, Syphilis, Tubercular)
  5. Ranks potential causal remedies (the "never been well since" remedies)

Usage:
    from oorep.causation_timeline_module import CausationTimelineAnalyzer
    analyzer = CausationTimelineAnalyzer()
    report = analyzer.analyze("symptoms started after a bereavement 6 months ago")
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class Miasm(Enum):
    PSORA = "psora"
    SYCOSIS = "sycosis"
    SYPHILIS = "syphilis"
    TUBERCULAR = "tubercular"


# Classical "ailments from" remedies
ETIOLOGY_LEXICON: Dict[str, List[str]] = {
    "grief": ["Ign.", "Nat-m.", "Puls.", "Phos-ac.", "Caust."],
    "bereavement": ["Ign.", "Nat-m.", "Puls.", "Phos-ac."],
    "anger": ["Staph.", "Cham.", "Nux-v.", "Coloc."],
    "indignation": ["Staph.", "Coloc.", "Nux-v."],
    "fright": ["Acon.", "Op.", "Gels.", "Ign."],
    "fear": ["Acon.", "Op.", "Gels."],
    "shock": ["Acon.", "Op.", "Gels.", "Arn."],
    "injury": ["Arn.", "Hyper.", "Led.", "Symph.", "Ruta.", "Calc-s."],
    "accident": ["Arn.", "Hyper.", "Led."],
    "surgery": ["Arn.", "Hyper.", "Staph.", "Phos."],
    "head injury": ["Arn.", "Nat-s.", "Hyper.", "Helleborus"],
    "exposure to cold": ["Acon.", "Bell.", "Camph.", "Coff."],
    "exposure to cold dry wind": ["Acon.", "Hep.", "Caust."],
    "exposure to cold damp": ["Dulc.", "Rhus-t.", "Med.", "Calc-p."],
    "overheating": ["Ant-c.", "Bry.", "Bell."],
    "sun exposure": ["Bell.", "Nat-c.", "Glon.", "Sol."],
    "getting wet": ["Rhus-t.", "Dulc.", "Ant-c.", "Puls."],
    "drowning": ["Ant-t.", "Hep."],
    "burns": ["Urt-u.", "Canth.", "Caust.", "Arn."],
    "poisoning": ["various — see materia medica"],
    "overwork": ["Nux-v.", "Picot.", "Kali-p.", "Calc-p."],
    "loss of sleep": ["Nux-v.", "Cocculus", "Puls."],
    "sexual excess": ["Phos-ac.", "Staph.", "Con.", "Agn."],
    "alcohol abuse": ["Nux-v.", "Lach.", "Sulph.", "Ars.", "Querc."],
    "drug abuse": ["Nux-v.", "Ars."],
    "vaccination": ["Thuj.", "Sil.", "Sulph.", "Maland.", "Variol."],
    "suppressed eruption": ["Sulph.", "Caust.", "Ars.", "Psor."],
    "suppressed sweat": ["Cham.", "Bell.", "Sulph."],
    "suppressed discharge": ["Puls.", "Sulph.", "Calc-p."],
    "menopause": ["Lach.", "Puls.", "Sulph.", "Calc.", "Sep."],
    "puberty": ["Calc-p.", "Puls.", "Aur."],
    "pregnancy": ["Puls.", "Sep.", "Lach.", "Calc."],
    "childbirth": ["Arn.", "Bell.", "Puls.", "Hyper."],
    "menarche": ["Puls.", "Calc-p.", "Phos."],
    "menses suppression": ["Puls.", "Sulph.", "Lach."],
    "over-study": ["Nux-v.", "Picot.", "Calc-p."],
    "disappointed love": ["Ign.", "Nat-m.", "Phos-ac.", "Aur."],
    "humiliation": ["Staph.", "Coloc.", "Aur.", "Pall."],
    "rejected love": ["Ign.", "Nat-m.", "Phos-ac.", "Aur.", "Hyos."],
    "mortification": ["Staph.", "Coloc.", "Puls."],
    "jealousy": ["Hyos.", "Lach.", "Apis.", "Stram."],
    "bad news": ["Gels.", "Ign.", "Nat-m."],
    "financial loss": ["Ars.", "Aur.", "Puls."],
    "ill news": ["Gels.", "Ign."],
    "worry": ["Ars.", "Nux-v.", "Puls.", "Sil."],
    "mental exertion": ["Nux-v.", "Picot.", "Kali-p."],
    "lifting": ["Rhus-t.", "Calc.", "Arn.", "Nux-v."],
    "strain": ["Rhus-t.", "Arn.", "Calc."],
}

# Miasmatic pattern markers
MIASM_MARKERS: Dict[Miasm, List[str]] = {
    Miasm.PSORA: [
        "itching", "skin eruptions", "eczema", "anxiety", "restlessness",
        "worse from cold", "worse at night", "pruritus", "nervous",
        "functional", "no organic change", "comes and goes",
    ],
    Miasm.SYCOSIS: [
        "warts", "gonorrhea", "suppressed gonorrhea", "condylomata",
        "worse in damp", "worse from cold damp", "fixed ideas",
        "irregular growths", "swellings", "slimy discharges", "worse at 3-4 am",
        "worse in spring", "emotional sensitivity", "secretiveness",
    ],
    Miasm.SYPHILIS: [
        "ulceration", "destruction", "bone pain", "worse at night", "decay",
        "abscesses", "suppurations", "self-destructive", "suicidal",
        "throat issues", "history of syphilis", "self-harm",
    ],
    Miasm.TUBERCULAR: [
        "tuberculosis", "chest", "respiratory", "worse from cold", "wants travel",
        "restless", "fear of suffocation", "recurrent", "cough", "weight loss",
        "family history of tb", "desire for change", "claustrophobia",
    ],
}


@dataclass
class TimelineEvent:
    when: str                            # Free-text when
    event_type: str                      # "symptom_onset", "treatment", "event", "suppression"
    description: str
    remedy_hints: List[str] = field(default_factory=list)


@dataclass
class CausationReport:
    chief_complaint: str
    etiology_detected: Optional[str]
    etiology_remedies: List[str]
    timeline: List[TimelineEvent]
    suppressions: List[str]              # Suppression patterns
    miasmatic_affinity: Dict[str, float]  # miasm -> score
    dominant_miasm: Optional[Miasm]
    remedies_considered: List[str]
    never_well_since: Optional[str]      # "Never been well since X"
    summary: str


class CausationTimelineAnalyzer:
    """Analyzes causation and timeline of a homeopathic case."""

    def __init__(self):
        self._etiology_patterns: Dict[str, List[re.Pattern]] = {
            trigger: [re.compile(rf"\b{re.escape(trigger)}\b", re.IGNORECASE)]
            for trigger in ETIOLOGY_LEXICON.keys()
        }
        # More flexible causation patterns
        self._causation_phrases = [
            r"(?:started|began|onset|came\s+on|developed)\s+(?:after|following|since)\s+(?:a\s+|an\s+)?([\w\s]+?)(?:\.|,|;|and)",
            r"(?:never\s+been\s+well\s+since|nwb\s+since)\s+(?:a\s+|an\s+)?([\w\s]+?)(?:\.|,|;|and|$)",
            r"after\s+(?:a\s+|an\s+|the\s+)?([\w\s]+?)\s+(?:i|patient|he|she|they)\s+(?:got|started|began|developed)",
            r"following\s+(?:a\s+|an\s+|the\s+)?([\w\s]+?)(?:\.|,|;|and|$)",
        ]
        self._time_patterns = [
            (r"(\d+)\s+years?\s+ago", "years"),
            (r"(\d+)\s+months?\s+ago", "months"),
            (r"(\d+)\s+weeks?\s+ago", "weeks"),
            (r"(\d+)\s+days?\s+ago", "days"),
            (r"in\s+(?P<year>\d{4})", "year"),
            (r"since\s+(\d{4})", "year"),
            (r"(?:last|past|previous)\s+(week|month|year)", "recent"),
        ]
        self._miasm_patterns: Dict[Miasm, re.Pattern] = {
            miasm: re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.IGNORECASE)
            for miasm, terms in MIASM_MARKERS.items()
        }

    def analyze(
        self,
        chief_complaint: str,
        timeline_text: str = "",
        history_text: str = "",
    ) -> CausationReport:
        """Analyze a case for causation and timeline."""
        full_text = " ".join([chief_complaint, timeline_text, history_text]).strip()
        if not full_text:
            return CausationReport(
                chief_complaint=chief_complaint,
                etiology_detected=None,
                etiology_remedies=[],
                timeline=[],
                suppressions=[],
                miasmatic_affinity={m.value: 0.0 for m in Miasm},
                dominant_miasm=None,
                remedies_considered=[],
                never_well_since=None,
                summary="Empty input.",
            )

        etiology, etiology_text = self._detect_etiology(full_text)
        timeline = self._build_timeline(full_text)
        suppressions = self._detect_suppressions(full_text)
        miasm_scores = self._score_miasms(full_text)
        dominant_miasm = max(miasm_scores, key=lambda k: miasm_scores[k]) if any(miasm_scores.values()) else None
        nwb = self._detect_never_well_since(full_text)
        remedies = set()
        if etiology:
            remedies.update(ETIOLOGY_LEXICON.get(etiology, []))
        for evt in timeline:
            remedies.update(evt.remedy_hints)
        summary = self._build_summary(
            etiology, etiology_text, timeline, suppressions, miasm_scores, nwb
        )

        return CausationReport(
            chief_complaint=chief_complaint,
            etiology_detected=etiology,
            etiology_remedies=sorted(remedies),
            timeline=timeline,
            suppressions=suppressions,
            miasmatic_affinity=miasm_scores,
            dominant_miasm=Miasm(dominant_miasm) if dominant_miasm else None,
            remedies_considered=sorted(remedies),
            never_well_since=nwb,
            summary=summary,
        )

    def _detect_etiology(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Detect a known etiology trigger and the matched phrase."""
        for trigger, patterns in self._etiology_patterns.items():
            for pat in patterns:
                m = pat.search(text)
                if m:
                    return trigger, m.group(0)
        return None, None

    def _build_timeline(self, text: str) -> List[TimelineEvent]:
        """Extract timeline events from the text."""
        events: List[TimelineEvent] = []

        # Date / time references
        for pattern, unit in self._time_patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                when = m.group(0)
                # Try to find associated event
                idx = m.end()
                context_window = text[idx:min(len(text), idx + 100)]
                description = context_window.split(".")[0].strip()[:100]
                # Heuristic event type
                event_type = "event"
                if any(w in context_window.lower() for w in ["start", "began", "onset", "develop"]):
                    event_type = "symptom_onset"
                elif any(w in context_window.lower() for w in ["treat", "medication", "drug", "surgery", "took"]):
                    event_type = "treatment"
                # Find remedy hints
                remedy_hints = []
                for trigger, remedies in ETIOLOGY_LEXICON.items():
                    if trigger in context_window.lower():
                        remedy_hints.extend(remedies[:2])
                events.append(TimelineEvent(
                    when=when,
                    event_type=event_type,
                    description=description,
                    remedy_hints=list(set(remedy_hints))[:3],
                ))

        # Sort by time (rough)
        return events[:20]

    def _detect_suppressions(self, text: str) -> List[str]:
        """Detect suppression patterns."""
        suppressions: List[str] = []
        patterns = [
            r"(\w+)\s+(?:went\s+away|disappeared|cleared\s+up)\s+but\s+(\w+\s+\w+)\s+(?:started|began|appeared|came)",
            r"after\s+(?:taking|using)\s+(\w+)\s+for\s+(\w+),?\s+(\w+\s+\w+)\s+(?:started|began|appeared)",
            r"suppressed?\s+(\w+)",
        ]
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                suppressions.append(m.group(0))
        return suppressions

    def _detect_never_well_since(self, text: str) -> Optional[str]:
        """Detect 'never been well since' pattern."""
        for pat_str in self._causation_phrases:
            pat = re.compile(pat_str, re.IGNORECASE)
            m = pat.search(text)
            if m:
                trigger = m.group(1).strip()
                if "never been well since" in text.lower():
                    return trigger
        # Generic "since" pattern
        m = re.search(r"never\s+(?:been\s+)?(?:well|right)\s+since\s+(?:a\s+|an\s+)?([\w\s]+?)(?:\.|,|;|$)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def _score_miasms(self, text: str) -> Dict[str, float]:
        """Score miasmatic affinity."""
        scores: Dict[str, float] = defaultdict(float)
        for miasm, pat in self._miasm_patterns.items():
            matches = pat.findall(text.lower())
            scores[miasm.value] = float(len(matches))
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        return dict(scores)

    def _build_summary(
        self,
        etiology: Optional[str],
        etiology_text: Optional[str],
        timeline: List[TimelineEvent],
        suppressions: List[str],
        miasm_scores: Dict[str, float],
        nwb: Optional[str],
    ) -> str:
        lines = []
        if etiology:
            lines.append(f"Detected etiology: '{etiology}' (cue: '{etiology_text}')")
        if nwb:
            lines.append(f"Never-well-since: '{nwb}'")
        if timeline:
            lines.append(f"Timeline events extracted: {len(timeline)}")
        if suppressions:
            lines.append(f"Suppression patterns: {len(suppressions)}")
        if any(miasm_scores.values()):
            top_miasm = max(miasm_scores, key=lambda k: miasm_scores[k])
            lines.append(f"Dominant miasm: {top_miasm} ({miasm_scores[top_miasm]:.0%})")
        return "\n".join(lines) if lines else "No causation or timeline cues detected."


# ── Quick function ─────────────────────────────────────────────────────────

def quick_causation(
    chief: str,
    timeline: str = "",
    history: str = "",
) -> CausationReport:
    """Quick helper to analyze causation and timeline."""
    return CausationTimelineAnalyzer().analyze(chief, timeline, history)
