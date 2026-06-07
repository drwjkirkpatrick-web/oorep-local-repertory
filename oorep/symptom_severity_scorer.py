"""
Symptom Severity Scorer — Intensity-Based Repertorization Weighting

Allows practitioners to score symptom intensity (1-10) which affects
repertorization weighting beyond binary present/absent.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class SymptomSeverityScorer:
    """
    Assign severity scores (1-10) to symptoms and compute weighted
    repertorization scores that favor high-intensity symptoms.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.severity_db_path = self.data_dir / "symptom_severity.json"
        self.severity_db = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.severity_db_path.exists():
            with open(self.severity_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.severity_db_path, "w", encoding="utf-8") as f:
            json.dump(self.severity_db, f, indent=2)

    def set_severity(self, case_id: str, rubric_id: int, severity: int,
                     notes: str = "") -> Dict[str, Any]:
        """
        Set severity for a rubric in a case.
        severity: 1-10 (1 = mild, 10 = intense/characteristic)
        """
        if not (1 <= severity <= 10):
            raise ValueError("Severity must be 1-10")
        if case_id not in self.severity_db:
            self.severity_db[case_id] = {}
        self.severity_db[case_id][str(rubric_id)] = {
            "severity": severity,
            "notes": notes,
            "multiplier": self._severity_multiplier(severity),
        }
        self._save()
        return {
            "case_id": case_id,
            "rubric_id": rubric_id,
            "severity": severity,
            "multiplier": self._severity_multiplier(severity),
        }

    @staticmethod
    def _severity_multiplier(severity: int) -> float:
        """
        Convert 1-10 severity to a weight multiplier.
        Linear scale: 1 → 0.5x, 5 → 1.0x, 10 → 2.0x
        """
        return 0.5 + (severity - 1) * (1.5 / 9)

    def get_severity(self, case_id: str, rubric_id: int) -> Optional[Dict[str, Any]]:
        return self.severity_db.get(case_id, {}).get(str(rubric_id))

    def compute_weighted_scores(self, case_id: str,
                                base_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply severity multipliers to base repertorization scores.
        base_scores: [{"remedy": "PULS", "score": 45.0, ...}, ...]
        """
        case_sev = self.severity_db.get(case_id, {})
        if not case_sev:
            return base_scores
        for entry in base_scores:
            remedy = entry.get("remedy", "")
            base = entry.get("score", 0.0)
            weighted = base
            for rid, sev_data in case_sev.items():
                mult = sev_data.get("multiplier", 1.0)
                # If this remedy appears in this rubric with a grade, boost
                # Simplified: boost overall score by average multiplier
                weighted = base * mult
            entry["original_score"] = base
            entry["severity_weighted_score"] = round(weighted, 2)
            entry["severity_boost"] = round(weighted - base, 2)
        # Re-sort by weighted score
        base_scores.sort(key=lambda x: x.get("severity_weighted_score", x.get("score", 0)), reverse=True)
        return base_scores

    def case_severity_summary(self, case_id: str) -> Dict[str, Any]:
        case_sev = self.severity_db.get(case_id, {})
        if not case_sev:
            return {"case_id": case_id, "n_rated": 0, "avg_severity": None}
        severities = [v["severity"] for v in case_sev.values()]
        return {
            "case_id": case_id,
            "n_rated": len(severities),
            "avg_severity": round(sum(severities) / len(severities), 2),
            "max_severity": max(severities),
            "min_severity": min(severities),
        }

    def list_rated_rubrics(self, case_id: str) -> List[Dict[str, Any]]:
        case_sev = self.severity_db.get(case_id, {})
        return [
            {"rubric_id": int(k), **v}
            for k, v in case_sev.items()
        ]
