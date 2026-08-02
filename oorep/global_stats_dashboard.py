"""
Global Stats Dashboard — Practice Analytics Overview

Global statistics: most-searched rubrics, most-prescribed remedies,
outcome rates by remedy, etc.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class GlobalStatsDashboard:
    """
    Aggregate statistics across the entire practice.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.stats_path = self.data_dir / "global_stats.json"

    def compute(self) -> Dict[str, Any]:
        """Compute global statistics from available databases."""
        stats = {
            "computed_at": None,
            "total_cases": 0,
            "total_prescriptions": 0,
            "top_remedies": [],
            "top_rubrics": [],
            "outcome_rates": {},
            "case_types": {},
        }

        # Try to read from prescription DB
        rx_db = self.data_dir / "remedy_relationships.db"
        if rx_db.exists():
            try:
                conn = sqlite3.connect(str(rx_db))
                rows = conn.execute("SELECT remedy, COUNT(*) FROM prescriptions GROUP BY remedy ORDER BY COUNT(*) DESC LIMIT 20").fetchall()
                stats["top_remedies"] = [{"remedy": r[0], "count": r[1]} for r in rows]
                stats["total_prescriptions"] = conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
                conn.close()
            except Exception as e:
                logger.debug("Rx DB read failed: %s", e)

        # Try constitutional DB
        const_db = self.data_dir / "constitutional.db"
        if const_db.exists():
            try:
                conn = sqlite3.connect(str(const_db))
                stats["total_cases"] = conn.execute("SELECT COUNT(DISTINCT case_id) FROM constitutional_history").fetchone()[0]
                by_type = conn.execute("SELECT prescription_type, COUNT(*) FROM constitutional_history GROUP BY prescription_type").fetchall()
                stats["case_types"] = {r[0]: r[1] for r in by_type}
                by_outcome = conn.execute("SELECT outcome, COUNT(*) FROM constitutional_history WHERE outcome IS NOT NULL GROUP BY outcome").fetchall()
                stats["outcome_rates"] = {r[0]: r[1] for r in by_outcome}
                conn.close()
            except Exception as e:
                logger.debug("Constitutional DB read failed: %s", e)

        # Try appointment DB
        appt_db = self.data_dir / "appointments.db"
        if appt_db.exists():
            try:
                conn = sqlite3.connect(str(appt_db))
                total_appts = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
                stats["total_appointments"] = total_appts
                conn.close()
            except Exception as e:
                logger.debug("Appointment DB read failed: %s", e)

        stats["computed_at"] = datetime.utcnow().isoformat()
        return stats

    def get_summary(self) -> Dict[str, Any]:
        stats = self.compute()
        return {
            "total_cases": stats.get("total_cases", 0),
            "total_prescriptions": stats.get("total_prescriptions", 0),
            "top_remedy": stats["top_remedies"][0] if stats.get("top_remedies") else None,
            "outcome_distribution": stats.get("outcome_rates", {}),
        }
