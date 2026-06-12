"""
Discriminant Rubric Selector (Module #121)

Reverse-engineers the PATIENT QUESTIONS that best differentiate the leading
remedy candidates. Given a list of candidate remedies, computes the marginal
discriminative value of every unreported rubric and returns the questions
ranked by information gain.

This is the "differential question engine" - it tells the practitioner
EXACTLY what to ask next to break ties between remedies.

Mathematical approach:
    For candidate remedies R = {r1, r2, ..., rk}, candidate pool size k
    For each unreported rubric u with remedy grades g(r, u):
        compute class-conditional probabilities P(r | u) for u ∈ {absent, low, med, high, bold}
        rank u by expected reduction in Shannon entropy of the posterior P(r | answers)
        = sum over answers of P(answer) * H(P(r | answer))

Usage:
    from oorep.discriminant_rubric_selector import DiscriminantRubricSelector
    selector = DiscriminantRubricSelector()
    questions = selector.next_questions(
        current_symptoms=["fear of death", "violent outbursts"],
        candidate_remedies=["Stram.", "Bell.", "Hyos."],
        n=5
    )
    # Returns top 5 questions that best differentiate these 3 remedies
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
    from ._v39_index import build_remedy_grade_index
except Exception:
    from homeopathic_repertory import HomeopathicRepertory
    from _v39_index import build_remedy_grade_index


# Classical homeopathic grade weights (Roman=1, Italic=2, Bold=3)
GRADE_WEIGHTS = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}


@dataclass
class DifferentialQuestion:
    """A single differential question suggested for the practitioner."""
    rubric_id: int
    rubric_text: str
    chapter: str
    expected_answer_options: List[str]  # ["absent", "grade-1", "grade-2", "grade-3", "grade-4"]
    prior_entropy: float                # Shannon entropy before asking
    expected_posterior_entropy: float    # Expected entropy after asking
    info_gain: float                    # bits of information gained
    remedy_breakdown: Dict[str, str]    # abbrev -> "present-bold"/"absent" etc
    rationale: str                      # Human-readable explanation


@dataclass
class DifferentialReport:
    candidates_evaluated: List[str]
    pool_entropy: float                 # Initial uncertainty
    n_questions: int
    questions: List[DifferentialQuestion]
    top_recommendation: Optional[str]   # Remedy with highest posterior
    posterior_distribution: Dict[str, float]  # P(remedy | current symptoms)
    runtime_ms: float


class DiscriminantRubricSelector:
    """
    Suggests follow-up questions that maximally differentiate the leading
    candidate remedies. Uses information-theoretic rubric ranking.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        # Build forward index: remedy_abbrev -> {rubric_id: max_grade}
        self._remedy_grades: Dict[str, Dict[int, int]] = build_remedy_grade_index(self.rep)

    def _shannon_entropy(self, distribution: Dict[str, float]) -> float:
        """Shannon entropy in bits: H = -sum p*log2(p)"""
        h = 0.0
        for p in distribution.values():
            if p > 0:
                h -= p * math.log2(p)
        return h

    def _normalize(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to a probability distribution."""
        total = sum(scores.values())
        if total <= 0:
            n = len(scores)
            return {k: 1.0 / n for k in scores} if n else {}
        return {k: v / total for k, v in scores.items()}

    def _grade_to_label(self, grade: int) -> str:
        if grade <= 0:
            return "absent"
        if grade == 1:
            return "grade-1"
        if grade == 2:
            return "grade-2"
        if grade == 3:
            return "grade-3"
        return "grade-4"

    def _compute_initial_posterior(
        self,
        current_symptoms: List[str],
        candidates: List[str],
    ) -> Dict[str, float]:
        """
        Compute the current posterior P(remedy | current symptoms)
        using a Naive Bayes log-likelihood update over the symptom rubric matches.
        """
        scores: Dict[str, float] = {r: 0.0 for r in candidates}
        for symptom in current_symptoms:
            # Look up matching rubric ids for this symptom string
            rubric_ids = self._symptom_to_rubric_ids(symptom)
            for rubric_id in rubric_ids:
                for remedy in candidates:
                    grade = self._remedy_grades[remedy].get(rubric_id, 0)
                    if grade > 0:
                        # Log-likelihood: log(P(rubric | remedy) * grade_weight)
                        scores[remedy] += math.log(1 + grade)
        # Convert log scores to probabilities
        max_score = max(scores.values()) if scores else 0
        exp_scores = {r: math.exp(s - max_score) for r, s in scores.items()}
        return self._normalize(exp_scores)

    def _symptom_to_rubric_ids(self, symptom: str) -> List[int]:
        """Map a free-text symptom to matching rubric ids via the repertory's lookup."""
        if not symptom:
            return []
        symptom_lc = symptom.lower().strip()
        rubric_ids: List[int] = []
        # Iterate rubric id -> links to find rubric text matches
        for rubric_id, rubric in getattr(self.rep, "rubrics", {}).items():
            fullpath = (rubric.get("fullpath") or rubric.get("path") or "").lower()
            if symptom_lc in fullpath or fullpath in symptom_lc:
                rubric_ids.append(rubric_id)
        return rubric_ids

    def _get_remedy_grade_for_rubric(self, remedy: str, rubric_id: int) -> int:
        return self._remedy_grades[remedy].get(rubric_id, 0)

    def _information_gain_for_rubric(
        self,
        rubric_id: int,
        candidates: List[str],
        prior: Dict[str, float],
    ) -> Tuple[float, Dict[str, str], str]:
        """
        Compute expected information gain (in bits) of asking about this rubric.

        For each answer option a ∈ {absent, grade-1, ..., grade-4}:
            P(a) = sum_r prior(r) * P(a | r)
            posterior P(r | a) ∝ P(a | r) * prior(r)
        Expected posterior entropy = sum_a P(a) * H(P(r | a))
        Info gain = H(prior) - Expected posterior entropy
        """
        # For each candidate remedy, get the grade (0=absent..4=bold)
        grades = {r: self._get_remedy_grade_for_rubric(r, rubric_id) for r in candidates}

        # P(answer | remedy) using a simple model: weight ∝ grade+1, normalized
        # For absent: a small uniform prior to avoid zero probabilities
        answer_options = ["absent", "grade-1", "grade-2", "grade-3", "grade-4"]

        # Expected posterior entropy
        expected_h = 0.0
        for ans in answer_options:
            # P(ans | r): look up the grade match
            likelihoods = {}
            for r in candidates:
                g = grades[r]
                if ans == "absent":
                    likelihoods[r] = 0.6 if g == 0 else 0.05
                else:
                    target_grade = int(ans.split("-")[1])
                    likelihoods[r] = 0.8 if g == target_grade else 0.05
            # Posterior ∝ likelihood * prior
            posteriors = {r: likelihoods[r] * prior.get(r, 1e-9) for r in candidates}
            posteriors = self._normalize(posteriors)
            # P(ans) = sum_r prior(r) * likelihoods(r)
            p_ans = sum(prior.get(r, 0) * likelihoods[r] for r in candidates)
            if p_ans > 0:
                expected_h += p_ans * self._shannon_entropy(posteriors)

        prior_h = self._shannon_entropy(prior)
        info_gain = max(0.0, prior_h - expected_h)

        # Build remedy breakdown for the practitioner
        breakdown: Dict[str, str] = {}
        for r in candidates:
            breakdown[r] = self._grade_to_label(grades[r])

        # Rationale
        if info_gain < 0.01:
            rationale = "All candidates respond similarly — low differentiation value."
        elif info_gain > prior_h * 0.4:
            rationale = f"High-value: splits top candidates (gain={info_gain:.2f} bits)."
        else:
            rationale = f"Moderate differentiation value (gain={info_gain:.2f} bits)."

        return info_gain, breakdown, rationale

    def next_questions(
        self,
        current_symptoms: List[str],
        candidate_remedies: List[str],
        n: int = 5,
        rubric_pool: Optional[List[int]] = None,
    ) -> DifferentialReport:
        """
        Return the top-n differential questions for the case.

        Parameters
        ----------
        current_symptoms : list of str
            Symptoms already elicited from the patient.
        candidate_remedies : list of str
            Short list of leading remedy candidates to differentiate.
        n : int
            How many questions to suggest (default 5).
        rubric_pool : list of int, optional
            Restrict candidates to a specific rubric id pool. If None, scans
            all rubrics where at least one candidate has a non-zero grade.

        Returns
        -------
        DifferentialReport
        """
        import time
        t0 = time.time()

        candidates = list(candidate_remedies)
        if len(candidates) < 2:
            return DifferentialReport(
                candidates_evaluated=candidates,
                pool_entropy=0.0,
                n_questions=0,
                questions=[],
                top_recommendation=candidates[0] if candidates else None,
                posterior_distribution={c: 1.0 for c in candidates},
                runtime_ms=(time.time() - t0) * 1000,
            )

        prior = self._compute_initial_posterior(current_symptoms, candidates)
        prior_h = self._shannon_entropy(prior)

        # Build candidate rubric pool
        if rubric_pool is None:
            pool: Set[int] = set()
            for remedy in candidates:
                pool.update(self._remedy_grades[remedy].keys())
            rubric_pool_list: List[int] = list(pool)
        else:
            rubric_pool_list = list(rubric_pool)

        # Score every rubric
        scored: List[Tuple[float, int, Dict[str, str], str]] = []
        for rubric_id in rubric_pool_list:
            info_gain, breakdown, rationale = self._information_gain_for_rubric(
                rubric_id, candidates, prior
            )
            scored.append((info_gain, rubric_id, breakdown, rationale))

        # Sort by info gain descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Build DifferentialQuestion list
        questions: List[DifferentialQuestion] = []
        for info_gain, rubric_id, breakdown, rationale in scored[:n]:
            rubric = getattr(self.rep, "rubrics", {}).get(rubric_id, {})
            rubric_text = (
                rubric.get("fullpath")
                or rubric.get("path")
                or rubric.get("name")
                or f"Rubric {rubric_id}"
            )
            chapter = rubric.get("chapter", "Unknown")
            dq = DifferentialQuestion(
                rubric_id=rubric_id,
                rubric_text=rubric_text,
                chapter=chapter,
                expected_answer_options=["absent", "grade-1", "grade-2", "grade-3", "grade-4"],
                prior_entropy=prior_h,
                expected_posterior_entropy=prior_h - info_gain,
                info_gain=info_gain,
                remedy_breakdown=breakdown,
                rationale=rationale,
            )
            questions.append(dq)

        # Top recommendation = argmax posterior
        top = max(prior.items(), key=lambda x: x[1])[0] if prior else None

        return DifferentialReport(
            candidates_evaluated=candidates,
            pool_entropy=prior_h,
            n_questions=len(questions),
            questions=questions,
            top_recommendation=top,
            posterior_distribution=prior,
            runtime_ms=(time.time() - t0) * 1000,
        )

    def why_not(
        self,
        current_symptoms: List[str],
        candidate_remedies: List[str],
        rejected_remedy: str,
    ) -> DifferentialReport:
        """
        For a given rejected remedy, return the questions that would most
        strongly argue against it. Useful for explaining why a runner-up
        was not chosen.
        """
        # Symmetric to next_questions but emphasizes the rejected remedy
        report = self.next_questions(current_symptoms, candidate_remedies, n=8)
        # Re-rank by how much the question would penalize the rejected remedy
        for q in report.questions:
            penalty = 0.0
            label = q.remedy_breakdown.get(rejected_remedy, "absent")
            if label == "absent":
                penalty = q.info_gain * 0.3
            elif label == "grade-4":
                penalty = -q.info_gain * 0.5
            q.info_gain = max(0.0, q.info_gain + penalty)
        report.questions.sort(key=lambda x: x.info_gain, reverse=True)
        return report


# ── Quick function ─────────────────────────────────────────────────────────

def quick_differential(
    symptoms: List[str],
    candidates: List[str],
    n: int = 5,
) -> DifferentialReport:
    """Quick helper to get top differential questions."""
    return DiscriminantRubricSelector().next_questions(symptoms, candidates, n=n)
