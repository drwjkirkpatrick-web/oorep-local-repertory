"""
Inter-Rater Reliability — Cohen's Kappa, Fleiss' Kappa, ICC (Module #69)

Measures agreement between practitioners or between practitioner and system.

Dashboard visual: Agreement heatmap + kappa interpretation table

Usage:
    from oorep.inter_rater_reliability import InterRaterReliability
    irr = InterRaterReliability()

    # Two practitioners
    kappa = irr.cohens_kappa(
        rater_a=["PULS", "ARS", "PULS", "NAT_M"],
        rater_b=["PULS", "PULS", "PULS", "NAT_M"],
    )

    # Multiple practitioners
    fleiss = irr.fleiss_kappa([
        ["PULS", "ARS", "PULS"],
        ["PULS", "PULS", "PULS"],
        ["ARS", "ARS", "PULS"],
    ])
"""

import math
from typing import Any, Dict, List, Optional
from collections import Counter


class InterRaterReliability:
    """Agreement statistics for remedy selection and rubric grading."""

    @staticmethod
    def cohens_kappa(rater_a: List[str], rater_b: List[str]) -> Dict[str, Any]:
        """Cohen's kappa for two raters."""
        if len(rater_a) != len(rater_b) or len(rater_a) == 0:
            return {"error": "Mismatched or empty ratings", "kappa": None}

        n = len(rater_a)
        # Observed agreement
        agreements = sum(1 for a, b in zip(rater_a, rater_b) if a == b)
        po = agreements / n

        # Expected agreement
        categories = set(rater_a) | set(rater_b)
        pa_counts = Counter(rater_a)
        pb_counts = Counter(rater_b)
        pe = sum((pa_counts.get(c, 0) / n) * (pb_counts.get(c, 0) / n) for c in categories)

        if pe == 1:
            kappa = 1.0 if po == 1 else 0.0
        else:
            kappa = (po - pe) / (1 - pe)

        return {
            "n_cases": n,
            "observed_agreement": round(po, 4),
            "expected_agreement": round(pe, 4),
            "kappa": round(kappa, 4),
            "agreements": agreements,
            "interpretation": InterRaterReliability._kappa_interpret(kappa),
        }

    @staticmethod
    def fleiss_kappa(ratings: List[List[str]]) -> Dict[str, Any]:
        """Fleiss' kappa for multiple raters on same items."""
        if not ratings or not ratings[0]:
            return {"error": "Empty ratings", "kappa": None}

        n = len(ratings[0])  # Number of items
        m = len(ratings)      # Number of raters

        categories = set()
        for r in ratings:
            categories.update(r)

        # Proportion of assignments to each category per item
        p: Dict[str, List[float]] = {c: [] for c in categories}
        for i in range(n):
            item_ratings = [r[i] for r in ratings]
            counts = Counter(item_ratings)
            for c in categories:
                p[c].append(counts.get(c, 0) / m)

        # P_hat: mean proportion of agreement
        p_hat = sum(sum(pi ** 2 for pi in p[c]) for c in categories) / n

        # P_e: expected agreement
        pe_hat = {c: sum(p[c]) / n for c in categories}
        pe = sum(pe_hat[c] ** 2 for c in categories)

        if pe == 1:
            kappa = 1.0
        else:
            kappa = (p_hat - pe) / (1 - pe)

        return {
            "n_items": n,
            "n_raters": m,
            "p_hat": round(p_hat, 4),
            "pe": round(pe, 4),
            "kappa": round(kappa, 4),
            "interpretation": InterRaterReliability._kappa_interpret(kappa),
        }

    @staticmethod
    def icc_consistency(ratings: List[List[float]]) -> Dict[str, Any]:
        """
        ICC(3,1) — Consistency between fixed raters.
        One-way random effects model (simplified).
        """
        if not ratings or not ratings[0]:
            return {"error": "Empty ratings", "icc": None}

        n = len(ratings[0])
        k = len(ratings)

        # Mean per item
        item_means = [sum(ratings[r][i] for r in range(k)) / k for i in range(n)]
        grand_mean = sum(item_means) / n

        # Between-item variance (MSB)
        ss_between = sum((m - grand_mean) ** 2 for m in item_means) * k
        msb = ss_between / (n - 1) if n > 1 else 0

        # Within-item variance (MSW)
        ss_within = sum(
            sum((ratings[r][i] - item_means[i]) ** 2 for r in range(k))
            for i in range(n)
        )
        msw = ss_within / (n * (k - 1)) if k > 1 else 0

        if msb + msw == 0:
            icc = 0
        else:
            icc = (msb - msw) / (msb + (k - 1) * msw)

        return {
            "n_items": n,
            "n_raters": k,
            "icc": round(max(0, icc), 4),
            "msb": round(msb, 4),
            "msw": round(msw, 4),
            "interpretation": "good" if icc > 0.75 else ("moderate" if icc > 0.5 else "poor"),
        }

    @staticmethod
    def _kappa_interpret(kappa: float) -> str:
        if kappa < 0:
            return "Poor (less than chance)"
        if kappa < 0.2:
            return "Slight agreement"
        if kappa < 0.4:
            return "Fair agreement"
        if kappa < 0.6:
            return "Moderate agreement"
        if kappa < 0.8:
            return "Substantial agreement"
        return "Almost perfect agreement"

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 69,
            "feature_name": "Inter-Rater Reliability",
            "version": "1.0",
            "supports": ["cohens_kappa", "fleiss_kappa", "icc_consistency"],
            "pure_python": True,
        }
