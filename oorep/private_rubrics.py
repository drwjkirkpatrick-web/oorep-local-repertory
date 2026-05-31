"""
Private Rubrics Manager

Allows practitioners to create custom rubrics that do not exist in the
standard OOREP repertory. Private rubrics live in a local SQLite table,
are attributed to the creating user, and can be integrated into
repertorization alongside standard rubrics.

Usage:
    from oorep.private_rubrics import PrivateRubricManager
    mgr = PrivateRubricManager()
    rubric_id = mgr.create_private_rubric(
        fullpath="Mind; Anxiety; Health; About one's own health (custom)",
        remedy_abbrevs={"Ars.": 3, "Acon.": 2, "Nux-v.": 1},
        practitioner_id="dr.walker",
        note="Clinic observation from 3 cured cases"
    )
"""

import json
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class PrivateRubric:
    private_rubric_id: str
    fullpath: str
    source: str          # Always "private"
    remedy_abbrevs: Dict[str, int]  # {"Ars.": 3, ...}
    practitioner_id: str
    note: Optional[str]
    created_at: str
    is_active: bool


class PrivateRubricManager:
    """SQLite-backed storage for practitioner-created private rubrics."""

    def __init__(self, db_path = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent / "data" / "private_rubrics.db"
        else:
            db_path = Path(db_path)
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS private_rubrics (
                private_rubric_id TEXT PRIMARY KEY,
                fullpath TEXT NOT NULL,
                source TEXT DEFAULT 'private',
                remedy_abbrevs TEXT NOT NULL,    -- JSON {"abbrev": weight}
                practitioner_id TEXT NOT NULL,
                note TEXT,
                created_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_private_practitioner
            ON private_rubrics(practitioner_id)
        ''')
        conn.commit()
        conn.close()

    def create_private_rubric(
        self,
        fullpath: str,
        remedy_abbrevs: Dict[str, int],
        practitioner_id: str,
        note: Optional[str] = None,
    ) -> str:
        """Create a new private rubric and return its ID."""
        rid = f"priv_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO private_rubrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rid, fullpath, "private", json.dumps(remedy_abbrevs), practitioner_id, note, now, 1))
        conn.commit()
        conn.close()
        return rid

    def get_private_rubric(self, rubric_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM private_rubrics WHERE private_rubric_id = ?', (rubric_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def list_private_rubrics(self, practitioner_id: Optional[str] = None,
                              limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if practitioner_id:
            cursor.execute(
                'SELECT * FROM private_rubrics WHERE practitioner_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT ?',
                (practitioner_id, limit),
            )
        else:
            cursor.execute(
                'SELECT * FROM private_rubrics WHERE is_active = 1 ORDER BY created_at DESC LIMIT ?',
                (limit,),
            )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def deactivate_private_rubric(self, rubric_id: str) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('UPDATE private_rubrics SET is_active = 0 WHERE private_rubric_id = ?', (rubric_id,))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def delete_private_rubric(self, rubric_id: str) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('DELETE FROM private_rubrics WHERE private_rubric_id = ?', (rubric_id,))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def _row_to_dict(self, row) -> Dict:
        return {
            "private_rubric_id": row[0],
            "fullpath": row[1],
            "source": row[2],
            "remedy_abbrevs": json.loads(row[3]),
            "practitioner_id": row[4],
            "note": row[5],
            "created_at": row[6],
            "is_active": bool(row[7]),
        }

    def merge_into_repertorization(self, remedy_scores: Dict, accepted_private_ids: List[str]) -> Dict:
        """
        Merge private rubrics into an existing repertorization score dict.

        remedy_scores: defaultdict from homeopathic_repertory.repertorize()
                     e.g. defaultdict({"score": 0, "matches": [], "_rubric_ids": set()})
        accepted_private_ids: list of private_rubric_id strings to include.

        Returns the updated remedy_scores dict.
        """
        for rid in accepted_private_ids:
            pr = self.get_private_rubric(rid)
            if not pr or not pr.get("is_active"):
                continue
            for abbrev, weight in pr["remedy_abbrevs"].items():
                remedy_scores[abbrev]["score"] += weight
                remedy_scores[abbrev]["matches"].append({
                    "query_symptom": "private_rubric",
                    "rubric_id": rid,
                    "rubric": pr["fullpath"],
                    "source": "private",
                    "weight": weight,
                })
                remedy_scores[abbrev]["_rubric_ids"].add(rid)
        return remedy_scores


def quick_create(fullpath: str, remedy_abbrevs: Dict[str, int], practitioner_id: str) -> str:
    """Convenience one-liner."""
    mgr = PrivateRubricManager()
    return mgr.create_private_rubric(fullpath, remedy_abbrevs, practitioner_id)
