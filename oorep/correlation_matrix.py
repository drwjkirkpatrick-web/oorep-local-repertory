"""
Remedy Correlation Matrix — Feature #21

Pre-computed remedy-to-remedy correlation matrix based on rubric co-occurrence.
Jaccard / cosine similarity across remedy rubric profiles.
Fast lookup for 'remedies similar to X' and 'remedies opposite to X'.

Usage:
    from oorep.correlation_matrix import CorrelationMatrixEngine
    engine = CorrelationMatrixEngine(rubric_to_remedies_json_path)

    sim = engine.jaccard_similarity("PULS", "ARS")
    neighbors = engine.nearest_neighbors("PULS", method="jaccard", top_n=5)
    opposites = engine.opposites("PULS", top_n=5)
"""

import json
import math
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class CorrelationMatrixEngine:
    """
    Remedy correlation matrix from rubric co-occurrence.
    Pre-computes rubric profiles from JSON data for fast similarity lookups.
    """

    def __init__(self, rubric_to_remedies_path: Optional[str] = None):
        self.profiles: Dict[str, Set[str]] = {}
        self.remedy_set: Set[str] = set()

        if rubric_to_remedies_path:
            self._load_data(rubric_to_remedies_path)

    def _load_data(self, path: str) -> None:
        """Load rubric-to-remedies mapping and build inverted index."""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return

        # data may be dict {rubric_id: [{remedy, grade}...]}
        if isinstance(data, dict):
            entries = data.items()
        elif isinstance(data, list):
            entries = enumerate(data)
        else:
            return

        for rid, remedies in entries:
            if not isinstance(remedies, list):
                continue
            for r in remedies:
                abbrev = r.get("remedy", "") if isinstance(r, dict) else str(r)
                if abbrev:
                    self.remedy_set.add(abbrev.upper())
                    self.profiles.setdefault(abbrev.upper(), set()).add(str(rid))

    # ── Core similarity methods ────────────────────────────────────────────

    @staticmethod
    def jaccard_similarity(a: Set[str], b: Set[str]) -> float:
        """Jaccard index: |A ∩ B| / |A ∪ B|."""
        if not a and not b:
            return 1.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

    @staticmethod
    def cosine_similarity(a: Set[str], b: Set[str]) -> float:
        """Cosine similarity for binary vectors."""
        if not a and not b:
            return 1.0
        inter = len(a & b)
        return inter / math.sqrt(len(a) * len(b)) if a and b else 0.0

    @staticmethod
    def overlap_coefficient(a: Set[str], b: Set[str]) -> float:
        """Overlap: |A ∩ B| / min(|A|, |B|)."""
        if not a and not b:
            return 1.0
        inter = len(a & b)
        return inter / min(len(a), len(b)) if a and b else 0.0

    # ── High-level API ──────────────────────────────────────────────────────

    def similarity(
        self,
        remedy_a: str,
        remedy_b: str,
        method: str = "jaccard",
    ) -> float:
        """Compute similarity between two remedies."""
        ra = self.profiles.get(remedy_a.upper())
        rb = self.profiles.get(remedy_b.upper())
        if ra is None or rb is None:
            return 0.0

        m = method.lower()
        if m == "jaccard":
            return self.jaccard_similarity(ra, rb)
        elif m == "cosine":
            return self.cosine_similarity(ra, rb)
        elif m == "overlap":
            return self.overlap_coefficient(ra, rb)
        else:
            return self.jaccard_similarity(ra, rb)

    def nearest_neighbors(
        self,
        remedy: str,
        method: str = "jaccard",
        top_n: int = 5,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Find most similar remedies."""
        r = self.profiles.get(remedy.upper())
        if r is None:
            return []

        scores = []
        for other in self.remedy_set:
            if other == remedy.upper():
                continue
            rb = self.profiles.get(other)
            if rb is None:
                continue
            s = self.similarity(remedy, other, method)
            if s >= min_similarity:
                scores.append({"remedy": other, "similarity": round(s, 4)})

        scores.sort(key=lambda x: x["similarity"], reverse=True)
        return scores[:top_n]

    def opposites(self, remedy: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Find 'opposite' remedies: dissimilar by Jaccard.
        These are often complementary or antidotes.
        """
        scores = []
        for other in self.remedy_set:
            if other == remedy.upper():
                continue
            s = self.similarity(remedy, other, method="jaccard")
            scores.append({"remedy": other, "similarity": round(s, 4)})

        scores.sort(key=lambda x: x["similarity"])
        return scores[:top_n]

    def shared_rubrics(self, remedy_a: str, remedy_b: str) -> List[str]:
        """List rubric IDs where both remedies appear."""
        ra = self.profiles.get(remedy_a.upper())
        rb = self.profiles.get(remedy_b.upper())
        if ra is None or rb is None:
            return []
        return sorted(list(ra & rb))

    def exclusive_rubrics(self, remedy_a: str, remedy_b: str) -> Dict[str, List[str]]:
        """Rubrics only in A vs only in B."""
        ra = self.profiles.get(remedy_a.upper())
        rb = self.profiles.get(remedy_b.upper())
        return {
            remedy_a: sorted(list(ra - rb)) if ra and rb else (sorted(list(ra)) if ra else []),
            remedy_b: sorted(list(rb - ra)) if ra and rb else (sorted(list(rb)) if rb else []),
        }

    def get_rubric_count(self, remedy: str) -> int:
        """Number of rubrics a remedy appears in."""
        ra = self.profiles.get(remedy.upper())
        return len(ra) if ra else 0

    def correlation_row(self, remedy: str, method: str = "jaccard") -> List[float]:
        """Full correlation row for matrix serialization."""
        r = self.profiles.get(remedy.upper())
        if r is None:
            return []
        return [self.similarity(remedy, other, method) for other in sorted(self.remedy_set)]

    def to_matrix(self, method: str = "jaccard") -> Dict[str, Any]:
        """
        Serialize full matrix. Keyed by remedy, value is list of similarities.
        Diagonal is 1.0.
        """
        result = {}
        remedies = sorted(self.remedy_set)
        for rem in remedies:
            row = []
            for other in remedies:
                if rem == other:
                    row.append(1.0)
                else:
                    row.append(round(self.similarity(rem, other, method), 4))
            result[rem] = row
        return {"remedies": remedies, "method": method, "matrix": result}

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 21,
            "feature_name": "Remedy Correlation Matrix",
            "methods": ["jaccard", "cosine", "overlap"],
            "remedies_indexed": len(self.remedy_set),
            "cold_start_capable": len(self.remedy_set) == 0,
            "version": "1.0",
        }
