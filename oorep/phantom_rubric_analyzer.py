"""
Phantom Rubric Analyzer

A "phantom rubric" is one that appears to differentiate but actually returns
the same polycrest remedies over and over.  This module computes statistical
metrics (Gini coefficient, top-remedy concentration, entropy) to flag
differentiation-poor rubrics so the practitioner knows which rubrics add
little discriminative power to a case.

Usage:
    from oorep.phantom_rubric_analyzer import PhantomRubricAnalyzer
    analyzer = PhantomRubricAnalyzer()
    phantoms = analyzer.find_phantom_rubrics(top_n=20)
    # Returns rubrics with low differentiation sorted by Gini coefficient
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class PhantomRubricReport:
    rubric_id: int
    fullpath: str
    source: str
    total_remedies: int
    gini_coefficient: float      # 0=equal distribution (poor differentiation), 1=single remedy
    top_3_concentration: float   # % of total grade-sum held by top 3 remedies
    entropy_bits: float          # Higher = more differentiation
    herfindahl_index: float      # 0=perfect spread, 1=monopoly
    is_flagged: bool             # True if fails differentiation threshold
    top_remedies: List[Dict]     # Top 5 remedies with weights
    flag_reason: str


class PhantomRubricAnalyzer:
    """Analyze rubric differentiation quality — flag phantom rubrics."""

    # Threshold defaults — tune for your repertory
    GINI_FLAG = 0.60          # Gini >= 0.60 = highly concentrated (potentially phantom)
    TOP3_FLAG = 0.50          # Top 3 hold >= 50% of grade mass
    ENTROPY_LOW = 2.0         # Fewer than 2 bits of entropy
    HERFINDAHL_FLAG = 0.25    # Remedy dominance index

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()

    @staticmethod
    def _gini(values: List[float]) -> float:
        """Compute Gini coefficient on a list of positive weights.
        0 = perfectly equal distribution (every remedy equally represented).
        1 = all weight in a single remedy.
        """
        if not values or sum(values) == 0:
            return 0.0
        # Sort ascending; use standard formula
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        cumsum = 0.0
        for i, v in enumerate(sorted_vals, start=1):
            cumsum += (2 * i - n - 1) * v
        denominator = n * sum(sorted_vals)
        return abs(cumsum) / denominator if denominator else 0.0

    @staticmethod
    def _entropy(values: List[float]) -> float:
        """Shannon entropy in bits."""
        total = sum(values)
        if total == 0:
            return 0.0
        bits = 0.0
        for v in values:
            if v > 0:
                p = v / total
                bits -= p * math.log2(p)
        return round(bits, 3)

    @staticmethod
    def _herfindahl(values: List[float]) -> float:
        """Herfindahl-Hirschman index: sum of squared market shares."""
        total = sum(values)
        if total == 0:
            return 0.0
        return round(sum((v / total) ** 2 for v in values), 4)

    def analyze_rubric(self, rubric_id: int) -> Optional[PhantomRubricReport]:
        """Analyze a single rubric's differentiation quality."""
        remedies = self.rep.get_remedies_for_rubric(rubric_id)
        if not remedies:
            return None

        rubric = self.rep.get_rubric_by_id(rubric_id) or {}
        weights = [r["weight"] for r in remedies]
        total = sum(weights)
        if total == 0:
            return None

        gini = round(self._gini(weights), 4)
        top3_weight = sum(sorted(weights, reverse=True)[:3])
        top3_conc = round(top3_weight / total, 4)
        entropy = round(self._entropy(weights), 3)
        hhi = self._herfindahl(weights)

        # Flagging logic
        flags = []
        if gini >= self.GINI_FLAG:
            flags.append(f"Gini={gini} (very concentrated)")
        if top3_conc >= self.TOP3_FLAG:
            flags.append(f"Top-3 hold {top3_conc:.0%}")
        if entropy < self.ENTROPY_LOW:
            flags.append(f"Entropy={entropy} bits (low diversity)")
        if hhi >= self.HERFINDAHL_FLAG:
            flags.append(f"HHI={hhi} (high dominance)")

        is_flagged = len(flags) > 0
        flag_reason = "; ".join(flags) if flags else "Differentiation OK"

        top_remedies = [
            {"abbrev": r.get("abbrev", "?"), "name": r.get("name", r.get("abbrev", "?")), "weight": r.get("weight", 1)}
            for r in remedies[:5]
        ]

        return PhantomRubricReport(
            rubric_id=rubric_id,
            fullpath=rubric.get("fullpath", "?"),
            source=rubric.get("source", "?"),
            total_remedies=len(remedies),
            gini_coefficient=gini,
            top_3_concentration=top3_conc,
            entropy_bits=entropy,
            herfindahl_index=hhi,
            is_flagged=is_flagged,
            top_remedies=top_remedies,
            flag_reason=flag_reason,
        )

    def find_phantom_rubrics(self, top_n: int = 20) -> List[PhantomRubricReport]:
        """
        Scan all rubrics and return the worst-differentiated ones.
        Sorted by Gini descending (most concentrated / least useful first).
        """
        reports = []
        for rubric_id in self.rep.rubric_to_remedies:
            report = self.analyze_rubric(rubric_id)
            if report and report.is_flagged:
                reports.append(report)
        # Sort: highest Gini = most phantom-like
        reports.sort(key=lambda r: r.gini_coefficient, reverse=True)
        return reports[:top_n]

    def differentiation_summary(self) -> Dict:
        """Aggregate summary across the entire repertory."""
        total_rubrics = len(self.rep.rubric_to_remedies)
        flagged = 0
        gini_sum = 0.0
        entropy_sum = 0.0
        total_remedies_per_rubric = []

        for rubric_id in self.rep.rubric_to_remedies:
            report = self.analyze_rubric(rubric_id)
            if report:
                gini_sum += report.gini_coefficient
                entropy_sum += report.entropy_bits
                total_remedies_per_rubric.append(report.total_remedies)
                if report.is_flagged:
                    flagged += 1

        avg_gini = round(gini_sum / total_rubrics, 4) if total_rubrics else 0
        avg_entropy = round(entropy_sum / total_rubrics, 3) if total_rubrics else 0
        avg_remedies = round(sum(total_remedies_per_rubric) / len(total_remedies_per_rubric), 1) if total_remedies_per_rubric else 0

        return {
            "total_rubrics_analyzed": total_rubrics,
            "flagged_phantom_rubrics": flagged,
            "phantom_percentage": round(100 * flagged / total_rubrics, 1) if total_rubrics else 0,
            "avg_gini_coefficient": avg_gini,
            "avg_entropy_bits": avg_entropy,
            "avg_remedies_per_rubric": avg_remedies,
            "median_remedies_per_rubric": sorted(total_remedies_per_rubric)[len(total_remedies_per_rubric) // 2] if total_remedies_per_rubric else 0,
        }


def quick_phantoms(top_n: int = 10) -> List[Dict]:
    """Convenience: return top phantom rubrics as dicts."""
    analyzer = PhantomRubricAnalyzer()
    return [asdict(r) for r in analyzer.find_phantom_rubrics(top_n=top_n)]
