"""
Confusion Matrix Differential (Module #125)

Computes the differential diagnostic confusion matrix: for each pair of
remedies, given a sample of historical cases, how often does repertorization
mistake remedy A for remedy B?

This module simulates the differential-diagnosis confusion from prior
prescription outcomes. For a new case, the confusion matrix helps the
practitioner know which other remedies are commonly confused with each
leading candidate, and the precision/recall per remedy at multiple score
thresholds.

Math:
    For each threshold t in [t_min, t_max]:
        predicted = [remedies with score > t]
        TP, FP, FN, TN computed vs. ground-truth remedy
        precision = TP / (TP + FP)
        recall = TP / (TP + FN)
        F1 = 2 * precision * recall / (precision + recall)
    For each pair (A, B): confusion_rate = #(prescribed A, true B) / #(true B)

Usage:
    from oorep.confusion_matrix_differential import ConfusionMatrixDifferential
    cmd = ConfusionMatrixDifferential()
    report = cmd.compute(historical_cases)
    print(report.confusion_pairs)  # sorted by confusion rate
"""

from __future__ import annotations

import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
    from ._v39_index import build_remedy_grade_index
except Exception:
    from homeopathic_repertory import HomeopathicRepertory
    from _v39_index import build_remedy_grade_index


@dataclass
class ConfusionPair:
    remedy_predicted: str
    remedy_actual: str
    confusion_rate: float
    n_cases: int
    rationale: str


@dataclass
class ThresholdMetrics:
    threshold: float
    precision: float
    recall: float
    f1: float
    support: int  # number of cases at this threshold


@dataclass
class ConfusionReport:
    n_historical_cases: int
    n_remedies: int
    top_confusion_pairs: List[ConfusionPair]
    per_remedy_metrics: Dict[str, List[ThresholdMetrics]]
    overall_precision: float
    overall_recall: float
    runtime_ms: float


