"""
Flashcard Spaced-Repetition Engine — Benefit #44

SM-2 algorithm for materia medica / clinical rubric memorization.

SQLite tables:
  - flashcard_decks (deck_id, name, description)
  - flashcards (card_id, deck_id, front, back, tags, created_at)
  - review_logs (card_id, due_date, interval_days, ease_factor, repetitions, status)

Usage:
    from oorep.flashcard_srs import FlashcardSRS, ReviewResult
    srs = FlashcardSRS()
    deck_id = srs.create_deck("Kent Mind Remedies")
    srs.add_card(deck_id, front="Fear of death, restlessness, burning pains",
                 back="Arsenicum Album", tags=["mind", "anxiety"])
    card = srs.get_due_card(deck_id)
    srs.review(card["card_id"], quality=4)  # 0-5 scale
    stats = srs.deck_stats(deck_id)
"""

import json
import sqlite3
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class ReviewResult(Enum):
    AGAIN = 0    # Complete blackout
    HARD = 1
    MEDIUM = 2
    EASY = 3
    GOOD = 4     # Correct with hesitation
    PERFECT = 5  # Perfect recall


# SM-2 default parameters
SM2_DEFAULT_EF = 2.5
SM2_MIN_EF = 1.3
SM2_MAX_INTERVAL = 365 * 2  # 2 years


