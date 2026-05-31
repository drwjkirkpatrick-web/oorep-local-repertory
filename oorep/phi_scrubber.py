"""
PHI Scrubber — Benefit #49

Detects and replaces Protected Health Information (PHI) in clinical text:
  - Names → [PATIENT]  (or reversible pseudonym [PT001])
  - Dates → [DATE]
  - SSN / national IDs → [ID]
  - Phone numbers → [PHONE]
  - Addresses → [ADDRESS]

In reversible mode, a mapping table in SQLite lets you restore original
values from their pseudonyms later.

Usage:
    from oorep.phi_scrubber import PHIScrubber
    scrubber = PHIScrubber(reversible=True)

    clean = scrubber.scrub("Alice lives at 123 Main St and her SSN is 123-45-6789.")
    # → "[PATIENT] lives at [ADDRESS] and her [ID] is [ID]."

    # Restore via reversible mapping
    real = scrubber.reveal("[PT001]")
"""

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


# ── Common name word list for lightweight NER heuristics ─────────────────────
_COMMON_FIRST_NAMES = frozenset([
    "james", "mary", "john", "patricia", "robert", "jennifer", "michael",
    "linda", "william", "elizabeth", "david", "barbara", "richard",
    "susan", "joseph", "jessica", "thomas", "sarah", "charles", "karen",
    "christopher", "nancy", "daniel", "lisa", "matthew", "betty",
    "anthony", "margaret", "mark", "sandra", "donald", "ashley",
    "steven", "kimberly", "paul", "emily", "andrew", "donna", "joshua",
    "michelle", "kenneth", "dorothy", "kevin", "carol", "brian", "amanda",
    "george", "melissa", "timothy", "deborah", "ronald", "stephanie",
    "edward", "rebecca", "jason", "sharon", "jeffrey", "laura", "ryan",
    "cynthia", "jacob", "kathleen", "gary", "amy", "nicholas", "angela",
    "eric", "shirley", "jonathan", "anna", "stephen", "brenda", "larry",
    "pamela", "justin", "emma", "scott", "nicole", "brandon", "helen",
    "benjamin", "samantha", "samuel", "katherine", "frank", "christine",
    "gregory", "debra", "raymond", "rachel", "alexander", "catherine",
    "patrick", "carolyn", "jack", "janet", "dennis", "ruth", "jerry",
    "maria", "tyler", "olivia", "aaron", "heather", "jose", "diane",
    "adam", "virginia", "nathan", "julie", "henry", "joyce",
    "walker", "alice", "clara", "mrs", "mr", "ms", "miss", "dr",
])

# ── Regex patterns for common PHI categories ─────────────────────────────────
_PHONE_PATTERNS = [
    r"\b\d{3}[\-\.\s]?\d{3}[\-\.\s]?\d{4}\b",           # US/CA phone
    r"\b\+?\d[\d\s\-\(\)]{7,20}\b",                     # loose international
]

_SSN_PATTERNS = [
    r"\b\d{3}[\-\s]?\d{2}[\-\s]?\d{4}\b",                # US SSN
    r"\b[A-Z]{0,2}[\-\s]?\d{6,10}[A-Z]{0,2}\b",         # generic national ID
]

_DATE_PATTERNS = [
    r"\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b",             # 05/30/2026
    r"\b\d{4}[\-/]\d{1,2}[\-/]\d{1,2}\b",               # 2026-05-30
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,)?\s+\d{4}\b",
]

# Simple address heuristic: digits + street-ish keywords
_ADDRESS_KEYWORDS = [
    "street", "st", "avenue", "ave", "road", "rd", "boulevard", "blvd",
    "drive", "dr", "lane", "ln", "way", "court", "ct", "circle", "cir",
    "highway", "hwy", "route", "rte", "parkway", "pkwy", "trail", "trl",
    "apartment", "apt", "suite", "unit", "floor", "building", "office",
    "zip", "postal",
]
_ADDRESS_PATTERNS = [
    # House number + street name + optional short suffix (#4, Suite B). Heavily bounded.
    r"\b\d+\s+[A-Za-z0-9\s]{0,20}(?:(?:" + "|".join(_ADDRESS_KEYWORDS) + r"))\b(?:[\s#]\w{0,8})?",
]

