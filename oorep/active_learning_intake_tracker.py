"""
Active Learning Intake Tracker (Module #129)

Tracks which symptoms have been asked about and which have not, and ranks
the unasked symptoms by information gain. This is the "checklist" companion
to the Adaptive Symptom Sequencer: it ensures comprehensive case-taking
coverage while still prioritizing high-value questions.

Practical use:
    - During a long case-taking session, the practitioner might forget
      which body systems or modalities have been explored.
    - The tracker surfaces under-explored areas AND ranks the unasked
      symptoms by IG to maximize info per minute of interview time.

Math:
    Coverage = (# chapters explored) / (# total chapters)
    Redundancy = avg pairwise correlation of asked symptoms
    Unasked-IG-rank = expected info gain (from Module #121) × (1 - recency_decay)
    where recency_decay = exp(-Δt / half_life)

Usage:
    from oorep.active_learning_intake_tracker import ActiveLearningIntakeTracker
    tracker = ActiveLearningIntakeTracker()
    tracker.record(symptom="fear of death", rubric_id=101, chapter="Mind")
    next_q = tracker.suggest_next()
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
    from .discriminant_rubric_selector import DiscriminantRubricSelector
except Exception:
    from homeopathic_repertory import HomeopathicRepertory
    from discriminant_rubric_selector import DiscriminantRubricSelector


@dataclass
class AskedSymptom:
    rubric_id: int
    rubric_text: str
    chapter: str
    grade: int
    timestamp: float


@dataclass
class IntakeStatus:
    n_asked: int
    n_chapters_covered: int
    total_chapters: int
    coverage_fraction: float
    redundancy_score: float  # 0.0 to 1.0
    avg_info_gain_asked: float
    n_remaining_high_value: int  # # of unasked symptoms with IG > threshold
    time_elapsed_seconds: float
    pace_per_minute: float
    recommendation: str


@dataclass
class IntakeSuggestion:
    rubric_id: int
    rubric_text: str
    chapter: str
    info_gain: float
    reason: str
    coverage_boost: float  # how much this question would add to chapter coverage


class ActiveLearningIntakeTracker:
    """
    Tracks case-taking progress and suggests the next high-value question.
    """

    EXPECTED_CHAPTERS = [
        "Mind", "Generals", "Sleep", "Dreams", "Appetite", "Stomach",
        "Abdomen", "Rectum", "Stool", "Urine", "Sexual", "Respiration",
        "Cough", "Expectoration", "Chest", "Back", "Extremities", "Skin",
        "Fever", "Perspiration", "Head", "Eye", "Ear", "Nose", "Face",
        "Mouth", "Teeth", "Throat", "Neck",
    ]

    def __init__(
        self,
        candidate_remedies: Optional[List[str]] = None,
        repertory: Optional[HomeopathicRepertory] = None,
    ):
        self.rep = repertory or HomeopathicRepertory()
        self.selector = DiscriminantRubricSelector(self.rep)
        self.candidate_remedies = candidate_remedies or []
        self.history: List[AskedSymptom] = []
        self._start_time = time.time()

    def reset(self) -> None:
        self.history = []
        self._start_time = time.time()

    def set_candidates(self, candidates: List[str]) -> None:
        self.candidate_remedies = list(candidates)

    def record(
        self,
        rubric_id: int,
        rubric_text: str = "",
        chapter: str = "",
        grade: int = 0,
    ) -> AskedSymptom:
        """Record that a question about this rubric was asked."""
        if not rubric_text:
            rubric = getattr(self.rep, "rubrics", {}).get(rubric_id, {})
            rubric_text = (
                rubric.get("fullpath")
                or rubric.get("path")
                or f"Rubric {rubric_id}"
            )
        if not chapter:
            # Infer from text
            chapter = rubric_text.split(";")[0].strip().title() if ";" in rubric_text else "Other"
        symptom = AskedSymptom(
            rubric_id=rubric_id,
            rubric_text=rubric_text,
            chapter=chapter,
            grade=grade,
            timestamp=time.time(),
        )
        self.history.append(symptom)
        return symptom

    def _chapters_covered(self) -> Set[str]:
        return {h.chapter for h in self.history}

    def _redundancy_score(self) -> float:
        """
        Crude redundancy: fraction of asked symptoms that share a chapter
        with another asked symptom.
        """
        chapter_counts: Dict[str, int] = defaultdict(int)
        for h in self.history:
            chapter_counts[h.chapter] += 1
        if not chapter_counts:
            return 0.0
        # Rubrics in chapters with > 1 entry are potentially redundant
        redundant = sum(c - 1 for c in chapter_counts.values() if c > 1)
        return min(1.0, redundant / max(1, len(self.history)))

    def status(self) -> IntakeStatus:
        """Snapshot the current intake status."""
        chapters_covered = self._chapters_covered()
        n_chapters = len(chapters_covered)
        total = len(self.EXPECTED_CHAPTERS)
        coverage = n_chapters / total if total > 0 else 0.0
        redundancy = self._redundancy_score()
        time_elapsed = max(0.0, time.time() - self._start_time)
        pace = len(self.history) / max(1.0, time_elapsed / 60.0)

        if coverage < 0.3:
            recommendation = "Expand to more chapters before diving deep."
        elif redundancy > 0.5:
            recommendation = "High redundancy — explore new chapters."
        elif pace < 0.5:
            recommendation = "Pace is slow — consider a more focused question."
        else:
            recommendation = "Good intake progress. Continue with high-IG questions."

        # Avg IG asked: stub — would integrate with selector
        avg_ig = 0.0
        if self.candidate_remedies and self.history:
            rids = [h.rubric_id for h in self.history]
            # Reuse selector's per-rubric IG calculation
            prior = self.selector._compute_initial_posterior(
                [h.rubric_text for h in self.history],
                self.candidate_remedies,
            )
            total_ig = 0.0
            for rid in rids:
                ig, _, _ = self.selector._information_gain_for_rubric(
                    rid, self.candidate_remedies, prior
                )
                total_ig += ig
            avg_ig = total_ig / max(1, len(rids))

        # Count unasked high-value (placeholder logic)
        n_remaining = max(0, 30 - len(self.history))

        return IntakeStatus(
            n_asked=len(self.history),
            n_chapters_covered=n_chapters,
            total_chapters=total,
            coverage_fraction=coverage,
            redundancy_score=redundancy,
            avg_info_gain_asked=avg_ig,
            n_remaining_high_value=n_remaining,
            time_elapsed_seconds=time_elapsed,
            pace_per_minute=pace,
            recommendation=recommendation,
        )

    def suggest_next(self, top_n: int = 5) -> List[IntakeSuggestion]:
        """
        Suggest the next high-value question, factoring in chapter coverage
        and information gain.
        """
        if not self.candidate_remedies or len(self.candidate_remedies) < 2:
            return []
        observed_ids = {h.rubric_id for h in self.history}
        # Use the discriminant selector
        report = self.selector.next_questions(
            current_symptoms=[h.rubric_text for h in self.history],
            candidate_remedies=self.candidate_remedies,
            n=top_n * 3,  # over-fetch to filter
        )
        # Filter out already-asked
        suggestions: List[IntakeSuggestion] = []
        for q in report.questions:
            if q.rubric_id in observed_ids:
                continue
            # Coverage boost: would this question add a new chapter?
            chapter = q.chapter
            covered = self._chapters_covered()
            boost = 1.0 if chapter not in covered else 0.0
            reason = f"Info gain {q.info_gain:.2f} bits"
            if boost > 0:
                reason += f" + new chapter ({chapter})"
            suggestions.append(
                IntakeSuggestion(
                    rubric_id=q.rubric_id,
                    rubric_text=q.rubric_text,
                    chapter=chapter,
                    info_gain=q.info_gain,
                    reason=reason,
                    coverage_boost=boost,
                )
            )
            if len(suggestions) >= top_n:
                break
        # Re-rank by (info_gain + 0.5 * coverage_boost) descending
        suggestions.sort(key=lambda s: s.info_gain + 0.5 * s.coverage_boost, reverse=True)
        return suggestions


# ── Quick function ─────────────────────────────────────────────────────────

def quick_intake_suggestion(
    asked: List[Tuple[int, str, str]],
    candidates: List[str],
    n: int = 5,
) -> List[IntakeSuggestion]:
    """Quick helper: given a list of (rubric_id, text, chapter) and candidates, suggest next."""
    tracker = ActiveLearningIntakeTracker(candidate_remedies=candidates)
    for rid, text, chapter in asked:
        tracker.record(rid, rubric_text=text, chapter=chapter)
    return tracker.suggest_next(n)
