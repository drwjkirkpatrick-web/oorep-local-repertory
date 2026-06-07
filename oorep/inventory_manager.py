"""
Inventory Manager — Remedy Stock & Pharmacy Tracking

Track remedy stock levels, expiry dates, and potency availability.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class InventoryManager:
    """
    Manage homeopathic remedy inventory: stock levels,
    expiry tracking, and reorder alerts.
    """

    def __init__(self, db_path: str = "data/inventory.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                remedy TEXT NOT NULL,
                potency TEXT NOT NULL,
                form TEXT DEFAULT "pellet",  -- pellet, liquid, tablet, cream
                quantity INTEGER DEFAULT 0,
                unit TEXT DEFAULT "grams",
                batch_number TEXT,
                manufacturer TEXT,
                expiry_date TEXT,
                reorder_level INTEGER DEFAULT 10,
                location TEXT,
                notes TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INTEGER PRIMARY KEY,
                inventory_id INTEGER,
                transaction_type TEXT,  -- received, dispensed, adjusted, expired
                quantity_change INTEGER,
                reason TEXT,
                practitioner TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_stock(self, remedy: str, potency: str, quantity: int,
                  form: str = "pellet", batch: str = "", expiry: str = "",
                  manufacturer: str = "", reorder_level: int = 10,
                  location: str = "", notes: str = "") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "INSERT INTO inventory (remedy, potency, form, quantity, batch_number, manufacturer, expiry_date, reorder_level, location, notes, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (remedy, potency, form, quantity, batch, manufacturer, expiry, reorder_level, location, notes, now)
        )
        inv_id = cur.lastrowid
        conn.execute(
            "INSERT INTO inventory_transactions (inventory_id, transaction_type, quantity_change, reason, created_at) VALUES (?,?,?,?,?)",
            (inv_id, "received", quantity, "Initial stock", now)
        )
        conn.commit()
        conn.close()
        return {"id": inv_id, "remedy": remedy, "potency": potency, "quantity": quantity}

    def dispense(self, inventory_id: int, quantity: int,
                 reason: str = "", practitioner: str = "") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "UPDATE inventory SET quantity = quantity - ?, updated_at = ? WHERE id = ?",
            (quantity, now, inventory_id)
        )
        conn.execute(
            "INSERT INTO inventory_transactions (inventory_id, transaction_type, quantity_change, reason, practitioner, created_at) VALUES (?,?,?,?,?,?)",
            (inventory_id, "dispensed", -quantity, reason, practitioner, now)
        )
        conn.commit()
        conn.close()
        return {"inventory_id": inventory_id, "dispensed": quantity, "reason": reason}

    def get_stock(self, remedy: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        if remedy:
            rows = conn.execute(
                "SELECT id, remedy, potency, form, quantity, expiry_date, reorder_level, location FROM inventory WHERE remedy = ? ORDER BY potency",
                (remedy,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, remedy, potency, form, quantity, expiry_date, reorder_level, location FROM inventory ORDER BY remedy, potency"
            ).fetchall()
        conn.close()
        return [
            {
                "id": r[0], "remedy": r[1], "potency": r[2], "form": r[3],
                "quantity": r[4], "expiry": r[5], "reorder_level": r[6], "location": r[7]
            }
            for r in rows
        ]

    def get_low_stock(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT id, remedy, potency, quantity, reorder_level FROM inventory WHERE quantity <= reorder_level ORDER BY remedy"
        ).fetchall()
        conn.close()
        return [{"id": r[0], "remedy": r[1], "potency": r[2], "quantity": r[3], "reorder": r[4]} for r in rows]

    def get_expiring(self, days: int = 90) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT id, remedy, potency, expiry_date, quantity FROM inventory WHERE expiry_date <= ? AND expiry_date IS NOT NULL ORDER BY expiry_date",
            (cutoff,)
        ).fetchall()
        conn.close()
        return [{"id": r[0], "remedy": r[1], "potency": r[2], "expiry": r[3], "quantity": r[4]} for r in rows]

    def stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        total_items = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        total_quantity = conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM inventory").fetchone()[0]
        low = conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity <= reorder_level").fetchone()[0]
        conn.close()
        return {"total_items": total_items, "total_quantity": total_quantity, "low_stock_count": low}
