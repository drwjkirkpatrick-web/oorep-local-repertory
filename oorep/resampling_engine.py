"""
Resampling Engine — Bootstrap, Permutation, Cross-Validation (Module #73)

Robustness testing for remedy predictions and outcome models.

Dashboard visual: Bootstrap distribution histogram + CV fold comparison

Usage:
    from oorep.resampling_engine import ResamplingEngine
    re = ResamplingEngine()
    
    # Bootstrap CI on remedy score
    ci = re.bootstrap_ci([25.3, 22.1, 28.0, 24.5, 26.2], statistic="mean")
    
    # Permutation test: is PULS better than random?
    p = re.permutation_test(
        outcomes_a=["cured", "improved", "cured"],
        outcomes_b=["unchanged", "worsened", "unchanged"],
    )
    
    # K-fold cross-validation
    cv = re.cross_validation(
        data=[...], model_fn=predict_fn, k=5
    )
"""

import math
import random
from typing import Any, Callable, Dict, List, Optional


class ResamplingEngine:
    """Resampling-based statistical validation."""

    @staticmethod
    def bootstrap_ci(
        data: List[float],
        statistic: str = "mean",
        n_iterations: int = 1000,
        ci: float = 0.95,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Bootstrap confidence interval for a statistic."""
        if not data:
            return {"error": "Empty data"}
        if seed is not None:
            random.seed(seed)

        n = len(data)
        stats = []
        for _ in range(n_iterations):
            sample = [random.choice(data) for _ in range(n)]
            if statistic == "mean":
                stats.append(sum(sample) / len(sample))
            elif statistic == "median":
                s = sorted(sample)
                stats.append(s[len(s) // 2] if len(s) % 2 else (s[len(s)//2 - 1] + s[len(s)//2]) / 2)
            else:
                stats.append(sum(sample) / len(sample))

        stats.sort()
        lower_idx = int((1 - ci) / 2 * n_iterations)
        upper_idx = int((1 + ci) / 2 * n_iterations)

        return {
            "statistic": statistic,
            "n_iterations": n_iterations,
            "point_estimate": sum(data) / len(data) if statistic == "mean" else sorted(data)[len(data) // 2],
            "ci_lower": round(stats[lower_idx], 4),
            "ci_upper": round(stats[upper_idx], 4),
            "std_error": round(
                math.sqrt(sum((s - sum(stats)/len(stats))**2 for s in stats) / len(stats)), 4
            ),
            "distribution": stats,
        }

    @staticmethod
    def permutation_test(
        outcomes_a: List[Any],
        outcomes_b: List[Any],
        n_iterations: int = 1000,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Permutation test for difference in outcome rates."""
        if not outcomes_a or not outcomes_b:
            return {"error": "Empty groups"}
        if seed is not None:
            random.seed(seed)

        # Positive outcomes
        positive = {"cured", "improved"}
        pa = sum(1 for o in outcomes_a if str(o).lower() in positive) / len(outcomes_a)
        pb = sum(1 for o in outcomes_b if str(o).lower() in positive) / len(outcomes_b)
        observed_diff = abs(pa - pb)

        combined = list(outcomes_a) + list(outcomes_b)
        n_a = len(outcomes_a)
        count_extreme = 0

        for _ in range(n_iterations):
            random.shuffle(combined)
            new_a = combined[:n_a]
            new_b = combined[n_a:]
            p_new_a = sum(1 for o in new_a if str(o).lower() in positive) / len(new_a)
            p_new_b = sum(1 for o in new_b if str(o).lower() in positive) / len(new_b)
            if abs(p_new_a - p_new_b) >= observed_diff:
                count_extreme += 1

        p_value = count_extreme / n_iterations

        return {
            "observed_difference": round(observed_diff, 4),
            "p_value": round(p_value, 4),
            "n_iterations": n_iterations,
            "significant": p_value < 0.05,
            "interpretation": "Significant difference" if p_value < 0.05 else "No significant difference",
        }

    @staticmethod
    def cross_validation(
        data: List[Any],
        model_fn: Callable[[List[Any], List[Any]], Dict[str, Any]],
        k: int = 5,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        K-fold cross-validation.
        model_fn(train_data, test_data) -> {"score": float}
        """
        if not data or k <= 1:
            return {"error": "Invalid data or k"}
        if seed is not None:
            random.seed(seed)

        shuffled = list(data)
        random.shuffle(shuffled)
        fold_size = len(shuffled) // k
        scores = []

        for i in range(k):
            start = i * fold_size
            end = start + fold_size if i < k - 1 else len(shuffled)
            test = shuffled[start:end]
            train = shuffled[:start] + shuffled[end:]
            result = model_fn(train, test)
            scores.append(result.get("score", 0))

        return {
            "k": k,
            "fold_scores": [round(s, 4) for s in scores],
            "mean_score": round(sum(scores) / len(scores), 4),
            "std_score": round(
                math.sqrt(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)), 4
            ) if scores else 0,
        }

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 73,
            "feature_name": "Resampling Engine",
            "version": "1.0",
            "supports": ["bootstrap_ci", "permutation_test", "cross_validation"],
            "pure_python": True,
        }
