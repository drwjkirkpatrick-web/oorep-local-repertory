"""
Case Similarity Search — Find Previous Cases Like the Current One

Use vector similarity on case symptom patterns to find similar
previous cases and what remedies worked.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class CaseSimilaritySearch:
    """
    Find similar cases in the practice based on symptom overlap.
    Helps answer: "What worked for cases like this?"
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cases_path = self.data_dir / "case_vectors.json"
        self._cases: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.cases_path.exists():
            with open(self.cases_path, "r", encoding="utf-8") as f:
                self._cases = json.load(f)

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.cases_path, "w", encoding="utf-8") as f:
            json.dump(self._cases, f, indent=2)

    def index_case(self, case_id: str, rubric_ids: List[int],
                   remedy: str, outcome: str,
                   case_type: str = "chronic") -> Dict[str, Any]:
        """
        Index a case for similarity search.
        rubric_ids: list of rubric IDs that characterize this case
        """
        self._cases[case_id] = {
            "rubric_ids": sorted(set(rubric_ids)),
            "remedy": remedy,
            "outcome": outcome,
            "case_type": case_type,
            "n_rubrics": len(set(rubric_ids)),
        }
        self._save()
        return {"case_id": case_id, "indexed": True, "n_rubrics": len(set(rubric_ids))}

    def find_similar(self, query_rubric_ids: List[int], top_n: int = 10,
                     min_overlap: float = 0.3) -> List[Dict[str, Any]]:
        """
        Find cases with similar symptom patterns.
        """
        query_set = set(query_rubric_ids)
        if not query_set:
            return []

        results = []
        for case_id, case in self._cases.items():
            case_set = set(case.get("rubric_ids", []))
            if not case_set:
                continue

            intersection = query_set & case_set
            union = query_set | case_set
            jaccard = len(intersection) / len(union) if union else 0
            overlap_ratio = len(intersection) / len(query_set) if query_set else 0

            if jaccard >= min_overlap:
                results.append({
                    "case_id": case_id,
                    "similarity": round(jaccard, 3),
                    "overlap_count": len(intersection),
                    "overlap_ratio": round(overlap_ratio, 3),
                    "remedy": case.get("remedy"),
                    "outcome": case.get("outcome"),
                    "case_type": case.get("case_type"),
                })

        results.sort(key=lambda x: -x["similarity"])
        return results[:top_n]

    def get_what_worked(self, query_rubric_ids: List[int],
                        outcome_filter: str = "cured") -> List[Dict[str, Any]]:
        """
        Find remedies that worked for similar cases.
        """
        similar = self.find_similar(query_rubric_ids)
        worked = [s for s in similar if s.get("outcome") == outcome_filter]

        # Aggregate by remedy
        remedy_counts: Dict[str, Dict[str, Any]] = {}
        for w in worked:
            r = w["remedy"]
            if r not in remedy_counts:
                remedy_counts[r] = {"remedy": r, "count": 0, "avg_similarity": 0.0, "cases": []}
            remedy_counts[r]["count"] += 1
            remedy_counts[r]["avg_similarity"] += w["similarity"]
            remedy_counts[r]["cases"].append(w["case_id"])

        for r in remedy_counts:
            remedy_counts[r]["avg_similarity"] = round(
                remedy_counts[r]["avg_similarity"] / remedy_counts[r]["count"], 3
            )

        ranked = sorted(remedy_counts.values(), key=lambda x: (-x["count"], -x["avg_similarity"]))
        return ranked

    def get_practice_stats(self) -> Dict[str, Any]:
        """Summary statistics of indexed cases."""
        outcomes = {}
        remedies = {}
        for case in self._cases.values():
            o = case.get("outcome", "unknown")
            r = case.get("remedy", "unknown")
            outcomes[o] = outcomes.get(o, 0) + 1
            remedies[r] = remedies.get(r, 0) + 1

        return {
            "total_cases": len(self._cases),
            "outcome_distribution": outcomes,
            "most_common_remedies": sorted(remedies.items(), key=lambda x: -x[1])[:10],
        }
