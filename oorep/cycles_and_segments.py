"""
Cycles and Segments — Benefit #NN (Homeopathic Case Analysis)

A system-dynamics approach to classical homeopathy based on the
Cycles & Segments method articulated by Drs. Paul Herscu and
Amy Rothenberg via the New England School of Homeopathy (NESH).

Core thesis: Disease is a unit — one disease, one person, one moment.
The vital force generates symptoms as a recurring dynamic pattern (cycle)
composed of fundamental defensive reactions (segments). Every symptom
in a case should correlate to at least one segment of the remedy cycle.

This module provides:
  - ``CycleSegment``: a single segment (theme) in a remedy cycle
  - ``RemedyCycle``: the full directed cycle for a remedy
  - ``CyclesAndSegmentsEngine``: query, match, and generalize

Usage:
    from oorep import CyclesAndSegmentsEngine, RemedyCycle

    engine = CyclesAndSegmentsEngine()
    stram = engine.get_cycle("Stramonium")
    print(stram.sentence)          # One-sentence essence
    for seg in stram.segments:
        print(seg.name, seg.symptoms[:3])

    # Match a patient's symptoms to a cycle
    case = ["fear of death", "violent outbursts", "wants to be alone"]
    match = engine.match_case_to_cycle(case, stram)
    print(match["coverage"], match["matched_segments"])

References:
  - Herscu, P. (1996). *Stramonium: With an Introduction to Analysis
    Using Cycles and Segments.* New England School of Homeopathy Press.
  - Herscu, P. "The Cycle of Vipera." New England Journal of Homeopathy.
  - Herscu, P. "The Cycle of Kali carbonicum." New England Journal of Homeopathy.
  - Herscu, P. & Ryan, C. "The Cycle of Conium maculatum."
    New England Journal of Homeopathy.
  - NESH course materials: https://nesh.com/what-is-dr-paul-herscus-cycles-segments-approach/
  - Homeopathy Hangout Ep 203: "Cycles and Segments with Paul Herscu"

Attribution: This implementation is an independent software encoding of
Herscu's clinical method. All cycle descriptions, segment names, and the
one-sentence remedy essences are derived from the published works above.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class CycleSegment:
    """A single segment (station) in a remedy cycle.

    Attributes:
        name: Human-readable segment label (e.g., "Fear of death").
        description: Narrative of the defensive reaction / perception pattern.
        symptoms: Representative rubric-like symptoms for this segment.
        generalizations: Boenninghausen-style generalizations of symptoms.
        next_segment: Name of the segment this flows into (None = terminal).
    """
    name: str
    description: str = ""
    symptoms: List[str] = field(default_factory=list)
    generalizations: List[str] = field(default_factory=list)
    next_segment: Optional[str] = None


@dataclass
class RemedyCycle:
    """Full directed cycle for one remedy.

    Attributes:
        remedy_name: Canonical remedy name (e.g., "Stramonium").
        remedy_abbrev: Standard abbreviation (e.g., "Stram.").
        sentence: One-sentence essence attempting to capture every symptom.
        segments: Ordered list of CycleSegment nodes.
        cycle_loop: Whether the last segment loops back to the first.
        map_of_hierarchy_phase: Optional phase if part of pediatric hierarchy.
        references: Source citations for this cycle description.
    """
    remedy_name: str
    remedy_abbrev: str
    sentence: str
    segments: List[CycleSegment] = field(default_factory=list)
    cycle_loop: bool = True
    map_of_hierarchy_phase: Optional[int] = None
    references: List[str] = field(default_factory=list)

    def segment_by_name(self, name: str) -> Optional[CycleSegment]:
        for seg in self.segments:
            if seg.name.lower() == name.lower():
                return seg
        return None

    def transition_pairs(self) -> List[Tuple[str, str]]:
        """Return (from, to) segment name pairs in order."""
        pairs: List[Tuple[str, str]] = []
        for i, seg in enumerate(self.segments):
            if seg.next_segment:
                pairs.append((seg.name, seg.next_segment))
            elif self.cycle_loop and i == len(self.segments) - 1:
                pairs.append((seg.name, self.segments[0].name))
        return pairs

    def all_symptoms(self) -> List[str]:
        out: List[str] = []
        for seg in self.segments:
            out.extend(seg.symptoms)
        return out

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict (JSON-friendly)."""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RemedyCycle:
        segs = [CycleSegment(**s) for s in data.get("segments", [])]
        return cls(
            remedy_name=data["remedy_name"],
            remedy_abbrev=data.get("remedy_abbrev", ""),
            sentence=data.get("sentence", ""),
            segments=segs,
            cycle_loop=data.get("cycle_loop", True),
            map_of_hierarchy_phase=data.get("map_of_hierarchy_phase"),
            references=data.get("references", []),
        )


