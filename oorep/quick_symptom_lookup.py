"""
Quick Symptom Lookup — Single-Symptom Fast Search Mode

Type one symptom → instant rubric list without full repertorization.
Fast lookup for answering single clinical questions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class QuickSymptomLookup:
    """
    Lightweight single-symptom lookup optimized for speed.
    No clipboard workflow needed — just query and get rubrics.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.index_path = self.data_dir / "rubric_search_index.json"
        self.rubrics_path = self.data_dir / "rubric_remedies_full.json"
        self._index: Optional[Dict[str, List[int]]] = None
        self._rubrics: Optional[Dict[str, Any]] = None

    def _load_index(self):
        if self._index is None and self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                self._index = json.load(f)
        if self._rubrics is None and self.rubrics_path.exists():
            with open(self.rubrics_path, "r", encoding="utf-8") as f:
                self._rubrics = json.load(f)

    def lookup(self, symptom: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Quick lookup of rubrics matching a single symptom phrase.
        Returns rubrics with remedy counts for rapid triage.
        """
        self._load_index()
        if not self._index or not self._rubrics:
            return []

        tokens = symptom.lower().split()
        matched_ids: set = set()
        for token in tokens:
            if token in self._index:
                matched_ids.update(self._index[token])

        results = []
        for rid in list(matched_ids)[:top_n]:
            rubric = self._rubrics.get(str(rid))
            if rubric:
                results.append({
                    "rubric_id": rid,
                    "path": rubric.get("path", ""),
                    "n_remedies": len(rubric.get("remedies", {})),
                    "top_remedies": self._top_remedies(rubric.get("remedies", {}), 5),
                })

        # Score by token overlap
        for r in results:
            r["match_score"] = sum(1 for t in tokens if t in r["path"].lower())
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_n]

    @staticmethod
    def _top_remedies(remedies: Dict[str, Any], n: int) -> List[Dict[str, Any]]:
        sorted_rems = sorted(remedies.items(), key=lambda x: x[1].get("grade", 1), reverse=True)
        return [{"remedy": r[0], "grade": r[1].get("grade", 1)} for r in sorted_rems[:n]]

    def get_rubric_detail(self, rubric_id: int) -> Optional[Dict[str, Any]]:
        self._load_index()
        if not self._rubrics:
            return None
        rubric = self._rubrics.get(str(rubric_id))
        if not rubric:
            return None
        return {
            "rubric_id": rubric_id,
            "path": rubric.get("path", ""),
            "remedies": rubric.get("remedies", {}),
            "n_remedies": len(rubric.get("remedies", {})),
        }
