"""
SOAP Assembler — Benefit #31

Assembles structured SOAP notes from case data or raw conversational text.
Integrates with the OOREP repertory so each SOAP note carries a
repertorization rationale tied to selected rubric IDs.

Usage:
    from oorep.soap_assembler import SOAPAssembler
    assembler = SOAPAssembler()

    # From pre-structured case data
    note = assembler.assemble_from_case({
        "subjective": "Patient reports headache worse in morning",
        "objective": "Pulse 72, BP 120/80",
        "assessment": "Acute headache, possible remedy match",
        "plan": "Prescribe Nux-v. 30C",
    })

    # From free-form conversation text
    parsed = assembler.assemble_from_conversation(
        text="The patient says she wakes with a splitting headache...",
        rubric_ids=[12345, 67890],
    )
"""

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


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


class SOAPAssembler:
    """
    Assemble and persist structured SOAP notes.

    Stores notes in a SQLite ``soap_notes`` table keyed by ``case_id``.
    Supports both structured input and template-driven parsing from
    unstructured clinical text (no external LLM required).
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Args:
            db_path: Path to SQLite database. Defaults to the project
                     feedback database so SOAP notes live alongside
                     prescriptions and outcomes.
        """
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Ensure the ``soap_notes`` table exists."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS soap_notes (
                case_id TEXT PRIMARY KEY,
                patient_pseudonym TEXT,
                sections_json TEXT NOT NULL,
                rubric_ids_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_soap_patient
            ON soap_notes(patient_pseudonym)
            """
        )
        conn.commit()
        conn.close()

    # ── Structured assembly ───────────────────────────────────────────────────

    def assemble_from_case(
        self,
        case_data: Dict[str, Any],
        patient_pseudonym: Optional[str] = None,
        rubric_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Build a structured SOAP note from pre-structured case data.

        Args:
            case_data: Dictionary containing at least subjective/objective/
                       assessment/plan keys. Additional keys are preserved.
            patient_pseudonym: Optional patient identifier (pseudonymized).
            rubric_ids: Optional list of OOREP rubric IDs tied to this case.

        Returns:
            Dict with ``case_id``, ``patient_pseudonym``, ``sections``,
            ``rubric_ids``, ``repertory_rationale``, and ``created_at``.
        """
        sections = {
            "subjective": case_data.get("subjective", "").strip(),
            "objective": case_data.get("objective", "").strip(),
            "assessment": case_data.get("assessment", "").strip(),
            "plan": case_data.get("plan", "").strip(),
        }
        # Preserve any extra keys the caller provided
        for key, value in case_data.items():
            if key not in sections:
                sections[key] = value

        rubric_ids = rubric_ids or []
        rationale = self._build_repertory_rationale(rubric_ids)

        case_id = case_data.get("case_id") or str(uuid.uuid4())[:12]
        record = {
            "case_id": case_id,
            "patient_pseudonym": patient_pseudonym,
            "sections": sections,
            "rubric_ids": rubric_ids,
            "repertory_rationale": rationale,
            "created_at": datetime.now().isoformat(),
        }

        self._persist(record)
        return record

    # ── Conversation / free-text parsing ──────────────────────────────────────

    def assemble_from_conversation(
        self,
        text: str,
        rubric_ids: Optional[List[int]] = None,
        patient_pseudonym: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract subjective / objective / assessment / plan from raw
        conversational text using lightweight template heuristics.

        No external LLM is used; parsing relies on keyword-section mapping
        and regex boundaries so it runs entirely offline on the local Jetson.

        Args:
            text: Raw case narrative or transcript.
            rubric_ids: Optional OOREP rubric IDs to attach.
            patient_pseudonym: Optional patient pseudonym.

        Returns:
            Structured SOAP dict (same schema as ``assemble_from_case``).
        """
        sections = self._parse_sections(text)
        rubric_ids = rubric_ids or []
        rationale = self._build_repertory_rationale(rubric_ids)

        case_id = str(uuid.uuid4())[:12]
        record = {
            "case_id": case_id,
            "patient_pseudonym": patient_pseudonym,
            "sections": sections,
            "rubric_ids": rubric_ids,
            "repertory_rationale": rationale,
            "created_at": datetime.now().isoformat(),
        }

        self._persist(record)
        return record

    def _parse_sections(self, text: str) -> Dict[str, str]:
        """
        Template-driven section extraction.

        Recognises explicit SOAP headers ("Subjective:", "S:", etc.) or
        falls back to keyword heuristics when headers are missing.
        """
        text = text.strip()
        lower = text.lower()

        # Explicit SOAP markers
        markers = [
            ("subjective", r"(?:subjective|subj?|s)[\s]*[:\-–—]"),
            ("objective", r"(?:objective|obj|o)[\s]*[:\-–—]"),
            ("assessment", r"(?:assessment|assess|a)[\s]*[:\-–—]"),
            ("plan", r"(?:plan|p)[\s]*[:\-–—]"),
        ]

        found_positions: List[tuple] = []
        for section_name, pattern in markers:
            for match in re.finditer(pattern, lower):
                start = match.start()
                found_positions.append((start, section_name, match.end()))

        if len(found_positions) >= 3:
            # Sort by position and slice between markers
            found_positions.sort(key=lambda x: x[0])
            parts: Dict[str, str] = {}
            for i, (pos, name, end) in enumerate(found_positions):
                nxt = found_positions[i + 1][0] if i + 1 < len(found_positions) else len(text)
                parts[name] = text[end:nxt].strip()
            # Ensure all 4 sections exist
            for key in ("subjective", "objective", "assessment", "plan"):
                parts.setdefault(key, "")
            return parts

        # ── Fallback heuristic parsing ───────────────────────────────────────
        parts: Dict[str, str] = {
            "subjective": "",
            "objective": "",
            "assessment": "",
            "plan": "",
        }

        # Objective markers (vitals, physical findings)
        obj_markers = [
            "pulse", "bp", "blood pressure", "temperature", "temp ",
            "heart rate", "respiratory rate", "o/e", "on examination",
            "physical exam", "auscultation", "inspection", "percussion",
        ]
        # Assessment markers
        assess_markers = [
            "diagnosis", "differential", "impression", "assessment",
            "clinical picture", "most likely", "appears to be",
        ]
        # Plan markers
        plan_markers = [
            "prescribe", "prescription", "follow up", "follow-up",
            "repertorization", "remedy", "potency", "dose", "dosing",
            "next visit", "monitor", "advice", "recommend",
        ]

        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            s_lower = sentence.lower()
            # Categorise by keyword; subjective is the default catch-all
            if any(m in s_lower for m in plan_markers):
                parts["plan"] += sentence + " "
            elif any(m in s_lower for m in assess_markers):
                parts["assessment"] += sentence + " "
            elif any(m in s_lower for m in obj_markers):
                parts["objective"] += sentence + " "
            else:
                parts["subjective"] += sentence + " "

        return {k: v.strip() for k, v in parts.items()}

    # ── Repertory rationale builder ───────────────────────────────────────────

    def _build_repertory_rationale(self, rubric_ids: List[int]) -> str:
        """
        Generate a short rationale string summarising why the attached
        rubric IDs were selected for this case.
        """
        if not rubric_ids:
            return "No rubrics selected."
        return (
            f"Case linked to {len(rubric_ids)} rubric(s). "
            f"Repertorization based on symptom totality covering rubric IDs: {rubric_ids}."
        )

    # ── Persistence helpers ─────────────────────────────────────────────────

    def _persist(self, record: Dict[str, Any]) -> None:
        """Upsert a SOAP record into SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO soap_notes (case_id, patient_pseudonym, sections_json, rubric_ids_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                patient_pseudonym=excluded.patient_pseudonym,
                sections_json=excluded.sections_json,
                rubric_ids_json=excluded.rubric_ids_json,
                updated_at=excluded.updated_at
            """,
            (
                record["case_id"],
                record.get("patient_pseudonym"),
                json.dumps(record["sections"]),
                json.dumps(record.get("rubric_ids", [])),
                record["created_at"],
                record["created_at"],
            ),
        )
        conn.commit()
        conn.close()

    # ── Retrieval API ───────────────────────────────────────────────────────

    def get_soap(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single SOAP note by ``case_id``.

        Returns:
            Full SOAP dict or ``None`` if not found.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT case_id, patient_pseudonym, sections_json, rubric_ids_json, created_at, updated_at "
            "FROM soap_notes WHERE case_id = ?",
            (case_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "case_id": row[0],
            "patient_pseudonym": row[1],
            "sections": json.loads(row[2]) if row[2] else {},
            "rubric_ids": json.loads(row[3]) if row[3] else [],
            "created_at": row[4],
            "updated_at": row[5],
        }

    def list_soaps(self, patient_pseudonym: str) -> List[Dict[str, Any]]:
        """
        List all SOAP notes for a given patient pseudonym,
        ordered by creation time (newest first).
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT case_id, patient_pseudonym, sections_json, rubric_ids_json, created_at, updated_at "
            "FROM soap_notes WHERE patient_pseudonym = ? ORDER BY created_at DESC",
            (patient_pseudonym,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "case_id": r[0],
                "patient_pseudonym": r[1],
                "sections": json.loads(r[2]) if r[2] else {},
                "rubric_ids": json.loads(r[3]) if r[3] else [],
                "created_at": r[4],
                "updated_at": r[5],
            }
            for r in rows
        ]

    def update_soap(
        self,
        case_id: str,
        sections: Dict[str, str],
        rubric_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing SOAP note's sections (and optionally rubric IDs).

        Args:
            case_id: Existing SOAP case ID.
            sections: New sections dict; will be merged with existing keys
                      unless the caller supplies a complete replacement.
            rubric_ids: Optional new rubric list (replaces existing if given).

        Returns:
            Updated SOAP dict.

        Raises:
            KeyError: If ``case_id`` does not exist.
        """
        existing = self.get_soap(case_id)
        if not existing:
            raise KeyError(f"SOAP note with case_id={case_id} not found")

        updated_sections = {**existing["sections"], **sections}
        updated_rubric_ids = rubric_ids if rubric_ids is not None else existing.get("rubric_ids", [])
        rationale = self._build_repertory_rationale(updated_rubric_ids)

        updated = {
            "case_id": case_id,
            "patient_pseudonym": existing.get("patient_pseudonym"),
            "sections": updated_sections,
            "rubric_ids": updated_rubric_ids,
            "repertory_rationale": rationale,
            "created_at": existing.get("created_at"),
            "updated_at": datetime.now().isoformat(),
        }

        self._persist(updated)
        return updated
