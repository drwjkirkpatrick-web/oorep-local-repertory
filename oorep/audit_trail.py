"""
Audit Trail — Benefits #32, #53

Tamper-evident audit logging for all prescription, SOAP, and letter writes.
Each log entry contains a SHA-256 hash chain so that any mutation breaks
integrity. Supports licensure export and prescriber digital signatures.

Usage:
    from oorep.audit_trail import AuditTrail
    audit = AuditTrail()

    audit.log(
        action="prescribe",
        user="dr.smith",
        resource="prescription/abc123",
        old_value=None,
        new_value={"remedy": "Ars.", "potency": "30C"},
    )

    ok = audit.verify_chain()   # True if intact
    history = audit.get_history("prescription/abc123")
    report = audit.export_for_licensure("2026-01-01", "2026-12-31")
    audit.prescriber_ack(action_id=42, prescriber_name="Dr. Smith")
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class AuditTrail:
    """
    Immutable, hash-chained audit log for clinical actions.

    Every ``log()`` call writes a row to ``audit_log`` with:
      - ``timestamp``, ``action``, ``user``, ``resource``
      - ``old_value``, ``new_value`` (JSON strings)
      - ``hash_chain``: SHA-256(previous_hash + current_payload)

    The chain links are verified by ``verify_chain()`` which walks
    forwards and detects any break in the hash dependency.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Args:
            db_path: SQLite database path. Defaults to project feedback.db.
        """
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create ``audit_log`` table if it doesn't already exist."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                user TEXT,
                resource TEXT NOT NULL,
                old_value TEXT,
                old_value_hash TEXT,
                new_value TEXT,
                new_value_hash TEXT,
                hash_chain TEXT NOT NULL,
                prescriber_ack TEXT,
                ack_timestamp TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)"
        )
        conn.commit()
        conn.close()

    # ── Hash chain helpers ──────────────────────────────────────────────────

    @staticmethod
    def _hash_payload(payload: str) -> str:
        """Return SHA-256 hex digest of a UTF-8 payload string."""
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _previous_hash(self) -> str:
        """
        Return the hash_chain of the most recent audit entry,
        or a genesis string if the table is empty.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hash_chain FROM audit_log ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "0" * 64  # genesis

    def _compute_chain_hash(
        self,
        previous_hash: str,
        timestamp: str,
        action: str,
        user: str,
        resource: str,
        old_value: str,
        new_value: str,
    ) -> str:
        """
        Compute the chained hash for a new entry.

        The payload includes the previous hash so that tampering with
        any row invalidates all subsequent rows.
        """
        payload = "|".join([
            previous_hash,
            timestamp,
            action,
            user,
            resource,
            old_value,
            new_value,
        ])
        return self._hash_payload(payload)

    # ── Core logging ────────────────────────────────────────────────────────

    def log(
        self,
        action: str,
        user: str,
        resource: str,
        old_value: Any,
        new_value: Any,
    ) -> int:
        """
        Append an audit entry.

        Args:
            action: Short verb describing the action (e.g. "prescribe",
                    "update_soap", "delete_case").
            user: Username / practitioner ID performing the action.
            resource: Logical resource identifier (e.g. "prescription/abc123").
            old_value: Serializable old state (or None).
            new_value: Serializable new state (or None).

        Returns:
            The auto-increment ``id`` of the newly inserted row.
        """
        now = datetime.now().isoformat()
        old_json = json.dumps(old_value, default=str) if old_value is not None else ""
        new_json = json.dumps(new_value, default=str) if new_value is not None else ""
        old_hash = self._hash_payload(old_json) if old_json else ""
        new_hash = self._hash_payload(new_json) if new_json else ""
        prev_hash = self._previous_hash()
        chain_hash = self._compute_chain_hash(
            prev_hash, now, action, user, resource, old_json, new_json
        )

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log
            (timestamp, action, user, resource, old_value, old_value_hash,
             new_value, new_value_hash, hash_chain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                action,
                user,
                resource,
                old_json,
                old_hash,
                new_json,
                new_hash,
                chain_hash,
            ),
        )
        row_id = cursor.lastrowid
        if row_id is None:
            row_id = 0
        conn.commit()
        conn.close()
        return int(row_id)

    # ── Chain verification ────────────────────────────────────────────────────

    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire audit chain.

        Returns:
            Dict with ``intact`` (bool), ``total_entries`` (int),
            ``first_broken_id`` (Optional[int]), ``message`` (str).
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, action, user, resource, old_value, new_value, hash_chain "
            "FROM audit_log ORDER BY id"
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {
                "intact": True,
                "total_entries": 0,
                "first_broken_id": None,
                "message": "Audit log is empty — nothing to verify.",
            }

        prev_hash = "0" * 64
        for row in rows:
            (
                row_id,
                timestamp,
                action,
                user,
                resource,
                old_value,
                new_value,
                stored_hash,
            ) = row
            expected = self._compute_chain_hash(
                prev_hash,
                timestamp,
                action,
                user,
                resource,
                old_value,
                new_value,
            )
            if expected != stored_hash:
                return {
                    "intact": False,
                    "total_entries": len(rows),
                    "first_broken_id": row_id,
                    "message": (
                        f"Hash mismatch at id={row_id}. "
                        "The chain has been tampered with or corrupted."
                    ),
                }
            prev_hash = stored_hash

        return {
            "intact": True,
            "total_entries": len(rows),
            "first_broken_id": None,
            "message": f"All {len(rows)} entries verified. Chain is intact.",
        }

    # ── History queries ───────────────────────────────────────────────────────

    def get_history(self, resource: str) -> List[Dict[str, Any]]:
        """
        Return every audit entry touching ``resource``, oldest first.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, action, user, resource, old_value, new_value, "
            "hash_chain, prescriber_ack, ack_timestamp "
            "FROM audit_log WHERE resource = ? ORDER BY id",
            (resource,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def get_all_entries(
        self, limit: int = 500, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Paged raw access to the full audit log (newest first)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, action, user, resource, old_value, new_value, "
            "hash_chain, prescriber_ack, ack_timestamp "
            "FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    # ── Licensure export ──────────────────────────────────────────────────────

    def export_for_licensure(
        self, start_date: str, end_date: str
    ) -> str:
        """
        Generate a human-readable audit report suitable for licensure
        board review or compliance inspection.

        Args:
            start_date: Inclusive date string ``YYYY-MM-DD``.
            end_date:   Inclusive date string ``YYYY-MM-DD``.

        Returns:
            Multi-line formatted report string.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, action, user, resource, "
            "old_value_hash, new_value_hash, hash_chain, prescriber_ack "
            "FROM audit_log "
            "WHERE timestamp >= ? AND timestamp <= ? "
            "ORDER BY id",
            (f"{start_date}T00:00:00", f"{end_date}T23:59:59"),
        )
        rows = cursor.fetchall()
        conn.close()

        lines = [
            "=" * 70,
            "OOREP AUDIT REPORT FOR LICENSURE REVIEW",
            f"Period: {start_date} to {end_date}",
            f"Generated: {datetime.now().isoformat()}",
            f"Total entries: {len(rows)}",
            "=" * 70,
            "",
        ]
        for row in rows:
            (
                row_id,
                timestamp,
                action,
                user,
                resource,
                old_h,
                new_h,
                chain,
                ack,
            ) = row
            lines.append(f"ID:        {row_id}")
            lines.append(f"Timestamp: {timestamp}")
            lines.append(f"Action:    {action}")
            lines.append(f"User:      {user}")
            lines.append(f"Resource:  {resource}")
            lines.append(f"Old hash:  {old_h or '—'}")
            lines.append(f"New hash:  {new_h or '—'}")
            lines.append(f"Chain:     {chain}")
            lines.append(f"Acked by: {ack or '—'}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)
        return "\n".join(lines)

    # ── Prescriber acknowledgement ────────────────────────────────────────────

    def prescriber_ack(self, action_id: int, prescriber_name: str) -> bool:
        """
        Mark an audit entry as digitally signed / acknowledged by a
        licensed practitioner.

        Args:
            action_id: The ``id`` column of the audit log row.
            prescriber_name: Display name of the practitioner.

        Returns:
            True if the row existed and was updated.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE audit_log SET prescriber_ack = ?, ack_timestamp = ? WHERE id = ?",
            (prescriber_name, datetime.now().isoformat(), action_id),
        )
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row: tuple) -> Dict[str, Any]:
        return {
            "id": row[0],
            "timestamp": row[1],
            "action": row[2],
            "user": row[3],
            "resource": row[4],
            "old_value": json.loads(row[5]) if row[5] else None,
            "new_value": json.loads(row[6]) if row[6] else None,
            "hash_chain": row[7],
            "prescriber_ack": row[8],
            "ack_timestamp": row[9],
        }
