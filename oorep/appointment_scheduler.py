"""
Appointment Scheduler — Follow-Up and Acute Appointment Calendar

Track appointments, follow-ups, and schedule reminders for cases.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class AppointmentScheduler:
    """
    Schedule and manage appointments for homeopathic cases.
    Tracks follow-ups, acute appointments, and case reviews.
    """

    def __init__(self, db_path: str = "data/appointments.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        # v4.3 Security: enable WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                case_id TEXT NOT NULL,
                appointment_type TEXT NOT NULL,  -- follow_up, acute, review, initial
                scheduled_date TEXT NOT NULL,
                scheduled_time TEXT,
                duration_minutes INTEGER DEFAULT 60,
                notes TEXT,
                status TEXT DEFAULT 'scheduled',  -- scheduled, completed, cancelled, no_show
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_appt_case ON appointments(case_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_appt_date ON appointments(scheduled_date)")
        conn.commit()
        conn.close()

    def schedule(self, case_id: str, appointment_type: str,
                 days_from_now: int, time: str = "10:00",
                 duration: int = 60, notes: str = "") -> Dict[str, Any]:
        """Schedule an appointment N days from now."""
        # v4.3 Security: validate inputs
        from oorep.security_manager import SecurityManager
        if not case_id or not isinstance(case_id, str):
            raise ValueError("case_id required")
        if appointment_type not in ("follow_up", "acute", "review", "initial"):
            raise ValueError("Invalid appointment_type")
        if not isinstance(days_from_now, int) or days_from_now < 0 or days_from_now > 365:
            raise ValueError("days_from_now must be 0-365")
        safe_notes = SecurityManager.sanitize_input(notes, max_length=2000) if notes else ""
        date = (datetime.utcnow() + timedelta(days=days_from_now)).strftime("%Y-%m-%d")
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "INSERT INTO appointments (case_id, appointment_type, scheduled_date, scheduled_time, duration_minutes, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (case_id, appointment_type, date, time, duration, safe_notes, now, now)
        )
        appt_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {
            "id": appt_id,
            "case_id": case_id,
            "type": appointment_type,
            "date": date,
            "time": time,
            "duration": duration,
            "notes": notes,
        }

    def get_upcoming(self, case_id: Optional[str] = None,
                     days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming appointments."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        future = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        conn = sqlite3.connect(str(self.db_path))
        if case_id:
            rows = conn.execute(
                "SELECT id, case_id, appointment_type, scheduled_date, scheduled_time, duration_minutes, notes, status FROM appointments WHERE case_id = ? AND scheduled_date BETWEEN ? AND ? AND status = 'scheduled' ORDER BY scheduled_date",
                (case_id, today, future)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, case_id, appointment_type, scheduled_date, scheduled_time, duration_minutes, notes, status FROM appointments WHERE scheduled_date BETWEEN ? AND ? AND status = 'scheduled' ORDER BY scheduled_date",
                (today, future)
            ).fetchall()
        conn.close()
        return [
            {
                "id": r[0], "case_id": r[1], "type": r[2],
                "date": r[3], "time": r[4], "duration": r[5],
                "notes": r[6], "status": r[7]
            }
            for r in rows
        ]

    def complete(self, appointment_id: int) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "UPDATE appointments SET status = 'completed', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), appointment_id)
        )
        conn.commit()
        conn.close()
        return {"id": appointment_id, "status": "completed"}

    def cancel(self, appointment_id: int) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "UPDATE appointments SET status = 'cancelled', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), appointment_id)
        )
        conn.commit()
        conn.close()
        return {"id": appointment_id, "status": "cancelled"}

    def stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        by_type = conn.execute("SELECT appointment_type, COUNT(*) FROM appointments GROUP BY appointment_type").fetchall()
        by_status = conn.execute("SELECT status, COUNT(*) FROM appointments GROUP BY status").fetchall()
        conn.close()
        return {
            "total": total,
            "by_type": {r[0]: r[1] for r in by_type},
            "by_status": {r[0]: r[1] for r in by_status},
        }
