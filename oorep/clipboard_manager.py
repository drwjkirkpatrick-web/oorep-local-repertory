"""
Clipboard Manager — RadarOpus-inspired multi-clipboard symptom collection.

Named clipboards where rubrics from any search can be collected, combined,
eliminated, and analyzed. Integrates with the repertorization engine.

Usage:
    from oorep.clipboard_manager import ClipboardManager

    cm = ClipboardManager()

    # Create a clipboard for a case
    cb = cm.create_clipboard("case_mrs_j_2024")

    # Add rubrics from searches
    cm.add_rubric(cb.id, rubric_id=12345, source="kent", weight=3)
    cm.add_rubric(cb.id, rubric_id=67890, source="kent", weight=2)

    # Create an elimination clipboard
    elim = cm.create_clipboard("exclude_mercury", clipboard_type="elimination")
    cm.add_rubric(elim.id, rubric_id=11111, source="kent", weight=1)

    # Run analysis with multiple clipboards
    analysis = cm.analyze([cb.id, elim.id], top_n=20)
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

# Reuse the feedback.db path for clipboard persistence
try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class ClipboardType(str, Enum):
    INCLUSION = "inclusion"      # Standard: rubrics add to remedy score
    ELIMINATION = "elimination"  # Remedies appearing here are excluded
    OPTIONAL = "optional"        # Weighted lower; doesn't penalize absence


@dataclass
class Clipboard:
    id: str
    name: str
    type: str
    description: Optional[str]
    rubric_count: int
    created_at: str
    updated_at: str


@dataclass
class ClipboardRubric:
    id: str          # UUID for this entry
    clipboard_id: str
    rubric_id: int
    rubric_fullpath: Optional[str]
    source: Optional[str]
    remedy_weight: int       # The grade/weight from the repertory
    user_weight: float        # User-adjustable multiplier (default 1.0)
    notes: Optional[str]
    added_at: str


class ClipboardManager:
    """
    Multi-clipboard symptom collection for OOREP.
    Stores clipboards and rubric entries in SQLite.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Schema ────────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clipboards (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'inclusion',
                description TEXT,
                rubric_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_rubrics (
                id TEXT PRIMARY KEY,
                clipboard_id TEXT NOT NULL,
                rubric_id INTEGER NOT NULL,
                rubric_fullpath TEXT,
                source TEXT,
                remedy_weight INTEGER DEFAULT 1,
                user_weight REAL DEFAULT 1.0,
                notes TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clipboard_id) REFERENCES clipboards(id) ON DELETE CASCADE
            )
        """)

        # Index for fast rubric lookups per clipboard
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_clipboard_rubrics_cb
            ON clipboard_rubrics(clipboard_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_clipboard_rubrics_rid
            ON clipboard_rubrics(rubric_id)
        """)

        conn.commit()
        conn.close()

    # ── Clipboard CRUD ────────────────────────────────────────────────────────

    def create_clipboard(
        self,
        name: str,
        clipboard_type: ClipboardType = ClipboardType.INCLUSION,
        description: Optional[str] = None,
    ) -> Clipboard:
        """Create a new named clipboard."""
        cb_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clipboards (id, name, type, description, rubric_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, ?)
        """, (cb_id, name, clipboard_type.value, description, now, now))
        conn.commit()
        conn.close()
        return Clipboard(
            id=cb_id, name=name, type=clipboard_type.value,
            description=description, rubric_count=0,
            created_at=now, updated_at=now,
        )

    def list_clipboards(self) -> List[Clipboard]:
        """Return all clipboards ordered by most recently updated."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, type, description, rubric_count, created_at, updated_at
            FROM clipboards ORDER BY updated_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            Clipboard(
                id=r[0], name=r[1], type=r[2], description=r[3],
                rubric_count=r[4], created_at=r[5], updated_at=r[6],
            )
            for r in rows
        ]

    def get_clipboard(self, clipboard_id: str) -> Optional[Clipboard]:
        """Get a single clipboard by ID."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, type, description, rubric_count, created_at, updated_at
            FROM clipboards WHERE id = ?
        """, (clipboard_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return Clipboard(
            id=row[0], name=row[1], type=row[2], description=row[3],
            rubric_count=row[4], created_at=row[5], updated_at=row[6],
        )

    def rename_clipboard(self, clipboard_id: str, new_name: str) -> bool:
        """Rename a clipboard."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE clipboards SET name = ?, updated_at = ? WHERE id = ?
        """, (new_name, now, clipboard_id))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def delete_clipboard(self, clipboard_id: str) -> bool:
        """Delete a clipboard and all its rubrics."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clipboards WHERE id = ?", (clipboard_id,))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    # ── Rubric Management ─────────────────────────────────────────────────────

    def add_rubric(
        self,
        clipboard_id: str,
        rubric_id: int,
        rubric_fullpath: Optional[str] = None,
        source: Optional[str] = None,
        remedy_weight: int = 1,
        user_weight: float = 1.0,
        notes: Optional[str] = None,
    ) -> ClipboardRubric:
        """Add a rubric to a clipboard."""
        entry_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clipboard_rubrics
            (id, clipboard_id, rubric_id, rubric_fullpath, source, remedy_weight, user_weight, notes, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, clipboard_id, rubric_id, rubric_fullpath, source, remedy_weight, user_weight, notes, now))

        # Update rubric_count and updated_at on the clipboard
        cursor.execute("""
            UPDATE clipboards
            SET rubric_count = rubric_count + 1, updated_at = ?
            WHERE id = ?
        """, (now, clipboard_id))

        conn.commit()
        conn.close()
        return ClipboardRubric(
            id=entry_id, clipboard_id=clipboard_id, rubric_id=rubric_id,
            rubric_fullpath=rubric_fullpath, source=source,
            remedy_weight=remedy_weight, user_weight=user_weight,
            notes=notes, added_at=now,
        )

    def remove_rubric(self, clipboard_id: str, rubric_id: int) -> bool:
        """Remove a rubric from a clipboard by rubric_id (removes all matching rows)."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM clipboard_rubrics
            WHERE clipboard_id = ? AND rubric_id = ?
        """, (clipboard_id, rubric_id))
        deleted = cursor.rowcount
        if deleted:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                UPDATE clipboards
                SET rubric_count = rubric_count - ?, updated_at = ?
                WHERE id = ?
            """, (deleted, now, clipboard_id))
        conn.commit()
        conn.close()
        return deleted > 0

    def get_rubrics(self, clipboard_id: str) -> List[ClipboardRubric]:
        """Get all rubric entries for a clipboard."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, clipboard_id, rubric_id, rubric_fullpath, source,
                   remedy_weight, user_weight, notes, added_at
            FROM clipboard_rubrics WHERE clipboard_id = ?
            ORDER BY added_at
        """, (clipboard_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            ClipboardRubric(
                id=r[0], clipboard_id=r[1], rubric_id=r[2], rubric_fullpath=r[3],
                source=r[4], remedy_weight=r[5], user_weight=r[6], notes=r[7], added_at=r[8],
            )
            for r in rows
        ]

    def set_user_weight(self, entry_id: str, user_weight: float) -> bool:
        """Adjust the user-defined weight multiplier for a rubric entry."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clipboard_rubrics SET user_weight = ? WHERE id = ?
        """, (user_weight, entry_id))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    # ── Analysis ──────────────────────────────────────────────────────────────

    def analyze(
        self,
        clipboard_ids: List[str],
        top_n: int = 20,
        repertory=None,
        grade_mode: str = "full",
        grade_weights: Optional[Dict[int, float]] = None,
    ) -> Dict[str, Any]:
        """
        Run repertorization across multiple clipboards with type-aware logic.

        - INCLUSION: remedies get weighted scores (remedy_weight * user_weight)
        - ELIMINATION: remedies appearing in any elimination clipboard are excluded
        - OPTIONAL: remedies get half-weighted scores; absence is not penalized

        Args:
            clipboard_ids: List of clipboard IDs to combine
            top_n: Number of top remedies to return
            repertory: Optional HomeopathicRepertory instance

        Returns:
            Dict with ranked remedies, elimination log, and per-clipboard summary.
        """
        try:
            from .homeopathic_repertory import HomeopathicRepertory
        except Exception:
            from homeopathic_repertory import HomeopathicRepertory

        if repertory is None:
            repertory = HomeopathicRepertory()

        # Gather all clipboards and their rubrics
        clipboards = []
        for cb_id in clipboard_ids:
            cb = self.get_clipboard(cb_id)
            if not cb:
                continue
            rubrics = self.get_rubrics(cb_id)
            clipboards.append({"clipboard": cb, "rubrics": rubrics})

        # Collect elimination set first
        eliminated_remedies: set = set()
        for entry in clipboards:
            if entry["clipboard"].type == ClipboardType.ELIMINATION.value:
                for cr in entry["rubrics"]:
                    remedies = repertory.get_remedies_for_rubric(cr.rubric_id)
                    for rem in remedies:
                        eliminated_remedies.add(rem["abbrev"])

        # Score inclusion + optional rubrics
        remedy_scores: Dict[str, Dict[str, Any]] = {}

        # Grade config
        default_weights = {1: 1.0, 2: 2.0, 3: 3.0}
        grade_w = grade_weights or default_weights
        grade_mode = (grade_mode or "full").strip().lower()
        if grade_mode not in {"full", "strict", "classical"}:
            grade_mode = "full"

        for entry in clipboards:
            cb_type = entry["clipboard"].type
            if cb_type == ClipboardType.ELIMINATION.value:
                continue  # Already handled above

            multiplier = 0.5 if cb_type == ClipboardType.OPTIONAL.value else 1.0

            for cr in entry["rubrics"]:
                remedies = repertory.get_remedies_for_rubric(cr.rubric_id)
                for rem in remedies:
                    abbrev = rem["abbrev"]
                    if abbrev in eliminated_remedies:
                        continue
                    raw_weight = rem["weight"]

                    if grade_mode == "classical" and raw_weight < 2:
                        continue

                    effective = grade_w.get(raw_weight, float(raw_weight)) * cr.user_weight * multiplier

                    if abbrev not in remedy_scores:
                        remedy_scores[abbrev] = {
                            "score": 0.0, "matches": [], "_rubric_ids": set(),
                            "remedy_name": rem["name"], "grade_distribution": {1: 0, 2: 0, 3: 0},
                        }
                    rubric_key = (cr.rubric_id, entry["clipboard"].id)
                    if rubric_key in remedy_scores[abbrev]["_rubric_ids"]:
                        continue
                    remedy_scores[abbrev]["score"] += effective
                    remedy_scores[abbrev]["remedy_name"] = rem["name"]
                    remedy_scores[abbrev]["_rubric_ids"].add(rubric_key)
                    remedy_scores[abbrev]["grade_distribution"][raw_weight] = remedy_scores[abbrev]["grade_distribution"].get(raw_weight, 0) + 1
                    remedy_scores[abbrev]["matches"].append({
                        "rubric_id": cr.rubric_id,
                        "rubric_fullpath": cr.rubric_fullpath,
                        "clipboard_id": entry["clipboard"].id,
                        "clipboard_name": entry["clipboard"].name,
                        "clipboard_type": cb_type,
                        "effective_weight": round(effective, 2),
                        "base_weight": raw_weight,
                        "user_weight": cr.user_weight,
                    })

        # Rank
        sorted_results = sorted(
            remedy_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True,
        )

        results = []
        for abbrev, data in sorted_results[:top_n]:
            results.append({
                "abbrev": abbrev,
                "name": data["remedy_name"],
                "score": round(data["score"], 2),
                "match_count": len(data["_rubric_ids"]),
                "grade_distribution": data["grade_distribution"],
                "matches": data["matches"][:5],
            })

        return {
            "eliminated_count": len(eliminated_remedies),
            "eliminated_remedies": sorted(list(eliminated_remedies))[:50],
            "total_clipboards": len(clipboards),
            "per_clipboard_summary": [
                {
                    "id": e["clipboard"].id,
                    "name": e["clipboard"].name,
                    "type": e["clipboard"].type,
                    "rubric_count": len(e["rubrics"]),
                }
                for e in clipboards
            ],
            "remedies": results,
        }

    # ── Convenience ───────────────────────────────────────────────────────────

    def quick_add_search_results(
        self,
        clipboard_id: str,
        search_results: List[Dict],
        notes: Optional[str] = None,
    ) -> int:
        """
        Bulk-add rubrics from a search result list (e.g. from search_rubrics).
        Returns count added.
        """
        added = 0
        for r in search_results:
            rid = r.get("id")
            if rid is None:
                continue
            self.add_rubric(
                clipboard_id=clipboard_id,
                rubric_id=int(rid),
                rubric_fullpath=r.get("fullpath"),
                source=r.get("source"),
                notes=notes,
            )
            added += 1
        return added

    def duplicate_clipboard(self, clipboard_id: str, new_name: Optional[str] = None) -> Optional[Clipboard]:
        """Clone a clipboard (rubrics and all) into a new one."""
        original = self.get_clipboard(clipboard_id)
        if not original:
            return None
        name = new_name or f"{original.name} (copy)"
        new_cb = self.create_clipboard(
            name=name,
            clipboard_type=ClipboardType(original.type),
            description=original.description,
        )
        for cr in self.get_rubrics(clipboard_id):
            self.add_rubric(
                clipboard_id=new_cb.id,
                rubric_id=cr.rubric_id,
                rubric_fullpath=cr.rubric_fullpath,
                source=cr.source,
                remedy_weight=cr.remedy_weight,
                user_weight=cr.user_weight,
                notes=cr.notes,
            )
        return new_cb


