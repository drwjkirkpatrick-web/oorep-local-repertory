"""
Practitioner Approval Gate

Enforces prescriber_ack before any remedy recommendation is recorded.
This is a clinical safety guardrail: the AI can suggest, but it cannot
log a prescription without explicit practitioner approval.

Usage:
    from oorep.practitioner_approval_gate import PractitionerApprovalGate, ApprovalRequired
    gate = PractitionerApprovalGate()
    try:
        gate.require_approval(prescriber_ack=True)
    except ApprovalRequired as e:
        # Trigger Hermes clarify() or HITL prompt
        print(f"Approval needed: {e.reason}")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ApprovalRecord:
    action: str           # "prescription", "repertorization_advice", "remedy_lookup"
    remedy_abbrev: Optional[str]
    patient_id: Optional[str]
    practitioner_id: str
    prescriber_ack: bool
    timestamp: str
    notes: Optional[str]


class ApprovalRequired(Exception):
    """Raised when prescriber acknowledgement is missing."""
    def __init__(self, action: str, remedy: Optional[str] = None, patient: Optional[str] = None,
                 reason: str = "Prescriber acknowledgment required"):
        self.action = action
        self.remedy = remedy
        self.patient = patient
        self.reason = reason
        super().__init__(f"[{action}] {reason} — remedy={remedy} patient={patient}")


class PractitionerApprovalGate:
    """
    Clinical safety gate for practitioner oversight.
    
    Modes:
        strict (default): Raises ApprovalRequired if prescriber_ack is False.
        audit_only:  Records but does not block; logs all decisions.
        test_mode:   Always passes (for pytest, CI, development).
    """

    def __init__(self, mode: str = "strict", log_db_path = None,
                 practitioner_id: str = "unknown"):
        self.mode = mode.lower().strip()
        self.practitioner_id = practitioner_id
        if log_db_path is None:
            log_db_path = Path(__file__).resolve().parent.parent / "data" / "approval_audit.db"
        else:
            log_db_path = Path(log_db_path)
        self.log_db_path = log_db_path
        self.log_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_log_db()

    def _init_log_db(self):
        conn = sqlite3.connect(str(self.log_db_path))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                action TEXT,
                remedy_abbrev TEXT,
                patient_id TEXT,
                practitioner_id TEXT,
                prescriber_ack INTEGER,
                decision TEXT,        -- "approved", "denied", "test_pass"
                notes TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def _log(self, record: ApprovalRecord, decision: str):
        conn = sqlite3.connect(str(self.log_db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO approval_decisions
            (timestamp, action, remedy_abbrev, patient_id, practitioner_id, prescriber_ack, decision, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.timestamp,
            record.action,
            record.remedy_abbrev,
            record.patient_id,
            record.practitioner_id,
            1 if record.prescriber_ack else 0,
            decision,
            record.notes,
        ))
        conn.commit()
        conn.close()

    def require_approval(
        self,
        action: str,
        prescriber_ack: bool,
        remedy_abbrev: Optional[str] = None,
        patient_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Validate prescriber approval for an action.

        Args:
            action: Description of the action (e.g. "prescription")
            prescriber_ack: True if practitioner has explicitly approved
            remedy_abbrev: Optional remedy involved
            patient_id: Optional patient pseudonym
            notes: Optional context for audit log

        Returns:
            True if approved

        Raises:
            ApprovalRequired: If ack is False and mode is strict.
        """
        record = ApprovalRecord(
            action=action,
            remedy_abbrev=remedy_abbrev,
            patient_id=patient_id,
            practitioner_id=self.practitioner_id,
            prescriber_ack=prescriber_ack,
            timestamp=datetime.now().isoformat(),
            notes=notes,
        )

        if self.mode == "test_mode":
            self._log(record, "test_pass")
            return True

        if prescriber_ack:
            self._log(record, "approved")
            return True

        self._log(record, "denied")

        if self.mode == "audit_only":
            return True  # Logged but not blocked

        # strict mode — raise
        raise ApprovalRequired(
            action=action,
            remedy=remedy_abbrev,
            patient=patient_id,
            reason="Prescriber acknowledgment required before proceeding",
        )

    def approve(self, action: str, remedy_abbrev: Optional[str] = None,
                patient_id: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """
        Explicit approval helper — use when practitioner confirms via Hermes clarify().
        """
        return self.require_approval(
            action=action,
            prescriber_ack=True,
            remedy_abbrev=remedy_abbrev,
            patient_id=patient_id,
            notes=notes,
        )

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Return recent approval decisions for audit review."""
        conn = sqlite3.connect(str(self.log_db_path))
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, action, remedy_abbrev, patient_id, practitioner_id,
                   prescriber_ack, decision, notes
            FROM approval_decisions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "timestamp": r[0],
                "action": r[1],
                "remedy_abbrev": r[2],
                "patient_id": r[3],
                "practitioner_id": r[4],
                "prescriber_ack": bool(r[5]),
                "decision": r[6],
                "notes": r[7],
            }
            for r in rows
        ]


def require_ack(action: str, prescriber_ack: bool, remedy_abbrev: Optional[str] = None,
                patient_id: Optional[str] = None) -> bool:
    """One-liner convenience. Default strict mode."""
    gate = PractitionerApprovalGate()
    return gate.require_approval(action, prescriber_ack, remedy_abbrev, patient_id)
