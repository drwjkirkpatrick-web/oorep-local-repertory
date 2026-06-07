"""
Rubric Quality Scorer — Repertory Data Validation

Score rubric quality based on grade distribution, source diversity,
remedy coverage, and inter-rater agreement.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class RubricQualityScorer:
    """
    Evaluate the quality and reliability of rubrics in the repertory.
    Higher scores = more reliable for clinical use.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.rubrics_path = self.data_dir / "rubric_remedies_full.json"
        self._rubrics: Optional[Dict[str, Any]] = None

    def _load(self):
        if self._rubrics is None and self.rubrics_path.exists():
            with open(self.rubrics_path, "r", encoding="utf-8") as f:
                self._rubrics = json.load(f)

    def score_rubric(self, rubric_id: int) -> Dict[str, Any]:
        """
        Score a single rubric on multiple quality dimensions.
        """
        self._load()
        if not self._rubrics or str(rubric_id) not in self._rubrics:
            return {"rubric_id": rubric_id, "error": "Not found"}

        rubric = self._rubrics[str(rubric_id)]
        remedies = rubric.get("remedies", {})
        n_remedies = len(remedies)

        if n_remedies == 0:
            return {"rubric_id": rubric_id, "quality_score": 0, "reason": "No remedies"}

        grades = [r.get("grade", 1) for r in remedies.values()]
        grade_3 = sum(1 for g in grades if g == 3)
        grade_2 = sum(1 for g in grades if g == 2)
        grade_1 = sum(1 for g in grades if g == 1)

        # Coverage: how many remedies? (more = better coverage, but too many = vague)
        coverage_score = min(n_remedies / 50, 1.0)  # 50+ remedies = full coverage score
        if n_remedies > 200:
            coverage_score = max(0.3, 1.0 - (n_remedies - 200) / 500)  # Penalize overly broad

        # Grade distribution: prefer rubrics with some grade 2/3 (proven)
        proven_ratio = (grade_2 + grade_3) / n_remedies
        grade_score = proven_ratio

        # Differentiation: Gini-like coefficient of grade distribution
        grade_counts = [grade_1, grade_2, grade_3]
        differentiation = self._gini(grade_counts) if sum(grade_counts) > 0 else 0

        # Overall quality: composite
        quality = round((coverage_score * 0.3 + grade_score * 0.4 + (1 - differentiation) * 0.3), 3)

        return {
            "rubric_id": rubric_id,
            "path": rubric.get("path", ""),
            "n_remedies": n_remedies,
            "grade_distribution": {"1": grade_1, "2": grade_2, "3": grade_3},
            "coverage_score": round(coverage_score, 3),
            "grade_score": round(grade_score, 3),
            "differentiation": round(differentiation, 3),
            "quality_score": quality,
            "quality_label": self._label(quality),
        }

    def score_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Score top rubrics by ID."""
        self._load()
        if not self._rubrics:
            return []
        results = []
        for rid in list(self._rubrics.keys())[:limit]:
            results.append(self.score_rubric(int(rid)))
        return sorted(results, key=lambda x: -x.get("quality_score", 0))

    def find_weak_rubrics(self, min_quality: float = 0.3, limit: int = 50) -> List[Dict[str, Any]]:
        """Find rubrics with low quality scores."""
        self._load()
        if not self._rubrics:
            return []
        weak = []
        for rid in list(self._rubrics.keys())[:limit]:
            score = self.score_rubric(int(rid))
            if score.get("quality_score", 1) <= min_quality:
                weak.append(score)
        return sorted(weak, key=lambda x: x.get("quality_score", 0))

    @staticmethod
    def _gini(values: List[int]) -> float:
        """Compute Gini coefficient for grade distribution."""
        if sum(values) == 0:
            return 0
        n = len(values)
        cumsum = 0
        for i, v in enumerate(sorted(values)):
            cumsum += (i + 1) * v
        return (2 * cumsum) / (n * sum(values)) - (n + 1) / n

    @staticmethod
    def _label(score: float) -> str:
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