# ── Standalone helpers ──────────────────────────────────────────────────────

def quick_clipboard(name: str, rubric_ids: List[int]) -> Dict:
    """One-liner: create a clipboard, add rubrics, return analysis-ready dict."""
    cm = ClipboardManager()
    cb = cm.create_clipboard(name)
    for rid in rubric_ids:
        cm.add_rubric(cb.id, rubric_id=rid)
    return {"clipboard_id": cb.id, "name": name, "rubric_count": len(rubric_ids)}


if __name__ == "__main__":
    print("Clipboard Manager — OOREP")
    print("=" * 50)

    cm = ClipboardManager()

    # Demo: create, add, analyze
    cb1 = cm.create_clipboard("demo_headache", description="Morning headache case")
    print(f"Created clipboard: {cb1.name} ({cb1.id[:8]}...)")

    # Add some sample rubrics (using real IDs from the repertory)
    rep = None
    try:
        from homeopathic_repertory import HomeopathicRepertory
        rep = HomeopathicRepertory()
        rubrics = rep.search_rubrics("headache morning", limit=5)
        for r in rubrics:
            cm.add_rubric(
                cb1.id,
                rubric_id=r["id"],
                rubric_fullpath=r.get("fullpath"),
                source=r.get("source"),
            )
        print(f"Added {len(rubrics)} rubrics from search.")

        # Run analysis
        result = cm.analyze([cb1.id], top_n=10, repertory=rep)
        print(f"\nAnalysis results: {len(result['remedies'])} remedies")
        for rem in result["remedies"][:5]:
            print(f"  {rem['abbrev']} ({rem['name']}): score {rem['score']}")

    except Exception as e:
        print(f"Demo requires repertory data: {e}")

    # Cleanup
    cm.delete_clipboard(cb1.id)
    print("\nClipboard deleted.")
