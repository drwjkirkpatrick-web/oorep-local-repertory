"""
Remedy Confidence Calibration (Module #130)

Calibrates the raw repertorization score into a true probability of
correct prescription. Uses Platt scaling and isotonic regression on
historical prescription outcomes.

The raw score is a sum of grades; it does NOT directly translate into
"probability this is the right remedy." Calibration fits a mapping:
    P(correct | score) = f(score)
using past cases where we know the actual outcome.

Math:
    Platt scaling: P(correct | x) = 1 / (1 + exp(A x + B))
        Fit A, B by maximum likelihood on (x, y) pairs from past cases.
    Isotonic regression: non-parametric, monotonic mapping fit via PAVA.
        Yields a calibrated probability for each score bucket.
    Reliability diagram: bin predictions, plot mean predicted vs.
        actual fraction correct. A perfectly calibrated model has all
        points on the diagonal.

Usage:
    from oorep.remedy_confidence_calibration import RemedyConfidenceCalibrator
    cal = RemedyConfidenceCalibrator()
    cal.fit(historical_cases)  # each = {"rubric_ids": [...], "true_remedy": "...", "score": 42, "correct": True/False}
    p = cal.predict(score=42, candidate_remedies=["Puls.", "Ars."])
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
class CalibrationPoint:
    score: float
    raw_confidence: float
    calibrated_probability: float
    was_correct: bool


@dataclass
class CalibrationReport:
    n_training_cases: int
    platt_a: float
    platt_b: float
    brier_score: float            # Lower is better
    log_loss: float               # Lower is better
    reliability_diagram: List[Tuple[float, float, int]]  # (bin_center, actual_freq, n)
    ece: float                    # Expected Calibration Error
    runtime_ms: float


@dataclass
class CalibratedPrediction:
    raw_score: float
    raw_rank: int
    platt_probability: float
    isotonic_probability: float
    ensemble_probability: float
    recommendation: str  # "high", "medium", "low"


class RemedyConfidenceCalibrator:
    """
    Maps raw repertorization scores to calibrated probabilities.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        self._platt_a: float = 1.0
        self._platt_b: float = 0.0
        self._isotonic: List[Tuple[float, float]] = []  # sorted (score, prob)
        self._fitted = False

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        e = math.exp(x)
        return e / (1.0 + e)

    def fit(self, training_cases: List[Dict[str, Any]]) -> "RemedyConfidenceCalibrator":
        """
        Fit Platt scaling and isotonic regression on training cases.

        Each case must have:
            - "score": float (the raw repertorization score)
            - "correct": bool (was this the right remedy?)
        """
        import time
        t0 = time.time()
        if not training_cases:
            self._fitted = True
            return self

        scores = [c["score"] for c in training_cases]
        labels = [1.0 if c.get("correct") else 0.0 for c in training_cases]

        # Platt scaling: fit A, B by gradient descent
        a, b = 1.0, 0.0
        lr = 0.01
        n = len(scores)
        for _ in range(500):
            grad_a = 0.0
            grad_b = 0.0
            for s, y in zip(scores, labels):
                z = a * s + b
                p = self._sigmoid(z)
                grad_a += (p - y) * s
                grad_b += (p - y)
            a -= lr * grad_a / n
            b -= lr * grad_b / n
        self._platt_a = a
        self._platt_b = b

        # Isotonic regression (PAVA) on binned scores
        # Bin scores into 20 buckets
        if scores:
            min_s, max_s = min(scores), max(scores)
            n_bins = 20
            bin_width = (max_s - min_s) / n_bins if max_s > min_s else 1.0
            bin_sums: Dict[int, List[float]] = defaultdict(list)
            for s, y in zip(scores, labels):
                bin_idx = int((s - min_s) / bin_width) if bin_width > 0 else 0
                bin_idx = min(n_bins - 1, max(0, bin_idx))
                bin_sums[bin_idx].append(y)
            bin_centers: List[float] = []
            bin_probs: List[float] = []
            for idx in sorted(bin_sums.keys()):
                vals = bin_sums[idx]
                bin_centers.append(min_s + (idx + 0.5) * bin_width)
                bin_probs.append(sum(vals) / len(vals))

            # PAVA (pool adjacent violators)
            self._isotonic = self._pava(bin_centers, bin_probs)
        else:
            self._isotonic = []

        self._fitted = True
        return self

    @staticmethod
    def _pava(xs: List[float], ys: List[float]) -> List[Tuple[float, float]]:
        """
        Pool-Adjacent-Violators Algorithm for isotonic regression.
        Returns a list of (x, y) points forming a monotonic increasing curve.
        """
        if not xs:
            return []
        pairs: List[Tuple[List[float], List[float]]] = [([xs[0]], [ys[0]])]
        for i in range(1, len(xs)):
            x, y = xs[i], ys[i]
            pairs.append(([x], [y]))
            # Pool backwards while constraint is violated
            while len(pairs) >= 2:
                prev_xs, prev_ys = pairs[-2]
                cur_xs, cur_ys = pairs[-1]
                prev_mean = sum(prev_ys) / len(prev_ys)
                cur_mean = sum(cur_ys) / len(cur_ys)
                if prev_mean <= cur_mean:
                    break
                # Pool
                pairs.pop()
                pairs[-1] = (prev_xs + cur_xs, prev_ys + cur_ys)
        # Flatten
        result: List[Tuple[float, float]] = []
        for xs_block, ys_block in pairs:
            mean_x = sum(xs_block) / len(xs_block)
            mean_y = sum(ys_block) / len(ys_block)
            result.append((mean_x, mean_y))
        return sorted(result, key=lambda t: t[0])

    def _isotonic_predict(self, score: float) -> float:
        """Linear interpolation on the isotonic curve."""
        if not self._isotonic:
            return 0.5
        if score <= self._isotonic[0][0]:
            return self._isotonic[0][1]
        if score >= self._isotonic[-1][0]:
            return self._isotonic[-1][1]
        for i in range(1, len(self._isotonic)):
            x0, y0 = self._isotonic[i - 1]
            x1, y1 = self._isotonic[i]
            if x0 <= score <= x1:
                t = (score - x0) / (x1 - x0) if x1 > x0 else 0.0
                return y0 + t * (y1 - y0)
        return 0.5

    def predict(
        self,
        score: float,
        candidate_remedies: Optional[List[str]] = None,
    ) -> CalibratedPrediction:
        """
        Predict the calibrated probability of correct prescription.
        """
        z = self._platt_a * score + self._platt_b
        platt_p = self._sigmoid(z)
        iso_p = self._isotonic_predict(score)
        ensemble = 0.5 * platt_p + 0.5 * iso_p

        if ensemble >= 0.8:
            rec = "high"
        elif ensemble >= 0.5:
            rec = "medium"
        else:
            rec = "low"

        return CalibratedPrediction(
            raw_score=score,
            raw_rank=0,  # caller can fill in
            platt_probability=platt_p,
            isotonic_probability=iso_p,
            ensemble_probability=ensemble,
            recommendation=rec,
        )

    def evaluate(
        self,
        test_cases: List[Dict[str, Any]],
        n_bins: int = 10,
    ) -> CalibrationReport:
        """
        Compute calibration metrics on test data.
        """
        import time
        t0 = time.time()
        if not test_cases:
            return CalibrationReport(
                n_training_cases=0, platt_a=self._platt_a, platt_b=self._platt_b,
                brier_score=0.0, log_loss=0.0, reliability_diagram=[], ece=0.0,
                runtime_ms=0.0,
            )

        scores = [c["score"] for c in test_cases]
        labels = [1.0 if c.get("correct") else 0.0 for c in test_cases]

        # Brier score
        brier = 0.0
        log_loss = 0.0
        preds: List[float] = []
        for s, y in zip(scores, labels):
            p = self.predict(s).ensemble_probability
            preds.append(p)
            brier += (p - y) ** 2
            p_clipped = max(1e-9, min(1 - 1e-9, p))
            log_loss -= y * math.log(p_clipped) + (1 - y) * math.log(1 - p_clipped)
        brier /= len(scores)
        log_loss /= len(scores)

        # Reliability diagram
        bin_edges = [
            i / n_bins for i in range(n_bins + 1)
        ]
        reliability: List[Tuple[float, float, int]] = []
        ece = 0.0
        for i in range(n_bins):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            bin_preds = [p for p, y in zip(preds, labels) if lo <= p < hi]
            bin_labels = [y for p, y in zip(preds, labels) if lo <= p < hi]
            if not bin_preds:
                continue
            mean_pred = sum(bin_preds) / len(bin_preds)
            mean_actual = sum(bin_labels) / len(bin_labels)
            n_in_bin = len(bin_preds)
            reliability.append((mean_pred, mean_actual, n_in_bin))
            ece += (n_in_bin / len(preds)) * abs(mean_pred - mean_actual)

        return CalibrationReport(
            n_training_cases=len(test_cases),
            platt_a=self._platt_a,
            platt_b=self._platt_b,
            brier_score=brier,
            log_loss=log_loss,
            reliability_diagram=reliability,
            ece=ece,
            runtime_ms=(time.time() - t0) * 1000,
        )


# ── Quick function ─────────────────────────────────────────────────────────

def quick_calibrate(
    training_cases: List[Dict[str, Any]],
    test_cases: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[RemedyConfidenceCalibrator, Optional[CalibrationReport]]:
    """Quick helper: fit a calibrator and optionally evaluate."""
    cal = RemedyConfidenceCalibrator()
    cal.fit(training_cases)
    if test_cases:
        report = cal.evaluate(test_cases)
        return cal, report
    return cal, None
