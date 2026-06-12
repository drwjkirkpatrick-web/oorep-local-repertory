"""
Adaptive Symptom Sequencer (Module #123)

Dynamically orders follow-up questions based on the current Bayesian posterior
over remedies. The next question is chosen to maximize expected information
gain given the running posterior, and the sequence is updated after each
answer is recorded.

This is the conversational case-taking version of the differential question
engine: it models the case-taking interaction as a sequential decision
process (a "20-questions" style algorithm for homeopathy).

Workflow:
    1. Practitioner records initial chief complaint and modalities.
    2. The sequencer computes P(remedy | current symptoms).
    3. The sequencer suggests the highest-IG question for the practitioner.
    4. The practitioner records the answer (grade or absent).
    5. Repeat until posterior concentration > threshold or budget exhausted.

Usage:
    from oorep.adaptive_symptom_sequencer import AdaptiveSymptomSequencer
    seq = AdaptiveSymptomSequencer()
    seq.observe(symptom="fear of death", grade=3)
    next_q = seq.next_question()
    # Returns the next question that will maximally reduce uncertainty
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
    from .discriminant_rubric_selector import DiscriminantRubricSelector
    from ._v39_index import build_remedy_grade_index
except Exception:
    from homeopathic_repertory import HomeopathicRepertory
    from discriminant_rubric_selector import DiscriminantRubricSelector
    from _v39_index import build_remedy_grade_index


@dataclass
class Observation:
    """A single observed symptom with a grade (0-4, 0=absent)."""
    rubric_id: int
    rubric_text: str
    grade: int  # 0=absent, 1, 2, 3, 4=bold


@dataclass
class NextQuestion:
    rubric_id: int
    rubric_text: str
    chapter: str
    expected_info_gain: float
    rationale: str
    running_posterior: Dict[str, float]


@dataclass
class SequencerState:
    n_observations: int
    n_distinct_remedies_with_mass: int
    top_remedy: Optional[str]
    top_remedy_mass: float
    posterior_entropy: float
    sufficiency: float
    observations: List[Observation]


class AdaptiveSymptomSequencer:
    """
    Sequential Bayesian case-taking assistant.
    """

    def __init__(
        self,
        candidate_pool: Optional[List[str]] = None,
        repertory: Optional[HomeopathicRepertory] = None,
    ):
        self.rep = repertory or HomeopathicRepertory()
        self.observations: List[Observation] = []
        self._remedy_grades: Dict[str, Dict[int, int]] = build_remedy_grade_index(self.rep)
        # Default candidate pool: top 30 remedies
        if candidate_pool is None:
            sorted_pool = sorted(
                self._remedy_grades.items(),
                key=lambda x: len(x[1]),
                reverse=True,
            )
            self.candidate_pool = [r for r, _ in sorted_pool[:30]]
        else:
            self.candidate_pool = list(candidate_pool)

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

    def _symptom_to_rubric_ids(self, symptom: str) -> List[int]:
        symptom_lc = symptom.lower().strip()
        rubric_ids: List[int] = []
        for rubric_id, rubric in getattr(self.rep, "rubrics", {}).items():
            fullpath = (rubric.get("fullpath") or rubric.get("path") or "").lower()
            if symptom_lc and (symptom_lc in fullpath or fullpath in symptom_lc):
                rubric_ids.append(rubric_id)
        return rubric_ids

    def _posterior(self) -> Dict[str, float]:
        """Compute the current posterior P(remedy | all observations)."""
        scores: Dict[str, float] = {r: 0.0 for r in self.candidate_pool}
        for obs in self.observations:
            for remedy in self.candidate_pool:
                # The actual grade in the repertory
                actual_grade = self._remedy_grades[remedy].get(obs.rubric_id, 0)
                if obs.grade == 0:
                    # Patient says "absent" — penalize remedies that have a high grade here
                    if actual_grade >= 3:
                        scores[remedy] -= math.log(1 + actual_grade) * 0.8
                else:
                    # Patient says present at grade g — boost remedies that also have a high grade
                    if actual_grade > 0:
                        scores[remedy] += math.log(1 + actual_grade)
        # Convert to probabilities
        max_s = max(scores.values()) if scores else 0
        exp_s = {r: math.exp(s - max_s) for r, s in scores.items()}
        return self._normalize(exp_s)

    def observe(self, symptom: str = "", grade: int = 0, rubric_id: Optional[int] = None,
                rubric_text: str = "") -> Observation:
        """
        Record a patient observation. Returns the Observation object.

        If `rubric_id` is not given, attempts to look up the rubric id from
        the symptom string. `grade` is 0 (absent), 1, 2, 3, or 4.
        """
        if rubric_id is None:
            ids = self._symptom_to_rubric_ids(symptom)
            if not ids:
                raise ValueError(f"Could not find rubric for symptom: {symptom!r}")
            rubric_id = ids[0]
        if not rubric_text:
            rubric = getattr(self.rep, "rubrics", {}).get(rubric_id, {})
            rubric_text = (
                rubric.get("fullpath")
                or rubric.get("path")
                or symptom
                or f"Rubric {rubric_id}"
            )
        obs = Observation(
            rubric_id=rubric_id,
            rubric_text=rubric_text,
            grade=int(grade),
        )
        self.observations.append(obs)
        return obs

    def next_question(self, n_candidates: int = 1) -> Optional[NextQuestion]:
        """
        Return the next question (or top n candidates) that maximally
        reduces uncertainty in the current posterior.

        Returns None if the candidate pool has effectively collapsed
        (entropy < 0.5 bits).
        """
        post = self._posterior()
        post_h = self._shannon_entropy(post)
        if post_h < 0.5:
            # Posterior is already concentrated; no need for more questions
            return None

        # Score all candidate rubrics by information gain
        observed_ids = {o.rubric_id for o in self.observations}
        scored: List[Tuple[float, int, str, str]] = []
        for remedy in self.candidate_pool:
            for rubric_id, grade in self._remedy_grades[remedy].items():
                if rubric_id in observed_ids:
                    continue
                # Compute expected IG for this rubric
                ig, breakdown = self._ig_for_rubric(rubric_id, post)
                if ig > 0:
                    rubric = getattr(self.rep, "rubrics", {}).get(rubric_id, {})
                    chapter = rubric.get("chapter", "Unknown")
                    text = rubric.get("fullpath") or rubric.get("path") or f"Rubric {rubric_id}"
                    scored.append((ig, rubric_id, text, chapter))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return None

        # Take the top n unique rubrics
        top = scored[0]
        ig, rubric_id, text, chapter = top
        return NextQuestion(
            rubric_id=rubric_id,
            rubric_text=text,
            chapter=chapter,
            expected_info_gain=ig,
            rationale=f"Information gain: {ig:.2f} bits. Splits current top remedies.",
            running_posterior=post,
        )

    def _ig_for_rubric(
        self,
        rubric_id: int,
        prior: Dict[str, float],
    ) -> Tuple[float, Dict[str, int]]:
        """Expected IG for asking about this rubric given the current posterior."""
        answer_options = ["absent", "grade-1", "grade-2", "grade-3", "grade-4"]
        grades = {r: self._remedy_grades[r].get(rubric_id, 0) for r in self.candidate_pool}

        expected_h = 0.0
        for ans in answer_options:
            likelihoods = {}
            for r in self.candidate_pool:
                g = grades[r]
                if ans == "absent":
                    likelihoods[r] = 0.6 if g == 0 else 0.05
                else:
                    target = int(ans.split("-")[1])
                    likelihoods[r] = 0.8 if g == target else 0.05
            posteriors = {r: likelihoods[r] * prior.get(r, 1e-9) for r in self.candidate_pool}
            posteriors = self._normalize(posteriors)
            p_ans = sum(prior.get(r, 0) * likelihoods[r] for r in self.candidate_pool)
            if p_ans > 0:
                expected_h += p_ans * self._shannon_entropy(posteriors)
        prior_h = self._shannon_entropy(prior)
        return max(0.0, prior_h - expected_h), grades

    def state(self) -> SequencerState:
        """Snapshot the current sequencer state."""
        post = self._posterior()
        top_remedy, top_mass = (None, 0.0)
        if post:
            top_remedy = max(post.items(), key=lambda x: x[1])[0]
            top_mass = post[top_remedy]
        n_distinct = sum(1 for p in post.values() if p > 0.01)
        # Sufficiency: 1 - normalized entropy
        max_h = math.log2(max(1, len(post)))
        post_h = self._shannon_entropy(post)
        sufficiency = 1.0 - (post_h / max_h) if max_h > 0 else 1.0
        return SequencerState(
            n_observations=len(self.observations),
            n_distinct_remedies_with_mass=n_distinct,
            top_remedy=top_remedy,
            top_remedy_mass=top_mass,
            posterior_entropy=post_h,
            sufficiency=sufficiency,
            observations=list(self.observations),
        )

    def reset(self) -> None:
        self.observations = []


# ── Quick function ─────────────────────────────────────────────────────────

def quick_sequence(initial_symptoms: Dict[str, int], n_questions: int = 5) -> List[NextQuestion]:
    """Quick helper: start a sequencer with initial symptoms and get N questions."""
    seq = AdaptiveSymptomSequencer()
    for symptom, grade in initial_symptoms.items():
        try:
            seq.observe(symptom=symptom, grade=grade)
        except ValueError:
            continue
    questions: List[NextQuestion] = []
    for _ in range(n_questions):
        q = seq.next_question()
        if q is None:
            break
        questions.append(q)
        # Don't actually record the answer — just preview the sequence
    return questions
