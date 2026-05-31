"""
Suppression Tracker

Records and queries suppression events: when a symptom was artificially
suppressed (by allopathic drug, topical steroid, surgery, etc.) and whether
it later recurred. Helps practitioners avoid prescribing remedies that
historically suppressed symptoms for a given case.

Usage:
    from oorep.suppression_tracker import SuppressionTracker
    st = SuppressionTracker()
    st.record_suppression("PT-001", "eczema", "topical steroid", "2024-01-15", "asthma flare")
    history = st.get_suppression_history("PT-001")
    warnings = st.check_suppression_warnings("Sulph.", "PT-001")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class SuppressionTracker:
    """
    SQLite-backed suppression event tracker.

    Stores suppression history with optional recurrence tracking, so that
    practitioners can flag historically unsafe prescribing pathways.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS suppression_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                suppressed_symptom TEXT NOT NULL,
                suppressing_agent TEXT,
                suppression_date TEXT,
                recurrence_symptoms TEXT,
                date_cleared TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_suppression_case ON suppression_history(case_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_suppression_agent ON suppression_history(suppressing_agent)"
        )
        conn.commit()
        conn.close()

    # ── Public API ───────────────────────────────────────────────────────────

    def record_suppression(
        self,
        case_id: str,
        symptom: str,
        agent: str,
        date: str,
        recurrence: Optional[str] = None,
        date_cleared: Optional[str] = None,
    ) -> int:
        """
        Record a suppression event.

        Args:
            case_id: Patient pseudonym.
            symptom: The symptom that was suppressed (e.g. "eczema").
            agent: What suppressed it (e.g. "topical steroid", "surgery", "Psor.").
            date: Date string (ISO or practitioner format).
            recurrence: Optional symptom that appeared after suppression.
            date_cleared: Optional date when the recurrence resolved.

        Returns:
            Row id of the inserted record.
        """
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO suppression_history
            (case_id, suppressed_symptom, suppressing_agent, suppression_date, recurrence_symptoms, date_cleared, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (case_id, symptom, agent, date, recurrence, date_cleared, now),
        )
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id or 0

    def get_suppression_history(self, case_id: str) -> List[Dict]:
        """Return all suppression events for a case."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, case_id, suppressed_symptom, suppressing_agent, suppression_date, recurrence_symptoms, date_cleared, created_at "
            "FROM suppression_history WHERE case_id = ? ORDER BY suppression_date",
            (case_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def get_suppression_chronology(self, case_id: str) -> List[Dict]:
        """
        Return ordered timeline of suppression events for a case,
        with inferred stage labels.
        """
        events = self.get_suppression_history(case_id)
        for i, ev in enumerate(events, start=1):
            ev["stage"] = i
        return events

    def check_suppression_warnings(
        self,
        prescribed_remedy: str,
        case_id: str,
    ) -> Dict:
        """
        Warn if the proposed remedy has historically suppressed symptoms
        that later recurred for this case.

        Args:
            prescribed_remedy: Remedy abbreviation being considered.
            case_id: Patient pseudonym.

        Returns:
            Dict:
                has_warning: bool
                warnings: List[str]
                matched_events: List[Dict]
        """
        history = self.get_suppression_history(case_id)
        warnings: List[str] = []
        matched: List[Dict] = []
        for ev in history:
            agent = ev.get("suppressing_agent", "")
            if not isinstance(agent, str):
                continue
            # Match on exact or fuzzy abbreviation
            a_norm = agent.strip().lower().rstrip(".")
            p_norm = prescribed_remedy.strip().lower().rstrip(".")
            if a_norm == p_norm:
                warnings.append(
                    f"WARNING: {prescribed_remedy} previously suppressed '{ev['suppressed_symptom']}' "
                    f"and led to recurrence: {ev.get('recurrence_symptoms', 'unknown')}."
                )
                matched.append(ev)
        return {
            "has_warning": len(warnings) > 0,
            "warnings": warnings,
            "matched_events": matched,
        }

    def list_all_agents(self, case_id: Optional[str] = None) -> List[str]:
        """Return distinct suppressing agents, optionally filtered by case."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if case_id:
            cursor.execute(
                "SELECT DISTINCT suppressing_agent FROM suppression_history WHERE case_id = ?",
                (case_id,),
            )
        else:
            cursor.execute("SELECT DISTINCT suppressing_agent FROM suppression_history")
        rows = cursor.fetchall()
        conn.close()
        return sorted({r[0] for r in rows if r[0]})

    @staticmethod
    def _row_to_dict(row) -> Dict:
        return {
            "id": row[0],
            "case_id": row[1],
            "suppressed_symptom": row[2],
            "suppressing_agent": row[3],
            "suppression_date": row[4],
            "recurrence_symptoms": row[5],
            "date_cleared": row[6],
            "created_at": row[7],
        }
