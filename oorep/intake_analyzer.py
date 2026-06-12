"""
Intake Analyzer (Module #140)

Final quality analyzer for a completed patient intake. Combines outputs
from the entire intake pipeline (chief complaint, modalities, mental,
generals, constitutional) and produces:

  1. A "case quality score" (0-100) — is this case well-taken?
  2. A breakdown by Hering's directions of cure
  3. Identified strengths and gaps in the case
  4. Recommendations for the practitioner
  5. The "total symptom picture" (TSP) for repertorization
  6. Suitability scores for the constitutional vs acute remedy

Usage:
    from oorep.intake_analyzer import IntakeAnalyzer
    analyzer = IntakeAnalyzer()
    report = analyzer.analyze(
        chief_complaint_text=chief,
        triage=triage,
        symptoms=symptoms,
        modalities=modalities,
        mental_profile=mental,
        generals_profile=generals,
        constitutional=constitutional,
    )
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .chief_complaint_triager import TriageResult, Urgency
    from .concomitant_detector import ConcomitantAnalysis
    from .modality_extractor import ModalityGrid
    from .mental_emotional_prober import MentalEmotionalProfile
    from .generals_survey import GeneralsProfile
    from .constitutional_snapshot import ConstitutionalProfile
    from .causation_timeline_module import CausationReport
except Exception:
    from chief_complaint_triager import TriageResult, Urgency
    from concomitant_detector import ConcomitantAnalysis
    from modality_extractor import ModalityGrid
    from mental_emotional_prober import MentalEmotionalProfile
    from generals_survey import GeneralsProfile
    from constitutional_snapshot import ConstitutionalProfile
    from causation_timeline_module import CausationReport


class CaseQuality(Enum):
    """Overall case quality classification."""
    EXCELLENT = "excellent"     # 80-100
    GOOD = "good"               # 60-79
    ADEQUATE = "adequate"       # 40-59
    POOR = "poor"               # 20-39
    INSUFFICIENT = "insufficient"  # 0-19


class HeringDirection(Enum):
    """Hering's directions of cure."""
    ABOVE_DOWN = "above_down"          # Symptoms move from upper body to lower
    CENTER_OUT = "center_out"          # From more important organs to less
    DISAPPEARANCE = "disappearance"     # In reverse order of appearance
    NEW_FIRST = "new_first"             # New symptoms should appear first then resolve


@dataclass
class CaseReport:
    """Final case quality report."""
    quality_score: float                # 0-100
    quality_classification: CaseQuality
    strengths: List[str]                # What's strong about this case
    gaps: List[str]                     # What's missing
    recommendations: List[str]          # What to do next
    hering_directions: Dict[str, bool]  # Direction met?
    srp_symptom_count: int
    total_symptoms: int
    coverage_by_phase: Dict[str, float] # phase -> 0-1
    total_symptom_picture: List[Dict[str, Any]]  # For repertorization
    constitutional_remedy: Optional[str]
    acute_remedy: Optional[str]
    differential: List[Tuple[str, float]]  # (remedy, score)
    summary: str
    is_ready_to_prescribe: bool


