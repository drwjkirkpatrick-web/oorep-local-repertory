"""
Information-Theoretic Case Workup (Module #122)

Computes case "completeness" from an information-theoretic standpoint. Given
a set of candidate remedies and the symptoms elicited so far, returns:

  - bits_of_information_needed: how many more bits of symptom information
    are needed to reach a target confidence threshold (e.g. 0.95)
  - case_completeness: 0.0 to 1.0 — fraction of necessary information gathered
  - missing_symptom_categories: which chapters (Mind, Generals, etc.) are
    under-represented vs. an average well-taken case
  - entropy_reduction_curve: H(symptoms) vs. # symptoms elicited
  - sufficiency_score: is the case "well-taken" enough to prescribe on?

Math:
    H(R | S) = -sum_r P(r | S) log2 P(r | S)        # residual remedy entropy
    bits_needed = max(0, H(R | S) - H_target)        # bits still needed
    completeness = 1 - H(R | S) / H(R)                # fraction reduced

Usage:
    from oorep.information_theoretic_case_workup import CaseWorkupAnalyzer
    analyzer = CaseWorkupAnalyzer()
    report = analyzer.assess(symptoms=["fear of death"], candidate_pool_size=20)
"""

from __future__ import annotations

import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
    from ._v39_index import build_remedy_grade_index
except Exception:
    from homeopathic_repertory import HomeopathicRepertory
    from _v39_index import build_remedy_grade_index


@dataclass
class CaseWorkupReport:
    symptoms_count: int
    candidate_pool_size: int
    prior_entropy: float                # H(R) — uniform over candidates
    posterior_entropy: float            # H(R | symptoms)
    bits_of_information_gained: float   # H(R) - H(R | symptoms)
    bits_still_needed: float            # to reach confidence threshold
    target_entropy: float
    case_completeness: float            # 0.0 to 1.0
    sufficiency_score: float            # 0.0 to 1.0 — ready to prescribe?
    missing_categories: List[str]       # chapters under-represented
    entropy_curve: List[Tuple[int, float]]  # (# symptoms, H) pairs
    recommendation: str
    runtime_ms: float


