"""
Meta-Analysis Engine — Pooled Effect Sizes Across Cases/Practitioners (Module #70)

Fixed-effect and random-effects meta-analysis for remedy outcomes.
Produces forest plots data and pooled statistics.

Dashboard visual: Forest plot (horizontal bars with CI for each study)

Usage:
    from oorep.meta_analysis_engine import MetaAnalysisEngine
    ma = MetaAnalysisEngine()
    result = ma.random_effects([
        {"study": "Clinic A", "n": 30, "positive": 22, "label": "PULS"},
        {"study": "Clinic B", "n": 25, "positive": 18, "label": "PULS"},
    ])
"""

import math
from typing import Any, Dict, List, Optional


class MetaAnalysisEngine:
    """Meta-analysis for homeopathic outcome data."""

    @staticmethod
    def _proportion_ci(positive: int, n: int, alpha: float = 0.05) -> List[float]:
        """Wilson score interval for proportion."""
        if n == 0:
            return [0, 0]
        p = positive / n
        z = 1.96  # 95% CI
        denom = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denom
        half_width = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
        return [max(0, centre - half_width), min(1, centre + half_width)]

    def fixed_effect(self, studies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fixed-effect meta-analysis (inverse variance weighting)."""
        if not studies:
            return {"error": "No studies provided"}

        # Convert to effect size (logit of proportion)
        effects = []
        for s in studies:
            pos = s.get("positive", 0)
            n = s.get("n", 0)
            if n == 0 or pos == 0 or pos == n:
                # Continuity correction
                pos = max(0.5, min(n - 0.5, pos + 0.5))
            p = pos / n
            # Logit
            es = math.log(p / (1 - p))
            # Variance of logit
            var = 1 / (n * p * (1 - p))
            effects.append({
                "study": s.get("study", ""),
                "effect_size": es,
                "variance": var,
                "weight": 1 / var,
                "n": n,
                "positive": pos,
                "ci": self._proportion_ci(int(pos), n),
            })

        # Weighted average
        total_weight = sum(e["weight"] for e in effects)
        pooled_es = sum(e["effect_size"] * e["weight"] for e in effects) / total_weight
        pooled_var = 1 / total_weight
        pooled_se = math.sqrt(pooled_var)

        # Convert back to proportion
        pooled_p = 1 / (1 + math.exp(-pooled_es))
        ci_low = 1 / (1 + math.exp(-(pooled_es - 1.96 * pooled_se)))
        ci_high = 1 / (1 + math.exp(-(pooled_es + 1.96 * pooled_se)))

        return {
            "model": "fixed_effect",
            "n_studies": len(studies),
            "pooled_proportion": round(pooled_p, 4),
            "ci_95": [round(ci_low, 4), round(ci_high, 4)],
            "pooled_effect_size": round(pooled_es, 4),
            "heterogeneity": None,  # Fixed effect assumes no heterogeneity
            "studies": effects,
        }

    def random_effects(self, studies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Random-effects meta-analysis (DerSimonian-Laird)."""
        if not studies:
            return {"error": "No studies provided"}

        effects = []
        for s in studies:
            pos = s.get("positive", 0)
            n = s.get("n", 0)
            if n == 0 or pos == 0 or pos == n:
                pos = max(0.5, min(n - 0.5, pos + 0.5))
            p = pos / n
            es = math.log(p / (1 - p))
            var = 1 / (n * p * (1 - p))
            effects.append({
                "study": s.get("study", ""),
                "effect_size": es,
                "variance": var,
                "n": n,
                "positive": pos,
            })

        k = len(effects)
        # Fixed-effect weights
        weights = [1 / e["variance"] for e in effects]
        total_w = sum(weights)
        fixed_mean = sum(e["effect_size"] * w for e, w in zip(effects, weights)) / total_w

        # Q statistic (heterogeneity)
        q = sum(w * (e["effect_size"] - fixed_mean) ** 2 for e, w in zip(effects, weights))

        # DerSimonian-Laird tau²
        if q <= k - 1:
            tau2 = 0
        else:
            tau2 = (q - (k - 1)) / (total_w - sum(w**2 for w in weights) / total_w)

        # Random-effects weights
        re_weights = [1 / (e["variance"] + tau2) for e in effects]
        total_re_w = sum(re_weights)
        pooled_es = sum(e["effect_size"] * w for e, w in zip(effects, re_weights)) / total_re_w
        pooled_var = 1 / total_re_w
        pooled_se = math.sqrt(pooled_var)

        pooled_p = 1 / (1 + math.exp(-pooled_es))
        ci_low = 1 / (1 + math.exp(-(pooled_es - 1.96 * pooled_se)))
        ci_high = 1 / (1 + math.exp(-(pooled_es + 1.96 * pooled_se)))

        # I² = (Q - df) / Q * 100%
        i2 = max(0, (q - (k - 1)) / q * 100) if q > 0 else 0

        return {
            "model": "random_effects",
            "n_studies": k,
            "pooled_proportion": round(pooled_p, 4),
            "ci_95": [round(ci_low, 4), round(ci_high, 4)],
            "pooled_effect_size": round(pooled_es, 4),
            "heterogeneity": {
                "Q": round(q, 2),
                "tau_squared": round(tau2, 4),
                "I_squared": round(i2, 1),
                "interpretation": "low" if i2 < 25 else ("moderate" if i2 < 50 else "high"),
            },
            "studies": [
                {**e, "weight": round(w, 2), "ci": self._proportion_ci(int(e["positive"]), e["n"])}
                for e, w in zip(effects, re_weights)
            ],
        }

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 70,
            "feature_name": "Meta-Analysis Engine",
            "version": "1.0",
            "supports": ["fixed_effect", "random_effects", "forest_plot_data", "heterogeneity"],
            "pure_python": True,
        }
