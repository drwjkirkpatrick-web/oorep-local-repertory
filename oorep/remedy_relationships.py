"""
Remedy Relationships

Models classical homeopathic remedy relationships:
- Complementary (completes the action of another remedy)
- Antidotal / Antidote (neutralizes or counteracts)
- Inimical (incompatible; do not follow well)
- Follows-well (good sequence)
- Comparative (similar remedy for comparison)

Even without full data, this module provides a starter dictionary
of ~50 classical relationships and persists custom additions in SQLite.

Usage:
    from oorep.remedy_relationships import RemedyRelationships
    rel = RemedyRelationships()
    rel.add_relationship("Ars.", "Rhus-t.", "complementary", "Boericke")
    print(rel.check_conflict("Nux-v.", "Puls."))
    print(rel.get_comparatives("Lyc."))
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


# Fallback for feedback DB path.
try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


# ── Classical starter dictionary (~50 entries) ─────────────────────────────
# Each entry: (remedy_a, remedy_b, rel_type, source)
# rel_type in: complementary, antidotal, antidote, inimical, follows-well, comparative
_CLASSICAL_RELATIONSHIPS: List[Tuple[str, str, str, str]] = [
    ("Ars.", "Rhus-t.", "complementary", "Clarke"),
    ("Ars.", "Nux-v.", "antidotal", "Hahnemann"),
    ("Puls.", "Nux-v.", "inimical", "Boericke"),
    ("Puls.", "Coff.", "inimical", "Boericke"),
    ("Puls.", "Lyc.", "complementary", "Allen"),
    ("Nux-v.", "Puls.", "inimical", "Boericke"),
    ("Nux-v.", "Ign.", "inimical", "Boericke"),
    ("Nux-v.", "Ars.", "antidotal", "Hahnemann"),
    ("Lyc.", "Puls.", "complementary", "Allen"),
    ("Lyc.", "Iod.", "follows-well", "Kent"),
    ("Lyc.", "Calc.", "complementary", "Hering"),
    ("Calc.", "Lyc.", "complementary", "Hering"),
    ("Calc.", "Rhus-t.", "follows-well", "Kent"),
    ("Sulph.", "Nux-v.", "follows-well", "Kent"),
    ("Sulph.", "Acon.", "antidotal", "Hahnemann"),
    ("Sulph.", "Puls.", "complementary", "Clarke"),
    ("Sil.", "Thuja", "complementary", "Hering"),
    ("Thuja", "Sil.", "complementary", "Hering"),
    ("Thuja", "Merc.", "follows-well", "Kent"),
    ("Merc.", "Nit-ac.", "complementary", "Allen"),
    ("Merc.", "Hep.", "complementary", "Hering"),
    ("Hep.", "Sil.", "follows-well", "Kent"),
    ("Hep.", "Merc.", "complementary", "Hering"),
    ("Bry.", "Rhus-t.", "antidotal", "Hahnemann"),
    ("Bry.", "Puls.", "follows-well", "Kent"),
    ("Rhus-t.", "Bry.", "antidotal", "Hahnemann"),
    ("Rhus-t.", "Calc.", "follows-well", "Kent"),
    ("Rhus-t.", "Ars.", "complementary", "Clarke"),
    ("Acon.", "Sulph.", "antidotal", "Hahnemann"),
    ("Acon.", "Coff.", "complementary", "Allen"),
    ("Coff.", "Acon.", "complementary", "Allen"),
    ("Coff.", "Puls.", "inimical", "Boericke"),
    ("Ign.", "Nux-v.", "inimical", "Boericke"),
    ("Nat-m.", "Ign.", "follows-well", "Kent"),
    ("Nat-m.", "Sep.", "complementary", "Hering"),
    ("Sep.", "Nat-m.", "complementary", "Hering"),
    ("Sep.", "Puls.", "inimical", "Boericke"),
    ("Phos.", "Ars.", "follows-well", "Kent"),
    ("Phos.", "Coff.", "complementary", "Clarke"),
    ("Caust.", "Staph.", "complementary", "Allen"),
    ("Staph.", "Caust.", "complementary", "Allen"),
    ("Lach.", "Crot-h.", "complementary", "Clarke"),
    ("Apis", "Puls.", "complementary", "Hering"),
    ("Apis", "Lach.", "complementary", "Clarke"),
    ("Ant-c.", "Sulph.", "follows-well", "Kent"),
    ("Cham.", "Puls.", "follows-well", "Kent"),
    ("Cina", "Calc.", "follows-well", "Kent"),
    ("Dros.", "Bry.", "follows-well", "Kent"),
    ("Graph.", "Lyc.", "follows-well", "Kent"),
    ("Kali-bi.", "Sep.", "follows-well", "Kent"),
    ("Kali-c.", "Nat-m.", "follows-well", "Kent"),
    ("Kreos.", "Ars.", "follows-well", "Kent"),
    ("Laur.", "Nux-v.", "follows-well", "Kent"),
    ("Mag-m.", "Phos.", "complementary", "Allen"),
    ("Mosch.", "Ign.", "complementary", "Clarke"),
    ("Nit-ac.", "Merc.", "complementary", "Allen"),
    ("Op.", "Nux-v.", "antidotal", "Hahnemann"),
    ("Samb.", "Ars.", "follows-well", "Kent"),
    ("Zinc.", "Puls.", "follows-well", "Kent"),
]

# Map rel_type -> reverse rel_type for symmetric lookups where appropriate
_REVERSE_MAP = {
    "complementary": "complementary",
    "antidotal": "antidote",
    "antidote": "antidotal",
    "inimical": "inimical",
    "follows-well": "precedes-well",
    "precedes-well": "follows-well",
    "comparative": "comparative",
}


@dataclass
class RelationshipRecord:
    remedy_a: str
    remedy_b: str
    rel_type: str
    source: str


class RemedyRelationships:
    """
    SQLite-backed remedy relationship manager with a classical starter set.

    The canonical store is feedback.db so that relationships live alongside
    prescriptions and outcomes.
    """

    _valid_types = frozenset(
        ["complementary", "antidotal", "antidote", "inimical", "follows-well", "precedes-well", "comparative"]
    )

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        # Seed once if empty
        self._seed_classical()

    def _init_db(self):
        """Create remedy_relationships table if missing."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS remedy_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy_a TEXT NOT NULL,
                remedy_b TEXT NOT NULL,
                rel_type TEXT NOT NULL,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rem_rel_a ON remedy_relationships(remedy_a)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rem_rel_b ON remedy_relationships(remedy_b)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rem_rel_type ON remedy_relationships(rel_type)"
        )
        conn.commit()
        conn.close()

    def _seed_classical(self):
        """Seed the classical starter set only if the table is empty."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM remedy_relationships")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        for a, b, rel_type, source in _CLASSICAL_RELATIONSHIPS:
            # Store ordered alphabetically by remedy so a < b is canonical
            a_norm = a.strip()
            b_norm = b.strip()
            if a_norm.lower() > b_norm.lower():
                a_norm, b_norm = b_norm, a_norm
            cursor.execute(
                "INSERT INTO remedy_relationships (remedy_a, remedy_b, rel_type, source) VALUES (?,?,?,?)",
                (a_norm, b_norm, rel_type, source),
            )
        conn.commit()
        conn.close()

    # ── Public API ───────────────────────────────────────────────────────────

    def add_relationship(
        self,
        remedy_a: str,
        remedy_b: str,
        rel_type: str,
        source: Optional[str] = None,
    ) -> int:
        """
        Register a remedy relationship.

        Args:
            remedy_a: First remedy abbreviation (e.g. "Ars.").
            remedy_b: Second remedy abbreviation.
            rel_type: One of complementary, antidotal, antidote, inimical,
                      follows-well, comparative.
            source: Optional classical source text (e.g. "Boericke").

        Returns:
            The row id of the inserted record.
        """
        rel_type = rel_type.lower().strip()
        if rel_type not in self._valid_types:
            raise ValueError(f"Invalid rel_type {rel_type}. Must be one of {sorted(self._valid_types)}")
        a_norm = remedy_a.strip()
        b_norm = remedy_b.strip()
        if a_norm.lower() > b_norm.lower():
            a_norm, b_norm = b_norm, a_norm
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO remedy_relationships (remedy_a, remedy_b, rel_type, source) VALUES (?,?,?,?)",
            (a_norm, b_norm, rel_type, source),
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id or 0

    def get_relationships(self, remedy: str, rel_type: Optional[str] = None) -> List[Dict]:
        """
        Return all relationships involving a given remedy.

        Args:
            remedy: Remedy abbreviation to query.
            rel_type: Optional filter by relationship type.

        Returns:
            List of relationship dicts with keys: remedy_a, remedy_b,
            rel_type, source, created_at.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        sql = (
            "SELECT remedy_a, remedy_b, rel_type, source, created_at "
            "FROM remedy_relationships WHERE (remedy_a = ? OR remedy_b = ?)"
        )
        params: Tuple = (remedy, remedy)
        if rel_type:
            sql += " AND rel_type = ?"
            params = (remedy, remedy, rel_type)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "remedy_a": r[0],
                "remedy_b": r[1],
                "rel_type": r[2],
                "source": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    def get_comparatives(self, remedy: str) -> List[Dict]:
        """Return all comparative relationships for a remedy."""
        return self.get_relationships(remedy, rel_type="comparative")

    def get_antidotes(self, remedy: str) -> List[Dict]:
        """
        Return antidotes for a remedy (both antidotal and antidote directions).

        Since the table stores canonical pairs, querying either direction
        returns the same row; we return the *partner* remedy in each case.
        """
        rows = self.get_relationships(remedy)
        out = []
        for r in rows:
            if r["rel_type"] in ("antidotal", "antidote"):
                partner = r["remedy_b"] if r["remedy_a"] == remedy else r["remedy_a"]
                out.append({"remedy": partner, **r})
        return out

    def check_conflict(self, remedy_a: str, remedy_b: str) -> Dict:
        """
        Check whether two remedies have a conflicting relationship
        (inimical, antidotal, antidote).

        Returns:
            Dict with keys:
                has_conflict: bool
                conflicts: list of conflicting relationship dicts
                severity: 'critical' for inimical, 'warning' for antidotal
        """
        a_norm = remedy_a.strip()
        b_norm = remedy_b.strip()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            (
                "SELECT remedy_a, remedy_b, rel_type, source, created_at "
                "FROM remedy_relationships WHERE "
                "((remedy_a = ? AND remedy_b = ?) OR (remedy_a = ? AND remedy_b = ?)) "
                "AND rel_type IN ('inimical','antidotal','antidote')"
            ),
            (a_norm, b_norm, b_norm, a_norm),
        )
        rows = cursor.fetchall()
        conn.close()
        conflicts = [
            {"remedy_a": r[0], "remedy_b": r[1], "rel_type": r[2], "source": r[3], "created_at": r[4]}
            for r in rows
        ]
        if any(c["rel_type"] == "inimical" for c in conflicts):
            severity = "critical"
        elif conflicts:
            severity = "warning"
        else:
            severity = "none"
        return {
            "has_conflict": len(conflicts) > 0,
            "conflicts": conflicts,
            "severity": severity,
        }

    def list_all(self, rel_type: Optional[str] = None, limit: int = 500) -> List[Dict]:
        """Return all stored relationships, optionally filtered by type."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        sql = (
            "SELECT remedy_a, remedy_b, rel_type, source, created_at "
            "FROM remedy_relationships"
        )
        params: Tuple = ()
        if rel_type:
            sql += " WHERE rel_type = ?"
            params = (rel_type,)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [
            {"remedy_a": r[0], "remedy_b": r[1], "rel_type": r[2], "source": r[3], "created_at": r[4]}
            for r in rows
        ]
