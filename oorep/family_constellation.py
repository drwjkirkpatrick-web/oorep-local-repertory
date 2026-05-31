"""
Family Constellation Analysis

Tracks remedy patterns, suppression history, and constitutional themes across
family members. Useful in miasmatic and hereditary prescribing where the
family remedy picture reveals deeper layers than the individual case alone.

Usage:
    from oorep.family_constellation import FamilyConstellation
    fc = FamilyConstellation()
    fc.add_family_member("fam-001", "Parent A", "mother", case_notes={"remedy_history": ["Puls.", "Sep."]})
    patterns = fc.get_family_remedy_patterns("fam-001")
    chain = fc.get_suppression_chain("fam-001")
    constellation = fc.find_constellation("fam-001")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter
from datetime import datetime


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class FamilyConstellation:
    """
    SQLite-backed family constellation manager.

    Stores family members (pseudonymised), their relationships, remedy histories,
    and suppression histories so that cross-family prescribing patterns can be
    mined and miasmatic threads traced.
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
            CREATE TABLE IF NOT EXISTS family_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                pseudonym TEXT NOT NULL,
                relationship TEXT,
                remedy_history_json TEXT,
                suppression_history_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_family_id ON family_cases(family_id)"
        )
        conn.commit()
        conn.close()

    # ── Public API ───────────────────────────────────────────────────────────

    def add_family_member(
        self,
        family_id: str,
        pseudonym: str,
        relationship: Optional[str] = None,
        case_notes: Optional[Dict] = None,
    ) -> int:
        """
        Add a family member record.

        Args:
            family_id: Practitioner-defined family identifier (e.g. "fam-001").
            pseudonym: Patient pseudonym within the family.
            relationship: E.g. "mother", "father", "child", "sibling", "grandparent".
            case_notes: Dict that may contain keys:
                - remedy_history: list of remedy abbrev strings
                - suppression_history: list of dicts with keys
                  suppressed_symptom, suppressing_agent, date, recurrence

        Returns:
            The inserted row id.
        """
        case_notes = case_notes or {}
        remedy_history = json.dumps(case_notes.get("remedy_history", []))
        suppression_history = json.dumps(case_notes.get("suppression_history", []))
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO family_cases
            (family_id, pseudonym, relationship, remedy_history_json, suppression_history_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (family_id, pseudonym, relationship, remedy_history, suppression_history, now, now),
        )
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id or 0

    def update_family_member(
        self,
        family_id: str,
        pseudonym: str,
        case_notes: Dict,
    ) -> bool:
        """
        Overwrite remedy_history and suppression_history for a family member.
        """
        remedy_history = json.dumps(case_notes.get("remedy_history", []))
        suppression_history = json.dumps(case_notes.get("suppression_history", []))
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE family_cases
            SET remedy_history_json = ?,
                suppression_history_json = ?,
                updated_at = ?
            WHERE family_id = ? AND pseudonym = ?
            """,
            (remedy_history, suppression_history, now, family_id, pseudonym),
        )
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return changed

    def get_family_members(self, family_id: str) -> List[Dict]:
        """Return all member records for a family."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT family_id, pseudonym, relationship, remedy_history_json, suppression_history_json, created_at, updated_at "
            "FROM family_cases WHERE family_id = ? ORDER BY created_at",
            (family_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def get_family_remedy_patterns(self, family_id: str) -> Dict:
        """
        Return remedies used across the family with frequency counts.

        Returns:
            Dict with:
                family_id: str
                member_count: int
                remedy_counts: Dict[str, int]
                most_common: List[str]
                remedy_set: List[str]
        """
        members = self.get_family_members(family_id)
        counter: Counter = Counter()
        for m in members:
            for r in m.get("remedy_history", []):
                counter[r.strip()] += 1
        most_common = [r for r, _ in counter.most_common()]
        return {
            "family_id": family_id,
            "member_count": len(members),
            "remedy_counts": dict(counter),
            "most_common": most_common,
            "remedy_set": sorted(set(counter.keys())),
        }

    def get_suppression_chain(self, family_id: str) -> List[Dict]:
        """
        Trace suppression history through the family.

        Returns a list of suppression events across all family members,
        ordered by date (if present) or by member pseudonym fallback.
        """
        members = self.get_family_members(family_id)
        chain: List[Dict] = []
        for m in members:
            for event in m.get("suppression_history", []):
                chain.append({
                    "family_member": m["pseudonym"],
                    "relationship": m["relationship"],
                    **event,
                })
        # Sort by date if available
        chain.sort(key=lambda x: x.get("date", "") or "")
        return chain

    def find_constellation(self, family_id: str) -> Dict:
        """
        Identify remedy themes across family members.

        A "constellation" is a grouping of remedies that recur across
        multiple members, suggesting a shared miasmatic or constitutional
        thread.

        Returns:
            Dict with:
                family_id: str
                constellation_size: int
                shared_themes: List[str]
                suppression_signals: List[str]
                miasmatic_hints: List[str]
                narrative: str
        """
        patterns = self.get_family_remedy_patterns(family_id)
        chain = self.get_suppression_chain(family_id)
        remedies = set(patterns["remedy_set"])

        # Simple heuristics for "themes"
        shared_themes: List[str] = []
        if any(r in remedies for r in ("Puls.", "Sep.", "Nat-m.", "Ign.", "Coff.")):
            shared_themes.append("Emotional/psychic sensitivity cluster")
        if any(r in remedies for r in ("Sulph.", "Psor.", "Graph.", "Mez.")):
            shared_themes.append("Psoric / suppressed skin cluster")
        if any(r in remedies for r in ("Thuja", "Med.", "Nit-ac.", "Merc.")):
            shared_themes.append("Sycotic / foreign-body / growth cluster")
        if any(r in remedies for r in ("Aur.", "Syph.", "Lach.", "Kali-i.")):
            shared_themes.append("Syphilitic / destructive / deep-bone cluster")
        if any(r in remedies for r in ("Calc.", "Sil.", "Bary-c.", "Bar-c.")):
            shared_themes.append("Developmental / structural / glandular cluster")
        if any(r in remedies for r in ("Ars.", "Phos.", "Lyc.", "Carb-v.")):
            shared_themes.append("Anxiety / collapse / metabolic cluster")

        suppression_signals: List[str] = []
        for event in chain:
            agent = event.get("suppressing_agent", "")
            if isinstance(agent, str) and agent:
                suppression_signals.append(f"{event['family_member']}: suppressed '{event.get('suppressed_symptom','?')}' with {agent}")

        # Miasmatic hints from remedy set overlap
        miasmatic_hints: List[str] = []
        if len(patterns.get("remedy_counts", {})) > 5:
            miasmatic_hints.append("Polypharmacy or complex miasmatic layering")
        if patterns.get("most_common"):
            top = patterns["most_common"][0]
            miasmatic_hints.append(f"Most frequent family remedy: {top}")

        narrative = (
            f"Family {family_id} has {patterns['member_count']} recorded members. "
            f"{len(patterns['remedy_set'])} distinct remedies have been used. "
            f"Top remedy: {patterns['most_common'][0] if patterns['most_common'] else 'N/A'}. "
            f"{len(suppression_signals)} suppression events recorded."
        )

        return {
            "family_id": family_id,
            "constellation_size": len(patterns["remedy_set"]),
            "shared_themes": shared_themes,
            "suppression_signals": suppression_signals,
            "miasmatic_hints": miasmatic_hints,
            "narrative": narrative,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row) -> Dict:
        return {
            "family_id": row[0],
            "pseudonym": row[1],
            "relationship": row[2],
            "remedy_history": json.loads(row[3]) if row[3] else [],
            "suppression_history": json.loads(row[4]) if row[4] else [],
            "created_at": row[5],
            "updated_at": row[6],
        }
