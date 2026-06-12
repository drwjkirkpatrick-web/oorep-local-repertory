"""
K-Nearest Proven Cases (Module #126)

Finds the k historical cases most similar to the current case, weighted
by their recorded outcomes. If a similar case was successfully prescribed
remedy X with strong outcome, that remedy is more likely to be a good
fit for the current case.

Math:
    For each historical case, compute a similarity score to the current
    case using:
        - Jaccard similarity on rubric id sets
        - TF-IDF cosine similarity on symptom texts (optional)
    Weight by outcome: similarity * (1 + outcome_score)
    Return top-k most similar cases with their prescribed remedies and
    outcome metadata.

Usage:
    from oorep.k_nearest_proven_cases import KNearestProvenCases
    knn = KNearestProvenCases()
    knn.fit(historical_cases)
    neighbors = knn.query(current_case_rubric_ids=[101, 102, 103], k=5)
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class HistoricalCase:
    case_id: str
    rubric_ids: List[int]
    prescribed_remedy: str
    outcome_score: float  # 0.0 to 1.0 (1.0 = full resolution)
    followup_notes: str = ""
    patient_id: str = ""
    date: str = ""


@dataclass
class Neighbor:
    case_id: str
    similarity: float
    prescribed_remedy: str
    outcome_score: float
    shared_rubrics: List[int]
    followup_notes: str
    weighted_vote: float


@dataclass
class KNNResult:
    k: int
    n_historical: int
    neighbors: List[Neighbor]
    remedy_votes: Dict[str, float]  # remedy -> total weighted vote
    top_recommendation: Optional[str]
    confidence: float
    runtime_ms: float


class KNearestProvenCases:
    """
    K-nearest-neighbors over past successful cases, with outcome-weighted
    voting.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        self.cases: List[HistoricalCase] = []

    def fit(self, historical_cases: List[HistoricalCase]) -> "KNearestProvenCases":
        self.cases = list(historical_cases)
        return self

    @staticmethod
    def _jaccard(a: List[int], b: List[int]) -> float:
        sa, sb = set(a), set(b)
        if not sa and not sb:
            return 0.0
        intersection = sa & sb
        union = sa | sb
        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def _weighted_jaccard(a: List[int], b: List[int], grade_lookup) -> float:
        """Weighted Jaccard: sum of min(grade_a, grade_b) / sum of max."""
        grades_a = {rid: grade_lookup(rid) for rid in a}
        grades_b = {rid: grade_lookup(rid) for rid in b}
        all_rubrics = set(grades_a) | set(grades_b)
        num = sum(min(grades_a.get(r, 0), grades_b.get(r, 0)) for r in all_rubrics)
        den = sum(max(grades_a.get(r, 0), grades_b.get(r, 0)) for r in all_rubrics)
        return num / den if den > 0 else 0.0

    def query(
        self,
        current_case_rubric_ids: List[int],
        k: int = 5,
        outcome_weight: float = 1.0,
    ) -> KNNResult:
        """
        Find the k nearest historical cases.
        """
        import time
        t0 = time.time()
        n = len(self.cases)
        similarities: List[Tuple[float, HistoricalCase, List[int]]] = []
        for case in self.cases:
            sim = self._jaccard(current_case_rubric_ids, case.rubric_ids)
            shared = list(set(current_case_rubric_ids) & set(case.rubric_ids))
            similarities.append((sim, case, shared))

        # Sort by similarity, then outcome
        similarities.sort(key=lambda x: (x[0], x[1].outcome_score), reverse=True)
        top = similarities[:k]

        neighbors: List[Neighbor] = []
        remedy_votes: Dict[str, float] = defaultdict(float)
        for sim, case, shared in top:
            # Weighted vote: similarity * (1 + outcome_weight * outcome_score)
            vote = sim * (1.0 + outcome_weight * case.outcome_score)
            remedy_votes[case.prescribed_remedy] += vote
            neighbors.append(
                Neighbor(
                    case_id=case.case_id,
                    similarity=sim,
                    prescribed_remedy=case.prescribed_remedy,
                    outcome_score=case.outcome_score,
                    shared_rubrics=shared,
                    followup_notes=case.followup_notes,
                    weighted_vote=vote,
                )
            )

        # Top recommendation
        if remedy_votes:
            top_remedy = max(remedy_votes.items(), key=lambda x: x[1])[0]
            total_votes = sum(remedy_votes.values())
            confidence = remedy_votes[top_remedy] / total_votes if total_votes > 0 else 0.0
        else:
            top_remedy = None
            confidence = 0.0

        return KNNResult(
            k=k,
            n_historical=n,
            neighbors=neighbors,
            remedy_votes=dict(remedy_votes),
            top_recommendation=top_remedy,
            confidence=confidence,
            runtime_ms=(time.time() - t0) * 1000,
        )

    def add_case(self, case: HistoricalCase) -> None:
        self.cases.append(case)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_knn(
    current_rubric_ids: List[int],
    historical_cases: List[HistoricalCase],
    k: int = 5,
) -> KNNResult:
    """Quick helper: query k nearest neighbors from historical cases."""
    knn = KNearestProvenCases()
    knn.fit(historical_cases)
    return knn.query(current_rubric_ids, k=k)
