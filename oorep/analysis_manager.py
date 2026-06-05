"""
Analysis Manager — Feature #16

RadarOpus-inspired analysis save/recall with versioning.
Captures repertorization snapshots so you can:
  - Save an analysis and name it
  - Auto-version when saving over the same consultation
  - Recall previous analyses for comparison
  - Compare two saved analyses side-by-side
  - Tag analyses as "baseline" for longitudinal tracking

Usage:
    from oorep.analysis_manager import AnalysisManager
    mgr = AnalysisManager()

    # Save a repertorization result
    analysis = mgr.save_analysis({
        "analysis_name": "MrsJ2024-Initial",
        "patient_pseudonym": "MrsJ2024",
        "consultation_id": "abc-123",      # optional; links to a consultation
        "symptoms": ["headache morning", "thirst small quantities"],
        "results": [{"abbrev": "Ars", "score": 34.0, "match_count": 13}, ...],
        "grade_mode": "full",
        "grade_weights": None,
        "clipboard_ids": ["clip-1"],
        "notes": "First repertorization before remedy selection",
        "is_baseline": True,
    })

    # List all analyses for a patient
    analyses = mgr.list_analyses(patient_pseudonym="MrsJ2024")

    # Recall a specific analysis
    recalled = mgr.get_analysis("analysis-id-123")

    # Compare two analyses
    diff = mgr.compare_analyses("id-a", "id-b")
"""

import json
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


