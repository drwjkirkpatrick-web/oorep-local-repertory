"""
Symptom Co-occurrence Lift Score (Module #128)

Computes association rule mining scores (lift, confidence, support) for
all symptom pairs in the repertory. Two rubrics with high lift appear
together much more often than chance — suggesting they form a natural
syndrome or "remedy signature".

Math:
    support(A) = P(A)
    support(A ∧ B) = P(A and B)
    confidence(A → B) = support(A ∧ B) / support(A)
    lift(A → B) = support(A ∧ B) / (support(A) * support(B))
    conviction(A → B) = (1 - support(B)) / (1 - confidence(A → B))

A lift > 1 indicates positive association; lift > 3 indicates strong
syndrome clustering.

Usage:
    from oorep.symptom_cooccurrence_lift import SymptomCooccurrenceLift
    lift = SymptomCooccurrenceLift()
    lift.fit(case_database)
    pairs = lift.top_pairs(min_lift=2.0, min_support=0.01)
"""

from __future__ import annotations

import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class AssociationPair:
    rubric_a: int
    rubric_b: int
    support: float         # P(A and B)
    confidence: float      # P(B | A)
    lift: float
    conviction: float
    co_occurrence_count: int


@dataclass
class LiftReport:
    n_cases: int
    n_pairs_above_threshold: int
    top_pairs: List[AssociationPair]
    runtime_ms: float


class SymptomCooccurrenceLift:
    """
    Association rule mining for symptom pairs.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        self.cases: List[Set[int]] = []

    def fit(self, case_database: List[List[int]]) -> "SymptomCooccurrenceLift":
        self.cases = [set(case) for case in case_database]
        return self

    def _support(self, rubric: int) -> float:
        n = len(self.cases)
        if n == 0:
            return 0.0
        return sum(1 for c in self.cases if rubric in c) / n

    def _pair_support(self, a: int, b: int) -> Tuple[float, int]:
        n = len(self.cases)
        if n == 0:
            return 0.0, 0
        count = sum(1 for c in self.cases if a in c and b in c)
        return count / n, count

    def pair_metrics(
        self,
        rubric_a: int,
        rubric_b: int,
    ) -> AssociationPair:
        """Compute lift, confidence, conviction for a single pair."""
        n = len(self.cases)
        support_a = self._support(rubric_a)
        support_b = self._support(rubric_b)
        support_ab, count = self._pair_support(rubric_a, rubric_b)
        confidence = support_ab / support_a if support_a > 0 else 0.0
        lift = support_ab / (support_a * support_b) if (support_a * support_b) > 0 else 0.0
        if confidence < 1.0 and support_b < 1.0:
            conviction = (1.0 - support_b) / (1.0 - confidence) if (1.0 - confidence) > 1e-9 else float("inf")
        else:
            conviction = float("inf") if confidence >= 1.0 else 0.0
        return AssociationPair(
            rubric_a=rubric_a,
            rubric_b=rubric_b,
            support=support_ab,
            confidence=confidence,
            lift=lift,
            conviction=conviction if conviction != float("inf") else 999.0,
            co_occurrence_count=count,
        )

    def top_pairs(
        self,
        min_support: float = 0.01,
        min_lift: float = 1.5,
        top_n: int = 50,
        rubric_ids: Optional[List[int]] = None,
    ) -> LiftReport:
        """
        Find the top symptom pairs by lift, subject to minimum support/lift.
        """
        import time
        t0 = time.time()
        n = len(self.cases)
        if n == 0:
            return LiftReport(0, 0, [], 0.0)

        # Default: take top 100 rubrics by frequency
        if rubric_ids is None:
            freq: Counter = Counter()
            for case in self.cases:
                for rid in case:
                    freq[rid] += 1
            rubric_ids = [rid for rid, c in freq.items() if c / n >= min_support]
            # Cap to top 100 by frequency to bound computation
            rubric_ids = [rid for rid, _ in freq.most_common(100) if freq[rid] / n >= min_support]

        # Pre-compute supports
        supports: Dict[int, float] = {r: self._support(r) for r in rubric_ids}

        # Enumerate all pairs (100^2/2 = 4950 max)
        pairs: List[AssociationPair] = []
        for i in range(len(rubric_ids)):
            for j in range(i + 1, len(rubric_ids)):
                a, b = rubric_ids[i], rubric_ids[j]
                support_ab, count = self._pair_support(a, b)
                if support_ab < min_support:
                    continue
                sa, sb = supports[a], supports[b]
                if sa * sb <= 0:
                    continue
                lift = support_ab / (sa * sb)
                if lift < min_lift:
                    continue
                confidence = support_ab / sa if sa > 0 else 0.0
                if confidence < 1.0 and sb < 1.0:
                    conviction = (1.0 - sb) / (1.0 - confidence) if (1.0 - confidence) > 1e-9 else 999.0
                else:
                    conviction = 999.0
                pairs.append(
                    AssociationPair(
                        rubric_a=a,
                        rubric_b=b,
                        support=support_ab,
                        confidence=confidence,
                        lift=lift,
                        conviction=conviction,
                        co_occurrence_count=count,
                    )
                )

        # Sort by lift descending
        pairs.sort(key=lambda x: x.lift, reverse=True)

        return LiftReport(
            n_cases=n,
            n_pairs_above_threshold=len(pairs),
            top_pairs=pairs[:top_n],
            runtime_ms=(time.time() - t0) * 1000,
        )

    def suggest_syndrome(
        self,
        observed_rubric_ids: List[int],
        min_lift: float = 2.0,
        top_n: int = 10,
    ) -> List[AssociationPair]:
        """
        Given an observed set of rubrics, return the rubric pairs from
        the observed set with the highest lift (syndrome candidates).
        """
        # Pre-compute all pairs from the observed set
        pairs: List[AssociationPair] = []
        for i in range(len(observed_rubric_ids)):
            for j in range(i + 1, len(observed_rubric_ids)):
                a, b = observed_rubric_ids[i], observed_rubric_ids[j]
                pair = self.pair_metrics(a, b)
                if pair.lift >= min_lift:
                    pairs.append(pair)
        pairs.sort(key=lambda x: x.lift, reverse=True)
        return pairs[:top_n]


# ── Quick function ─────────────────────────────────────────────────────────

def quick_lift(
    case_database: List[List[int]],
    min_lift: float = 1.5,
    min_support: float = 0.01,
) -> LiftReport:
    """Quick helper: compute top symptom co-occurrence lift pairs."""
    sc = SymptomCooccurrenceLift()
    sc.fit(case_database)
    return sc.top_pairs(min_lift=min_lift, min_support=min_support)
