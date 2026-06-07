"""
Billing Integration — Invoice & Insurance Tracking

Generate invoices, track payments, and manage insurance claim codes.
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class BillingIntegration:
    """
    Simple billing system for homeopathic consultations.
    Generates invoices and tracks payment status.
    """

    def __init__(self, db_path: str = "data/billing.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                case_id TEXT NOT NULL,
                invoice_number TEXT NOT NULL,
                date TEXT NOT NULL,
                line_items TEXT,  -- JSON array
                subtotal REAL,
                tax REAL,
                total REAL,
                status TEXT DEFAULT 'outstanding',  -- outstanding, paid, partial, cancelled
                payment_method TEXT,
                insurance_code TEXT,
                notes TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_invoice(self, case_id: str, line_items: List[Dict[str, Any]],
                       tax_rate: float = 0.0,
                       insurance_code: str = "",
                       notes: str = "") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        date = datetime.utcnow().strftime("%Y-%m-%d")
        invoice_num = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{case_id[:6]}"

        subtotal = sum(item.get("amount", 0) for item in line_items)
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "INSERT INTO invoices (case_id, invoice_number, date, line_items, subtotal, tax, total, insurance_code, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (case_id, invoice_num, date, json.dumps(line_items), subtotal, tax, total, insurance_code, notes, now)
        )
        inv_id = cur.lastrowid
        conn.commit()
        conn.close()

        return {
            "id": inv_id,
            "invoice_number": invoice_num,
            "case_id": case_id,
            "date": date,
            "line_items": line_items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "status": "outstanding",
        }

    def mark_paid(self, invoice_id: int, method: str = "") -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "UPDATE invoices SET status = 'paid', payment_method = ? WHERE id = ?",
            (method, invoice_id)
        )
        conn.commit()
        conn.close()
        return {"invoice_id": invoice_id, "status": "paid", "method": method}

    def get_invoices(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        if case_id:
            rows = conn.execute(
                "SELECT id, invoice_number, date, total, status FROM invoices WHERE case_id = ? ORDER BY date DESC",
                (case_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, invoice_number, date, total, status FROM invoices ORDER BY date DESC"
            ).fetchall()
        conn.close()
        return [{"id": r[0], "number": r[1], "date": r[2], "total": r[3], "status": r[4]} for r in rows]

    def get_outstanding_total(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute(
            "SELECT COALESCE(SUM(total), 0) FROM invoices WHERE status = 'outstanding'"
        ).fetchone()[0]
        count = conn.execute(
            "SELECT COUNT(*) FROM invoices WHERE status = 'outstanding'"
        ).fetchone()[0]
        conn.close()
        return {"outstanding_total": total, "outstanding_count": count}

    def standard_line_items(self) -> List[Dict[str, Any]]:
        return [
            {"code": "CONSULT_INITIAL", "description": "Initial Consultation (90 min)", "amount": 250.00},
            {"code": "CONSULT_FOLLOW", "description": "Follow-up Consultation (30 min)", "amount": 125.00},
            {"code": "CONSULT_ACUTE", "description": "Acute Consultation (15 min)", "amount": 75.00},
            {"code": "REMEDY", "description": "Homeopathic Remedy", "amount": 15.00},
            {"code": "SHIPPING", "description": "Shipping & Handling", "amount": 8.00},
        ]
