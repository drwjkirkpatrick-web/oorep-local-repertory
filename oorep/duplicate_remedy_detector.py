"""
Duplicate Remedy Detector — Antidote & Inimical Prescription Warnings

Prevents prescribing remedies that are antidotes or inimical to
previously prescribed remedies.
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class DuplicateRemedyDetector:
    """
    Check remedy prescriptions against relationship rules:
      - Antidotes: remedy A antidotes remedy B
      - Inimical: remedy A and B should not follow each other
      - Complementary: safe but noted for reference
    """

    def __init__(self, db_path: str = "data/remedy_relationships.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()
        self._seed_defaults()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY,
                case_id TEXT NOT NULL,
                remedy TEXT NOT NULL,
                potency TEXT,
                date TEXT NOT NULL,
                practitioner TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relationship_rules (
                remedy_a TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                remedy_b TEXT NOT NULL,
                source TEXT,
                PRIMARY KEY (remedy_a, relation_type, remedy_b)
            )
        """)
        conn.commit()
        conn.close()

    def _seed_defaults(self):
        defaults = [
            ("NUX-V", "antidote", "PULS", "Clarke"),
            ("PULS", "antidote", "NUX-V", "Clarke"),
            ("COFF", "antidote", "NUX-V", "Hahnemann"),
            ("COFF", "antidote", "IGN", "Hahnemann"),
            ("IGN", "antidote", "COFF", "Hahnemann"),
            ("NUX-V", "inimical", "IGN", "Kent"),
            ("IGN", "inimical", "NUX-V", "Kent"),
            ("LYC", "complementary", "PULS", "Boenninghausen"),
            ("SULPH", "complementary", "NUX-V", "Boenninghausen"),
            ("SIL", "complementary", "PULS", "Boenninghausen"),
        ]
        conn = sqlite3.connect(str(self.db_path))
        conn.executemany(
            "INSERT OR IGNORE INTO relationship_rules VALUES (?,?,?,?)",
            defaults
        )
        conn.commit()
        conn.close()

    def add_prescription(self, case_id: str, remedy: str, potency: str,
                         date: str, practitioner: str = "") -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO prescriptions (case_id, remedy, potency, date, practitioner) VALUES (?,?,?,?,?)",
            (case_id, remedy, potency, date, practitioner)
        )
        conn.commit()
        conn.close()
        return {"case_id": case_id, "remedy": remedy, "potency": potency, "date": date}

    def get_prescription_history(self, case_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT remedy, potency, date, practitioner FROM prescriptions WHERE case_id = ? ORDER BY date DESC LIMIT ?",
            (case_id, limit)
        ).fetchall()
        conn.close()
        return [
            {"remedy": r[0], "potency": r[1], "date": r[2], "practitioner": r[3]}
            for r in rows
        ]

    def check_interactions(self, case_id: str, proposed_remedy: str) -> Dict[str, Any]:
        """
        Check proposed remedy against all previous prescriptions for this case.
        Returns warnings, safe_to_prescribe flag, and reasoning.
        """
        history = self.get_prescription_history(case_id)
        if not history:
            return {"safe": True, "warnings": [], "reason": "No prior prescriptions"}

        warnings = []
        for prev in history:
            prev_remedy = prev["remedy"]
            if prev_remedy == proposed_remedy:
                warnings.append({
                    "type": "duplicate",
                    "severity": "info",
                    "message": f"{proposed_remedy} was previously prescribed on {prev['date']}. Consider if repetition or potency change is appropriate.",
                    "previous": prev,
                })
                continue

            conn = sqlite3.connect(str(self.db_path))
            # Check A → B
            rows = conn.execute(
                "SELECT relation_type, source FROM relationship_rules WHERE remedy_a = ? AND remedy_b = ?",
                (prev_remedy, proposed_remedy)
            ).fetchall()
            # Check B → A
            rows += conn.execute(
                "SELECT relation_type, source FROM relationship_rules WHERE remedy_a = ? AND remedy_b = ?",
                (proposed_remedy, prev_remedy)
            ).fetchall()
            conn.close()

            for rel_type, source in rows:
                if rel_type == "antidote":
                    warnings.append({
                        "type": "antidote",
                        "severity": "critical",
                        "message": f"{prev_remedy} antidotes {proposed_remedy} (source: {source}). Do not prescribe.",
                        "previous": prev,
                        "source": source,
                    })
                elif rel_type == "inimical":
                    warnings.append({
                        "type": "inimical",
                        "severity": "warning",
                        "message": f"{prev_remedy} and {proposed_remedy} are inimical (source: {source}). Avoid sequential use.",
                        "previous": prev,
                        "source": source,
                    })
                elif rel_type == "complementary":
                    warnings.append({
                        "type": "complementary",
                        "severity": "info",
                        "message": f"{prev_remedy} is complementary to {proposed_remedy} (source: {source}). Good follow-up candidate.",
                        "previous": prev,
                        "source": source,
                    })

        safe = not any(w["severity"] == "critical" for w in warnings)
        return {
            "safe": safe,
            "warnings": warnings,
            "history_count": len(history),
            "proposed_remedy": proposed_remedy,
        }
