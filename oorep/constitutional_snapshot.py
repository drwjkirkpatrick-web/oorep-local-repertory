"""
Constitutional Snapshot (Module #139)

Builds a constitutional picture of the patient from their intake data.
A "constitutional remedy" is the deepest, most stable, lifelong pattern
of a person — not just the current chief complaint.

This module:
  1. Synthesizes information from mental, general, and physical patterns
  2. Identifies the constitutional type based on miasm, temperament, and generals
  3. Ranks constitutional remedy candidates
  4. Distinguishes the constitutional remedy from the current acute remedy
  5. Tracks the stability of the constitutional pattern (how well-established)

Usage:
    from oorep.constitutional_snapshot import ConstitutionalSnapshot
    snap = ConstitutionalSnapshot()
    profile = snap.build(
        mental_profile=mental,
        generals_profile=generals,
        modality_grid=modalities,
    )
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .mental_emotional_prober import MentalEmotionalProfile
    from .generals_survey import GeneralsProfile
    from .modality_extractor import ModalityGrid
except Exception:
    from mental_emotional_prober import MentalEmotionalProfile
    from generals_survey import GeneralsProfile
    from modality_extractor import ModalityGrid


# Constitutional archetypes with characteristic signatures
CONSTITUTIONAL_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "psora_pulsatilla": {
        "name": "Pulsatilla constitution",
        "remedies": ["Puls.", "Puls-n."],
        "signature": {
            "thermal": "warm",
            "company": "amel",
            "consolation": "amel",
            "mood": "weepy",
            "cravings": [],
            "side": None,
            "modality": ["open air better", "evening worse"],
        },
        "weight": 4,
    },
    "psora_nux_vomica": {
        "name": "Nux vomica constitution",
        "remedies": ["Nux-v."],
        "signature": {
            "thermal": "cold",
            "company": "agg",
            "consolation": "agg",
            "mood": "irritable",
            "cravings": ["fat", "coffee", "alcohol"],
            "side": None,
            "modality": ["morning worse", "after overwork"],
        },
        "weight": 4,
    },
    "psora_arsenicum": {
        "name": "Arsenicum album constitution",
        "remedies": ["Ars.", "Ars-i."],
        "signature": {
            "thermal": "cold",
            "company": "agg",
            "consolation": "agg",
            "mood": "anxious",
            "cravings": ["fat"],
            "side": None,
            "modality": ["1-2am worse", "thirst for small sips"],
        },
        "weight": 4,
    },
    "psora_sulphur": {
        "name": "Sulphur constitution",
        "remedies": ["Sulph."],
        "signature": {
            "thermal": "warm",
            "company": "neutral",
            "consolation": "neutral",
            "mood": "ego",
            "cravings": ["sweet"],
            "side": "left",
            "modality": ["morning worse", "warmth worse"],
        },
        "weight": 3,
    },
    "sycotic_medorrhinum": {
        "name": "Medorrhinum (Tubercular) constitution",
        "remedies": ["Med.", "Tub."],
        "signature": {
            "thermal": "warm",
            "company": "amel",
            "consolation": "agg",
            "mood": "restless",
            "cravings": ["ice", "salt"],
            "side": None,
            "modality": ["seashore better", "damp worse", "3-4am worse"],
        },
        "weight": 4,
    },
    "sycotic_thuja": {
        "name": "Thuja (Sycotic) constitution",
        "remedies": ["Thuj."],
        "signature": {
            "thermal": "cold",
            "company": "neutral",
            "consolation": "neutral",
            "mood": "secretive",
            "cravings": ["tea"],
            "side": "left",
            "modality": ["damp worse", "warts"],
        },
        "weight": 3,
    },
    "syphilitic_aurum": {
        "name": "Aurum (Syphilitic) constitution",
        "remedies": ["Aur.", "Aur-m.", "Aur-s."],
        "signature": {
            "thermal": "cold",
            "company": "amel",
            "consolation": "neutral",
            "mood": "depressed",
            "cravings": [],
            "side": None,
            "modality": ["night worse", "music amel"],
        },
        "weight": 4,
    },
    "tubercular_calc_phos": {
        "name": "Calcarea phosphorica (Tubercular) constitution",
        "remedies": ["Calc-p.", "Calc."],
        "signature": {
            "thermal": "cold",
            "company": "agg",
            "consolation": "amel",
            "mood": "irritable",
            "cravings": ["salt", "fat", "eggs", "ice"],
            "side": "right",
            "modality": ["damp worse", "cold worse"],
        },
        "weight": 4,
    },
    "carbon_calc": {
        "name": "Calcarea carbonica constitution",
        "remedies": ["Calc.", "Calc-ar."],
        "signature": {
            "thermal": "cold",
            "company": "agg",
            "consolation": "neutral",
            "mood": "anxious",
            "cravings": ["eggs", "salt", "ice"],
            "side": "right",
            "modality": ["cold damp worse", "slow development"],
        },
        "weight": 3,
    },
    "phosphoric_lycopodium": {
        "name": "Lycopodium constitution",
        "remedies": ["Lyc.", "Lyc-v."],
        "signature": {
            "thermal": "warm",
            "company": "neutral",
            "consolation": "agg",
            "mood": "ego",
            "cravings": ["sweet", "warm drinks"],
            "side": "right",
            "modality": ["4-8pm worse", "warmth worse", "fasting worse"],
        },
        "weight": 4,
    },
    "natrum_muriaticum": {
        "name": "Natrum muriaticum constitution",
        "remedies": ["Nat-m.", "Nat-ar."],
        "signature": {
            "thermal": "cold",
            "company": "agg",
            "consolation": "agg",
            "mood": "grief",
            "cravings": ["salt"],
            "side": "left",
            "modality": ["seashore worse", "sun worse", "10am worse"],
        },
        "weight": 4,
    },
    "silicea": {
        "name": "Silicea constitution",
        "remedies": ["Sil."],
        "signature": {
            "thermal": "cold",
            "company": "neutral",
            "consolation": "neutral",
            "mood": "yielding",
            "cravings": [],
            "side": "right",
            "modality": ["cold worse", "new moon worse"],
        },
        "weight": 3,
    },
}


@dataclass
class ConstitutionalArchetypeMatch:
    archetype_id: str
    name: str
    remedies: List[str]
    match_score: float
    matched_features: List[str]
    missing_features: List[str]


@dataclass
class ConstitutionalProfile:
    archetype_matches: List[ConstitutionalArchetypeMatch]
    top_constitutional_remedy: Optional[str]
    top_score: float
    stability: float                      # 0-1
    lifelong_patterns: List[str]            # Generals that have been lifelong
    recommendations: List[str]
    summary: str


class ConstitutionalSnapshot:
    """Builds a constitutional picture of the patient."""

    def __init__(self):
        self.archetypes = CONSTITUTIONAL_ARCHETYPES

    def build(
        self,
        mental_profile: Optional[MentalEmotionalProfile] = None,
        generals_profile: Optional[GeneralsProfile] = None,
        modality_grid: Optional[ModalityGrid] = None,
    ) -> ConstitutionalProfile:
        """
        Build a constitutional profile from intake data.
        """
        matches: List[ConstitutionalArchetypeMatch] = []
        for arch_id, archetype in self.archetypes.items():
            score, matched, missing = self._match_archetype(
                archetype, mental_profile, generals_profile, modality_grid
            )
            if score > 0.0:
                matches.append(ConstitutionalArchetypeMatch(
                    archetype_id=arch_id,
                    name=archetype["name"],
                    remedies=archetype["remedies"],
                    match_score=score,
                    matched_features=matched,
                    missing_features=missing,
                ))

        # Sort by score
        matches.sort(key=lambda m: m.match_score, reverse=True)

        top_match = matches[0] if matches else None
        top_remedy = top_match.remedies[0] if top_match else None
        top_score = top_match.match_score if top_match else 0.0

        # Stability: how many features agree
        stability = self._compute_stability(matches)

        lifelong = []
        if generals_profile and generals_profile.thermal_state:
            lifelong.append(f"Thermally {generals_profile.thermal_state}-blooded")
        if generals_profile and generals_profile.sleep_position:
            lifelong.append(f"Sleeps on {generals_profile.sleep_position}")
        if generals_profile and generals_profile.food_cravings:
            lifelong.append(f"Craves: {', '.join(generals_profile.food_cravings)}")

        recommendations = self._build_recommendations(top_match, mental_profile, generals_profile)
        summary = self._build_summary(top_match, stability, lifelong, recommendations)

        return ConstitutionalProfile(
            archetype_matches=matches,
            top_constitutional_remedy=top_remedy,
            top_score=top_score,
            stability=stability,
            lifelong_patterns=lifelong,
            recommendations=recommendations,
            summary=summary,
        )

    def _match_archetype(
        self,
        archetype: Dict[str, Any],
        mental: Optional[MentalEmotionalProfile],
        generals: Optional[GeneralsProfile],
        modalities: Optional[ModalityGrid],
    ) -> Tuple[float, List[str], List[str]]:
        """Match a case against an archetype signature."""
        sig = archetype["signature"]
        matched: List[str] = []
        missing: List[str] = []
        points = 0.0
        max_points = 0.0

        # Thermal
        max_points += 1.0
        if generals and generals.thermal_state == sig.get("thermal"):
            points += 1.0
            matched.append(f"thermal: {sig['thermal']}")
        elif generals and generals.thermal_state is not None:
            missing.append(f"thermal: expected {sig['thermal']}, got {generals.thermal_state}")
        else:
            missing.append("thermal: unknown")

        # Company
        max_points += 1.0
        if mental and mental.company_response == sig.get("company"):
            points += 1.0
            matched.append(f"company: {sig['company']}")
        elif mental and mental.company_response is not None:
            missing.append(f"company: expected {sig['company']}")
        else:
            missing.append("company: unknown")

        # Consolation
        max_points += 0.8
        if mental and mental.consolation_response == sig.get("consolation"):
            points += 0.8
            matched.append(f"consolation: {sig['consolation']}")
        elif mental and mental.consolation_response is not None:
            missing.append(f"consolation: expected {sig['consolation']}")
        else:
            missing.append("consolation: unknown")

        # Cravings overlap
        max_points += 1.0
        if generals and sig.get("cravings"):
            overlap = set(generals.food_cravings) & set(sig["cravings"])
            if overlap:
                points += 1.0 * len(overlap) / len(sig["cravings"])
                matched.append(f"cravings: {', '.join(overlap)}")
            else:
                missing.append(f"cravings: expected any of {', '.join(sig['cravings'])}")
        else:
            missing.append("cravings: unknown")

        # Side
        if sig.get("side"):
            max_points += 0.5
            if generals and generals.side_affinity == sig["side"]:
                points += 0.5
                matched.append(f"side: {sig['side']}")
            else:
                missing.append(f"side: expected {sig['side']}")

        # Mood from mental
        if sig.get("mood") and mental:
            max_points += 1.0
            mood = sig["mood"]
            mood_matched = False
            if mood == "weepy" and any("weep" in s.symptom_type for s in mental.symptoms_detected):
                mood_matched = True
            elif mood == "anxious" and any("anxiet" in s.symptom_type for s in mental.symptoms_detected):
                mood_matched = True
            elif mood == "irritable" and any("irritab" in s.symptom_type for s in mental.symptoms_detected):
                mood_matched = True
            elif mood == "grief" and any("grief" in s.symptom_type for s in mental.symptoms_detected):
                mood_matched = True
            elif mood == "restless" and any("restless" in s.symptom_type for s in mental.symptoms_detected):
                mood_matched = True
            elif mood == "ego" and any("domineer" in s.symptom_type or "sensitive_crit" in s.symptom_type for s in mental.symptoms_detected):
                mood_matched = True
            if mood_matched:
                points += 1.0
                matched.append(f"mood: {mood}")
            else:
                missing.append(f"mood: expected {mood}")

        score = points / max_points if max_points > 0 else 0.0
        return score, matched, missing

    def _compute_stability(self, matches: List[ConstitutionalArchetypeMatch]) -> float:
        """How stable is the constitutional pattern?"""
        if not matches:
            return 0.0
        top = matches[0]
        # High stability if top match is much better than 2nd
        if len(matches) >= 2:
            gap = top.match_score - matches[1].match_score
        else:
            gap = top.match_score
        return min(1.0, top.match_score * 0.7 + gap * 0.3)

    def _build_recommendations(
        self,
        top: Optional[ConstitutionalArchetypeMatch],
        mental: Optional[MentalEmotionalProfile],
        generals: Optional[GeneralsProfile],
    ) -> List[str]:
        recs = []
        if top and top.match_score > 0.6:
            recs.append(f"Constitutional remedy: {top.remedies[0]} (match {top.match_score:.0%})")
        if top and top.missing_features:
            recs.append(f"Consider asking about: {', '.join(top.missing_features[:3])}")
        if not mental or not mental.fear_spectrum:
            recs.append("Probe fears more deeply (death, alone, suffocation)")
        if not generals or not generals.dream_themes:
            recs.append("Capture dream themes (fire, water, animals, etc.)")
        if not generals or not generals.thermal_state:
            recs.append("Confirm thermal state (warm vs cold constitution)")
        return recs

    def _build_summary(
        self,
        top: Optional[ConstitutionalArchetypeMatch],
        stability: float,
        lifelong: List[str],
        recs: List[str],
    ) -> str:
        lines = []
        if top:
            lines.append(f"Best constitutional match: {top.name} ({top.match_score:.0%})")
        lines.append(f"Pattern stability: {stability:.0%}")
        if lifelong:
            lines.append(f"Lifelong patterns: {'; '.join(lifelong)}")
        if recs:
            lines.append("Recommendations:")
            for r in recs:
                lines.append(f"  - {r}")
        return "\n".join(lines) if lines else "Insufficient data for constitutional analysis."


# ── Quick function ─────────────────────────────────────────────────────────

def quick_constitutional(
    mental: Optional[MentalEmotionalProfile] = None,
    generals: Optional[GeneralsProfile] = None,
    modalities: Optional[ModalityGrid] = None,
) -> ConstitutionalProfile:
    """Quick helper to build a constitutional profile."""
    return ConstitutionalSnapshot().build(mental, generals, modalities)
