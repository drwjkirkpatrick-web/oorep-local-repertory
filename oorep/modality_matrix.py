"""
Modality Matrix — Boenninghausen-Style Symptom-Modality Grid

Display modalities as columns and remedies as rows with grades,
for rapid Boenninghausen-style analysis.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ModalityMatrix:
    """
    Build a Boenninghausen-style modality matrix.
    Rows = remedies, Columns = modalities, Cells = grades.
    """

    COMMON_MODALITIES = [
        "worse morning", "worse afternoon", "worse evening", "worse night",
        "better motion", "worse motion",
        "better rest", "worse rest",
        "better cold", "worse cold",
        "better heat", "worse heat",
        "better pressure", "worse pressure",
        "better eating", "worse eating",
        "better open air", "worse open air",
    ]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.rubrics_path = self.data_dir / "rubric_remedies_full.json"
        self._rubrics: Optional[Dict[str, Any]] = None

    def _load(self):
        if self._rubrics is None and self.rubrics_path.exists():
            with open(self.rubrics_path, "r", encoding="utf-8") as f:
                self._rubrics = json.load(f)

    def build_matrix(self, remedies: List[str],
                     modalities: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Build modality matrix for a set of remedies.
        Returns matrix data ready for heatmap visualization.
        """
        self._load()
        if not self._rubrics:
            return {"remedies": [], "modalities": [], "matrix": []}

        use_modalities = modalities or self.COMMON_MODALITIES

        # For each remedy, find grades in each modality rubric
        matrix = []
        for remedy in remedies:
            row = {"remedy": remedy, "grades": []}
            for mod in use_modalities:
                grade = self._find_modality_grade(remedy, mod)
                row["grades"].append({
                    "modality": mod,
                    "grade": grade,
                    "has_grade": grade > 0,
                })
            matrix.append(row)

        return {
            "remedies": remedies,
            "modalities": use_modalities,
            "matrix": matrix,
            "summary": self._matrix_summary(matrix),
        }

    def _find_modality_grade(self, remedy: str, modality: str) -> int:
        """Find the highest grade for a remedy in a modality rubric."""
        if not self._rubrics:
            return 0
        max_grade = 0
        for rubric in self._rubrics.values():
            path = rubric.get("path", "").lower()
            if modality.lower() in path:
                remedies = rubric.get("remedies", {})
                if remedy in remedies:
                    grade = remedies[remedy].get("grade", 1)
                    max_grade = max(max_grade, grade)
        return max_grade

    def _matrix_summary(self, matrix: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_cells = len(matrix) * len(matrix[0]["grades"]) if matrix else 0
        filled = sum(1 for r in matrix for g in r["grades"] if g["has_grade"])
        return {
            "total_cells": total_cells,
            "filled_cells": filled,
            "sparsity": round(1 - filled / max(total_cells, 1), 3),
        }

    def compare_remedies(self, remedy_a: str, remedy_b: str) -> Dict[str, Any]:
        """Compare two remedies by their modality profiles."""
        matrix = self.build_matrix([remedy_a, remedy_b])
        if not matrix["matrix"]:
            return {"remedy_a": remedy_a, "remedy_b": remedy_b, "differences": []}

        a_grades = matrix["matrix"][0]["grades"]
        b_grades = matrix["matrix"][1]["grades"] if len(matrix["matrix"]) > 1 else []

        differences = []
        for a, b in zip(a_grades, b_grades):
            if a["grade"] != b.get("grade", 0):
                differences.append({
                    "modality": a["modality"],
                    "grade_a": a["grade"],
                    "grade_b": b.get("grade", 0),
                    "difference": abs(a["grade"] - b.get("grade", 0)),
                })

        return {
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "modalities": matrix["modalities"],
            "differences": sorted(differences, key=lambda x: -x["difference"]),
        }