class ConfusionMatrixDifferential:
    """
    Computes differential confusion between remedies from historical
    prescription outcomes.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        # Build remedy → {rubric_id: max grade}
        self._remedy_grades: Dict[str, Dict[int, int]] = build_remedy_grade_index(self.rep)

    def _compute_score(
        self,
        case_rubric_ids: List[int],
        remedy: str,
    ) -> float:
        """Compute the simple grade sum score for (case, remedy)."""
        return float(sum(self._remedy_grades[remedy].get(rid, 0) for rid in case_rubric_ids))

    def compute(
        self,
        historical_cases: List[Dict[str, Any]],
        thresholds: Optional[List[float]] = None,
        top_n_confusion: int = 10,
    ) -> ConfusionReport:
        """
        Parameters
        ----------
        historical_cases : list of dict
            Each case must have keys: "rubric_ids" (List[int]) and
            "true_remedy" (str). Optional: "predicted_remedy" (str).
        thresholds : list of float, optional
            Score thresholds for precision/recall curves. Default:
            [5, 10, 15, 20, 25, 30, 40, 50].
        top_n_confusion : int
            Number of top confusion pairs to return.

        Returns
        -------
        ConfusionReport
        """
        import time
        t0 = time.time()

        if not thresholds:
            thresholds = [5, 10, 15, 20, 25, 30, 40, 50]

        # 1. Confusion matrix: (predicted, actual) → count
        # For each case: take the top-scoring remedy as predicted
        confusion: Counter = Counter()
        n_correct = 0
        n_total = 0
        remedy_support: Counter = Counter()

        # 2. Per-remedy per-threshold TP/FP/FN
        per_remedy: Dict[str, Dict[float, Dict[str, int]]] = defaultdict(
            lambda: {t: {"tp": 0, "fp": 0, "fn": 0} for t in thresholds}
        )

        for case in historical_cases:
            rubric_ids = case.get("rubric_ids", [])
            true_remedy = case.get("true_remedy")
            if not rubric_ids or not true_remedy:
                continue

            # Score all remedies
            scores = {r: self._compute_score(rubric_ids, r) for r in self._remedy_grades}
            # Top remedy by score
            top_remedy = max(scores.items(), key=lambda x: x[1])[0]
            top_score = scores[top_remedy]

            confusion[(top_remedy, true_remedy)] += 1
            remedy_support[true_remedy] += 1
            n_total += 1
            if top_remedy == true_remedy:
                n_correct += 1

            # Per-threshold metrics
            for t in thresholds:
                predicted_remedies = {r for r, s in scores.items() if s >= t}
                if true_remedy in predicted_remedies:
                    per_remedy[true_remedy][t]["tp"] += 1
                else:
                    per_remedy[true_remedy][t]["fn"] += 1
                # FP: predicted but not actual
                for p in predicted_remedies:
                    if p != true_remedy:
                        per_remedy[p][t]["fp"] += 1

        # 3. Top confusion pairs: confusion[A, B] / support[B]
        confusion_pairs: List[ConfusionPair] = []
        for (predicted, actual), count in confusion.items():
            if predicted == actual:
                continue
            support = remedy_support[actual]
            if support < 2:
                continue
            rate = count / support
            rationale = (
                f"{predicted} mistaken for {actual} in {count} of {support} "
                f"{actual} cases ({rate:.0%})."
            )
            confusion_pairs.append(
                ConfusionPair(
                    remedy_predicted=predicted,
                    remedy_actual=actual,
                    confusion_rate=rate,
                    n_cases=count,
                    rationale=rationale,
                )
            )
        confusion_pairs.sort(key=lambda x: x.confusion_rate, reverse=True)

        # 4. Per-remedy threshold metrics
        per_remedy_metrics: Dict[str, List[ThresholdMetrics]] = {}
        for remedy, tdict in per_remedy.items():
            metrics_list: List[ThresholdMetrics] = []
            support = remedy_support[remedy]
            for t in thresholds:
                tp = tdict[t]["tp"]
                fp = tdict[t]["fp"]
                fn = tdict[t]["fn"]
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = (
                    2 * precision * recall / (precision + recall)
                    if (precision + recall) > 0 else 0.0
                )
                metrics_list.append(
                    ThresholdMetrics(
                        threshold=t,
                        precision=precision,
                        recall=recall,
                        f1=f1,
                        support=support,
                    )
                )
            per_remedy_metrics[remedy] = metrics_list

        # 5. Overall precision/recall at the median threshold
        median_threshold = thresholds[len(thresholds) // 2] if thresholds else 20
        all_tp = sum(tdict[median_threshold]["tp"] for tdict in per_remedy.values())
        all_fp = sum(tdict[median_threshold]["fp"] for tdict in per_remedy.values())
        all_fn = sum(tdict[median_threshold]["fn"] for tdict in per_remedy.values())
        overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0.0
        overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0.0

        return ConfusionReport(
            n_historical_cases=n_total,
            n_remedies=len(self._remedy_grades),
            top_confusion_pairs=confusion_pairs[:top_n_confusion],
            per_remedy_metrics=per_remedy_metrics,
            overall_precision=overall_precision,
            overall_recall=overall_recall,
            runtime_ms=(time.time() - t0) * 1000,
        )

    def predict_with_confusion(
        self,
        case_rubric_ids: List[int],
        confusion_report: ConfusionReport,
    ) -> List[Tuple[str, float, List[str]]]:
        """
        Score remedies for a new case, then adjust for known confusion
        patterns. Returns list of (remedy, adjusted_score, confused_with).
        """
        scores = {r: self._compute_score(case_rubric_ids, r) for r in self._remedy_grades}
        # Build confusion penalty: if A is often confused for B, penalize A
        # when B has a similar score
        confusion_penalty: Dict[str, float] = defaultdict(float)
        for pair in confusion_report.top_confusion_pairs:
            # If we predict A but B has the same score, reduce A
            confusion_penalty[pair.remedy_predicted] += pair.confusion_rate * 0.3

        adjusted: List[Tuple[str, float, List[str]]] = []
        for r, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:15]:
            adj = s - confusion_penalty.get(r, 0.0) * s
            confused = [
                p.remedy_actual
                for p in confusion_report.top_confusion_pairs
                if p.remedy_predicted == r
            ][:3]
            adjusted.append((r, adj, confused))
        return adjusted


# ── Quick function ─────────────────────────────────────────────────────────

def quick_confusion(historical_cases: List[Dict[str, Any]]) -> ConfusionReport:
    """Quick helper to compute a confusion report from historical cases."""
    return ConfusionMatrixDifferential().compute(historical_cases)
