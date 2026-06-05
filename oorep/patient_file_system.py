"""
Patient File System — Feature #14

RadarOpus-inspired unified patient management.
Connects patients → consultations → SOAP notes → prescriptions → analyses.

Usage:
    from oorep.patient_file_system import PatientFileSystem
    pfs = PatientFileSystem()

    # Create a patient
    patient = pfs.create_patient({
        "pseudonym": "MrsJ2024",
        "gender": "F",
        "date_of_birth": "1985-03-15",
        "notes": "First visit — anxiety chief complaint"
    })

    # Start a consultation
    consult = pfs.create_consultation({
        "patient_pseudonym": "MrsJ2024",
        "consultation_type": "initial",
        "chief_complaint": "Anxiety with morning headache",
        "soap_case_id": "abc-123",          # from SOAPAssembler
        "prescription_id": "rx-456",        # from RemedyFeedbackStore
        "clipboard_ids": "[\"clip-1\"]",    # JSON list
        "analysis_snapshot": {...}         # JSON of repertorization results
    })

    # Query patient timeline
    timeline = pfs.get_patient_timeline("MrsJ2024")
"""

import json
import sqlite3
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class PatientFileSystem:
    """
    Unified patient file manager with consultation tracking.

    Creates two new tables in the existing feedback database:
      - ``patients``          — demographics + status
      - ``consultations``     — visits linking SOAP, prescriptions, clipboards, analyses

    Integrates with existing tables:
      - ``soap_notes``        (via soap_case_id)
      - ``prescriptions``     (via prescription_id)
      - ``clipboards``        (via clipboard_ids JSON)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Schema bootstrap ─────────────────────────────────────────────────────

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                pseudonym TEXT PRIMARY KEY,
                gender TEXT CHECK(gender IN ('M','F','O','U')),
                date_of_birth TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive','deceased','transferred')),
                notes TEXT,
                contact_consent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS consultations (
                consultation_id TEXT PRIMARY KEY,
                patient_pseudonym TEXT NOT NULL,
                consultation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                consultation_type TEXT DEFAULT 'followup' CHECK(consultation_type IN ('initial','acute','followup','emergency','review')),
                chief_complaint TEXT,
                practitioner_id TEXT,
                soap_case_id TEXT,
                prescription_id TEXT,
                clipboard_ids TEXT,
                analysis_snapshot TEXT,
                outcome_notes TEXT,
                next_visit_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_pseudonym) REFERENCES patients(pseudonym) ON DELETE CASCADE
            )
            """
        )

        # Indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_consult_patient ON consultations(patient_pseudonym)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_consult_date ON consultations(consultation_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_consult_type ON consultations(consultation_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_consult_soap ON consultations(soap_case_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_consult_rx ON consultations(prescription_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_patient_status ON patients(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_patient_last_seen ON patients(last_seen)"
        )

        conn.commit()
        conn.close()

    # ── Patient CRUD ───────────────────────────────────────────────────────

    def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new patient.

        Required: ``pseudonym``.
        Optional: gender, date_of_birth, notes, contact_consent.
        """
        pseudonym = patient_data.get("pseudonym")
        if not pseudonym:
            raise ValueError("pseudonym is required")

        now = datetime.now().isoformat()
        record = {
            "pseudonym": pseudonym,
            "gender": patient_data.get("gender", "U")[:1].upper() if patient_data.get("gender") else "U",
            "date_of_birth": patient_data.get("date_of_birth"),
            "first_seen": now,
            "last_seen": now,
            "status": patient_data.get("status", "active"),
            "notes": patient_data.get("notes", ""),
            "contact_consent": bool(patient_data.get("contact_consent")),
            "created_at": now,
            "updated_at": now,
        }

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO patients (pseudonym, gender, date_of_birth, first_seen, last_seen,
                                 status, notes, contact_consent, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["pseudonym"],
                record["gender"],
                record["date_of_birth"],
                record["first_seen"],
                record["last_seen"],
                record["status"],
                record["notes"],
                record["contact_consent"],
                record["created_at"],
                record["updated_at"],
            ),
        )
        conn.commit()
        conn.close()
        return record

    def get_patient(self, pseudonym: str) -> Optional[Dict[str, Any]]:
        """Retrieve patient record by pseudonym."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pseudonym, gender, date_of_birth, first_seen, last_seen, "
            "status, notes, contact_consent, created_at, updated_at "
            "FROM patients WHERE pseudonym = ?",
            (pseudonym,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "pseudonym": row[0],
            "gender": row[1],
            "date_of_birth": row[2],
            "first_seen": row[3],
            "last_seen": row[4],
            "status": row[5],
            "notes": row[6],
            "contact_consent": bool(row[7]),
            "created_at": row[8],
            "updated_at": row[9],
        }

    def update_patient(self, pseudonym: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update patient demographics or status.

        Allowed keys: gender, date_of_birth, status, notes, contact_consent.
        Automatically sets updated_at.
        """
        allowed = {"gender", "date_of_birth", "status", "notes", "contact_consent"}
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            raise ValueError("No allowed fields to update")

        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [pseudonym]

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE patients SET {set_clause} WHERE pseudonym = ?",
            values,
        )
        if cursor.rowcount == 0:
            conn.close()
            raise KeyError(f"Patient '{pseudonym}' not found")
        conn.commit()
        conn.close()
        return self.get_patient(pseudonym)

    def list_patients(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all patients, optionally filtered by status."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "SELECT pseudonym, gender, date_of_birth, first_seen, last_seen, "
                "status, notes, contact_consent, created_at, updated_at "
                "FROM patients WHERE status = ? ORDER BY last_seen DESC",
                (status,),
            )
        else:
            cursor.execute(
                "SELECT pseudonym, gender, date_of_birth, first_seen, last_seen, "
                "status, notes, contact_consent, created_at, updated_at "
                "FROM patients ORDER BY last_seen DESC"
            )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "pseudonym": r[0],
                "gender": r[1],
                "date_of_birth": r[2],
                "first_seen": r[3],
                "last_seen": r[4],
                "status": r[5],
                "notes": r[6],
                "contact_consent": bool(r[7]),
                "created_at": r[8],
                "updated_at": r[9],
            }
            for r in rows
        ]

    def delete_patient(self, pseudonym: str) -> bool:
        """Delete patient and cascade consultations. Returns True if deleted."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("DELETE FROM patients WHERE pseudonym = ?", (pseudonym,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ── Consultation CRUD ────────────────────────────────────────────────────

    def create_consultation(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Record a new consultation visit.

        Required: ``patient_pseudonym``.
        Optional: consultation_type, chief_complaint, practitioner_id,
                  soap_case_id, prescription_id, clipboard_ids (list),
                  analysis_snapshot (dict), outcome_notes, next_visit_date.
        """
        patient_pseudonym = data.get("patient_pseudonym")
        if not patient_pseudonym:
            raise ValueError("patient_pseudonym is required")

        # Verify patient exists
        if not self.get_patient(patient_pseudonym):
            raise KeyError(f"Patient '{patient_pseudonym}' not found. Create patient first.")

        consult_id = str(uuid.uuid4())[:12]
        now = datetime.now().isoformat()

        clipboard_ids = data.get("clipboard_ids", [])
        if isinstance(clipboard_ids, list):
            clipboard_ids = json.dumps(clipboard_ids)

        analysis_snapshot = data.get("analysis_snapshot")
        if isinstance(analysis_snapshot, dict):
            analysis_snapshot = json.dumps(analysis_snapshot)

        record = {
            "consultation_id": consult_id,
            "patient_pseudonym": patient_pseudonym,
            "consultation_date": data.get("consultation_date", now),
            "consultation_type": data.get("consultation_type", "followup"),
            "chief_complaint": data.get("chief_complaint", ""),
            "practitioner_id": data.get("practitioner_id", ""),
            "soap_case_id": data.get("soap_case_id"),
            "prescription_id": data.get("prescription_id"),
            "clipboard_ids": clipboard_ids,
            "analysis_snapshot": analysis_snapshot,
            "outcome_notes": data.get("outcome_notes", ""),
            "next_visit_date": data.get("next_visit_date"),
            "created_at": now,
            "updated_at": now,
        }

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO consultations (consultation_id, patient_pseudonym, consultation_date,
                consultation_type, chief_complaint, practitioner_id, soap_case_id,
                prescription_id, clipboard_ids, analysis_snapshot, outcome_notes,
                next_visit_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["consultation_id"],
                record["patient_pseudonym"],
                record["consultation_date"],
                record["consultation_type"],
                record["chief_complaint"],
                record["practitioner_id"],
                record["soap_case_id"],
                record["prescription_id"],
                record["clipboard_ids"],
                record["analysis_snapshot"],
                record["outcome_notes"],
                record["next_visit_date"],
                record["created_at"],
                record["updated_at"],
            ),
        )

        # Update patient's last_seen
        cursor.execute(
            "UPDATE patients SET last_seen = ? WHERE pseudonym = ?",
            (record["consultation_date"], patient_pseudonym),
        )

        conn.commit()
        conn.close()
        return self.get_consultation(consult_id)

    def get_consultation(self, consult_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single consultation by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT consultation_id, patient_pseudonym, consultation_date, consultation_type, "
            "chief_complaint, practitioner_id, soap_case_id, prescription_id, "
            "clipboard_ids, analysis_snapshot, outcome_notes, next_visit_date, "
            "created_at, updated_at FROM consultations WHERE consultation_id = ?",
            (consult_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_consultation(row)

    def list_consultations(
        self,
        patient_pseudonym: Optional[str] = None,
        consult_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List consultations, optionally filtered by patient or type."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        conditions = []
        params = []
        if patient_pseudonym:
            conditions.append("patient_pseudonym = ?")
            params.append(patient_pseudonym)
        if consult_type:
            conditions.append("consultation_type = ?")
            params.append(consult_type)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor.execute(
            f"SELECT consultation_id, patient_pseudonym, consultation_date, consultation_type, "
            f"chief_complaint, practitioner_id, soap_case_id, prescription_id, "
            f"clipboard_ids, analysis_snapshot, outcome_notes, next_visit_date, "
            f"created_at, updated_at FROM consultations {where} "
            f"ORDER BY consultation_date DESC LIMIT ?",
            params + [limit],
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_consultation(r) for r in rows]

    def update_consultation(self, consult_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update consultation fields. Allowed: all except consultation_id, patient_pseudonym, created_at."""
        blocked = {"consultation_id", "patient_pseudonym", "created_at"}
        fields = {k: v for k, v in updates.items() if k not in blocked}
        if not fields:
            raise ValueError("No allowed fields to update")

        # JSON-serialize lists/dicts
        if "clipboard_ids" in fields and isinstance(fields["clipboard_ids"], list):
            fields["clipboard_ids"] = json.dumps(fields["clipboard_ids"])
        if "analysis_snapshot" in fields and isinstance(fields["analysis_snapshot"], dict):
            fields["analysis_snapshot"] = json.dumps(fields["analysis_snapshot"])

        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [consult_id]

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE consultations SET {set_clause} WHERE consultation_id = ?",
            values,
        )
        if cursor.rowcount == 0:
            conn.close()
            raise KeyError(f"Consultation '{consult_id}' not found")
        conn.commit()
        conn.close()
        return self.get_consultation(consult_id)

    def delete_consultation(self, consult_id: str) -> bool:
        """Delete a consultation. Returns True if deleted."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM consultations WHERE consultation_id = ?", (consult_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ── Patient Timeline (aggregate view) ────────────────────────────────────

    def get_patient_timeline(self, pseudonym: str) -> Dict[str, Any]:
        """
        Build a complete patient timeline:
          - patient demographics
          - all consultations (newest first)
          - prescription count from linked consultations
          - days since first visit
        """
        patient = self.get_patient(pseudonym)
        if not patient:
            raise KeyError(f"Patient '{pseudonym}' not found")

        consultations = self.list_consultations(patient_pseudonym=pseudonym, limit=100)

        # Count prescriptions linked to consultations
        rx_count = sum(1 for c in consultations if c.get("prescription_id"))

        # Days since first visit
        try:
            first_seen_dt = datetime.fromisoformat(patient["first_seen"])
            days_in_practice = (datetime.now() - first_seen_dt).days
        except Exception:
            days_in_practice = None

        return {
            "patient": patient,
            "consultation_count": len(consultations),
            "prescription_count": rx_count,
            "days_in_practice": days_in_practice,
            "consultations": consultations,
        }

    def get_patient_chief_complaints(self, pseudonym: str) -> List[str]:
        """Return all recorded chief complaints across consultations."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT chief_complaint FROM consultations "
            "WHERE patient_pseudonym = ? AND chief_complaint != '' "
            "ORDER BY consultation_date DESC",
            (pseudonym,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows if r[0]]

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _row_to_consultation(self, row) -> Dict[str, Any]:
        clipboard_ids = row[8]
        analysis_snapshot = row[9]
        try:
            clipboard_ids = json.loads(clipboard_ids) if clipboard_ids else []
        except Exception:
            clipboard_ids = clipboard_ids or []
        try:
            analysis_snapshot = json.loads(analysis_snapshot) if analysis_snapshot else None
        except Exception:
            analysis_snapshot = analysis_snapshot
        return {
            "consultation_id": row[0],
            "patient_pseudonym": row[1],
            "consultation_date": row[2],
            "consultation_type": row[3],
            "chief_complaint": row[4],
            "practitioner_id": row[5],
            "soap_case_id": row[6],
            "prescription_id": row[7],
            "clipboard_ids": clipboard_ids,
            "analysis_snapshot": analysis_snapshot,
            "outcome_notes": row[10],
            "next_visit_date": row[11],
            "created_at": row[12],
            "updated_at": row[13],
        }