class IntakeAnalyzer:
    """Final analyzer for a completed intake."""

    def __init__(self):
        pass

    def analyze(
        self,
        chief_complaint_text: str,
        triage: Optional[TriageResult] = None,
        symptoms: Optional[List[Any]] = None,
        modalities: Optional[ModalityGrid] = None,
        concomitants: Optional[ConcomitantAnalysis] = None,
        mental_profile: Optional[MentalEmotionalProfile] = None,
        generals_profile: Optional[GeneralsProfile] = None,
        constitutional: Optional[ConstitutionalProfile] = None,
        causation: Optional[CausationReport] = None,
        phases_covered: Optional[Dict[str, float]] = None,
    ) -> CaseReport:
        """
        Analyze a complete intake and produce a final case report.
        """
        symptoms = symptoms or []
        strengths: List[str] = []
        gaps: List[str] = []
        recommendations: List[str] = []

        # 1. SRP symptom count
        srp_count = 0
        if mental_profile and mental_profile.srp_signals:
            srp_count += len(mental_profile.srp_signals)
        if concomitants and concomitants.srp_signals:
            srp_count += len(concomitants.srp_signals)
        # Count high-SRP symptoms
        srp_count += sum(1 for s in symptoms if getattr(s, "srp_score", 0) > 0.6)

        # 2. Coverage by phase
        default_phases = {
            "opening": 0.5,
            "chief_complaint": 0.5,
            "history": 0.0,
            "modalities": 0.0,
            "concomitants": 0.0,
            "mind": 0.0,
            "generals": 0.0,
            "constitution": 0.0,
        }
        coverage = phases_covered or default_phases
        if modalities and modalities.modalities:
            coverage["modalities"] = min(1.0, len(modalities.axes_covered) / 4)
        if concomitants and concomitants.concomitants:
            coverage["concomitants"] = min(1.0, len(concomitants.concomitants) / 5)
        if mental_profile and mental_profile.symptoms_detected:
            coverage["mind"] = min(1.0, len(mental_profile.symptoms_detected) / 5)
        if generals_profile:
            coverage["generals"] = generals_profile.coverage_completeness
        if constitutional and constitutional.top_constitutional_remedy:
            coverage["constitution"] = constitutional.stability
        if causation and causation.etiology_detected:
            coverage["history"] = 0.8

        # 3. Strengths
        if srp_count >= 3:
            strengths.append(f"Strong SRP symptom count ({srp_count} SRP signals)")
        if mental_profile and mental_profile.characteristic_remedies:
            strengths.append(f"Mental symptoms identify {len(mental_profile.characteristic_remedies)} candidate remedies")
        if modalities and modalities.modalities:
            strengths.append(f"Captured {len(modalities.modalities)} modalities across {len(modalities.axes_covered)} axes")
        if generals_profile and generals_profile.coverage_completeness >= 0.5:
            strengths.append(f"Good generals coverage ({generals_profile.coverage_completeness:.0%})")
        if causation and causation.etiology_detected:
            strengths.append(f"Etiology identified: '{causation.etiology_detected}' (clear repertorization path)")
        if constitutional and constitutional.top_score >= 0.6:
            strengths.append(f"Strong constitutional match: {constitutional.top_constitutional_remedy}")

        # 4. Gaps
        if coverage["modalities"] < 0.5:
            gaps.append("Modalities under-explored — amel/agg of chief complaint need detail")
        if coverage["mind"] < 0.4:
            gaps.append("Mental symptoms thin — key for differentiating polycrest remedies")
        if coverage["generals"] < 0.4:
            gaps.append("Generals (thermal, sleep, food) incomplete")
        if coverage["concomitants"] < 0.4:
            gaps.append("Concomitants weak — Kent: 'Concomitants decide the case'")
        if not srp_count:
            gaps.append("No SRP (Strange-Rare-Peculiar) symptoms captured")
        if coverage["history"] < 0.3:
            gaps.append("Causation/timeline unclear — ask 'never been well since?'")

        # 5. Recommendations
        if coverage["modalities"] < 0.5:
            recommendations.append("Probe chief complaint modalities in detail: time, temperature, position, motion")
        if coverage["mind"] < 0.4:
            recommendations.append("Probe mental symptoms: fears, consolation, company, criticism reaction")
        if coverage["generals"] < 0.4:
            recommendations.append("Capture generals: thermal state, sleep position, food cravings/aversions, dreams")
        if srp_count < 2:
            recommendations.append("Probe for SRP symptoms: 'Anything strange, unusual, or peculiar?'")
        if triage and triage.urgency == Urgency.EMERGENCY:
            recommendations.insert(0, "⚠ RED FLAG — refer for medical care before continuing homeopathic treatment")
        if not recommendations and not gaps:
            recommendations.append("Case is well-taken. Proceed to repertorization.")

        # 6. Quality score (0-100)
        weights = {
            "modalities": 25,
            "mind": 20,
            "generals": 20,
            "concomitants": 20,
            "srp_bonus": 10,
            "constitution": 5,
        }
        quality = (
            coverage["modalities"] * weights["modalities"] +
            coverage["mind"] * weights["mind"] +
            coverage["generals"] * weights["generals"] +
            coverage["concomitants"] * weights["concomitants"] +
            min(1.0, srp_count / 5) * weights["srp_bonus"] +
            coverage["constitution"] * weights["constitution"]
        )
        quality = min(100.0, quality)

        # Classification
        if quality >= 80:
            classification = CaseQuality.EXCELLENT
        elif quality >= 60:
            classification = CaseQuality.GOOD
        elif quality >= 40:
            classification = CaseQuality.ADEQUATE
        elif quality >= 20:
            classification = CaseQuality.POOR
        else:
            classification = CaseQuality.INSUFFICIENT

        # 7. Hering's directions (rough heuristics)
        hering = {
            HeringDirection.ABOVE_DOWN.value: bool(constitutional and constitutional.top_constitutional_remedy),
            HeringDirection.CENTER_OUT.value: bool(causation and causation.suppressions),
            HeringDirection.DISAPPEARANCE.value: bool(causation and causation.timeline and len(causation.timeline) >= 2),
            HeringDirection.NEW_FIRST.value: bool(srp_count > 0),
        }

        # 8. Total Symptom Picture (TSP) — for repertorization
        tsp: List[Dict[str, Any]] = []
        for s in symptoms:
            tsp.append({
                "text": getattr(s, "text", ""),
                "chapter": getattr(s, "chapter", "General"),
                "grade": getattr(s, "grade", 2),
                "srp_score": getattr(s, "srp_score", 0),
            })
        if concomitants:
            for c in concomitants.concomitants:
                tsp.append({
                    "text": c.text,
                    "chapter": c.system,
                    "grade": 3,
                    "srp_score": c.srp_score,
                })
        if mental_profile:
            for m in mental_profile.symptoms_detected:
                tsp.append({
                    "text": m.text,
                    "chapter": "Mind",
                    "grade": m.weight,
                    "srp_score": m.srp_score,
                })
        if generals_profile:
            for g in generals_profile.symptoms:
                tsp.append({
                    "text": g.rubric_phrase,
                    "chapter": "Generals",
                    "grade": g.weight,
                    "srp_score": 0.5,
                })
        if modalities:
            for mod in modalities.modalities:
                tsp.append({
                    "text": mod.rubric_phrase,
                    "chapter": "Modalities",
                    "grade": 3 if mod.srp_score > 0.5 else 2,
                    "srp_score": mod.srp_score,
                })

        # 9. Differential — aggregate remedy scores
        remedy_scores: Dict[str, float] = defaultdict(float)
        for s in tsp:
            for r in self._lookup_symptom_remedies(s.get("text", "")):
                remedy_scores[r] += s.get("grade", 1) * 0.1 + s.get("srp_score", 0) * 0.5
        # Add constitutional
        if constitutional and constitutional.top_constitutional_remedy:
            remedy_scores[constitutional.top_constitutional_remedy] += constitutional.top_score * 5
        # Add mental
        if mental_profile:
            for r, w in zip(mental_profile.characteristic_remedies, [3, 2, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 0.5]):
                remedy_scores[r] += w
        # Add causation
        if causation and causation.etiology_remedies:
            for r in causation.etiology_remedies[:3]:
                remedy_scores[r] += 2
        # Add generals
        if generals_profile:
            for r, w in zip(generals_profile.characteristic_remedies, [3, 2, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 0.5]):
                remedy_scores[r] += w

        differential = sorted(remedy_scores.items(), key=lambda x: -x[1])[:10]
        top_constitutional = constitutional.top_constitutional_remedy if constitutional else None
        top_acute = differential[0][0] if differential and differential[0][1] > 0 else None

        is_ready = (
            quality >= 50 and
            srp_count >= 1 and
            coverage["modalities"] >= 0.4 and
            coverage["mind"] >= 0.4
        )

        summary = self._build_summary(
            quality, classification, srp_count, len(symptoms),
            coverage, strengths, gaps, is_ready, top_constitutional, top_acute,
        )

        return CaseReport(
            quality_score=quality,
            quality_classification=classification,
            strengths=strengths,
            gaps=gaps,
            recommendations=recommendations,
            hering_directions=hering,
            srp_symptom_count=srp_count,
            total_symptoms=len(symptoms) + (len(concomitants.concomitants) if concomitants else 0),
            coverage_by_phase=coverage,
            total_symptom_picture=tsp,
            constitutional_remedy=top_constitutional,
            acute_remedy=top_acute,
            differential=differential,
            summary=summary,
            is_ready_to_prescribe=is_ready,
        )

    def _lookup_symptom_remedies(self, symptom_text: str) -> List[str]:
        """Quick lookup of remedies for a symptom (using lexicon)."""
        # This would ideally use the full repertory, but for the analyzer
        # we use a quick keyword-based lookup
        text_lower = symptom_text.lower()
        remedies: List[str] = []
        # Common remedy triggers
        if "fever" in text_lower or "hot" in text_lower:
            remedies += ["Acon.", "Bell.", "Ferr-p.", "Gels."]
        if "headache" in text_lower or "migraine" in text_lower:
            remedies += ["Bell.", "Bry.", "Nux-v.", "Puls.", "Sep."]
        if "anxious" in text_lower or "anxiety" in text_lower:
            remedies += ["Ars.", "Acon.", "Calc.", "Phos."]
        if "thirst" in text_lower:
            remedies += ["Ars.", "Bry.", "Nat-m.", "Phos."]
        if "weep" in text_lower or "crying" in text_lower:
            remedies += ["Puls.", "Nat-m.", "Ign.", "Sep."]
        if "fear" in text_lower:
            remedies += ["Acon.", "Ars.", "Stram.", "Phos."]
        if "stomach" in text_lower or "nausea" in text_lower:
            remedies += ["Puls.", "Nux-v.", "Ars.", "Ipec."]
        return list(set(remedies))

    def _build_summary(
        self,
        quality: float,
        classification: CaseQuality,
        srp_count: int,
        total_symptoms: int,
        coverage: Dict[str, float],
        strengths: List[str],
        gaps: List[str],
        is_ready: bool,
        constitutional: Optional[str],
        acute: Optional[str],
    ) -> str:
        lines = [
            f"## Case Quality: {quality:.0f}/100 ({classification.value})",
            f"SRP symptoms: {srp_count} | Total symptoms: {total_symptoms}",
        ]
        lines.append("### Coverage by phase:")
        for phase, cov in coverage.items():
            bar = "█" * int(cov * 10) + "░" * (10 - int(cov * 10))
            lines.append(f"  {phase:20s} {bar} {cov:.0%}")
        if strengths:
            lines.append("### Strengths:")
            for s in strengths:
                lines.append(f"  ✓ {s}")
        if gaps:
            lines.append("### Gaps:")
            for g in gaps:
                lines.append(f"  ⚠ {g}")
        if constitutional:
            lines.append(f"Constitutional: {constitutional}")
        if acute:
            lines.append(f"Top acute differential: {acute}")
        lines.append("")
        lines.append(f"**{'READY TO PRESCRIBE' if is_ready else 'CONTINUE INTAKE'}**")
        return "\n".join(lines)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_analyze(
    chief: str,
    symptoms: Optional[List[Any]] = None,
    modalities: Optional[ModalityGrid] = None,
    mental: Optional[MentalEmotionalProfile] = None,
    generals: Optional[GeneralsProfile] = None,
    constitutional: Optional[ConstitutionalProfile] = None,
) -> CaseReport:
    """Quick helper to analyze a case."""
    return IntakeAnalyzer().analyze(
        chief_complaint_text=chief,
        symptoms=symptoms,
        modalities=modalities,
        mental_profile=mental,
        generals_profile=generals,
        constitutional=constitutional,
    )
