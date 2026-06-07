"""
Clinical Tips Engine — Practitioner Notes & Author Commentary on Rubrics

Attach practitioner notes, clinical tips, and author commentary to rubrics.
Builds institutional knowledge over time.
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class ClinicalTipsEngine:
    """
    Store and retrieve clinical tips on rubrics.
    Tips can be tagged by author, source, reliability, and indication.
    """

    def __init__(self, db_path: str = "data/clinical_tips.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tips (
                id INTEGER PRIMARY KEY,
                rubric_id INTEGER,
                rubric_path TEXT,
                tip TEXT NOT NULL,
                author TEXT,
                source TEXT,
                reliability TEXT CHECK(reliability IN ('anecdotal', 'clinical', 'proven', 'controversial')),
                indication TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tips_rubric ON tips(rubric_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tips_path ON tips(rubric_path)")
        conn.commit()
        conn.close()

    def add_tip(self, rubric_id: Optional[int], rubric_path: str, tip: str,
                author: str = "", source: str = "",
                reliability: str = "clinical",
                indication: str = "") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute(
            "INSERT INTO tips (rubric_id, rubric_path, tip, author, source, reliability, indication, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (rubric_id, rubric_path, tip, author, source, reliability, indication, now, now)
        )
        conn.commit()
        tip_id = cur.lastrowid
        conn.close()
        return {
            "id": tip_id,
            "rubric_id": rubric_id,
            "rubric_path": rubric_path,
            "tip": tip,
            "author": author,
            "reliability": reliability,
            "indication": indication,
        }

    def get_tips_for_rubric(self, rubric_id: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT id, tip, author, source, reliability, indication, created_at FROM tips WHERE rubric_id = ? ORDER BY created_at DESC",
            (rubric_id,)
        ).fetchall()
        conn.close()
        return [
            {
                "id": r[0], "tip": r[1], "author": r[2], "source": r[3],
                "reliability": r[4], "indication": r[5], "created_at": r[6]
            }
            for r in rows
        ]

    def search_tips(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT id, rubric_path, tip, author, reliability, indication FROM tips WHERE tip LIKE ? OR rubric_path LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "rubric_path": r[1], "tip": r[2], "author": r[3], "reliability": r[4], "indication": r[5]}
            for r in rows
        ]

    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute("SELECT COUNT(*) FROM tips").fetchone()[0]
        by_reliability = conn.execute(
            "SELECT reliability, COUNT(*) FROM tips GROUP BY reliability"
        ).fetchall()
        by_author = conn.execute(
            "SELECT author, COUNT(*) FROM tips GROUP BY author ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall()
        conn.close()
        return {
            "total_tips": total,
            "by_reliability": {r[0]: r[1] for r in by_reliability},
            "top_authors": {r[0]: r[1] for r in by_author},
        }
