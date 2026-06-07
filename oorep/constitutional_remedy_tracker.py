"""
Constitutional Remedy Tracker — Longitudinal Constitutional Prescription History

Track a patient's constitutional remedy over years: confirmations,
potency escalations, LM series, acute intercurrents, and constitutional
return.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class ConstitutionalRemedyTracker:
    """
    Track constitutional remedy history per patient.
    Distinguishes constitutional, acute intercurrent, and drainage remedies.
    """

    def __init__(self, db_path: str = "data/constitutional.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS constitutional_history (
                id INTEGER PRIMARY KEY,
                case_id TEXT NOT NULL,
                remedy TEXT NOT NULL,
                potency TEXT NOT NULL,
                prescription_type TEXT NOT NULL,  -- constitutional, acute, intercurrent, drainage, LM_series
                date TEXT NOT NULL,
                notes TEXT,
                outcome TEXT,  -- confirmed, partial, failed, not_yet_assessed
                confirmed_on TEXT,
                practitioner TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_const_case ON constitutional_history(case_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_const_date ON constitutional_history(date)")
        conn.commit()
        conn.close()

    def record(self, case_id: str, remedy: str, potency: str,
               prescription_type: str, date: str,
               notes: str = "", outcome: str = "not_yet_assessed",
               confirmed_on: str = "", practitioner: str = "") -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO constitutional_history (case_id, remedy, potency, prescription_type, date, notes, outcome, confirmed_on, practitioner) VALUES (?,?,?,?,?,?,?,?,?)",
            (case_id, remedy, potency, prescription_type, date, notes, outcome, confirmed_on, practitioner)
        )
        conn.commit()
        conn.close()
        return {
            "case_id": case_id, "remedy": remedy, "potency": potency,
            "type": prescription_type, "date": date, "outcome": outcome,
        }

    def get_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT remedy, potency, prescription_type, date, notes, outcome, confirmed_on FROM constitutional_history WHERE case_id = ? ORDER BY date",
            (case_id,)
        ).fetchall()
        conn.close()
        return [
            {
                "remedy": r[0], "potency": r[1], "type": r[2],
                "date": r[3], "notes": r[4], "outcome": r[5], "confirmed_on": r[6]
            }
            for r in rows
        ]

    def identify_constitutional(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Identify the current constitutional remedy (most recent confirmed)."""
        timeline = self.get_timeline(case_id)
        constitutional = [t for t in timeline if t["type"] == "constitutional"]
        if not constitutional:
            return None
        # Most recent confirmed
        confirmed = [t for t in constitutional if t["outcome"] == "confirmed"]
        if confirmed:
            return confirmed[-1]
        # If none confirmed, return most recent constitutional
        return constitutional[-1]

    def get_intercurrents(self, case_id: str) -> List[Dict[str, Any]]:
        timeline = self.get_timeline(case_id)
        return [t for t in timeline if t["type"] in ("acute", "intercurrent")]

    def potency_escalation(self, case_id: str) -> Dict[str, Any]:
        """Track potency escalation for the constitutional remedy."""
        timeline = self.get_timeline(case_id)
        constitutional = [t for t in timeline if t["type"] == "constitutional"]
        if not constitutional:
            return {"case_id": case_id, "escalation": [], "n_steps": 0}

        # Map potency to numeric level
        potency_order = {"6C": 1, "12C": 2, "30C": 3, "200C": 4, "1M": 5, "10M": 6, "50M": 7, "CM": 8}
        escalation = []
        prev_level = 0
        for t in constitutional:
            level = potency_order.get(t["potency"], 0)
            direction = "escalated" if level > prev_level else "same" if level == prev_level else "reduced"
            escalation.append({
                **t,
                "level": level,
                "direction": direction,
            })
            prev_level = level

        return {
            "case_id": case_id,
            "constitutional_remedy": constitutional[-1]["remedy"] if constitutional else None,
            "escalation": escalation,
            "n_steps": len(escalation),
            "max_potency": constitutional[-1]["potency"] if constitutional else None,
        }

    def stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute("SELECT COUNT(*) FROM constitutional_history").fetchone()[0]
        by_type = conn.execute("SELECT prescription_type, COUNT(*) FROM constitutional_history GROUP BY prescription_type").fetchall()
        by_outcome = conn.execute("SELECT outcome, COUNT(*) FROM constitutional_history GROUP BY outcome").fetchall()
        conn.close()
        return {
            "total_prescriptions": total,
            "by_type": {r[0]: r[1] for r in by_type},
            "by_outcome": {r[0]: r[1] for r in by_outcome},
        }