class FlashcardSRS:
    """Spaced repetition flashcard engine using SM-2 algorithm."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_decks (
                deck_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                card_id TEXT PRIMARY KEY,
                deck_id TEXT NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                tags_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deck_id) REFERENCES flashcard_decks(deck_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS review_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL,
                reviewed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                quality INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                interval_days REAL DEFAULT 0,
                ease_factor REAL DEFAULT 2.5,
                repetitions INTEGER DEFAULT 0,
                status TEXT DEFAULT "active",
                FOREIGN KEY (card_id) REFERENCES flashcards(card_id)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_rl_card ON review_logs(card_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rl_due ON review_logs(due_date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rl_status ON review_logs(status)")
        conn.commit()
        conn.close()

    def create_deck(self, name: str, description="") -> str:
        deck_id = f"deck_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}"
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("INSERT INTO flashcard_decks (deck_id, name, description) VALUES (?,?,?)",
                  (deck_id, name, description))
        conn.commit()
        conn.close()
        return deck_id

    def add_card(self, deck_id: str, front: str, back: str, tags=None) -> str:
        card_id = f"card_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}"
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("INSERT INTO flashcards (card_id, deck_id, front, back, tags_json) VALUES (?,?,?,?,?)",
                  (card_id, deck_id, front, back, json.dumps(tags or [])))
        # Initialize review log
        due = (datetime.now() + timedelta(days=0)).strftime('%Y-%m-%d')
        c.execute(
            "INSERT INTO review_logs (card_id, quality, due_date, interval_days, ease_factor, repetitions, status) VALUES (?,?,?,?,?,?,?)",
            (card_id, 0, due, 0, SM2_DEFAULT_EF, 0, "active")
        )
        conn.commit()
        conn.close()
        return card_id

    def get_due_cards(self, deck_id=None, limit=20, include_new=True) -> List[Dict]:
        """Return cards due for review (or never reviewed)."""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        sql = """
            SELECT f.card_id, f.front, f.back, f.tags_json, r.due_date, r.interval_days, r.ease_factor, r.repetitions
            FROM flashcards f
            JOIN review_logs r ON f.card_id = r.card_id
            WHERE r.status = 'active' AND r.due_date <= ?
        """
        params = [today]
        if deck_id:
            sql += " AND f.deck_id = ?"
            params.append(deck_id)
        if not include_new:
            sql += " AND r.repetitions > 0"
        sql += " ORDER BY r.repetitions ASC, r.due_date ASC LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()
        return [
            {"card_id": r[0], "front": r[1], "back": r[2],
             "tags": json.loads(r[3]) if r[3] else [],
             "due_date": r[4], "interval": r[5], "ease": r[6], "repetitions": r[7]}
            for r in rows
        ]

    def get_card(self, card_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT card_id, front, back, tags_json FROM flashcards WHERE card_id=?", (card_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {"card_id": row[0], "front": row[1], "back": row[2], "tags": json.loads(row[3]) if row[3] else []}

    def review(self, card_id: str, quality: int) -> Dict:
        """
        Record a review and compute next due date using SM-2.

        quality: 0-5 (SM-2 scale).
        """
        if quality < 0 or quality > 5:
            raise ValueError("quality must be 0-5")
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        # Get latest review data
        c.execute(
            "SELECT interval_days, ease_factor, repetitions FROM review_logs WHERE card_id=? AND status='active' ORDER BY reviewed_at DESC LIMIT 1",
            (card_id,)
        )
        row = c.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"No active review log for card {card_id}")
        interval, ef, reps = row[0], row[1], row[2]
        # SM-2 algorithm
        ef = max(SM2_MIN_EF, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        if quality < 3:
            # Failed — reset to 1 day
            new_interval = 1
            new_reps = 0
        else:
            if reps == 0:
                new_interval = 1
            elif reps == 1:
                new_interval = 6
            else:
                new_interval = min(interval * ef, SM2_MAX_INTERVAL)
            new_reps = reps + 1
        new_due = (datetime.now() + timedelta(days=math.ceil(new_interval))).strftime('%Y-%m-%d')
        # Update old entry to status 'reviewed'
        c.execute("UPDATE review_logs SET status='reviewed' WHERE card_id=? AND status='active'", (card_id,))
        c.execute(
            """INSERT INTO review_logs (card_id, quality, due_date, interval_days, ease_factor, repetitions, status)
            VALUES (?,?,?,?,?,?,?)""",
            (card_id, quality, new_due, round(new_interval, 2), round(ef, 2), new_reps, "active")
        )
        conn.commit()
        conn.close()
        return {"card_id": card_id, "next_due": new_due, "interval": round(new_interval, 2), "ease": round(ef, 2), "repetitions": new_reps}

    def deck_stats(self, deck_id: str) -> Dict:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM flashcards WHERE deck_id=?", (deck_id,))
        total_cards = c.fetchone()[0]
        c.execute("""
            SELECT COUNT(DISTINCT f.card_id) FROM flashcards f
            JOIN review_logs r ON f.card_id = r.card_id
            WHERE f.deck_id=? AND r.status='active' AND r.repetitions=0
        """, (deck_id,))
        new_cards = c.fetchone()[0]
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("""
            SELECT COUNT(DISTINCT f.card_id) FROM flashcards f
            JOIN review_logs r ON f.card_id = r.card_id
            WHERE f.deck_id=? AND r.status='active' AND r.due_date <= ? AND r.repetitions > 0
        """, (deck_id, today))
        due_today = c.fetchone()[0]
        # Average ease
        c.execute("""
            SELECT AVG(r.ease_factor) FROM review_logs r
            JOIN flashcards f ON r.card_id = f.card_id
            WHERE f.deck_id=? AND r.status='active'
        """, (deck_id,))
        avg_ease = c.fetchone()[0] or SM2_DEFAULT_EF
        conn.close()
        return {
            "deck_id": deck_id, "total_cards": total_cards,
            "new_cards": new_cards, "due_today": due_today,
            "average_ease": round(avg_ease, 2),
        }

    def browse_cards(self, deck_id: str) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT card_id, front, back, tags_json FROM flashcards WHERE deck_id=?", (deck_id,))
        rows = c.fetchall()
        conn.close()
        return [{"card_id": r[0], "front": r[1], "back": r[2], "tags": json.loads(r[3]) if r[3] else []} for r in rows]

    def list_decks(self) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT deck_id, name, description, created_at FROM flashcard_decks ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return [{"deck_id": r[0], "name": r[1], "description": r[2], "created_at": r[3]} for r in rows]

    def delete_card(self, card_id: str):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("DELETE FROM review_logs WHERE card_id=?", (card_id,))
        c.execute("DELETE FROM flashcards WHERE card_id=?", (card_id,))
        conn.commit()
        conn.close()
