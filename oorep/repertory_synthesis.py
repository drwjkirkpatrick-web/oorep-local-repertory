"""
Repertory Synthesis — Custom Repertory Builder

Create personal repertories by selecting rubrics from multiple sources,
adding clinical observations, and exporting as new repertory files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class RepertorySynthesis:
    """
    Build custom repertories from existing rubrics plus practitioner additions.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.custom_reps_dir = self.data_dir / "custom_repertories"
        self.custom_reps_dir.mkdir(parents=True, exist_ok=True)
        self._repertories: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self):
        for f in self.custom_reps_dir.glob("*.json"):
            rep_id = f.stem
            with open(f, "r", encoding="utf-8") as fh:
                self._repertories[rep_id] = json.load(fh)

    def create(self, rep_id: str, name: str, author: str,
               source_repertories: List[str]) -> Dict[str, Any]:
        """
        Create a new custom repertory.
        source_repertories: ["kent_1899", "synthesis_9.1", ...]
        """
        rep = {
            "id": rep_id,
            "name": name,
            "author": author,
            "created_at": datetime.utcnow().isoformat(),
            "source_repertories": source_repertories,
            "rubrics": {},  # rubric_id -> {path, remedies, source, notes}
            "n_rubrics": 0,
        }
        self._repertories[rep_id] = rep
        self._save(rep_id)
        return rep

    def add_rubric(self, rep_id: str, rubric_id: int, path: str,
                   remedies: Dict[str, Any], source: str = "",
                   practitioner_notes: str = "") -> Dict[str, Any]:
        rep = self._repertories.get(rep_id)
        if not rep:
            return {"error": "Repertory not found"}
        rep["rubrics"][str(rubric_id)] = {
            "path": path,
            "remedies": remedies,
            "source": source,
            "practitioner_notes": practitioner_notes,
        }
        rep["n_rubrics"] = len(rep["rubrics"])
        self._save(rep_id)
        return {"repertory": rep_id, "rubric_id": rubric_id, "added": True}

    def remove_rubric(self, rep_id: str, rubric_id: int) -> Dict[str, Any]:
        rep = self._repertories.get(rep_id)
        if not rep:
            return {"error": "Repertory not found"}
        key = str(rubric_id)
        if key in rep["rubrics"]:
            del rep["rubrics"][key]
            rep["n_rubrics"] = len(rep["rubrics"])
            self._save(rep_id)
            return {"removed": True}
        return {"removed": False}

    def get_repertory(self, rep_id: str) -> Optional[Dict[str, Any]]:
        return self._repertories.get(rep_id)

    def list_repertories(self) -> List[Dict[str, Any]]:
        return [
            {"id": k, "name": v["name"], "author": v["author"], "n_rubrics": v.get("n_rubrics", 0)}
            for k, v in self._repertories.items()
        ]

    def export(self, rep_id: str, format_type: str = "json") -> Dict[str, Any]:
        rep = self._repertories.get(rep_id)
        if not rep:
            return {"error": "Not found"}
        if format_type == "json":
            export_path = self.custom_reps_dir / f"{rep_id}_export.json"
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(rep, f, indent=2)
            return {"format": "json", "path": str(export_path), "n_rubrics": rep["n_rubrics"]}
        return {"error": f"Format {format_type} not supported"}

    def _save(self, rep_id: str):
        path = self.custom_reps_dir / f"{rep_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._repertories[rep_id], f, indent=2)
