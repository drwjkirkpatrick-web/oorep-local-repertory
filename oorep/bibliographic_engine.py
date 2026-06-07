"""
Bibliographic Citation Engine — Feature #26

Track and cite sources for every rubric, remedy, and clinical decision.
Link rubrics to original provings (Hahnemann, Kent, Allen, etc.).
Generate footnotes for repertorization printouts.
Support BibTeX, Vancouver, and plain citation formats.
Enable evidence-based homeopathic practice documentation.

Usage:
    from oorep.bibliographic_engine import BibliographicEngine

    engine = BibliographicEngine()

    # Register a classical source
    engine.register_source(
        source_id="hahnemann_1810",
        title="Organon of Medicine",
        author="Hahnemann, Samuel",
        year=1810,
        edition="6th",
        publisher="Dudens",
        url="https://archive.org/details/organonofmedicin00hahn",
    )

    # Link a rubric to a source
    engine.link_rubric_to_source(rubric_id=12345, source_id="kent_1900", page="247")

    # Get citations for a remedy
    cites = engine.get_remedy_citations("ARS")

    # Format a bibliography for a repertorization
    bib = engine.format_bibliography(
        rubric_ids=[12345, 67890],
        remedies=["ARS", "PULS"],
        style="vancouver",
    )
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


# ──────────────────────────────────────────────────────────────────────────────
# Constants — Classical homeopathic bibliography
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_CLASSICAL_SOURCES: Dict[str, Dict[str, Any]] = {
    "hahnemann_1810": {
        "title": "Organon of the Art of Healing",
        "author": "Hahnemann, Samuel",
        "year": 1810,
        "edition": "1st",
        "publisher": "Arnoldischen Buchhandlung, Leipzig",
        "type": "treatise",
    },
    "hahnemann_1842": {
        "title": "Organon of Medicine",
        "author": "Hahnemann, Samuel",
        "year": 1842,
        "edition": "6th",
        "publisher": "Schwabe, Leipzig",
        "type": "treatise",
    },
    "hahnemann_1828": {
        "title": "Chronic Diseases, Their Nature and Homeopathic Cure",
        "author": "Hahnemann, Samuel",
        "year": 1828,
        "edition": "1st",
        "publisher": "Arnoldischen Buchhandlung, Leipzig",
        "type": "treatise",
    },
    "kent_1900": {
        "title": "Lectures on Homeopathic Materia Medica",
        "author": "Kent, James Tyler",
        "year": 1900,
        "edition": "1st",
        "publisher": "Ehrhart & Karl, Chicago",
        "type": "materia_medica",
    },
    "kent_1897": {
        "title": "Repertory of the Homeopathic Materia Medica",
        "author": "Kent, James Tyler",
        "year": 1897,
        "edition": "1st",
        "publisher": "Ehrhart & Karl, Chicago",
        "type": "repertory",
    },
    "allen_1874": {
        "title": "Handbook of Materia Medica and Homeopathic Therapeutics",
        "author": "Allen, Timothy Field",
        "year": 1874,
        "edition": "1st",
        "publisher": "Boericke & Tafel, Philadelphia",
        "type": "materia_medica",
    },
    "boenninghausen_1846": {
        "title": "The Therapeutic Pocketbook",
        "author": "Boenninghausen, Clemens von",
        "year": 1846,
        "edition": "1st",
        "publisher": "Bonn",
        "type": "repertory",
    },
    "hering_1879": {
        "title": "Guiding Symptoms of Our Materia Medica",
        "author": "Hering, Constantine",
        "year": 1879,
        "edition": "1st",
        "publisher": "American Homeopathic Publishing, Philadelphia",
        "type": "materia_medica",
    },
    "clarke_1900": {
        "title": "A Dictionary of Practical Materia Medica",
        "author": "Clarke, John Henry",
        "year": 1900,
        "edition": "1st",
        "publisher": "Homeopathic Publishing, London",
        "type": "materia_medica",
    },
    "nash_1898": {
        "title": "Leaders in Homeopathic Therapeutics",
        "author": "Nash, Eugene Beauharnais",
        "year": 1898,
        "edition": "1st",
        "publisher": "Boericke & Runyon, New York",
        "type": "materia_medica",
    },
    "boger_1905": {
        "title": "Boenninghausen's Characteristics and Repertory",
        "author": "Boger, Cyrus Maxwell",
        "year": 1905,
        "edition": "1st",
        "publisher": "Boericke & Tafel, Philadelphia",
        "type": "repertory",
    },
    "herscu_1996": {
        "title": "Stramonium: With an Introduction to Analysis Using Cycles and Segments",
        "author": "Herscu, Paul",
        "year": 1996,
        "edition": "1st",
        "publisher": "NESH Press, Amherst, MA",
        "type": "monograph",
    },
    "oorep_2024": {
        "title": "Open Online Repertory (OOREP) Database",
        "author": "Bauer, Andreas",
        "year": 2024,
        "edition": "Publicum",
        "publisher": "OOREP Project",
        "url": "https://www.oorep.com/",
        "type": "database",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Source:
    source_id: str
    title: str
    author: str
    year: int
    edition: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    type: str = "other"  # treatise | materia_medica | repertory | monograph | database | other

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CitationLink:
    rubric_id: Optional[int] = None
    remedy_abbrev: Optional[str] = None
    source_id: str = ""
    page: Optional[str] = None
    volume: Optional[str] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# BibliographicEngine
# ──────────────────────────────────────────────────────────────────────────────

class BibliographicEngine:
    """
    Bibliographic Citation Engine for homeopathic repertory work.

    SQLite-backed with:
    - sources table: classical proving and reference works
    - citation_links table: many-to-many rubric↔source and remedy↔source links
    """

    def __init__(self, db_path: Optional[Path] = None, repertory: Optional[Any] = None):
        self.db_path = Path(db_path) if db_path else Path.home() / "projects" / "oorep-local-repertory" / "data" / "bibliography.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.rep = repertory
        self._init_db()
        self._seed_classical_sources()

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                year INTEGER,
                edition TEXT,
                publisher TEXT,
                url TEXT,
                type TEXT DEFAULT 'other'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS citation_links (
                link_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rubric_id INTEGER,
                remedy_abbrev TEXT,
                source_id TEXT NOT NULL,
                page TEXT,
                volume TEXT,
                notes TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
            )
        """)

        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_citation_rubric ON citation_links(rubric_id)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_citation_remedy ON citation_links(remedy_abbrev)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_citation_source ON citation_links(source_id)
        """)

        conn.commit()
        conn.close()

    def _seed_classical_sources(self) -> None:
        """Pre-populate classical homeopathic bibliography if empty."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sources")
        count = c.fetchone()[0]
        if count == 0:
            for sid, data in DEFAULT_CLASSICAL_SOURCES.items():
                c.execute("""
                    INSERT OR IGNORE INTO sources (source_id, title, author, year, edition, publisher, url, type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sid,
                    data.get("title", ""),
                    data.get("author", ""),
                    data.get("year", 0),
                    data.get("edition"),
                    data.get("publisher"),
                    data.get("url"),
                    data.get("type", "other"),
                ))
            conn.commit()
        conn.close()

    # ── Source CRUD ───────────────────────────────────────────────────────────

    def register_source(
        self,
        source_id: str,
        title: str,
        author: str = "",
        year: int = 0,
        edition: Optional[str] = None,
        publisher: Optional[str] = None,
        url: Optional[str] = None,
        type: str = "other",
    ) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO sources (source_id, title, author, year, edition, publisher, url, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, title, author, year, edition, publisher, url, type))
        conn.commit()
        conn.close()
        return True

    def get_source(self, source_id: str) -> Optional[Source]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT source_id, title, author, year, edition, publisher, url, type FROM sources WHERE source_id = ?", (source_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return Source(*row)

    def list_sources(self, type_filter: Optional[str] = None) -> List[Source]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        if type_filter:
            c.execute("SELECT * FROM sources WHERE type = ? ORDER BY year", (type_filter,))
        else:
            c.execute("SELECT * FROM sources ORDER BY year")
        rows = c.fetchall()
        conn.close()
        return [Source(*r) for r in rows]

    def delete_source(self, source_id: str) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))
        conn.commit()
        affected = c.rowcount > 0
        conn.close()
        return affected

    # ── Citation links ────────────────────────────────────────────────────────

    def link_rubric_to_source(
        self,
        rubric_id: int,
        source_id: str,
        page: Optional[str] = None,
        volume: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO citation_links (rubric_id, source_id, page, volume, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (rubric_id, source_id, page, volume, notes))
        conn.commit()
        conn.close()
        return True

    def link_remedy_to_source(
        self,
        remedy_abbrev: str,
        source_id: str,
        page: Optional[str] = None,
        volume: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO citation_links (remedy_abbrev, source_id, page, volume, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (remedy_abbrev, source_id, page, volume, notes))
        conn.commit()
        conn.close()
        return True

    def get_rubric_citations(self, rubric_id: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            SELECT s.source_id, s.title, s.author, s.year, s.edition, s.type,
                   cl.page, cl.volume, cl.notes
            FROM citation_links cl
            JOIN sources s ON cl.source_id = s.source_id
            WHERE cl.rubric_id = ?
            ORDER BY s.year
        """, (rubric_id,))
        rows = c.fetchall()
        conn.close()
        return [
            {
                "source_id": r[0], "title": r[1], "author": r[2], "year": r[3],
                "edition": r[4], "type": r[5], "page": r[6], "volume": r[7], "notes": r[8],
            }
            for r in rows
        ]

    def get_remedy_citations(self, remedy_abbrev: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            SELECT s.source_id, s.title, s.author, s.year, s.edition, s.type,
                   cl.page, cl.volume, cl.notes
            FROM citation_links cl
            JOIN sources s ON cl.source_id = s.source_id
            WHERE cl.remedy_abbrev = ?
            ORDER BY s.year
        """, (remedy_abbrev,))
        rows = c.fetchall()
        conn.close()
        return [
            {
                "source_id": r[0], "title": r[1], "author": r[2], "year": r[3],
                "edition": r[4], "type": r[5], "page": r[6], "volume": r[7], "notes": r[8],
            }
            for r in rows
        ]

    def get_source_citations(self, source_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Return all rubrics and remedies linked to a given source."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT rubric_id, remedy_abbrev, page, notes FROM citation_links WHERE source_id = ?", (source_id,))
        rows = c.fetchall()
        conn.close()
        rubrics = []
        remedies = []
        for rid, rem, page, notes in rows:
            entry = {"page": page, "notes": notes}
            if rid is not None:
                entry["rubric_id"] = rid
                rubrics.append(entry)
            if rem is not None:
                entry["remedy_abbrev"] = rem
                remedies.append(entry)
        return {"rubrics": rubrics, "remedies": remedies}

    # ── Formatting ─────────────────────────────────────────────────────────────

    @staticmethod
    def format_vancouver(source: Source) -> str:
        ed = f", {source.edition} ed." if source.edition else ""
        pub = f". {source.publisher}" if source.publisher else ""
        return f"{source.author}. {source.title}{ed}{pub}; {source.year}."

    @staticmethod
    def format_bibtex(source: Source) -> str:
        key = source.source_id.replace(" ", "_").lower()
        return (
            f"@book{{{key},\n"
            f"  author = {{{source.author}}},\n"
            f"  title = {{{source.title}}},\n"
            f"  year = {{{source.year}}},\n"
            f"  edition = {{{source.edition or ''}}},\n"
            f"  publisher = {{{source.publisher or ''}}},\n"
            f"  type = {{{source.type}}}\n"
            f"}}"
        )

    @staticmethod
    def format_plain(source: Source) -> str:
        ed = f" ({source.edition} ed.)" if source.edition else ""
        return f"{source.author}. '{source.title}'{ed}. {source.publisher or 'Unknown publisher'}, {source.year}."

    def format_source(self, source_id: str, style: str = "vancouver") -> Optional[str]:
        source = self.get_source(source_id)
        if not source:
            return None
        if style == "vancouver":
            return self.format_vancouver(source)
        if style == "bibtex":
            return self.format_bibtex(source)
        return self.format_plain(source)

    def format_bibliography(
        self,
        rubric_ids: Optional[List[int]] = None,
        remedies: Optional[List[str]] = None,
        style: str = "vancouver",
    ) -> Dict[str, Any]:
        """
        Generate a formatted bibliography for a set of rubrics and/or remedies.
        """
        source_ids: Set[str] = set()

        if rubric_ids:
            for rid in rubric_ids:
                cites = self.get_rubric_citations(rid)
                for c in cites:
                    source_ids.add(c["source_id"])

        if remedies:
            for rem in remedies:
                cites = self.get_remedy_citations(rem)
                for c in cites:
                    source_ids.add(c["source_id"])

        # Always include OOREP database citation
        source_ids.add("oorep_2024")

        entries = []
        for sid in sorted(source_ids):
            fmt = self.format_source(sid, style=style)
            if fmt:
                source = self.get_source(sid)
                entries.append({
                    "source_id": sid,
                    "formatted": fmt,
                    "style": style,
                    "source": source.to_dict() if source else None,
                })

        return {
            "style": style,
            "entry_count": len(entries),
            "entries": entries,
        }

    def footnote_for_rubric(self, rubric_id: int, style: str = "vancouver") -> Optional[str]:
        """Return a footnote string for a rubric's primary source."""
        cites = self.get_rubric_citations(rubric_id)
        if not cites:
            return None
        primary = cites[0]
        source = self.get_source(primary["source_id"])
        if not source:
            return None
        page = f", p. {primary['page']}" if primary.get("page") else ""
        if style == "vancouver":
            return f"{source.author}, {source.year}{page}."
        return f"{source.author}, '{source.title}'{page} ({source.year})."

    # ── Analysis ──────────────────────────────────────────────────────────────

    def get_source_coverage_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sources")
        total_sources = c.fetchone()[0]

        c.execute("SELECT type, COUNT(*) FROM sources GROUP BY type")
        by_type = {r[0]: r[1] for r in c.fetchall()}

        c.execute("SELECT COUNT(DISTINCT rubric_id) FROM citation_links WHERE rubric_id IS NOT NULL")
        rubrics_cited = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(DISTINCT remedy_abbrev) FROM citation_links WHERE remedy_abbrev IS NOT NULL")
        remedies_cited = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM citation_links")
        total_links = c.fetchone()[0] or 0

        conn.close()
        return {
            "total_sources": total_sources,
            "by_type": by_type,
            "rubrics_with_citations": rubrics_cited,
            "remedies_with_citations": remedies_cited,
            "total_citation_links": total_links,
        }

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 26,
            "feature_name": "Bibliographic Citation Engine",
            "version": "1.0",
            "supports": ["source_registration", "rubric_links", "remedy_links",
                         "vancouver", "bibtex", "plain", "bibliography_generation",
                         "footnote_generation", "coverage_stats"],
            "classical_sources_preloaded": len(DEFAULT_CLASSICAL_SOURCES),
        }
