"""
Outcome Comparator — Statistical Comparison of Remedy Outcomes (Module #66)

Compares outcomes between two or more remedies using:
  - Mann-Whitney U test (pure Python, no scipy)
  - Odds ratio + 95% CI (Woolf method with continuity correction)
  - Cohen's d (standardized mean difference)
  - Cliff's delta (non-parametric effect size)
  - Risk ratio
  - NNT / NNH

Dashboard visual: Forest plot of effect sizes + comparison table

Usage:
    from oorep.outcome_comparator import OutcomeComparator
    comp = OutcomeComparator(db_path="data/feedback.db")
    result = comp.compare_remedies("PULS", "NAT_M", positive=["cured", "improved"])
"""

import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Sequence
from collections import defaultdict


class OutcomeComparator:
    """Statistical comparison of remedy outcomes."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else (
            Path.home() / "projects" / "oorep-local-repertory" / "data" / "feedback.db"
        )

    def _load_outcomes(self, remedy: str, positive_outcomes: List[str]) -> List[int]:
        positive_set = set(o.lower() for o in positive_outcomes)
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT outcome_score FROM prescriptions WHERE remedy_abbrev=? AND outcome_score IS NOT NULL",
                    (remedy,))
        rows = c.fetchall()
        conn.close()
        mapping = {"cured": 2, "improved": 1, "unchanged": 0, "worsened": -1}
        return [mapping.get(str(r[0]).lower(), 0) for r in rows]

    def _mann_whitney_u(self, a: List[float], b: List[float]) -> Tuple[float, float]:
        """Mann-Whitney U test — pure Python."""
        n1, n2 = len(a), len(b)
        if n1 == 0 or n2 == 0:
            return 0.0, 1.0

        combined = [(v, 0) for v in a] + [(v, 1) for v in b]
        combined.sort(key=lambda x: x[0])

        ranks = []
        i = 0
        while i < len(combined):
            j = i
            while j < len(combined) and combined[j][0] == combined[i][0]:
                j += 1
            avg_rank = (i + 1 + j) / 2
            for k in range(i, j):
                ranks.append((combined[k][1], avg_rank))
            i = j

        r1 = sum(r for g, r in ranks if g == 0)
        u1 = r1 - n1 * (n1 + 1) / 2
        u2 = n1 * n2 - u1
        u = min(u1, u2)

        mean_u = n1 * n2 / 2
        tie_groups = defaultdict(int)
        for v, _ in combined:
            tie_groups[v] += 1
        tie_correction = sum(t**3 - t for t in tie_groups.values() if t > 1)
        denom = 12 * (n1 + n2) * (n1 + n2 - 1)
        std_u = math.sqrt(max(0.0001, (n1 * n2 * (n1 + n2 + 1) / 12) - (n1 * n2 * tie_correction) / denom))

        z = (u - mean_u) / std_u
        p = 2 * (1 - self._normal_cdf(abs(z)))
        return u, p

    @staticmethod
    def _normal_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _odds_ratio(self, pos_a: int, neg_a: int, pos_b: int, neg_b: int) -> Tuple[float, List[float]]:
        a, b, c, d = pos_a + 0.5, neg_a + 0.5, pos_b + 0.5, neg_b + 0.5
        or_val = (a * d) / (b * c)
        log_or = math.log(or_val)
        se_log_or = math.sqrt(1/a + 1/b + 1/c + 1/d)
        ci_low = math.exp(log_or - 1.96 * se_log_or)
        ci_high = math.exp(log_or + 1.96 * se_log_or)
        return or_val, [round(ci_low, 3), round(ci_high, 3)]

    def _cohens_d(self, a: List[float], b: List[float]) -> Tuple[Optional[float], List[Optional[float]]]:
        n1, n2 = len(a), len(b)
        if n1 < 2 or n2 < 2:
            return None, [None, None]
        m1, m2 = sum(a)/n1, sum(b)/n2
        v1 = sum((x - m1)**2 for x in a) / (n1 - 1)
        v2 = sum((x - m2)**2 for x in b) / (n2 - 1)
        sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
        if sp == 0:
            return None, [None, None]
        d = (m1 - m2) / sp
        se = math.sqrt(((n1 + n2) / (n1 * n2)) + (d**2 / (2 * (n1 + n2))))
        return round(d, 4), [round(d - 1.96 * se, 4), round(d + 1.96 * se, 4)]

    def _cliffs_delta(self, a: Sequence[float], b: Sequence[float]) -> float:
        n1, n2 = len(a), len(b)
        if n1 == 0 or n2 == 0:
            return 0.0
        dominance = 0
        for x in a:
            for y in b:
                if x > y:
                    dominance += 1
                elif x < y:
                    dominance -= 1
        return dominance / (n1 * n2)

    def compare_remedies(
        self,
        remedy_a: str,
        remedy_b: str,
        positive_outcomes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if positive_outcomes is None:
            positive_outcomes = ["cured", "improved"]

        outcomes_a = self._load_outcomes(remedy_a, positive_outcomes)
        outcomes_b = self._load_outcomes(remedy_b, positive_outcomes)

        n_a = len(outcomes_a)
        n_b = len(outcomes_b)
        pos_a = sum(1 for o in outcomes_a if o > 0)
        pos_b = sum(1 for o in outcomes_b if o > 0)
        neg_a = n_a - pos_a
        neg_b = n_b - pos_b

        if n_a == 0 or n_b == 0:
            return {"error": "Insufficient data", "remedy_a": remedy_a, "remedy_b": remedy_b}

        mw_u, mw_p = self._mann_whitney_u([float(x) for x in outcomes_a], [float(x) for x in outcomes_b])
        or_val, or_ci = self._odds_ratio(pos_a, neg_a, pos_b, neg_b)
        cd, cd_ci = self._cohens_d([float(x) for x in outcomes_a], [float(x) for x in outcomes_b])
        cliff = self._cliffs_delta(outcomes_a, outcomes_b)

        rr = None
        if n_b > 0:
            p_a = pos_a / n_a
            p_b = pos_b / n_b
            if p_b > 0:
                rr = p_a / p_b

        nnt = None
        if rr is not None and rr != 1:
            p_a = pos_a / n_a
            p_b = pos_b / n_b
            nnt = 1 / abs(p_a - p_b) if p_a != p_b else None

        return {
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "n_a": n_a,
            "n_b": n_b,
            "positive_a": pos_a,
            "positive_b": pos_b,
            "positive_rate_a": round(pos_a / n_a, 3),
            "positive_rate_b": round(pos_b / n_b, 3),
            "mann_whitney_u": round(mw_u, 2),
            "mann_whitney_p": round(mw_p, 4),
            "significant": mw_p < 0.05,
            "odds_ratio": round(or_val, 3) if or_val else None,
            "odds_ratio_ci_95": or_ci,
            "cohens_d": cd,
            "cohens_d_ci_95": cd_ci,
            "cliffs_delta": round(cliff, 3),
            "cliffs_interpretation": self._cliff_interpret(abs(cliff)),
            "risk_ratio": round(rr, 3) if rr else None,
            "nnt": round(nnt, 1) if nnt else None,
        }

    @staticmethod
    def _cliff_interpret(delta: float) -> str:
        if delta < 0.147:
            return "negligible"
        if delta < 0.33:
            return "small"
        if delta < 0.474:
            return "medium"
        return "large"

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 66,
            "feature_name": "Outcome Comparator",
            "version": "1.0",
            "supports": ["mann_whitney_u", "odds_ratio", "cohens_d", "cliffs_delta", "risk_ratio", "nnt"],
            "pure_python": True,
        }
