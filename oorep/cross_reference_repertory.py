"""
Cross-Reference Repertory — Universal Rubric Concordance

Link rubrics across different repertories (Kent → Boenninghausen →
Boger → Synthesis → OOREP) to find equivalent rubrics in each system.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class CrossReferenceRepertory:
    """
    Map rubrics across repertory editions.
    Requires manual or algorithmic mapping database.
    """

    SUPPORTED_REPERTORIES = [
        "kent_1899", "boenninghausen_1846", "boger_1931",
        "synthesis_9.1", "oorep_publicum", "therapeutic_pocket_book"
    ]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.mappings_path = self.data_dir / "cross_reference_mappings.json"
        self._mappings: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.mappings_path.exists():
            with open(self.mappings_path, "r", encoding="utf-8") as f:
                self._mappings = json.load(f)

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.mappings_path, "w", encoding="utf-8") as f:
            json.dump(self._mappings, f, indent=2)

    def add_mapping(self, source_rep: str, source_rubric_id: int,
                    target_rep: str, target_rubric_id: int,
                    confidence: float = 1.0) -> Dict[str, Any]:
        """
        Add a cross-reference mapping between two repertories.
        """
        key = f"{source_rep}:{source_rubric_id}"
        if key not in self._mappings:
            self._mappings[key] = {}
        self._mappings[key][target_rep] = {
            "target_rubric_id": target_rubric_id,
            "confidence": confidence,
        }
        self._save()
        return {
            "source": f"{source_rep}#{source_rubric_id}",
            "target": f"{target_rep}#{target_rubric_id}",
            "confidence": confidence,
        }

    def find_equivalents(self, source_rep: str, source_rubric_id: int) -> Dict[str, Any]:
        """
        Find equivalent rubrics in all other repertories.
        """
        key = f"{source_rep}:{source_rubric_id}"
        equivalents = self._mappings.get(key, {})
        return {
            "source": f"{source_rep}#{source_rubric_id}",
            "equivalents": [
                {"repertory": rep, **data}
                for rep, data in equivalents.items()
            ],
            "n_mappings": len(equivalents),
        }

    def get_supported_repertories(self) -> List[str]:
        return self.SUPPORTED_REPERTORIES

    def seed_sample_mappings(self) -> int:
        """Seed with sample mappings for demonstration."""
        samples = [
            ("kent_1899", 12345, "synthesis_9.1", 12345, 1.0),
            ("kent_1899", 12345, "oorep_publicum", 12345, 0.95),
            ("kent_1899", 67890, "boenninghausen_1846", 11111, 0.8),
        ]
        count = 0
        for s in samples:
            key = f"{s[0]}:{s[1]}"
            if key not in self._mappings or s[2] not in self._mappings.get(key, {}):
                self.add_mapping(*s)
                count += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        total_mappings = sum(len(v) for v in self._mappings.values())
        by_source = {}
        for key in self._mappings:
            rep = key.split(":")[0]
            by_source[rep] = by_source.get(rep, 0) + 1
        return {
            "total_rubrics_mapped": len(self._mappings),
            "total_mappings": total_mappings,
            "by_source_repertory": by_source,
            "coverage_note": "Mappings require manual curation or algorithmic alignment. This is a scaffold.",
        }
