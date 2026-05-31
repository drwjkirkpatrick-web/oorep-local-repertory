"""
Materia Medica Full-Text Database — Benefits #18, #21

Stores and searches materia medica proving texts with full-text indexing.

Usage:
    from oorep.materia_medica import MateriaMedica
    mm = MateriaMedica()
    hits = mm.search("burning pains", limit=10)
    text = mm.get_proving_text("Ars.", author="Kent", section="stomach")
    comp = mm.compare_remedies("Ars.", "Phos.", query="burning")
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


_SEED_ENTRIES: List[Dict] = [
    {"remedy_id": 1, "remedy_abbrev": "Ars.",   "author": "Kent", "section": "mind",
     "text": "Arsenicum Album: Great anxiety, restlessness, fear of death. The patient is constantly moving, cannot sit still. Fastidiousness, desire for order and cleanliness. Burning pains in various parts ameliorated by heat."},
    {"remedy_id": 1, "remedy_abbrev": "Ars.",   "author": "Kent", "section": "stomach",
     "text": "Stomach: Burning pains, intense thirst for small quantities of water. Nausea and vomiting after eating or drinking. Great weakness and prostration."},
    {"remedy_id": 2, "remedy_abbrev": "Puls.",   "author": "Kent", "section": "mind",
     "text": "Pulsatilla: Mild, yielding, tearful disposition. Changeable mood. Sensitive to everything, especially warmth. Weeping disposition. No thirst."},
    {"remedy_id": 2, "remedy_abbrev": "Puls.",   "author": "Kent", "section": "female",
     "text": "Female: Suppressed menses from wet feet. Delayed menses. Labour pains too weak. After-pains violent. Milk suppressed after emotion."},
    {"remedy_id": 3, "remedy_abbrev": "Nux-v.",  "author": "Kent", "section": "mind",
     "text": "Nux Vomica: Very irritable, sensitive to all impressions. Angry, impatient, quarrelsome. Chilly. Over-sensitive to noise, odors, light."},
    {"remedy_id": 3, "remedy_abbrev": "Nux-v.",  "author": "Kent", "section": "stomach",
     "text": "Stomach: Sour taste and nausea in morning. Heartburn with flatulence. Desire for stimulants. Constipation with ineffectual urging. Worse after eating."},
    {"remedy_id": 4, "remedy_abbrev": "Lyc.",   "author": "Kent", "section": "mind",
     "text": "Lycopodium: Loss of self-confidence, though haughty and domineering to family. Dreads undertaking new things. Intellectually keen but physically weak. Afraid of being alone."},
    {"remedy_id": 4, "remedy_abbrev": "Lyc.",   "author": "Kent", "section": "digestive",
     "text": "Digestive: Flatulence, much bloating after meals. Desire for sweets. Hunger, yet fullness after a few mouthfuls. Worse from 4 to 8 PM. Right-sided complaints."},
    {"remedy_id": 5, "remedy_abbrev": "Sulph.",  "author": "Kent", "section": "mind",
     "text": "Sulphur: Lazy, selfish, no desire to work. Theorizes about philosophy and religion but neglects practical details. Burning heat, especially soles and vertex. Irritable and depressed."},
    {"remedy_id": 5, "remedy_abbrev": "Sulph.",  "author": "Kent", "section": "skin",
     "text": "Skin: Burning, itching, worse from heat of bed. Dry, scaly eruptions. Every little injury suppurates. Redness around orifices."},
    {"remedy_id": 6, "remedy_abbrev": "Calc.",   "author": "Kent", "section": "mind",
     "text": "Calcarea Carbonica: Fear of misfortune, contagious disease, or impending calamity. Apprehensive, especially in evening. Desire for protection and company. Obstinate and slow."},
    {"remedy_id": 6, "remedy_abbrev": "Calc.",   "author": "Kent", "section": "constitutional",
     "text": "Constitutional: Fat, flabby, profuse sweating especially of head at night. Cold, damp feet. Craving for eggs. Late dentition and fontanelle closure. Polyps, warts."},
    {"remedy_id": 7, "remedy_abbrev": "Phos.",   "author": "Kent", "section": "mind",
     "text": "Phosphorus: Sympathetic, friendly, wants affection and company. Fear of thunder, darkness, being alone. Suggestible, impressionable. Burning pains with great thirst for cold drinks."},
    {"remedy_id": 7, "remedy_abbrev": "Phos.",   "author": "Kent", "section": "respiratory",
     "text": "Respiratory: Hoarseness, worse evening. Croupy cough, hollow, barking. Tightness across chest. Burning in chest. Hemoptysis, bright red blood. Worse lying on left side."},
    {"remedy_id": 8, "remedy_abbrev": "Sil.",   "author": "Kent", "section": "mind",
     "text": "Silica: Yielding, faint-hearted, want of grit. Timid and anxious. Obstinate but irresolute. Sensitive to cold, noise, pain. Desires to be magnetized."},
    {"remedy_id": 8, "remedy_abbrev": "Sil.",   "author": "Kent", "section": "constitutional",
     "text": "Constitutional: Profuse sweating of feet, fetid, cold. Every little injury suppurates. Splinters work their way out slowly. Late walking. Constipation, stool recedes."},
    {"remedy_id": 9, "remedy_abbrev": "Merc.",   "author": "Kent", "section": "mind",
     "text": "Mercurius: Slow in answering questions; loss of memory. Suspicious and mistrustful. Profuse sweating without relief. Offensive discharges from all orifices."},
    {"remedy_id": 9, "remedy_abbrev": "Merc.",   "author": "Kent", "section": "throat",
     "text": "Throat: Sore throat with much saliva and perspiration. Swollen tonsils, ulcers, yellow patches. Pain worse at night, from warmth of bed. Fetid breath."},
    {"remedy_id": 10, "remedy_abbrev": "Acon.",  "author": "Kent", "section": "mind",
     "text": "Aconitum: Great fear, anxiety, and worry accompany every ailment. Restless, changing position constantly. Sudden onset of symptoms after cold, dry wind."},
    {"remedy_id": 10, "remedy_abbrev": "Acon.",  "author": "Kent", "section": "fever",
     "text": "Fever: High, dry burning heat with thirst. Hard, bounding pulse. Skin hot and dry. Worse at night, from cold wind. First stage of inflammatory fever."},
]


class MateriaMedica:
    """Full-text materia medica database with FTS5."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS materia_medica_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy_id INTEGER,
                remedy_abbrev TEXT NOT NULL,
                author TEXT NOT NULL,
                section TEXT NOT NULL,
                text TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(remedy_abbrev, author, section)
            )
        """)
        try:
            c.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS mm_fts USING fts5(
                    text, content='materia_medica_entries', content_rowid='id'
                )
            """)
        except sqlite3.OperationalError:
            pass
        c.execute("CREATE INDEX IF NOT EXISTS idx_mm_remedy ON materia_medica_entries(remedy_abbrev)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_mm_author ON materia_medica_entries(author)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_mm_section ON materia_medica_entries(section)")
        conn.commit()
        conn.close()
        self._seed_data()

    def _seed_data(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM materia_medica_entries")
        count = c.fetchone()[0]
        if count == 0 and _SEED_ENTRIES:
            for entry in _SEED_ENTRIES:
                c.execute(
                    """INSERT OR IGNORE INTO materia_medica_entries
                    (remedy_id, remedy_abbrev, author, section, text, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (entry.get("remedy_id"), entry["remedy_abbrev"], entry["author"], entry["section"],
                     entry["text"], json.dumps({"source": "public_domain", "seeded": True}))
                )
            conn.commit()
        conn.close()
        self._rebuild_fts()
    def _rebuild_fts(self):
        """Rebuild FTS5 index after bulk insert. Silently skip on failure."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        try:
            c.execute("DELETE FROM mm_fts")
            c.execute("INSERT INTO mm_fts(rowid, text) SELECT id, text FROM materia_medica_entries")
            conn.commit()
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            # FTS5 may not be available or contentless mode may conflict
            conn.rollback()
        conn.close()

    def _snippet(self, text: str, query: str, context: int = 80) -> str:
        ql = query.lower()
        idx = text.lower().find(ql)
        if idx == -1:
            for word in ql.split():
                idx = text.lower().find(word)
                if idx != -1:
                    ql = word
                    break
        if idx == -1:
            return text[:160] + ("..." if len(text) > 160 else "")
        start = max(0, idx - context)
        end = min(len(text), idx + len(ql) + context)
        snip = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
        return snip

    def search(self, query: str, remedy_filter=None, author_filter=None, section_filter=None, limit=20):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        params = []
        try:
            fts_query = " ".join(query.split())
            sql = """
                SELECT e.id, e.remedy_abbrev, e.author, e.section, e.text, rank
                FROM mm_fts
                JOIN materia_medica_entries e ON mm_fts.rowid = e.id
                WHERE mm_fts MATCH ?
            """
            params.append(fts_query)
            if remedy_filter:
                sql += " AND e.remedy_abbrev = ?"; params.append(remedy_filter)
            if author_filter:
                sql += " AND e.author = ?"; params.append(author_filter)
            if section_filter:
                sql += " AND e.section = ?"; params.append(section_filter)
            sql += " ORDER BY rank LIMIT ?"; params.append(limit)
            c.execute(sql, params)
            rows = c.fetchall()
            results = [{"id": row[0], "remedy_abbrev": row[1], "author": row[2],
                        "section": row[3], "text_snippet": self._snippet(row[4], query), "rank": row[5]}
                       for row in rows]
            conn.close()
            return results
        except sqlite3.OperationalError:
            conn.close()
            return self._fallback_search(query, remedy_filter, author_filter, section_filter, limit)

    def _fallback_search(self, query, remedy_filter, author_filter, section_filter, limit):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        terms = query.split()
        conditions = [" text LIKE ? " for _ in terms]
        sql = "SELECT id, remedy_abbrev, author, section, text FROM materia_medica_entries WHERE " + " AND ".join(conditions)
        params = [f"%{t}%" for t in terms]
        if remedy_filter:
            sql += " AND remedy_abbrev = ?"; params.append(remedy_filter)
        if author_filter:
            sql += " AND author = ?"; params.append(author_filter)
        if section_filter:
            sql += " AND section = ?"; params.append(section_filter)
        sql += f" LIMIT {int(limit)}"
        c.execute(sql, params)
        rows = c.fetchall()
        results = [{"id": r[0], "remedy_abbrev": r[1], "author": r[2],
                    "section": r[3], "text_snippet": self._snippet(r[4], query), "rank": 0} for r in rows]
        conn.close()
        return results

    def get_proving_text(self, remedy_abbrev: str, author=None, section=None):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        sql = "SELECT id, author, section, text, metadata_json FROM materia_medica_entries WHERE remedy_abbrev = ?"
        params = [remedy_abbrev]
        if author:
            sql += " AND author = ?"; params.append(author)
        if section:
            sql += " AND section = ?"; params.append(section)
        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "author": r[1], "section": r[2], "text": r[3],
                 "metadata": json.loads(r[4]) if r[4] else {}} for r in rows]

    def compare_remedies(self, abbrev_a: str, abbrev_b: str, query=None):
        a_entries = self.get_proving_text(abbrev_a)
        b_entries = self.get_proving_text(abbrev_b)
        if query:
            ql = query.lower()
            a_entries = [e for e in a_entries if ql in e["text"].lower() or ql in e["section"].lower()]
            b_entries = [e for e in b_entries if ql in e["text"].lower() or ql in e["section"].lower()]
        a_sections = {e["section"]: e for e in a_entries}
        b_sections = {e["section"]: e for e in b_entries}
        overlap = set(a_sections) & set(b_sections)
        a_only = [{"section": s, "text": a_sections[s]["text"]} for s in a_sections if s not in b_sections]
        b_only = [{"section": s, "text": b_sections[s]["text"]} for s in b_sections if s not in a_sections]
        shared = [{"section": sec, "a_text": a_sections[sec]["text"], "b_text": b_sections[sec]["text"]} for sec in overlap]
        all_a = " ".join(e["text"].lower() for e in a_entries)
        all_b = " ".join(e["text"].lower() for e in b_entries)
        a_words = set(re.findall(r"\b[a-z]{4,}\b", all_a))
        b_words = set(re.findall(r"\b[a-z]{4,}\b", all_b))
        shared_kw = sorted(a_words & b_words)
        return {
            "remedy_a": abbrev_a, "remedy_b": abbrev_b, "query": query,
            "overlapping_sections": shared, "a_only": a_only, "b_only": b_only,
            "shared_keywords": shared_kw[:50],
            "a_word_count": len(a_words), "b_word_count": len(b_words),
            "shared_word_count": len(shared_kw),
            "similarity_ratio": round(len(shared_kw) / max(len(a_words), len(b_words), 1), 4),
        }

    def list_remedies(self, author_filter=None):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        sql = "SELECT DISTINCT remedy_abbrev FROM materia_medica_entries"
        params = []
        if author_filter:
            sql += " WHERE author = ?"; params.append(author_filter)
        sql += " ORDER BY remedy_abbrev"
        c.execute(sql, params)
        rows = [r[0] for r in c.fetchall()]
        conn.close()
        return rows

    def list_sections(self, remedy_abbrev: str):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT DISTINCT section FROM materia_medica_entries WHERE remedy_abbrev = ? ORDER BY section", (remedy_abbrev,))
        rows = [r[0] for r in c.fetchall()]
        conn.close()
        return rows

    def add_proving_text(self, remedy_abbrev: str, author: str, section: str, text: str, remedy_id=None) -> int:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute(
            """INSERT OR REPLACE INTO materia_medica_entries
            (remedy_id, remedy_abbrev, author, section, text, metadata_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (remedy_id, remedy_abbrev, author, section, text,
             json.dumps({"added_manually": True, "timestamp": datetime.now().isoformat()}),
             datetime.now().isoformat())
        )
        row_id = c.lastrowid
        conn.commit()
        conn.close()
        self._rebuild_fts()
        return row_id

    def get_sources_for_remedy(self, remedy_abbrev: str):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""SELECT author, section, COUNT(*) FROM materia_medica_entries WHERE remedy_abbrev = ? GROUP BY author, section ORDER BY author, section""", (remedy_abbrev,))
        rows = c.fetchall()
        conn.close()
        return [{"author": r[0], "section": r[1], "entry_count": r[2]} for r in rows]