class CaseWorkupAnalyzer:
    """
    Assess the information-theoretic completeness of a homeopathic case.
    """

    # Classical homeopathic case-taking expects coverage in these chapters
    EXPECTED_CHAPTERS = [
        "Mind", "Generals", "Sleep", "Dreams", "Appetite", "Stomach",
        "Abdomen", "Rectum", "Stool", "Urine", "Sexual", "Respiration",
        "Cough", "Expectoration", "Chest", "Back", "Extremities", "Skin",
        "Fever", "Perspiration", "Head", "Eye", "Ear", "Nose", "Face",
        "Mouth", "Teeth", "Throat", "Neck", "Bladder", "Kidney",
        "Male", "Female", "Pregnancy", "Parturition", "Larynx",
    ]

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        # Build forward index
        self._remedy_grades: Dict[str, Dict[int, int]] = build_remedy_grade_index(self.rep)

    def _shannon_entropy(self, distribution: Dict[str, float]) -> float:
        h = 0.0
        for p in distribution.values():
            if p > 0:
                h -= p * math.log2(p)
        return h

    def _normalize(self, scores: Dict[str, float]) -> Dict[str, float]:
        total = sum(scores.values())
        if total <= 0:
            n = len(scores)
            return {k: 1.0 / n for k in scores} if n else {}
        return {k: v / total for k, v in scores.items()}

    def _symptom_to_chapter(self, symptom: str) -> str:
        """Extract chapter from a symptom string (e.g. 'Mind; anxiety' → 'Mind')."""
        s = symptom.strip()
        if ";" in s:
            return s.split(";")[0].strip().title()
        # Common synonyms
        s_lc = s.lower()
        if any(k in s_lc for k in ["anxiety", "fear", "irritable", "sad", "weep"]):
            return "Mind"
        if any(k in s_lc for k in ["chill", "heat", "sweat", "energy"]):
            return "Generals"
        if "sleep" in s_lc or "dream" in s_lc:
            return "Sleep"
        return "Other"

    def _symptom_to_rubric_ids(self, symptom: str) -> List[int]:
        symptom_lc = symptom.lower().strip()
        rubric_ids: List[int] = []
        for rubric_id, rubric in getattr(self.rep, "rubrics", {}).items():
            fullpath = (rubric.get("fullpath") or rubric.get("path") or "").lower()
            if symptom_lc and (symptom_lc in fullpath or fullpath in symptom_lc):
                rubric_ids.append(rubric_id)
        return rubric_ids

    def _compute_posterior(
        self,
        symptoms: List[str],
        candidate_pool: List[str],
    ) -> Dict[str, float]:
        """Naive Bayes log-likelihood for each candidate remedy."""
        scores: Dict[str, float] = {r: 0.0 for r in candidate_pool}
        for symptom in symptoms:
            rubric_ids = self._symptom_to_rubric_ids(symptom)
            for rubric_id in rubric_ids:
                for remedy in candidate_pool:
                    grade = self._remedy_grades[remedy].get(rubric_id, 0)
                    if grade > 0:
                        scores[remedy] += math.log(1 + grade)
        max_s = max(scores.values()) if scores else 0
        exp_s = {r: math.exp(s - max_s) for r, s in scores.items()}
        return self._normalize(exp_s)

    def _entropy_curve(
        self,
        symptoms: List[str],
        candidate_pool: List[str],
    ) -> List[Tuple[int, float]]:
        """Compute H(R | first n symptoms) for n = 0, 1, 2, ..., len(symptoms)."""
        curve: List[Tuple[int, float]] = []
        for n in range(0, len(symptoms) + 1):
            partial = symptoms[:n]
            post = self._compute_posterior(partial, candidate_pool)
            curve.append((n, self._shannon_entropy(post)))
        return curve

    def assess(
        self,
        symptoms: List[str],
        candidate_pool: Optional[List[str]] = None,
        target_confidence: float = 0.95,
    ) -> CaseWorkupReport:
        """
        Assess the information-theoretic completeness of a case.

        Parameters
        ----------
        symptoms : list of str
            Symptoms already elicited.
        candidate_pool : list of str, optional
            The remedies the practitioner is considering. If None, uses top 20
            most frequently prescribed remedies.
        target_confidence : float
            Desired posterior confidence (default 0.95).
        """
        import time
        t0 = time.time()

        # Default candidate pool: top 20 by rubric coverage
        if candidate_pool is None:
            sorted_by_coverage = sorted(
                self._remedy_grades.items(),
                key=lambda x: len(x[1]),
                reverse=True,
            )
            candidate_pool = [r for r, _ in sorted_by_coverage[:20]]

        n = len(candidate_pool)
        # Prior: uniform over the candidate pool
        prior = {r: 1.0 / n for r in candidate_pool} if n else {}
        prior_h = self._shannon_entropy(prior)

        # Posterior after current symptoms
        post = self._compute_posterior(symptoms, candidate_pool)
        post_h = self._shannon_entropy(post)

        bits_gained = max(0.0, prior_h - post_h)
        # H_target = bits needed to reach target confidence
        # P(recommendation) >= target_confidence  =>  H <= -log2(target)
        target_h = -math.log2(target_confidence) if 0 < target_confidence < 1 else 0.0
        bits_needed = max(0.0, post_h - target_h)
        completeness = bits_gained / prior_h if prior_h > 0 else 1.0
        completeness = min(1.0, max(0.0, completeness))

        # Chapter coverage
        chapters_present: Counter = Counter()
        for s in symptoms:
            chapters_present[self._symptom_to_chapter(s)] += 1
        # A well-taken case should touch at least 5 distinct chapters
        distinct_chapters = len(chapters_present)
        expected_minimum = 5
        chapter_coverage = min(1.0, distinct_chapters / expected_minimum)

        # Missing categories = EXPECTED_CHAPTERS not yet touched
        missing = [c for c in self.EXPECTED_CHAPTERS if c not in chapters_present][:5]

        # Sufficiency: weighted combination
        sufficiency = 0.6 * completeness + 0.4 * chapter_coverage
        sufficiency = min(1.0, max(0.0, sufficiency))

        if sufficiency >= 0.85:
            recommendation = "Case is well-taken. Safe to consider prescription."
        elif sufficiency >= 0.65:
            recommendation = "Adequate. Consider 1-2 more questions in under-represented chapters."
        elif sufficiency >= 0.4:
            recommendation = "Case is thin. Elicit symptoms from Mind, Generals, and a key body system."
        else:
            recommendation = "Case is too thin. Continue case-taking across multiple chapters."

        curve = self._entropy_curve(symptoms, candidate_pool)

        return CaseWorkupReport(
            symptoms_count=len(symptoms),
            candidate_pool_size=n,
            prior_entropy=prior_h,
            posterior_entropy=post_h,
            bits_of_information_gained=bits_gained,
            bits_still_needed=bits_needed,
            target_entropy=target_h,
            case_completeness=completeness,
            sufficiency_score=sufficiency,
            missing_categories=missing,
            entropy_curve=curve,
            recommendation=recommendation,
            runtime_ms=(time.time() - t0) * 1000,
        )


# ── Quick function ─────────────────────────────────────────────────────────

def quick_workup(symptoms: List[str], n_candidates: int = 20) -> CaseWorkupReport:
    """Quick helper to assess case completeness."""
    sorted_by_coverage = sorted(
        HomeopathicRepertory().rubric_to_remedies.items(), key=lambda x: 0
    )
    rep = HomeopathicRepertory()
    return CaseWorkupAnalyzer(rep).assess(symptoms, candidate_pool=None)
