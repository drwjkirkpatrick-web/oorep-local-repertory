"""
Outcome Predictor Statistics — Statistical Validation Module #1

Validates the clinical predictive value of rubric coverage, keynote matching,
and composite scoring. Computes ROC curves, AUC, calibration plots, and
bootstrap confidence intervals on outcome data.

Pure Python / stdlib — no scipy dependency.  
Dashboard visual: ROC curve + calibration curve + confidence band chart

Usage:
    from oorep.outcome_predictor_stats import OutcomePredictorStats
    stats = OutcomePredictorStats(db_path="data/feedback.db")

    # Validate: does rubric coverage predict positive outcomes?
    roc = stats.compute_roc(
        predictor="rubric_coverage",
        positive_outcomes=["cured", "improved"],
    )

    # Calibration: are predicted probabilities well-calibrated?
    cal = stats.calibration_analysis(
        bin_count=5,
        predictor="composite_score",
    )

    # Bootstrap CI on AUC
    ci = stats.bootstrap_auc(
        predictor="rubric_coverage",
        n_iterations=1000,
        positive_outcomes=["cured", "improved"],
    )

    # Full report
    report = stats.full_validation_report()
"""

import math
import random
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ROCPoint:
    threshold: float
    tpr: float   # True positive rate (sensitivity)
    fpr: float   # False positive rate (1 - specificity)
    precision: float
    f1: float


@dataclass
class CalibrationBin:
    bin_min: float
    bin_max: float
    predicted_prob: float
    observed_rate: float
    count: int


