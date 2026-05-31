"""
Remedy Freshness Tracker — Benefit #39

Tracks how recently each remedy's data has been updated, flags stale records
for review, and logs new proving information.  Provides an overall freshness
score per remedy and a review-queue calendar via SQLite.

Usage:
    from oorep.remedy_freshness_tracker import RemedyFreshnessTracker
    tracker = RemedyFreshnessTracker()

    # Check which remedies are stale
    stale = tracker.check_staleness(threshold_days=90)

    # Flag remedies for human review
    tracker.flag_for_review(["Lyc.", "Puls."], reason="Outdated proving data")

    # Record new proving information
    tracker.record_proving_update("Lyc.", source="Hahnemann Proving 2024", date="2024-08-15")

    # Overall freshness report
    report = tracker.get_freshness_report()

    # Schedule a review date
    tracker.schedule_review("Puls.", review_date="2025-03-01")
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


class RemedyFreshnessTracker:
    """
    SQLite-backed freshness tracker for remedy data quality.

    Each remedy gets:
      - last_update_date: when the remedy record was last modified
      - proving_log: JSON list of proving source references with dates
      - review_queue: flagged items with reason and scheduled review date
      - overall_freshness_score: composite metric (1.0 = fresh, 0.0 = stale)
    """

    # Scoring constants
    FRESHNESS_FULL_SCORE = 1.0
    FRESHNESS_HALF_SCORE = 0.5
    FRESHNESS_ZERO = 0.0
    DEFAULT_THRESHOLD_DAYS = 90

    def __init__(
        self,
        db_path: Optional[Path] = None,
        repertory: Optional[HomeopathicRepertory] = None,
    ):
        """
        Args:
            db_path: SQLite database path. Defaults to feedback.db.
            repertory: Existing HomeopathicRepertory for remedy enumeration.
        """
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.rep = repertory or HomeopathicRepertory()
        self._init_db()
        # Ensure every known remedy has a row
        self._seed_remedies()

    # ── Schema ──────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create ``remedy_freshness``, ``remedy_proving_log``,
        and ``remedy_review_queue`` tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS remedy_freshness (
                remedy_abbrev TEXT PRIMARY KEY,
                last_update_date TEXT,
                freshness_score REAL DEFAULT 1.0,
                provenance TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS remedy_proving_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy_abbrev TEXT NOT NULL,
                source TEXT NOT NULL,
                source_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS remedy_review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy_abbrev TEXT NOT NULL,
                reason TEXT,
                scheduled_review_date TEXT,
                status TEXT DEFAULT 'open',
                resolved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_freshness_score ON remedy_freshness(freshness_score)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_review_queue_status ON remedy_review_queue(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_review_queue_date ON remedy_review_queue(scheduled_review_date)"
        )
        conn.commit()
        conn.close()

    def _seed_remedies(self) -> None:
        """
        Insert every remedy from the repertory into ``remedy_freshness``
        with a default last_update_date so they are trackable even if never
        explicitly touched.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        for _, remedy in self.rep.remedies.items():
            abbrev = remedy.get("abbrev", "")
            if not abbrev:
                continue
            cursor.execute(
                """
                INSERT OR IGNORE INTO remedy_freshness
                (remedy_abbrev, last_update_date, freshness_score)
                VALUES (?, ?, 1.0)
                """,
                (abbrev, datetime.now().isoformat()),
            )
        conn.commit()
        conn.close()

    # ── Staleness Check ─────────────────────────────────────────────────────

    def check_staleness(self, threshold_days: int = DEFAULT_THRESHOLD_DAYS) -> List[Dict[str, Any]]:
        """
        Return remedies whose last_update_date is older than ``threshold_days``.

        Args:
            threshold_days: Number of days after which a record is considered stale.

        Returns:
            List of dicts: remedy_abbrev, last_update_date, days_since_update,
            freshness_score.
        """
        cutoff = datetime.now() - timedelta(days=threshold_days)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT remedy_abbrev, last_update_date, freshness_score
            FROM remedy_freshness
            WHERE last_update_date < ?
               OR last_update_date IS NULL
            ORDER BY last_update_date ASC
            """,
            (cutoff.isoformat(),),
        )
        rows = cursor.fetchall()
        conn.close()

        stale = []
        for abbrev, last_date, score in rows:
            days = None
            if last_date:
                try:
                    last = datetime.fromisoformat(last_date)
                    days = (datetime.now() - last).days
                except Exception:
                    days = None
            stale.append({
                "remedy_abbrev": abbrev,
                "last_update_date": last_date,
                "days_since_update": days,
                "freshness_score": score,
            })
        return stale

    # ── Review Queue ──────────────────────────────────────────────────────────

    def flag_for_review(
        self, remedy_list: List[str], reason: str, scheduled_date: Optional[str] = None
    ) -> List[int]:
        """
        Flag one or more remedies for human review.

        Args:
            remedy_list: Remedy abbreviations to flag.
            reason: Human-readable reason for review (e.g., "Outdated proving").
            scheduled_date: Optional ISO date string for when review should happen.

        Returns:
            List of inserted row IDs.
        """
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        ids = []
        for abbrev in remedy_list:
            cursor.execute(
                """
                INSERT INTO remedy_review_queue (remedy_abbrev, reason, scheduled_review_date, status, created_at)
                VALUES (?, ?, ?, 'open', ?)
                """,
                (abbrev, reason, scheduled_date, now),
            )
            ids.append(cursor.lastrowid or 0)
        conn.commit()
        conn.close()
        return ids

    # ── Proving Update Logging ────────────────────────────────────────────────

    def record_proving_update(
        self,
        remedy: str,
        source: str,
        date: str,
        notes: Optional[str] = None,
    ) -> int:
        """
        Log a new proving or materia medica update for a remedy.

        Also bumps ``last_update_date`` and recalculates ``freshness_score``.

        Args:
            remedy: Remedy abbreviation.
            source: Proving source reference.
            date: ISO date of the proving / update.
            notes: Optional clinician or researcher notes.

        Returns:
            Row ID of the inserted proving log entry.
        """
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO remedy_proving_log (remedy_abbrev, source, source_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (remedy, source, date, notes, now),
        )
        row_id = cursor.lastrowid or 0

        # Update freshness: score = 1.0 whenever a proving is added
        cursor.execute(
            """
            INSERT INTO remedy_freshness (remedy_abbrev, last_update_date, freshness_score, updated_at)
            VALUES (?, ?, 1.0, ?)
            ON CONFLICT(remedy_abbrev) DO UPDATE SET
                last_update_date = excluded.last_update_date,
                freshness_score = excluded.freshness_score,
                updated_at = excluded.updated_at
            """,
            (remedy, now, now),
        )
        conn.commit()
        conn.close()
        return row_id

    # ── Freshness Report ────────────────────────────────────────────────────

    def get_freshness_report(self) -> Dict[str, Any]:
        """
        Compute overall freshness statistics across the entire remedy set.

        Returns:
            Dict with keys:
              - total_remedies, fresh_count, stale_count, average_score,
              - score_distribution, stale_list, queue_summary.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT remedy_abbrev, last_update_date, freshness_score FROM remedy_freshness"
        )
        rows = cursor.fetchall()
        conn.close()

        total = len(rows)
        fresh_count = sum(1 for _, _, score in rows if (score or 0) >= self.FRESHNESS_HALF_SCORE)
        stale_count = total - fresh_count
        scores = [score for _, _, score in rows if score is not None]
        avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

        distribution = {"0.0-0.25": 0, "0.25-0.5": 0, "0.5-0.75": 0, "0.75-1.0": 0}
        for _, _, score in rows:
            s = score if score is not None else 0.0
            if s < 0.25:
                distribution["0.0-0.25"] += 1
            elif s < 0.5:
                distribution["0.25-0.5"] += 1
            elif s < 0.75:
                distribution["0.5-0.75"] += 1
            else:
                distribution["0.75-1.0"] += 1

        stale_list = [
            {"remedy_abbrev": r[0], "last_update_date": r[1], "score": r[2]}
            for r in rows
            if (r[2] or 0) < self.FRESHNESS_HALF_SCORE
        ]
        stale_list.sort(key=lambda x: x["score"] if x["score"] is not None else 0.0)

        queue_summary = self._get_queue_summary()

        return {
            "total_remedies": total,
            "fresh_count": fresh_count,
            "stale_count": stale_count,
            "average_score": avg_score,
            "score_distribution": distribution,
            "stale_list": stale_list[:20],
            "queue_summary": queue_summary,
        }

    def _get_queue_summary(self) -> Dict[str, Any]:
        """Return counts of open / resolved review queue entries."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, COUNT(*) FROM remedy_review_queue GROUP BY status"
        )
        rows = cursor.fetchall()
        conn.close()
        return {"status_counts": {r[0]: r[1] for r in rows}}

    # ── Calendar Integration ────────────────────────────────────────────────

    def schedule_review(self, remedy: str, review_date: str) -> int:
        """
        Schedule a remedy review on a specific date.

        If an open queue entry already exists for the remedy, its scheduled
        date is updated; otherwise a new queue entry is created.

        Args:
            remedy: Remedy abbreviation.
            review_date: ISO date (e.g., "2025-03-01").

        Returns:
            Row ID of the updated or inserted queue entry.
        """
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM remedy_review_queue
            WHERE remedy_abbrev = ? AND status = 'open'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (remedy,),
        )
        existing = cursor.fetchone()
        if existing:
            row_id = existing[0]
            cursor.execute(
                "UPDATE remedy_review_queue SET scheduled_review_date = ?, created_at = ? WHERE id = ?",
                (review_date, now, row_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO remedy_review_queue (remedy_abbrev, reason, scheduled_review_date, status, created_at)
                VALUES (?, 'Scheduled review', ?, 'open', ?)
                """,
                (remedy, review_date, now),
            )
            row_id = cursor.lastrowid or 0
        conn.commit()
        conn.close()
        return row_id

    # ── Batch Scoring Refresh ────────────────────────────────────────────────

    def refresh_all_scores(self, threshold_days: int = DEFAULT_THRESHOLD_DAYS) -> None:
        """
        Recalculate freshness scores for all remedies based on days since update.

        Scoring model:
          - updated today: 1.0
          - within threshold: linear decay 1.0 → 0.5
          - beyond threshold: linear decay 0.5 → 0.0
        """
        now = datetime.now()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT remedy_abbrev, last_update_date FROM remedy_freshness"
        )
        rows = cursor.fetchall()
        for abbrev, last_date in rows:
            score = self._calculate_score(last_date, now, threshold_days)
            cursor.execute(
                "UPDATE remedy_freshness SET freshness_score = ?, updated_at = ? WHERE remedy_abbrev = ?",
                (round(score, 4), now.isoformat(), abbrev),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def _calculate_score(last_date_str: Optional[str], now: datetime, threshold_days: int) -> float:
        """Compute a freshness score from a last-update date string."""
        if not last_date_str:
            return 0.0
        try:
            last = datetime.fromisoformat(last_date_str)
            delta = (now - last).days
        except Exception:
            return 0.0
        if delta <= 0:
            return 1.0
        if delta <= threshold_days:
            return 1.0 - (0.5 * delta / threshold_days)
        # Beyond threshold: 0.5 down to 0.0 at double threshold
        extra = delta - threshold_days
        return max(0.0, 0.5 - (0.5 * extra / threshold_days))
