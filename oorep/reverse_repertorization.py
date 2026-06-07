"""
Reverse Repertorization — Remedy → Rubric Inquiry

Given a remedy abbreviation, display all rubrics where it appears
with classical grades — the inverse of normal repertorization.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReverseRepertorization:
    """
    Generate a structured "remedy picture" by listing all rubrics
    for a given remedy with grades and hierarchy.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.rubrics_path = self.data_dir / "rubric_remedies_full.json"
        self.remedies_path = self.data_dir / "remedies.json"
        self._rubrics: Optional[Dict[str, Any]] = None
        self._remedies: Optional[Dict[str, Any]] = None

    def _load(self):
        if self._rubrics is None and self.rubrics_path.exists():
            with open(self.rubrics_path, "r", encoding="utf-8") as f:
                self._rubrics = json.load(f)
        if self._remedies is None and self.remedies_path.exists():
            with open(self.remedies_path, "r", encoding="utf-8") as f:
                self._remedies = json.load(f)

    def query(self, remedy: str, top_n: int = 200,
              grade_filter: Optional[int] = None) -> Dict[str, Any]:
        """
        Return all rubrics for a remedy with grades.
        remedy: abbreviation (e.g., "PULS")
        """
        self._load()
        if not self._rubrics:
            return {"remedy": remedy, "rubrics": [], "error": "No rubric data"}

        matches = []
        for rid, rubric in self._rubrics.items():
            remedies = rubric.get("remedies", {})
            if remedy in remedies:
                grade = remedies[remedy].get("grade", 1)
                if grade_filter is None or grade >= grade_filter:
                    matches.append({
                        "rubric_id": int(rid),
                        "path": rubric.get("path", ""),
                        "grade": grade,
                        "grade_label": self._grade_label(grade),
                    })

        matches.sort(key=lambda x: (-x["grade"], x["path"]))

        # Group by chapter (first segment of path)
        by_chapter: Dict[str, List[Dict[str, Any]]] = {}
        for m in matches:
            chapter = m["path"].split(";")[0] if ";" in m["path"] else "General"
            by_chapter.setdefault(chapter, []).append(m)

        return {
            "remedy": remedy,
            "remedy_name": self._remedy_name(remedy),
            "total_rubrics": len(matches),
            "grade_3_count": sum(1 for m in matches if m["grade"] == 3),
            "grade_2_count": sum(1 for m in matches if m["grade"] == 2),
            "grade_1_count": sum(1 for m in matches if m["grade"] == 1),
            "by_chapter": by_chapter,
            "top_rubrics": matches[:top_n],
        }

    def compare_two_remedies(self, remedy_a: str, remedy_b: str) -> Dict[str, Any]:
        """
        Side-by-side comparison of two remedies by shared rubrics.
        """
        a_data = self.query(remedy_a)
        b_data = self.query(remedy_b)

        a_rubrics = {r["path"]: r["grade"] for r in a_data.get("top_rubrics", [])}
        b_rubrics = {r["path"]: r["grade"] for r in b_data.get("top_rubrics", [])}

        shared = set(a_rubrics.keys()) & set(b_rubrics.keys())
        only_a = set(a_rubrics.keys()) - set(b_rubrics.keys())
        only_b = set(b_rubrics.keys()) - set(a_rubrics.keys())

        return {
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "shared_rubrics": sorted([
                {"path": p, "grade_a": a_rubrics[p], "grade_b": b_rubrics[p]}
                for p in shared
            ], key=lambda x: -(x["grade_a"] + x["grade_b"])),
            "only_a": sorted(only_a)[:50],
            "only_b": sorted(only_b)[:50],
            "shared_count": len(shared),
            "a_total": len(a_rubrics),
            "b_total": len(b_rubrics),
            "similarity": round(len(shared) / max(len(a_rubrics), len(b_rubrics), 1), 3),
        }

    @staticmethod
    def _grade_label(grade: int) -> str:
        labels = {1: "regular", 2: "italic", 3: "bold"}
        return labels.get(grade, "regular")

    def _remedy_name(self, abbrev: str) -> str:
        if self._remedies and abbrev in self._remedies:
            return self._remedies[abbrev].get("name", abbrev)
        return abbrev
