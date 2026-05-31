#!/usr/bin/env python3
"""
Case Memory for OOREP-Hermes Bridge.

Lightweight SQLite patient case persistence using the existing remedy_feedback.py
schema. Stores pseudonymized cases with prescription details, rubric rationale,
and follow-up outcomes.

All patient data uses pseudonyms only — no PHI stored.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


# Use the same DB path as remedy_feedback.py for consistency
DEFAULT_DB_PATH = Path.home() / "projects" / "oorep-local-repertory" / "data" / "feedback.db"


class CaseMemoryStore:
    """
    SQLite-backed case memory for homeopathic prescriptions and follow-ups.
    Integrates with remedy_feedback.py schema when available; falls back
    to its own tables.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize tables if not present."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Mirror the remedy_feedback.py prescriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                prescription_id TEXT PRIMARY KEY,
                patient_id TEXT,
                remedy_abbrev TEXT,
                remedy_name TEXT,
                potency TEXT,
                prescriber_id TEXT,
                prescriber_ack INTEGER,
                rubric_ids TEXT,
                rubric_paths TEXT,
                dynamic_symptoms TEXT,
                status TEXT,
                prescribed_date TEXT,
                completed_date TEXT,
                outcome_score TEXT,
                final_notes TEXT
            )
        ''')

        # Additional case memory metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS case_notes (
                note_id TEXT PRIMARY KEY,
                prescription_id TEXT,
                note_type TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patient_id 
            ON prescriptions(patient_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status 
            ON prescriptions(status)
        ''')

        conn.commit()
        conn.close()

    def add_case(
        self,
        patient_pseudonym: str,
        remedy_abbrev: str,
        remedy_name: str,
        potency: str,
        rubric_ids: List[int],
        rubric_paths: List[str],
        prescriber_id: str = "walker_nd",
        symptoms: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Record a new prescription case.

        Args:
            patient_pseudonym: Anonymized patient ID (e.g., "MrsJ2024")
            remedy_abbrev: Remedy abbreviation (e.g., "Ars.")
            remedy_name: Full remedy name
            potency: Potency and repetition (e.g., "200c QD 3 doses")
            rubric_ids: List of OOREP rubric IDs used in rationale
            rubric_paths: Corresponding rubric fullpaths
            prescriber_id: Licensed practitioner identifier
            sympotms: List of original symptoms presented
            notes: Free-text clinical notes

        Returns:
            prescription_id: UUID for this prescription
        """
        prescription_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prescriptions
            (prescription_id, patient_id, remedy_abbrev, remedy_name, potency,
             prescriber_id, prescriber_ack, rubric_ids, rubric_paths,
             dynamic_symptoms, status, prescribed_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prescription_id,
            patient_pseudonym,
            remedy_abbrev,
            remedy_name,
            potency,
            prescriber_id,
            0,  # prescriber_ack = False until approved
            json.dumps(rubric_ids),
            json.dumps(rubric_paths),
            json.dumps(symptoms or []),
            "pending_review",
            now,
        ))

        if notes:
            cursor.execute('''
                INSERT INTO case_notes (note_id, prescription_id, note_type, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4())[:12], prescription_id, "initial", notes, now))

        conn.commit()
        conn.close()
        return prescription_id

    def get_cases_for_patient(self, patient_pseudonym: str) -> List[Dict]:
        """Retrieve all cases for a pseudonym."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT prescription_id, remedy_abbrev, remedy_name, potency,
                   status, prescribed_date, completed_date, outcome_score,
                   final_notes, rubric_ids, rubric_paths
            FROM prescriptions WHERE patient_id = ?
            ORDER BY prescribed_date DESC
        ''', (patient_pseudonym,))
        rows = cursor.fetchall()
        conn.close()

        cases = []
        for row in rows:
            cases.append({
                "prescription_id": row[0],
                "remedy": row[1],
                "remedy_name": row[2],
                "potency": row[3],
                "status": row[4],
                "date": row[5],
                "completed": row[6],
                "outcome": row[7] or "unknown",
                "notes": row[8],
                "rubric_ids": json.loads(row[9]) if row[9] else [],
                "rubric_paths": json.loads(row[10]) if row[10] else [],
            })
        return cases

    def get_case_by_id(self, prescription_id: str) -> Optional[Dict]:
        """Get a single case by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT patient_id, remedy_abbrev, remedy_name, potency,
                   status, prescribed_date, outcome_score, final_notes,
                   rubric_ids, rubric_paths, prescriber_ack
            FROM prescriptions WHERE prescription_id = ?
        ''', (prescription_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None

        return {
            "patient_id": row[0],
            "remedy": row[1],
            "remedy_name": row[2],
            "potency": row[3],
            "status": row[4],
            "date": row[5],
            "outcome": row[6] or "unknown",
            "notes": row[7],
            "rubric_ids": json.loads(row[8]) if row[8] else [],
            "rubric_paths": json.loads(row[9]) if row[9] else [],
            "practitioner_approved": bool(row[10]),
        }

    def approve_prescription(self, prescription_id: str, prescriber_id: str) -> bool:
        """
        Mark a prescription as practitioner-approved.
        This enforces the clinical guardrail: no prescription is actionable
        until a licensed practitioner reviews and approves it.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE prescriptions
            SET prescriber_ack = 1, status = 'active', prescriber_id = ?
            WHERE prescription_id = ?
        ''', (prescriber_id, prescription_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def resolve_case(self, prescription_id: str, outcome: str, notes: Optional[str] = None) -> bool:
        """
        Mark a case as completed with an outcome.

        outcome: one of "cured", "major_improvement", "improved",
                         "unchanged", "worsened", "unknown"
        """
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE prescriptions
            SET status = 'completed',
                completed_date = ?,
                outcome_score = ?,
                final_notes = COALESCE(?, final_notes)
            WHERE prescription_id = ?
        ''', (now, outcome, notes, prescription_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    # ============ TIMELINE & CROSS-CASE FEATURES (Benefits #8, #9, #11) ============

    def get_patient_timeline(self, patient_pseudonym: str) -> List[Dict]:
        """
        Chronological timeline of all events for a patient.
        Combines prescriptions, follow-ups (symptom_reports), and case notes
        into a single sorted list of timeline events.

        Returns list of dicts with keys: type, date, description, data
        """
        events = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Prescriptions
        cursor.execute('''
            SELECT prescription_id, remedy_abbrev, remedy_name, potency,
                   status, prescribed_date, completed_date, outcome_score,
                   final_notes, prescriber_ack
            FROM prescriptions WHERE patient_id = ?
            ORDER BY prescribed_date
        ''', (patient_pseudonym,))
        for row in cursor.fetchall():
            events.append({
                "type": "prescription",
                "date": row[5],
                "description": f"💊 Prescribed {row[1]} ({row[2]}) {row[3]}",
                "data": {
                    "prescription_id": row[0],
                    "remedy_abbrev": row[1],
                    "remedy_name": row[2],
                    "potency": row[3],
                    "status": row[4],
                    "outcome": row[7] or "unknown",
                    "practitioner_approved": bool(row[9]),
                    "notes": row[8],
                }
            })
            if row[6]:  # completed_date exists
                events.append({
                    "type": "outcome",
                    "date": row[6],
                    "description": f"🏁 Case resolved: {row[7] or 'unknown'}",
                    "data": {
                        "prescription_id": row[0],
                        "outcome": row[7],
                        "notes": row[8],
                    }
                })

        # Follow-up reports from symptom_reports table if exists
        try:
            cursor.execute('''
                SELECT sr.report_id, sr.prescription_id, sr.timestamp, sr.overall_status,
                       sr.general_note, sr.next_followup, p.remedy_abbrev
                FROM symptom_reports sr
                JOIN prescriptions p ON sr.prescription_id = p.prescription_id
                WHERE p.patient_id = ?
                ORDER BY sr.timestamp
            ''', (patient_pseudonym,))
            for row in cursor.fetchall():
                events.append({
                    "type": "followup",
                    "date": row[2],
                    "description": f"🔄 Follow-up: {row[3]} with {row[6]}",
                    "data": {
                        "report_id": row[0],
                        "prescription_id": row[1],
                        "overall_status": row[3],
                        "note": row[4],
                        "next_followup": row[5],
                        "remedy_abbrev": row[6],
                    }
                })
        except sqlite3.OperationalError:
            pass  # symptom_reports table may not exist in this DB copy

        conn.close()

        # Sort all events by date
        events.sort(key=lambda e: e.get("date") or "")
        return events

    def find_recurring_rubrics(self, patient_pseudonym: str) -> Dict[str, Any]:
        """
        Across all cases for a patient, find rubrics that appear repeatedly.
        Identifies chronic / constitutional patterns.

        Returns dict with recurring_rubrics list and pattern_score.
        """
        cases = self.get_cases_for_patient(patient_pseudonym)
        if not cases:
            return {"message": "No cases found for this patient"}

        from collections import Counter
        rubric_counter = Counter()
        total_cases = len(cases)

        for c in cases:
            for path in c.get("rubric_paths", []):
                rubric_counter[path] += 1

        recurring = []
        for rubric, count in rubric_counter.most_common(20):
            frequency = count / total_cases
            if frequency >= 0.3:  # Appears in 30%+ of cases
                recurring.append({
                    "rubric": rubric,
                    "count": count,
                    "frequency": round(frequency, 2),
                    "percentage": round(frequency * 100, 1),
                })

        # Also track remedy recurrence
        remedy_counter = Counter(c["remedy"] for c in cases if c.get("remedy"))
        recurring_remedies = [
            {"remedy": rem, "count": cnt, "frequency": round(cnt / total_cases, 2)}
            for rem, cnt in remedy_counter.most_common(5)
        ]

        return {
            "patient_pseudonym": patient_pseudonym,
            "total_cases": total_cases,
            "recurring_rubrics": recurring,
            "recurring_remedies": recurring_remedies,
            "constitutional_signal": len(recurring) >= 3,  # Heuristic: 3+ recurring rubrics suggests constitutional
        }

    def get_patient_summary(self, patient_pseudonym: str) -> Dict[str, Any]:
        """
        High-level clinical summary of a patient across all cases.
        """
        cases = self.get_cases_for_patient(patient_pseudonym)
        timeline = self.get_patient_timeline(patient_pseudonym)
        patterns = self.find_recurring_rubrics(patient_pseudonym)

        completed = [c for c in cases if c.get("status") == "completed"]
        active = [c for c in cases if c.get("status") == "active"]
        pending = [c for c in cases if c.get("status") == "pending_review"]
        outcomes = [c.get("outcome", "unknown") for c in completed]

        from collections import Counter
        outcome_counts = Counter(outcomes)

        return {
            "patient_pseudonym": patient_pseudonym,
            "total_cases": len(cases),
            "active": len(active),
            "pending_review": len(pending),
            "completed": len(completed),
            "outcome_distribution": dict(outcome_counts),
            "most_common_remedies": patterns.get("recurring_remedies", []),
            "constitutional_signal": patterns.get("constitutional_signal", False),
            "timeline_length": len(timeline),
            "first_visit": timeline[0]["date"] if timeline else None,
            "latest_visit": timeline[-1]["date"] if timeline else None,
        }

    # ============ SUPPRESSION TRACKING (Benefit #11) ============

    def add_suppression_event(
        self,
        patient_pseudonym: str,
        suppression_type: str,
        substance_or_factor: str,
        suppressed_symptoms: List[str],
        date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Record a suppression event (e.g., steroid use, vaccine, surgery)
        that may affect homeopathic case management.

        suppression_type: e.g., "steroid", "immunosuppressant", "vaccine",
                                   "surgical", "antibiotic", "birth_control"
        """
        event_id = str(uuid.uuid4())[:8]
        now = date or datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create suppression_events table if missing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppression_events (
                event_id TEXT PRIMARY KEY,
                patient_id TEXT,
                suppression_type TEXT,
                substance_or_factor TEXT,
                suppressed_symptoms TEXT,
                event_date TEXT,
                notes TEXT,
                created_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_spp_patient ON suppression_events(patient_id)
        ''')

        cursor.execute('''
            INSERT INTO suppression_events
            (event_id, patient_id, suppression_type, substance_or_factor,
             suppressed_symptoms, event_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id, patient_pseudonym, suppression_type, substance_or_factor,
            json.dumps(suppressed_symptoms), now, notes, datetime.now().isoformat(),
        ))
        conn.commit()
        conn.close()
        return event_id

    def get_suppression_history(self, patient_pseudonym: str) -> List[Dict]:
        """Retrieve suppression events for a patient."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT event_id, suppression_type, substance_or_factor,
                       suppressed_symptoms, event_date, notes
                FROM suppression_events WHERE patient_id = ?
                ORDER BY event_date
            ''', (patient_pseudonym,))
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            conn.close()
            return []

        conn.close()
        return [{
            "event_id": r[0],
            "type": r[1],
            "substance": r[2],
            "suppressed_symptoms": json.loads(r[3]) if r[3] else [],
            "date": r[4],
            "notes": r[5],
        } for r in rows]


if __name__ == "__main__":
    # Quick smoke test
    store = CaseMemoryStore()
    pid = store.add_case(
        patient_pseudonym="TestPatient01",
        remedy_abbrev="Puls.",
        remedy_name="Pulsatilla",
        potency="200c",
        rubric_ids=[34400, 34401],
        rubric_paths=["Mind, weeping", "Mind, changeable mood"],
        symptoms=["weeping easily", "worse warm room"],
        notes="First prescription. 12-year-old female.",
    )
    print(f"Added case with prescription_id: {pid}")
    cases = store.get_cases_for_patient("TestPatient01")
    print(f"Retrieved {len(cases)} case(s)")
    for c in cases:
        print(f"  {c['remedy']} {c['potency']} | status={c['status']} | outcome={c['outcome']}")