# ── Engine ───────────────────────────────────────────────────────────────────

class CyclesAndSegmentsEngine:
    """Query, match, and generalize using the Cycles & Segments method.

    Holds an in-memory registry of RemedyCycle objects. The canonical
    Stramonium cycle is baked in as the verified prototype; additional
    cycles can be registered at runtime or loaded from JSON.
    """

    # ── Built-in canonical cycles (verified against Herscu's publications) ─
    _CANONICAL_CYCLES: List[Dict[str, Any]] = [
        {
            "remedy_name": "Stramonium",
            "remedy_abbrev": "Stram.",
            "sentence": (
                "Driven by confusion, fears, and vulnerability, Stramonium is "
                "engaged in an ongoing and violent battle between the unconscious "
                "and the conscious, between darkness and light, between succumbing "
                "to the death realm and yearning to exist in the life realm."
            ),
            "cycle_loop": True,
            "map_of_hierarchy_phase": 4,
            "references": [
                'Herscu, P. (1996). "Stramonium: With an Introduction to Analysis '
                'Using Cycles and Segments." NESH Press.',
                'Herscu, P. "The Cycle of Stramonium." NESH curriculum materials.',
            ],
            "segments": [
                {
                    "name": "Fear of death or injury",
                    "description": (
                        "Profound panic, terror of dying, fear of the dark, of being "
                        "alone, of sudden violence. Nightmares, startles easily."
                    ),
                    "symptoms": [
                        "fear of death",
                        "fear of the dark",
                        "fear of being alone",
                        "nightmares",
                        "startling easily",
                        "terror on waking",
                        "anxiety about health",
                    ],
                    "generalizations": [
                        "fear",
                        "terror",
                        "panic",
                        "afraid",
                    ],
                    "next_segment": "Vulnerability and clinginess",
                },
                {
                    "name": "Vulnerability and clinginess",
                    "description": (
                        "After the terror, a desperate need for protection, to be held, "
                        "to never be left alone. Child clings to mother; adult is needy "
                        "and reassurance-seeking."
                    ),
                    "symptoms": [
                        "clinginess",
                        "desire for company",
                        "cannot be alone",
                        "needs to be held",
                        "whining",
                        "reassurance seeking",
                        "fear of abandonment",
                    ],
                    "generalizations": [
                        "clingy",
                        "dependent",
                        "needs company",
                        "aversion to solitude",
                    ],
                    "next_segment": "Violent overreaction",
                },
                {
                    "name": "Violent overreaction",
                    "description": (
                        "The suppressed terror erupts as rage, striking, biting, kicking, "
                        "destructiveness. The battle between darkness and light becomes "
                        "externalized. May be openly aggressive or passive-aggressive."
                    ),
                    "symptoms": [
                        "rage",
                        "striking",
                        "biting",
                        "destructive behavior",
                        "violent outbursts",
                        "fury",
                        "hits people",
                        "kicking",
                        "screaming",
                    ],
                    "generalizations": [
                        "violence",
                        "rage",
                        "destructive",
                        "aggressive",
                        "furious",
                    ],
                    "next_segment": "Desire to close off / shut down",
                },
                {
                    "name": "Desire to close off / shut down",
                    "description": (
                        "Overwhelmed by the violence, the individual withdraws, wants "
                        "darkness, silence, to shut everything out. Introversion, "
                        "aversion to light and noise."
                    ),
                    "symptoms": [
                        "desire for darkness",
                        "aversion to light",
                        "aversion to noise",
                        "withdrawal",
                        "introversion",
                        "wants to be alone",
                        "stares into space",
                        "unresponsive",
                    ],
                    "generalizations": [
                        "withdrawal",
                        "shut down",
                        "introverted",
                        "unresponsive",
                        "darkness",
                    ],
                    "next_segment": "Death and deadness",
                },
                {
                    "name": "Death and deadness",
                    "description": (
                        "A state of emotional and mental flatness: half alive, half dead. "
                        "Autistic features, loss of affect, as if the life force has "
                        "retreated to a minimal level."
                    ),
                    "symptoms": [
                        "absence of emotion",
                        "flat affect",
                        "autistic features",
                        "no reaction to stimuli",
                        "stupor",
                        "as if dead",
                        "half alive",
                    ],
                    "generalizations": [
                        "deadness",
                        "flat",
                        "stupor",
                        "no emotion",
                        "autism",
                    ],
                    "next_segment": "Confusion over dual state",
                },
                {
                    "name": "Confusion over dual state",
                    "description": (
                        "Awareness of being both alive and dead creates profound confusion. "
                        "Hallucinations, religious delusions, sees spirits, talks to the dead. "
                        "The cycle loops back to renewed fear."
                    ),
                    "symptoms": [
                        "confusion",
                        "hallucinations",
                        "religious delusions",
                        "sees spirits",
                        "talks to dead people",
                        "divided self",
                        "half alive half dead",
                    ],
                    "generalizations": [
                        "confused",
                        "hallucinating",
                        "delusional",
                        "sees things",
                        "divided",
                    ],
                    "next_segment": "Fear of death or injury",
                },
            ],
        },
    ]

    def __init__(self, data_path: Optional[str] = None):
        """
        Args:
            data_path: Optional directory or JSON file with extra cycles.
                      If omitted, auto-loads from ``data/cycles/`` beneath the
                      package root (if it exists).
        """
        self._cycles: Dict[str, RemedyCycle] = {}
        # Register canonical built-in cycles
        for raw in self._CANONICAL_CYCLES:
            rc = RemedyCycle.from_dict(raw)
            self._register(rc)

        # Auto-load from data/cycles/ if it exists
        auto_dir = Path(__file__).parent.parent / "data" / "cycles"
        if auto_dir.is_dir():
            for f in auto_dir.glob("*.json"):
                self._load_json_file(f)

        # Load extras if provided
        if data_path:
            p = Path(data_path)
            if p.is_file() and p.suffix == ".json":
                self._load_json_file(p)
            elif p.is_dir():
                for f in p.glob("*.json"):
                    self._load_json_file(f)

    def _register(self, rc: RemedyCycle) -> None:
        """Index by canonical name and abbreviation."""
        self._cycles[rc.remedy_name.lower()] = rc
        if rc.remedy_abbrev:
            # strip trailing period for flexibility
            ab = rc.remedy_abbrev.lower().rstrip(".")
            self._cycles[ab] = rc

    def _load_json_file(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Accept either a single dict or a list
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            rc = RemedyCycle.from_dict(entry)
            self._register(rc)

    # ── Public API ──────────────────────────────────────────────────────────

    def list_cycles(self) -> List[str]:
        """Return canonical remedy names of all registered cycles."""
        seen: set = set()
        out: List[str] = []
        for rc in self._cycles.values():
            if rc.remedy_name not in seen:
                seen.add(rc.remedy_name)
                out.append(rc.remedy_name)
        return out

    def get_cycle(self, remedy: str) -> Optional[RemedyCycle]:
        """Fetch a RemedyCycle by name or abbreviation (case-insensitive)."""
        key = remedy.lower()
        # Try exact match first (handles names with trailing periods like "L.")
        result = self._cycles.get(key)
        if result:
            return result
        # Fall back: strip trailing period for abbreviation flexibility
        return self._cycles.get(key.rstrip("."))

    def match_case_to_cycle(
        self,
        case_symptoms: List[str],
        cycle: RemedyCycle,
        generalize: bool = True,
    ) -> Dict[str, Any]:
        """Score how well a patient's symptoms map onto a remedy cycle.

        Returns dict with:
            matched_segments: list of segment names hit
            coverage: float 0..1 (symptoms matched / total symptoms)
            segment_scores: Dict[segment_name, float]
            generalized_hits: list of generalizations that fired
            missing_segments: list of segment names with zero hits
        """
        if not case_symptoms:
            return {
                "matched_segments": [],
                "coverage": 0.0,
                "segment_scores": {},
                "generalized_hits": [],
                "missing_segments": [s.name for s in cycle.segments],
            }

        # Normalize case symptoms
        case_tokens = [self._tokenize(s) for s in case_symptoms]

        segment_scores: Dict[str, float] = {}
        matched_segments: List[str] = []
        generalized_hits: List[str] = []
        missing_segments: List[str] = []

        total_possible = 0
        total_matched = 0

        for seg in cycle.segments:
            score = 0.0
            # Direct symptom match
            for sym in seg.symptoms:
                total_possible += 1
                sym_tokens = self._tokenize(sym)
                if any(self._overlap(sym_tokens, ct) for ct in case_tokens):
                    score += 1.0
                    total_matched += 1

            # Generalization match (if enabled)
            if generalize:
                for gen in seg.generalizations:
                    gen_tokens = self._tokenize(gen)
                    if any(self._overlap(gen_tokens, ct) for ct in case_tokens):
                        score += 0.5
                        generalized_hits.append(gen)

            segment_scores[seg.name] = score
            if score > 0:
                matched_segments.append(seg.name)
            else:
                missing_segments.append(seg.name)

        coverage = total_matched / total_possible if total_possible else 0.0

        return {
            "matched_segments": matched_segments,
            "coverage": round(coverage, 3),
            "segment_scores": {k: round(v, 2) for k, v in segment_scores.items()},
            "generalized_hits": list(set(generalized_hits)),
            "missing_segments": missing_segments,
        }

    def suggest_cycles_for_case(
        self,
        case_symptoms: List[str],
        limit: int = 5,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Rank all registered cycles by coverage for this case.

        Returns list of (remedy_name, coverage, match_dict) sorted desc.
        """
        scored: List[Tuple[str, float, Dict[str, Any]]] = []
        for name in self.list_cycles():
            cycle = self._cycles[name.lower()]
            match = self.match_case_to_cycle(case_symptoms, cycle)
            scored.append((name, match["coverage"], match))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def generalize_symptom(self, symptom: str, segment: CycleSegment) -> Optional[str]:
        """Apply Boenninghausen-style generalization.

        If the symptom matches the segment's symptom list, return the most
        appropriate generalization category; otherwise None.
        """
        sym_tokens = self._tokenize(symptom)
        for sym in segment.symptoms:
            if self._overlap(sym_tokens, self._tokenize(sym)):
                # Return first matching generalization as the broad category
                return segment.generalizations[0] if segment.generalizations else None
        return None

    def get_map_of_hierarchy(
        self,
    ) -> Dict[int, List[str]]:
        """Return phases → remedy names for the pediatric behavioral hierarchy.

        Phases (Herscu's Map of Hierarchy):
            1: Polychrests
            2: Nosodes
            3: Transition remedies (doorway between conscious/unconscious)
            4: Phase 4 remedies (uncontrolled passions or increasing dullness)
        """
        hierarchy: Dict[int, List[str]] = defaultdict(list)
        for rc in self._cycles.values():
            if rc.map_of_hierarchy_phase is not None:
                hierarchy[rc.map_of_hierarchy_phase].append(rc.remedy_name)
        # dedupe
        return {k: list(dict.fromkeys(v)) for k, v in hierarchy.items()}

    def enrich_repertorization(
        self,
        repertorization_results: List[Dict],
        case_symptoms: List[str],
        min_segments_matched: int = 2,
        min_coverage: float = 0.20,
    ) -> List[Dict]:
        """Enrich classical repertorization results with cycle/segment analysis.

        For each top remedy that has a registered cycle, this computes:
          - How many of the cycle's segments were hit by the case symptoms
          - Segment coverage ratio (segments matched / total segments)
          - Whether the cycle match meets configurable thresholds

        The enriched dict for each remedy gains a ``cycle_analysis`` key::

            {
                "remedy_cycle": str or None,
                "segment_matches": [str, ...],
                "segments_matched_count": int,
                "total_segments": int,
                "coverage": float,          # symptom-level coverage from match_case_to_cycle
                "segment_coverage": float,  # segments matched / total segments
                "generalized_hits": [str, ...],
                "cycle_sentence": str or None,
                "map_of_hierarchy_phase": int or None,
                "meets_threshold": bool,
            }

        Args:
            repertorization_results: Output list from ``HomeopathicRepertory.repertorize()``.
            case_symptoms: The original symptom strings the user entered.
            min_segments_matched: Minimum distinct segments that must match (default 2).
            min_coverage: Minimum *segment* coverage ratio required (default 0.20,
                i.e. at least 20% of the cycle's segments must be matched).

        Returns:
            The same list of dicts, each with an added ``cycle_analysis`` field.
        """
        out: List[Dict] = []
        for entry in repertorization_results:
            abbrev = entry.get("abbrev") or entry.get("name", "")
            cycle = self.get_cycle(abbrev)

            if cycle is None:
                entry["cycle_analysis"] = {
                    "remedy_cycle": None,
                    "segment_matches": [],
                    "segments_matched_count": 0,
                    "total_segments": 0,
                    "coverage": 0.0,
                    "segment_coverage": 0.0,
                    "generalized_hits": [],
                    "cycle_sentence": None,
                    "map_of_hierarchy_phase": None,
                    "meets_threshold": False,
                }
                out.append(entry)
                continue

            match = self.match_case_to_cycle(case_symptoms, cycle, generalize=True)
            seg_count = len(match["matched_segments"])
            tot = len(cycle.segments)
            segment_coverage = seg_count / tot if tot else 0.0
            meets = (seg_count >= min_segments_matched) and (segment_coverage >= min_coverage)

            entry["cycle_analysis"] = {
                "remedy_cycle": cycle.remedy_name,
                "segment_matches": match["matched_segments"],
                "segments_matched_count": seg_count,
                "total_segments": tot,
                "coverage": match["coverage"],
                "segment_coverage": round(segment_coverage, 3),
                "generalized_hits": match["generalized_hits"],
                "cycle_sentence": cycle.sentence,
                "map_of_hierarchy_phase": cycle.map_of_hierarchy_phase,
                "meets_threshold": meets,
            }
            out.append(entry)
        return out

    def export_cycles_json(self, path: str) -> None:
        """Serialize all registered cycles to a JSON file."""
        payload = [rc.to_dict() for rc in self._cycles.values()]
        # deduplicate by remedy_name before writing
        seen: set = set()
        clean: List[Dict[str, Any]] = []
        for item in payload:
            if item["remedy_name"] not in seen:
                seen.add(item["remedy_name"])
                clean.append(item)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> set:
        return set(re.findall(r"[a-z]{3,}", text.lower()))

    @staticmethod
    def _overlap(a: set, b: set) -> bool:
        return bool(a & b)
