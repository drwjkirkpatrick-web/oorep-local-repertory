"""
Power Analysis — Sample Size & Effect Size Calculations (Module #71)

Calculate required sample sizes and achievable power for homeopathic studies.

Dashboard visual: Power curve (sample size vs. power) + minimum detectable effect table

Usage:
    from oorep.power_analysis import PowerAnalysis
    pa = PowerAnalysis()
    
    n = pa.sample_size_proportion(
        baseline_rate=0.3, expected_rate=0.6, alpha=0.05, power=0.8
    )
    
    achievable = pa.power_for_proportion(
        n=50, baseline_rate=0.3, expected_rate=0.6
    )
"""

import math
from typing import Any, Dict, List, Optional


class PowerAnalysis:
    """Sample size and power calculations for clinical studies."""

    @staticmethod
    def _normal_quantile(p: float) -> float:
        """Inverse normal CDF (probit approximation)."""
        if p <= 0.01:
            return -2.33
        if p >= 0.99:
            return 2.33
        # Beasley-Springer-Moro approximation
        c = [2.515517, 0.802853, 0.010328]
        d = [1.432788, 0.189269, 0.001308]
        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
            sign = -1
        else:
            t = math.sqrt(-2 * math.log(1 - p))
            sign = 1
        poly = c[0] + c[1]*t + c[2]*t**2
        denom = 1 + d[0]*t + d[1]*t**2 + d[2]*t**3
        return sign * (t - poly / denom)

    @staticmethod
    def _normal_cdf_approx(z: float) -> float:
        """Normal CDF approximation."""
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def sample_size_proportion(
        self,
        baseline_rate: float,
        expected_rate: float,
        alpha: float = 0.05,
        power: float = 0.8,
        two_sided: bool = True,
    ) -> Dict[str, Any]:
        """Sample size per group for comparing two proportions."""
        p1 = baseline_rate
        p2 = expected_rate
        p_avg = (p1 + p2) / 2

        z_alpha = self._normal_quantile(1 - alpha / (2 if two_sided else 1))
        z_beta = self._normal_quantile(power)

        numerator = (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) +
                     z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p1 - p2) ** 2

        n = math.ceil(numerator / denominator) if denominator > 0 else float("inf")

        return {
            "sample_size_per_group": n if n != float("inf") else None,
            "total_sample_size": n * 2 if n != float("inf") else None,
            "baseline_rate": baseline_rate,
            "expected_rate": expected_rate,
            "alpha": alpha,
            "power": power,
            "effect_size": round(abs(p2 - p1), 4),
        }

    def power_for_proportion(
        self,
        n: int,
        baseline_rate: float,
        expected_rate: float,
        alpha: float = 0.05,
        two_sided: bool = True,
    ) -> Dict[str, Any]:
        """Achievable power given sample size."""
        p1 = baseline_rate
        p2 = expected_rate
        p_avg = (p1 + p2) / 2

        z_alpha = self._normal_quantile(1 - alpha / (2 if two_sided else 1))

        se_null = math.sqrt(2 * p_avg * (1 - p_avg) / n)
        se_alt = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / n)

        z_score = (abs(p2 - p1) - z_alpha * se_null) / se_alt if se_alt > 0 else 0
        # Approximate power from z-score
        power = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

        return {
            "n_per_group": n,
            "achievable_power": round(min(1, power), 4),
            "baseline_rate": baseline_rate,
            "expected_rate": expected_rate,
            "alpha": alpha,
            "effect_size": round(abs(p2 - p1), 4),
        }

    def minimum_detectable_effect(
        self,
        n: int,
        baseline_rate: float,
        alpha: float = 0.05,
        power: float = 0.8,
        two_sided: bool = True,
    ) -> Dict[str, Any]:
        """Smallest effect detectable with given sample size."""
        z_alpha = self._normal_quantile(1 - alpha / (2 if two_sided else 1))
        z_beta = self._normal_quantile(power)
        p = baseline_rate

        se = math.sqrt(2 * p * (1 - p) / n)
        mde = (z_alpha + z_beta) * se

        return {
            "n_per_group": n,
            "minimum_detectable_difference": round(mde, 4),
            "minimum_detectable_rate": round(p + mde, 4),
            "baseline_rate": baseline_rate,
            "alpha": alpha,
            "power": power,
        }

    def power_curve(
        self,
        baseline_rate: float,
        expected_rate: float,
        alpha: float = 0.05,
        n_range: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate power curve data for plotting."""
        if n_range is None:
            n_range = list(range(10, 201, 10))

        curve = []
        for n in n_range:
            p = self.power_for_proportion(n, baseline_rate, expected_rate, alpha)
            curve.append({
                "n": n,
                "power": p["achievable_power"],
                "effect_size": p["effect_size"],
            })
        return curve

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 71,
            "feature_name": "Power Analysis",
            "version": "1.0",
            "supports": ["sample_size", "power_calculation", "minimum_detectable_effect", "power_curve"],
            "pure_python": True,
        }