class AnalysisManager:
    """
    Save, version, recall, and compare repertorization analyses.

    Schema:
      - ``analyses`` — analysis snapshots with auto-versioning per consultation
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Schema bootstrap ─────────────────────────────────────────────────────

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                analysis_id TEXT PRIMARY KEY,
                analysis_name TEXT NOT NULL,
                patient_pseudonym TEXT,
                consultation_id TEXT,
                version INTEGER DEFAULT 1,
                symptoms_json TEXT,
                results_json TEXT,
                grade_mode TEXT,
                grade_weights_json TEXT,
                clipboard_ids_json TEXT,
                is_baseline INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (consultation_id) REFERENCES consultations(consultation_id) ON DELETE SET NULL,
                FOREIGN KEY (patient_pseudonym) REFERENCES patients(pseudonym) ON DELETE SET NULL
            )
            """
        )

        # Indexes for fast lookups
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_patient ON analyses(patient_pseudonym)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_consult ON analyses(consultation_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_name ON analyses(analysis_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_baseline ON analyses(is_baseline)"
        )

        conn.commit()
        conn.close()

    # ── Save / Create ──────────────────────────────────────────────────────────

    def save_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a new analysis snapshot.

        If ``consultation_id`` is provided and an analysis already exists for
        that consultation, auto-increment version.

        Args:
            data: Dictionary with keys:
                - analysis_name (required)
                - patient_pseudonym (optional)
                - consultation_id (optional)
                - symptoms (list of strings)
                - results (list of remedy result dicts)
                - grade_mode (str)
                - grade_weights (dict or None)
                - clipboard_ids (list of strings)
                - is_baseline (bool)
                - notes (str)

        Returns:
            Saved analysis record with generated ``analysis_id`` and ``version``.
        """
        analysis_name = data.get("analysis_name", "").strip()
        if not analysis_name:
            raise ValueError("analysis_name is required")

        consultation_id = data.get("consultation_id")
        patient_pseudonym = data.get("patient_pseudonym")

        # Determine version
        version = 1
        if consultation_id:
            version = self._next_version_for_consultation(consultation_id)

        analysis_id = str(uuid.uuid4())[:12]
        now = datetime.now().isoformat()

        symptoms = data.get("symptoms", [])
        results = data.get("results", [])
        grade_weights = data.get("grade_weights")
        clipboard_ids = data.get("clipboard_ids", [])

        record = {
            "analysis_id": analysis_id,
            "analysis_name": analysis_name,
            "patient_pseudonym": patient_pseudonym,
            "consultation_id": consultation_id,
            "version": version,
            "symptoms": symptoms,
            "results": results,
            "grade_mode": data.get("grade_mode", "full"),
            "grade_weights": grade_weights,
            "clipboard_ids": clipboard_ids,
            "is_baseline": bool(data.get("is_baseline", False)),
            "notes": data.get("notes", ""),
            "created_at": now,
            "updated_at": now,
        }

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analyses (analysis_id, analysis_name, patient_pseudonym, consultation_id,
                version, symptoms_json, results_json, grade_mode, grade_weights_json,
                clipboard_ids_json, is_baseline, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["analysis_id"],
                record["analysis_name"],
                record["patient_pseudonym"],
                record["consultation_id"],
                record["version"],
                json.dumps(record["symptoms"]),
                json.dumps(record["results"]),
                record["grade_mode"],
                json.dumps(record["grade_weights"]) if record["grade_weights"] is not None else None,
                json.dumps(record["clipboard_ids"]),
                1 if record["is_baseline"] else 0,
                record["notes"],
                record["created_at"],
                record["updated_at"],
            ),
        )
        conn.commit()
        conn.close()
        return record

    def _next_version_for_consultation(self, consultation_id: str) -> int:
        """Return the next version number for a given consultation_id."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(version) FROM analyses WHERE consultation_id = ?",
            (consultation_id,),
        )
        row = cursor.fetchone()
        conn.close()
        max_ver = row[0] if row and row[0] is not None else 0
        return max_ver + 1

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single analysis by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT analysis_id, analysis_name, patient_pseudonym, consultation_id, "
            "version, symptoms_json, results_json, grade_mode, grade_weights_json, "
            "clipboard_ids_json, is_baseline, notes, created_at, updated_at "
            "FROM analyses WHERE analysis_id = ?",
            (analysis_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_analysis(row)

    def list_analyses(
        self,
        patient_pseudonym: Optional[str] = None,
        consultation_id: Optional[str] = None,
        baseline_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List analyses with optional filters.

        Args:
            patient_pseudonym: Filter by patient
            consultation_id: Filter by consultation
            baseline_only: Only return baseline-flagged analyses
            limit: Max results
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        conditions = []
        params = []
        if patient_pseudonym:
            conditions.append("patient_pseudonym = ?")
            params.append(patient_pseudonym)
        if consultation_id:
            conditions.append("consultation_id = ?")
            params.append(consultation_id)
        if baseline_only:
            conditions.append("is_baseline = 1")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor.execute(
            f"SELECT analysis_id, analysis_name, patient_pseudonym, consultation_id, "
            f"version, symptoms_json, results_json, grade_mode, grade_weights_json, "
            f"clipboard_ids_json, is_baseline, notes, created_at, updated_at "
            f"FROM analyses {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit],
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_analysis(r) for r in rows]

    def get_baseline_for_consultation(self, consultation_id: str) -> Optional[Dict[str, Any]]:
        """Return the baseline analysis for a consultation, or None."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT analysis_id, analysis_name, patient_pseudonym, consultation_id, "
            "version, symptoms_json, results_json, grade_mode, grade_weights_json, "
            "clipboard_ids_json, is_baseline, notes, created_at, updated_at "
            "FROM analyses WHERE consultation_id = ? AND is_baseline = 1 "
            "ORDER BY version DESC LIMIT 1",
            (consultation_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return self._row_to_analysis(row) if row else None

    # ── Update ─────────────────────────────────────────────────────────────────

    def update_analysis(self, analysis_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update analysis metadata (name, notes, is_baseline).
        Does NOT modify symptoms/results — create a new version instead.
        """
        allowed = {"analysis_name", "notes", "is_baseline"}
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            raise ValueError("No allowed fields to update. Only: analysis_name, notes, is_baseline")

        if "is_baseline" in fields:
            fields["is_baseline"] = 1 if fields["is_baseline"] else 0

        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [analysis_id]

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE analyses SET {set_clause} WHERE analysis_id = ?",
            values,
        )
        if cursor.rowcount == 0:
            conn.close()
            raise KeyError(f"Analysis '{analysis_id}' not found")
        conn.commit()
        conn.close()
        return self.get_analysis(analysis_id)

    # ── Delete ─────────────────────────────────────────────────────────────────

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis. Returns True if deleted."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE analysis_id = ?", (analysis_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ── Compare ────────────────────────────────────────────────────────────────

    def compare_analyses(self, analysis_id_a: str, analysis_id_b: str) -> Dict[str, Any]:
        """
        Side-by-side comparison of two saved analyses.

        Returns:
            Dict with common_top_remedies, changed_ranks, new_remedies, dropped_remedies,
            and a human-readable summary.
        """
        a = self.get_analysis(analysis_id_a)
        b = self.get_analysis(analysis_id_b)
        if not a or not b:
            missing = []
            if not a:
                missing.append(analysis_id_a)
            if not b:
                missing.append(analysis_id_b)
            raise KeyError(f"Analysis not found: {', '.join(missing)}")

        a_results = {r.get("abbrev", r.get("name", "?")): r for r in a.get("results", [])}
        b_results = {r.get("abbrev", r.get("name", "?")): r for r in b.get("results", [])}

        common = []
        changed = []
        new_remedies = []
        dropped = []

        for abbrev, a_r in a_results.items():
            if abbrev in b_results:
                b_r = b_results[abbrev]
                a_score = a_r.get("score", 0)
                b_score = b_r.get("score", 0)
                a_rank = list(a_results.keys()).index(abbrev) + 1
                b_rank = list(b_results.keys()).index(abbrev) + 1
                if a_score == b_score and a_rank == b_rank:
                    common.append({"abbrev": abbrev, "score": a_score, "rank": a_rank})
                else:
                    changed.append({
                        "abbrev": abbrev,
                        "old_score": a_score,
                        "new_score": b_score,
                        "old_rank": a_rank,
                        "new_rank": b_rank,
                        "score_delta": round(b_score - a_score, 2),
                        "rank_delta": a_rank - b_rank,
                    })
            else:
                dropped.append({"abbrev": abbrev, "score": a_r.get("score", 0)})

        for abbrev, b_r in b_results.items():
            if abbrev not in a_results:
                new_remedies.append({"abbrev": abbrev, "score": b_r.get("score", 0)})

        return {
            "analysis_a": {"id": a["analysis_id"], "name": a["analysis_name"], "version": a["version"]},
            "analysis_b": {"id": b["analysis_id"], "name": b["analysis_name"], "version": b["version"]},
            "common": common,
            "changed": changed,
            "new_remedies": new_remedies,
            "dropped_remedies": dropped,
            "total_in_a": len(a_results),
            "total_in_b": len(b_results),
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _row_to_analysis(self, row) -> Dict[str, Any]:
        symptoms = row[5]
        results = row[6]
        grade_weights = row[8]
        clipboard_ids = row[9]
        try:
            symptoms = json.loads(symptoms) if symptoms else []
        except Exception:
            symptoms = []
        try:
            results = json.loads(results) if results else []
        except Exception:
            results = []
        try:
            grade_weights = json.loads(grade_weights) if grade_weights else None
        except Exception:
            grade_weights = None
        try:
            clipboard_ids = json.loads(clipboard_ids) if clipboard_ids else []
        except Exception:
            clipboard_ids = []
        return {
            "analysis_id": row[0],
            "analysis_name": row[1],
            "patient_pseudonym": row[2],
            "consultation_id": row[3],
            "version": row[4],
            "symptoms": symptoms,
            "results": results,
            "grade_mode": row[7],
            "grade_weights": grade_weights,
            "clipboard_ids": clipboard_ids,
            "is_baseline": bool(row[10]),
            "notes": row[11],
            "created_at": row[12],
            "updated_at": row[13],
        }
