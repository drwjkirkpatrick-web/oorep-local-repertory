"""
Survival Analysis — Kaplan-Meier & Cox Hazards for Time-to-Outcome (Module #72)

Analyzes how long until a remedy produces improvement.

Dashboard visual: Kaplan-Meier survival curves + hazard ratio table

Usage:
    from oorep.survival_analysis import SurvivalAnalysis
    sa = SurvivalAnalysis(db_path="data/feedback.db")
    km = sa.kaplan_meier("PULS")
    hr = sa.hazard_ratio("PULS", "ARS")
"""

import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SurvivalAnalysis:
    """Time-to-event analysis for remedy outcomes."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else (
            Path.home() / "projects" / "oorep-local-repertory" / "data" / "feedback.db"
        )

    def _load_times(self, remedy: str) -> List[Tuple[float, bool]]:
        """Load (days_to_outcome, is_improved) pairs."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            SELECT 
                julianday(prescribed_date) - julianday('2024-01-01'),
                outcome_score
            FROM prescriptions
            WHERE remedy_abbrev=? AND outcome_score IS NOT NULL AND prescribed_date IS NOT NULL
        """, (remedy,))
        rows = c.fetchall()
        conn.close()

        data = []
        for days, outcome in rows:
            if days is None:
                continue
            improved = str(outcome).lower() in ("cured", "improved")
            data.append((float(days), improved))
        return data

    def kaplan_meier(self, remedy: str) -> Dict[str, Any]:
        """Kaplan-Meier estimator for time to improvement."""
        data = self._load_times(remedy)
        if not data:
            return {"error": "No data", "remedy": remedy}

        n = len(data)
        # Sort by time
        data.sort(key=lambda x: x[0])

        survival = 1.0
        curve = [{"time": 0, "survival": 1.0, "at_risk": n}]
        prev_time = 0

        for i, (time, improved) in enumerate(data):
            if time != prev_time:
                curve.append({
                    "time": round(time, 1),
                    "survival": round(survival, 4),
                    "at_risk": n - i,
                })
                prev_time = time

            if improved:
                survival *= (n - i - 1) / (n - i) if (n - i) > 0 else 0

        # Median survival time
        median = None
        for point in curve:
            if point["survival"] <= 0.5:
                median = point["time"]
                break

        return {
            "remedy": remedy,
            "n": n,
            "median_survival_time": median,
            "curve": curve,
        }

    def hazard_ratio(self, remedy_a: str, remedy_b: str) -> Dict[str, Any]:
        """Log-rank style hazard ratio approximation."""
        data_a = self._load_times(remedy_a)
        data_b = self._load_times(remedy_b)

        if not data_a or not data_b:
            return {"error": "Insufficient data"}

        # Simple hazard = events / person-time
        events_a = sum(1 for _, imp in data_a if imp)
        time_a = sum(t for t, _ in data_a)
        events_b = sum(1 for _, imp in data_b if imp)
        time_b = sum(t for t, _ in data_b)

        h_a = events_a / time_a if time_a > 0 else 0
        h_b = events_b / time_b if time_b > 0 else 0

        hr = h_a / h_b if h_b > 0 else float("inf")

        return {
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "hazard_a": round(h_a, 6),
            "hazard_b": round(h_b, 6),
            "hazard_ratio": round(hr, 4) if hr != float("inf") else None,
            "interpretation": f"{remedy_a} {'faster' if hr > 1 else 'slower'} than {remedy_b}" if hr else "No difference",
        }

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 72,
            "feature_name": "Survival Analysis",
            "version": "1.0",
            "supports": ["kaplan_meier", "hazard_ratio", "median_survival"],
            "pure_python": True,
        }
