"""
Rubric Co-occurrence Engine

Mines which remedies appear together across rubrics to reveal:
  - Polycrest remedy "clusters" (remedies that share rubric spaces)
  - Common remedy pairs in clinical practice
  - Remedy association rules for differential diagnosis

Usage:
    from oorep.rubric_cooccurrence import RubricCooccurrenceEngine
    engine = RubricCooccurrenceEngine()
    pairs = engine.top_pairs(min_cooccurrence=50)
    # Returns list of {remedy_a, remedy_b, joint_count, ...}
"""

import math
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class RemedyPair:
    remedy_a: str
    remedy_b: str
    joint_count: int          # Number of rubrics shared by both
    jaccard: float            # Intersection / Union (0..1)
    overlap_ratio_a: float    # joint_count / total_rubrics_a
    overlap_ratio_b: float    # joint_count / total_rubrics_b
    avg_rubric_size: float    # Average number of remedies in shared rubrics
    lift: float               # P(B|A) / P(B)


class RubricCooccurrenceEngine:
    """
    Analyze remedy co-occurrence patterns across rubrics.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        # Pre-compute: remedy abbrev -> set of rubric IDs
        self._remedy_rubrics: Dict[str, Set[int]] = defaultdict(set)
        self._remedy_counts: Dict[str, int] = {}
        self._total_rubrics = len(self.rep.rubric_to_remedies)
        self._build_index()

    def _build_index(self):
        """Build inverted index and counts."""
        for rubric_id, links in self.rep.rubric_to_remedies.items():
            seen_abbrevs = set()
            for link in links:
                abbrev = link.get("abbrev")
                if abbrev and abbrev not in seen_abbrevs:
                    self._remedy_rubrics[abbrev].add(rubric_id)
                    seen_abbrevs.add(abbrev)
        self._remedy_counts = {a: len(s) for a, s in self._remedy_rubrics.items()}

    def get_common_rubrics(self, abbrev_a: str, abbrev_b: str) -> List[Dict]:
        """Return all rubrics shared by two remedies, with weights."""
        set_a = self._remedy_rubrics.get(abbrev_a, set())
        set_b = self._remedy_rubrics.get(abbrev_b, set())
        common = sorted(set_a & set_b)
        results = []
        for rid in common:
            rubric = self.rep.get_rubric_by_id(rid)
            if not rubric:
                continue
            # Get weights for each remedy in this rubric
            links = self.rep.get_remedies_for_rubric(rid)
            wa = next((l["weight"] for l in links if l["abbrev"] == abbrev_a), 1)
            wb = next((l["weight"] for l in links if l["abbrev"] == abbrev_b), 1)
            results.append({
                "rubric_id": rid,
                "fullpath": rubric.get("fullpath"),
                "source": rubric.get("source"),
                f"{abbrev_a}_weight": wa,
                f"{abbrev_b}_weight": wb,
            })
        return results

    def _pair_key(self, a: str, b: str) -> Tuple[str, str]:
        """Canonical ordering for pair keys."""
        return (a, b) if a < b else (b, a)

    def compute_pair(self, abbrev_a: str, abbrev_b: str) -> Optional[RemedyPair]:
        """Compute co-occurrence metrics for a single pair."""
        set_a = self._remedy_rubrics.get(abbrev_a)
        set_b = self._remedy_rubrics.get(abbrev_b)
        if not set_a or not set_b:
            return None
        joint = len(set_a & set_b)
        if joint == 0:
            return None
        total_a = len(set_a)
        total_b = len(set_b)
        union = len(set_a | set_b)
        jaccard = joint / union if union else 0.0
        # Lift: P(B|A) / P(B)
        prob_b = total_b / self._total_rubrics if self._total_rubrics else 0
        prob_b_given_a = joint / total_a if total_a else 0
        lift = prob_b_given_a / prob_b if prob_b > 0 else 0.0

        # Average rubric size in shared rubrics
        sizes = []
        for rid in (set_a & set_b):
            sizes.append(len(self.rep.get_remedies_for_rubric(rid)))
        avg_size = round(sum(sizes) / len(sizes), 1) if sizes else 0

        return RemedyPair(
            remedy_a=abbrev_a,
            remedy_b=abbrev_b,
            joint_count=joint,
            jaccard=round(jaccard, 4),
            overlap_ratio_a=round(joint / total_a, 4),
            overlap_ratio_b=round(joint / total_b, 4),
            avg_rubric_size=avg_size,
            lift=round(lift, 3),
        )

    def top_pairs(self, abbrev_filter: Optional[str] = None, min_cooccurrence: int = 20,
                  min_jaccard: float = 0.0, limit: int = 50) -> List[RemedyPair]:
        """
        Find top remedy pairs. Optionally filter by a specific remedy.
        Sorted by joint_count descending, then jaccard descending.
        """
        remedies = list(self._remedy_rubrics.keys())
        pairs = []
        if abbrev_filter:
            target = abbrev_filter
            for other in remedies:
                if other == target:
                    continue
                pair = self.compute_pair(target, other)
                if pair and pair.joint_count >= min_cooccurrence and pair.jaccard >= min_jaccard:
                    pairs.append(pair)
        else:
            # All pairs — expensive on large data; use generator internally
            seen = set()
            for i, a in enumerate(remedies):
                for b in remedies[i + 1:]:
                    key = self._pair_key(a, b)
                    if key in seen:
                        continue
                    seen.add(key)
                    pair = self.compute_pair(a, b)
                    if pair and pair.joint_count >= min_cooccurrence and pair.jaccard >= min_jaccard:
                        pairs.append(pair)

        pairs.sort(key=lambda p: (p.joint_count, p.jaccard), reverse=True)
        return pairs[:limit]

    def cluster_for_remedy(self, abbrev: str, min_cooccurrence: int = 10) -> Dict:
        """
        Return the "remedy cluster" around a given remedy — its closest neighbors.
        """
        pairs = self.top_pairs(abbrev_filter=abbrev, min_cooccurrence=min_cooccurrence, limit=15)
        return {
            "target_remedy": abbrev,
            "cluster_size": len(pairs),
            "total_rubrics": self._remedy_counts.get(abbrev, 0),
            "neighbors": [asdict(p) for p in pairs],
        }

    def polycrest_clusters(self, min_cooccurrence: int = 50) -> List[Dict]:
        """
        Identify classic polycrest remedy clusters (groups of remedies that share
        large numbers of rubrics — useful for comparative materia medica study).
        """
        # Find top pairs where both are "large" remedies (> 300 rubrics)
        large_remedies = {a for a, c in self._remedy_counts.items() if c >= 300}
        pairs = []
        seen = set()
        remedies_list = sorted(large_remedies)
        for i, a in enumerate(remedies_list):
            for b in remedies_list[i + 1:]:
                key = self._pair_key(a, b)
                if key in seen:
                    continue
                seen.add(key)
                pair = self.compute_pair(a, b)
                if pair and pair.joint_count >= min_cooccurrence:
                    pairs.append(pair)
        pairs.sort(key=lambda p: p.joint_count, reverse=True)
        return [asdict(p) for p in pairs[:20]]


def top_remedy_pairs(min_cooccurrence: int = 50, limit: int = 20) -> List[Dict]:
    """Convenience function."""
    engine = RubricCooccurrenceEngine()
    return [asdict(p) for p in engine.top_pairs(min_cooccurrence=min_cooccurrence, limit=limit)]