# Name detection heuristic: Title-cased words that look like given names
# (not at sentence start, and in common-name list or close to typical name shape)
_NAME_RE = re.compile(r"\b([A-Z][a-z]{1,15}(?:\s+[A-Z][a-z]{1,15}){0,2})\b")


class PHIScrubber:
    """
    Scrub PHI from clinical strings with optional reversible pseudonymisation.

    Reversible mode stores a mapping in ``phi_mappings`` so you can restore
    the original text later using ``reveal()``.
    """

    def __init__(
        self,
        reversible: bool = False,
        db_path: Optional[Path] = None,
        name_list: Optional[set] = None,
    ):
        """
        Args:
            reversible: If True, original values are mapped to stable
                        pseudonyms like ``[PT001]`` instead of generic tags.
            db_path: SQLite database path for the mapping table.
            name_list: Optional custom set of name strings to recognise.
        """
        self.reversible = reversible
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._names: set = name_list or set()
        self._pseudonym_counter = self._load_max_counter()

    def _init_db(self) -> None:
        """Create ``phi_mappings`` table for reversible scrubbing."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS phi_mappings (
                pseudonym TEXT PRIMARY KEY,
                real_value TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def _load_max_counter(self) -> int:
        """Return the highest existing pseudonym number so new IDs are unique."""
        if not self.reversible:
            return 0
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pseudonym FROM phi_mappings WHERE pseudonym LIKE 'PT%'"
        )
        rows = cursor.fetchall()
        conn.close()
        max_n = 0
        for (p,) in rows:
            digits = re.sub(r"\D", "", p)
            if digits.isdigit():
                max_n = max(max_n, int(digits))
        return max_n

    def _next_pseudonym(self, phi_type: str) -> str:
        """Generate a new reversible pseudonym (e.g. ``[PT001]``)."""
        self._pseudonym_counter += 1
        return f"[PT{self._pseudonym_counter:03d}]"

    def _store_mapping(self, pseudonym: str, real_value: str, phi_type: str) -> None:
        """Persist a pseudonym → real value mapping."""
        if not self.reversible:
            return
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO phi_mappings (pseudonym, real_value, type, created_at) VALUES (?, ?, ?, ?)",
            (pseudonym, real_value, phi_type, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    # ── Scrubbing API ─────────────────────────────────────────────────────────

    def scrub(self, text: str) -> str:
        """
        Replace PHI in ``text`` with safe tags (or reversible pseudonyms).

        Returns:
            Scrubbed text string.
        """
        if not text:
            return text
        # Work on a copy; track replacements so overlapping patterns behave deterministically.
        scrubbed = text
        scrubbed = self._scrub_addresses(scrubbed)
        scrubbed = self._scrub_phones(scrubbed)
        scrubbed = self._scrub_ssn(scrubbed)
        scrubbed = self._scrub_dates(scrubbed)
        scrubbed = self._scrub_names(scrubbed)
        return scrubbed

    def scrub_case_notes(self, case_notes: Any) -> Any:
        """
        Recursively scrub PHI from a dict / list / string structure.

        Args:
            case_notes: Arbitrary nested JSON-like structure.

        Returns:
            Same shape with all strings scrubbed.
        """
        if isinstance(case_notes, str):
            return self.scrub(case_notes)
        if isinstance(case_notes, list):
            return [self.scrub_case_notes(item) for item in case_notes]
        if isinstance(case_notes, dict):
            return {k: self.scrub_case_notes(v) for k, v in case_notes.items()}
        return case_notes

    # ── Individual scrubbers ────────────────────────────────────────────────

    def _scrub_phones(self, text: str) -> str:
        for pat in _PHONE_PATTERNS:
            text = re.sub(pat, lambda m: self._tag_or_pseudo(m.group(0), "phone"), text)
        return text

    def _scrub_ssn(self, text: str) -> str:
        for pat in _SSN_PATTERNS:
            text = re.sub(pat, lambda m: self._tag_or_pseudo(m.group(0), "ssn"), text)
        return text

    def _scrub_dates(self, text: str) -> str:
        for pat in _DATE_PATTERNS:
            text = re.sub(pat, lambda m: self._tag_or_pseudo(m.group(0), "date"), text)
        return text

    def _scrub_addresses(self, text: str) -> str:
        for pat in _ADDRESS_PATTERNS:
            text = re.sub(
                pat,
                lambda m: self._tag_or_pseudo(m.group(0).strip(), "address"),
                text,
                flags=re.IGNORECASE,
            )
        return text

    def _scrub_names(self, text: str) -> str:
        """
        Replace probable person names.

        Heuristic:
          - Match Title-case word sequences (1–3 words).
          - Skip if the word is at sentence start (common false positive).
          - Keep if the word is in the known-name list OR common suffixes.
        """
        # Build a set from common first names + any caller-supplied names
        known = _COMMON_FIRST_NAMES | self._names

        def replacer(match: re.Match) -> str:
            raw = match.group(1)
            parts = raw.split()
            # Heuristic: at least one word must look like a known name
            looks_like_name = any(p.lower() in known for p in parts)
            if not looks_like_name and len(parts) > 1:
                # If multi-word, and initials, skip
                if all(len(p) <= 2 for p in parts):
                    return raw
            if not looks_like_name:
                # Still suspicious if capitalised in mid-sentence without prior sentence end
                start = match.start()
                preceding = text[max(0, start - 2):start]
                if preceding not in (" ", "\n", ",", ";", ":", "-"):
                    return raw
            return self._tag_or_pseudo(raw, "name")

        scrubbed = _NAME_RE.sub(replacer, text)
        return scrubbed

    def _tag_or_pseudo(self, value: str, phi_type: str) -> str:
        """Return a generic tag or a reversible pseudonym for a PHI value."""
        if not self.reversible:
            tag_map = {
                "name": "[PATIENT]",
                "date": "[DATE]",
                "ssn": "[ID]",
                "phone": "[PHONE]",
                "address": "[ADDRESS]",
            }
            return tag_map.get(phi_type, "[REDACTED]")
        # Reversible mode: use or create a pseudonym
        existing = self.get_pseudonym(value)
        if existing:
            return existing
        new_pseudo = self._next_pseudonym(phi_type)
        self._store_mapping(new_pseudo, value, phi_type)
        return new_pseudo

    # ── Reversible mapping API ────────────────────────────────────────────────

    def get_pseudonym(self, real_value: str) -> Optional[str]:
        """
        Return an existing pseudonym for a real value, or ``None``.
        """
        if not self.reversible:
            return None
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pseudonym FROM phi_mappings WHERE real_value = ?",
            (real_value,),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def reveal(self, pseudonym: str) -> Optional[str]:
        """
        Back-convert a pseudonym to its original real value.

        Returns:
            Original string or ``None`` if no mapping exists.
        """
        if not self.reversible:
            return None
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT real_value FROM phi_mappings WHERE pseudonym = ?",
            (pseudonym,),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def restore_text(self, scrubbed_text: str) -> str:
        """
        Restore all pseudonyms in a scrubbed string back to original values.

        Non-mapped tokens are left untouched.
        """
        if not self.reversible:
            return scrubbed_text
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT pseudonym, real_value FROM phi_mappings")
        mappings = dict(cursor.fetchall())
        conn.close()
        restored = scrubbed_text
        for pseudo, real in mappings.items():
            restored = restored.replace(pseudo, real)
        return restored

    def list_mappings(self, limit: int = 200) -> List[Dict[str, str]]:
        """Return all stored PHI mappings for audit / review."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pseudonym, real_value, type, created_at FROM phi_mappings ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "pseudonym": r[0],
                "real_value": r[1],
                "type": r[2],
                "created_at": r[3],
            }
            for r in rows
        ]