class OutcomePredictorStats:
    """
    Statistical validation engine for outcome predictions.

    Works against the prescriptions table schema:
        prescription_id, patient_id, remedy_abbrev, potency, status,
        outcome_score, prescribed_date, final_notes

    outcome_score values: 'cured', 'improved', 'unchanged', 'worsened'
    """

    def __init__(self, db_path: Optional[Path] = None):
        # v4.3 Security: use env var for data directory instead of hardcoded path
        import os
        _env_data = os.environ.get("OOREP_DATA_DIR")
        if _env_data:
            _default_db = Path(_env_data) / "feedback.db"
        else:
            _default_db = Path(__file__).resolve().parent.parent / "data" / "feedback.db"
        self.db_path = Path(db_path) if db_path else _default_db
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema_if_needed()

    def _init_schema_if_needed(self) -> None:
        """Ensure prescriptions table exists for testing."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        # v4.3 Security: enable WAL mode for concurrent read access
        conn.execute("PRAGMA journal_mode=WAL")
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                prescription_id TEXT PRIMARY KEY,
                patient_id TEXT,
                remedy_abbrev TEXT,
                potency TEXT,
                status TEXT,
                outcome_score TEXT,
                prescribed_date TEXT,
                final_notes TEXT,
                rubric_coverage REAL DEFAULT 0.0,
                keynote_match REAL DEFAULT 0.0,
                composite_score REAL DEFAULT 0.0
            )
        """)
        conn.commit()
        conn.close()

    def _load_data(self, predictor: str, positive_outcomes: List[str]) -> List[Tuple[float, int]]:
        """
        Load (predictor_value, is_positive) pairs from DB.
        Returns list sorted by predictor value descending.

        Security note: The predictor parameter is validated against a strict
        allowlist and then used to select a hardcoded SQL column. The f-string
        interpolation is safe because ``_PREDICTOR_COLUMNS`` maps validated
        input to fixed identifiers — the user value never reaches the SQL.
        """
        # Strict allowlist mapping: validated input → hardcoded column name
        # This prevents SQL injection even if the allowlist check is modified
        _PREDICTOR_COLUMNS = {
            "rubric_coverage": "rubric_coverage",
            "keynote_match": "keynote_match",
            "composite_score": "composite_score",
        }
        if predictor not in _PREDICTOR_COLUMNS:
            raise ValueError(f"predictor must be one of {set(_PREDICTOR_COLUMNS.keys())}")

        # Use the hardcoded column name, not the user-supplied value
        col = _PREDICTOR_COLUMNS[predictor]
        positive_set = set(o.lower() for o in positive_outcomes)
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        # SECURITY: col is validated against _PREDICTOR_COLUMNS allowlist
        # (hardcoded mapping at line 125) before reaching SQL. Column names
        # cannot use SQL parameterization (?), so allowlist validation is
        # the correct defense. The value used in SQL is the hardcoded
        # allowlist value, never the raw user input.
        assert col in _PREDICTOR_COLUMNS.values(), "Allowlist check failed"
        sql = (
            f"SELECT {col}, outcome_score FROM prescriptions "
            f"WHERE {col} IS NOT NULL AND outcome_score IS NOT NULL"
        )
        c.execute(sql)
        rows = c.fetchall()
        conn.close()

        data = []
        for val, outcome in rows:
            is_positive = 1 if str(outcome).lower() in positive_set else 0
            data.append((float(val), is_positive))

        # Sort by predictor value descending (higher = more likely positive)
        data.sort(key=lambda x: x[0], reverse=True)
        return data

    # ── ROC / AUC ──────────────────────────────────────────────────────────────

    def compute_roc(
        self,
        predictor: str = "composite_score",
        positive_outcomes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute ROC curve and AUC using the trapezoidal rule.
        Pure Python implementation — no scipy required.
        """
        if positive_outcomes is None:
            positive_outcomes = ["cured", "improved"]

        data = self._load_data(predictor, positive_outcomes)
        n = len(data)
        if n == 0:
            return {"error": "No data available", "auc": 0.5, "points": []}

        n_pos = sum(1 for _, y in data if y == 1)
        n_neg = n - n_pos
        if n_pos == 0 or n_neg == 0:
            return {"error": "Only one outcome class present", "auc": 0.5, "points": []}

        # Generate ROC points at each unique threshold
        tp = 0
        fp = 0
        points: List[ROCPoint] = []

        prev_val = None
        for val, y in data:
            if prev_val is not None and val != prev_val:
                # Emit point at threshold between prev and current
                tpr = tp / n_pos if n_pos else 0
                fpr = fp / n_neg if n_neg else 0
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                f1 = 2 * precision * tpr / (precision + tpr) if (precision + tpr) > 0 else 0
                points.append(ROCPoint(
                    threshold=(prev_val + val) / 2,
                    tpr=round(tpr, 4),
                    fpr=round(fpr, 4),
                    precision=round(precision, 4),
                    f1=round(f1, 4),
                ))
            if y == 1:
                tp += 1
            else:
                fp += 1
            prev_val = val

        # Final point (all classified positive)
        points.append(ROCPoint(threshold=0, tpr=1.0, fpr=1.0, precision=n_pos / n, f1=0))

        # Compute AUC via trapezoidal rule
        auc = self._auc_trapezoidal(points)

        # Find optimal threshold (Youden's J = max(TPR - FPR))
        best = max(points, key=lambda p: p.tpr - p.fpr)

        # Find point nearest top-left corner (min sqrt(FPR² + (1-TPR)²))
        closest = min(points, key=lambda p: math.sqrt(p.fpr**2 + (1 - p.tpr)**2))

        return {
            "predictor": predictor,
            "positive_outcomes": positive_outcomes,
            "n_total": n,
            "n_positive": n_pos,
            "n_negative": n_neg,
            "auc": round(auc, 4),
            "auc_interpretation": self._auc_interpret(auc),
            "optimal_threshold": round(best.threshold, 4),
            "optimal_tpr": best.tpr,
            "optimal_fpr": best.fpr,
            "closest_to_top_left": {
                "threshold": round(closest.threshold, 4),
                "tpr": closest.tpr,
                "fpr": closest.fpr,
            },
            "points": [
                {"threshold": p.threshold, "tpr": p.tpr, "fpr": p.fpr,
                 "precision": p.precision, "f1": p.f1}
                for p in points
            ],
        }

    @staticmethod
    def _auc_trapezoidal(points: List[ROCPoint]) -> float:
        """Compute AUC using trapezoidal rule."""
        # Sort by FPR ascending for proper integration
        sorted_pts = sorted(points, key=lambda p: p.fpr)
        auc = 0.0
        for i in range(1, len(sorted_pts)):
            dx = sorted_pts[i].fpr - sorted_pts[i - 1].fpr
            avg_height = (sorted_pts[i].tpr + sorted_pts[i - 1].tpr) / 2
            auc += dx * avg_height
        return auc

    @staticmethod
    def _auc_interpret(auc: float) -> str:
        if auc < 0.5:
            return "Worse than random (check predictor logic)"
        if auc < 0.6:
            return "Poor discrimination"
        if auc < 0.7:
            return "Fair discrimination"
        if auc < 0.8:
            return "Good discrimination"
        if auc < 0.9:
            return "Very good discrimination"
        return "Excellent discrimination"

    # ── Calibration ─────────────────────────────────────────────────────────────

    def calibration_analysis(
        self,
        bin_count: int = 5,
        predictor: str = "composite_score",
        positive_outcomes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calibration analysis: bin predictions and compare predicted vs observed rates.
        Uses equal-frequency binning (quantile-based).
        """
        if positive_outcomes is None:
            positive_outcomes = ["cured", "improved"]

        data = self._load_data(predictor, positive_outcomes)
        n = len(data)
        if n == 0:
            return {"error": "No data available", "bins": [], "reliability_diagram": []}

        # Normalize predictor to [0, 1] pseudo-probability
        max_val = max(v for v, _ in data) if data else 1
        min_val = min(v for v, _ in data) if data else 0
        denom = max_val - min_val if max_val != min_val else 1

        normalized = [(v - min_val) / denom for v, _ in data]
        outcomes = [y for _, y in data]

        # Sort by normalized score
        pairs = sorted(zip(normalized, outcomes), key=lambda x: x[0])

        # Equal-frequency binning
        bin_size = max(1, n // bin_count)
        bins: List[CalibrationBin] = []

        for i in range(0, n, bin_size):
            chunk = pairs[i:i + bin_size]
            if not chunk:
                break
            pred_vals = [p[0] for p in chunk]
            obs_vals = [p[1] for p in chunk]
            bins.append(CalibrationBin(
                bin_min=round(min(pred_vals), 3),
                bin_max=round(max(pred_vals), 3),
                predicted_prob=round(sum(pred_vals) / len(pred_vals), 3),
                observed_rate=round(sum(obs_vals) / len(obs_vals), 3),
                count=len(chunk),
            ))

        # Mean squared calibration error
        mse = sum((b.predicted_prob - b.observed_rate) ** 2 for b in bins) / len(bins) if bins else 0

        # Expected calibration error (weighted by bin size)
        total = sum(b.count for b in bins)
        ece = sum(abs(b.predicted_prob - b.observed_rate) * (b.count / total) for b in bins) if total else 0

        # Reliability diagram data (for plotting)
        reliability = [
            {"predicted": b.predicted_prob, "observed": b.observed_rate, "count": b.count}
            for b in bins
        ]

        return {
            "predictor": predictor,
            "bin_count": len(bins),
            "bins": [
                {
                    "range": [b.bin_min, b.bin_max],
                    "predicted_prob": b.predicted_prob,
                    "observed_rate": b.observed_rate,
                    "count": b.count,
                }
                for b in bins
            ],
            "mean_squared_error": round(mse, 4),
            "expected_calibration_error": round(ece, 4),
            "calibration_quality": "well-calibrated" if ece < 0.05 else ("fair" if ece < 0.15 else "poor"),
            "reliability_diagram": reliability,
            "perfect_calibration_line": [[0, 0], [1, 1]],  # y=x reference
        }

    # ── Bootstrap CI on AUC ────────────────────────────────────────────────────

    def bootstrap_auc(
        self,
        predictor: str = "composite_score",
        n_iterations: int = 1000,
        positive_outcomes: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Bootstrap confidence interval for AUC.
        Uses percentile method.
        """
        if positive_outcomes is None:
            positive_outcomes = ["cured", "improved"]

        data = self._load_data(predictor, positive_outcomes)
        n = len(data)
        if n == 0:
            return {"error": "No data available", "ci_95": [0, 0], "mean_auc": 0.5}

        if seed is not None:
            random.seed(seed)

        aucs = []
        for _ in range(n_iterations):
            # Resample with replacement
            sample = [random.choice(data) for _ in range(n)]
            sample.sort(key=lambda x: x[0], reverse=True)
            auc = self._auc_from_sample(sample)
            aucs.append(auc)

        aucs.sort()
        alpha = 0.05
        lower_idx = int(alpha / 2 * n_iterations)
        upper_idx = int((1 - alpha / 2) * n_iterations)
        lower_idx = max(0, min(lower_idx, n_iterations - 1))
        upper_idx = max(0, min(upper_idx, n_iterations - 1))

        return {
            "predictor": predictor,
            "n_iterations": n_iterations,
            "n_samples": n,
            "mean_auc": round(sum(aucs) / len(aucs), 4),
            "median_auc": round(aucs[len(aucs) // 2], 4),
            "std_auc": round(math.sqrt(sum((a - sum(aucs)/len(aucs))**2 for a in aucs) / len(aucs)), 4),
            "ci_95": [round(aucs[lower_idx], 4), round(aucs[upper_idx], 4)],
            "ci_90": [round(aucs[int(0.05 * n_iterations)], 4), round(aucs[int(0.95 * n_iterations)], 4)],
            "distribution": aucs,  # Full distribution for histogram
        }

    @staticmethod
    def _auc_from_sample(sample: List[Tuple[float, int]]) -> float:
        """Compute AUC from a bootstrap sample."""
        n_pos = sum(1 for _, y in sample if y == 1)
        n_neg = len(sample) - n_pos
        if n_pos == 0 or n_neg == 0:
            return 0.5

        tp = 0
        fp = 0
        auc = 0.0
        prev_val = None
        for val, y in sample:
            if prev_val is not None and val != prev_val:
                tpr = tp / n_pos
                fpr = fp / n_neg
                prev_tpr = max(0, (tp - (1 if y == 1 else 0)) / n_pos)
                prev_fpr = max(0, (fp - (1 if y == 0 else 0)) / n_neg)
                auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2
            if y == 1:
                tp += 1
            else:
                fp += 1
            prev_val = val

        # Add final segment
        if prev_val is not None:
            tpr = tp / n_pos
            fpr = fp / n_neg
            prev_tpr = max(0, (tp - (1 if sample[-1][1] == 1 else 0)) / n_pos)
            prev_fpr = max(0, (fp - (1 if sample[-1][1] == 0 else 0)) / n_neg)
            auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2

        return auc

    # ── Full report ───────────────────────────────────────────────────────────

    def full_validation_report(
        self,
        predictors: Optional[List[str]] = None,
        positive_outcomes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report for all predictors.
        """
        if predictors is None:
            predictors = ["rubric_coverage", "keynote_match", "composite_score"]
        if positive_outcomes is None:
            positive_outcomes = ["cured", "improved"]

        report = {
            "predictors": {},
            "summary": {
                "n_total": 0,
                "n_positive": 0,
                "positive_rate": 0,
            },
        }

        # Get overall counts
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT outcome_score FROM prescriptions WHERE outcome_score IS NOT NULL")
        all_outcomes = [r[0] for r in c.fetchall()]
        conn.close()

        positive_set = set(o.lower() for o in positive_outcomes)
        n_pos = sum(1 for o in all_outcomes if str(o).lower() in positive_set)
        n_total = len(all_outcomes)

        report["summary"] = {
            "n_total": n_total,
            "n_positive": n_pos,
            "n_negative": n_total - n_pos,
            "positive_rate": round(n_pos / n_total, 4) if n_total else 0,
        }

        for pred in predictors:
            roc = self.compute_roc(pred, positive_outcomes)
            cal = self.calibration_analysis(5, pred, positive_outcomes)
            boot = self.bootstrap_auc(pred, 200, positive_outcomes, seed=42)

            report["predictors"][pred] = {
                "roc": roc,
                "calibration": cal,
                "bootstrap_ci": boot,
            }

        # Rank predictors by AUC
        ranked = sorted(
            report["predictors"].items(),
            key=lambda x: x[1]["roc"]["auc"],
            reverse=True,
        )
        report["predictor_ranking"] = [
            {"predictor": k, "auc": v["roc"]["auc"], "ci_95": v["bootstrap_ci"]["ci_95"]}
            for k, v in ranked
        ]

        return report

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 64,
            "feature_name": "Outcome Predictor Statistics",
            "version": "1.0",
            "supports": ["roc_auc", "calibration_analysis", "bootstrap_ci", "full_validation_report"],
            "dependencies": ["prescriptions table with rubric_coverage, keynote_match, composite_score columns"],
            "pure_python": True,
        }
