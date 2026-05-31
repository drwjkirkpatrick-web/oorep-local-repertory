"""
Remedy Comparator

Multi-remedy side-by-side comparison:
- Overlap analysis: rubrics shared by remedies
- Divergence analysis: rubrics where one remedy has a higher grade
- Exclusive rubrics: rubrics unique to each remedy

Usage:
    from oorep.remedy_comparator import RemedyComparator
    comp = RemedyComparator()
    result = comp.compare_remedies(["Puls.", "Nux-v.", "Ars."])
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class RemedyComparisonResult:
    remedies: List[str]                    # Abbreviations compared
    overlap_rubrics: List[Dict]              # Rubrics shared by all
    pairwise_divergence: List[Dict]          # Head-to-head divergences
    exclusive_rubrics: Dict[str, List[Dict]] # Rubrics unique per remedy
    similarity_matrix: Dict[str, Dict[str, float]]  # Jaccard similarity
    total_rubrics: Dict[str, int]            # Total rubric count per remedy


class RemedyComparator:
    """Compare multiple remedies side-by-side."""

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        # Build inverted index: remedy_abbrev -> {rubric_id: weight}
        self._remedy_rubric_index: Dict[str, Dict[int, int]] = defaultdict(dict)
        self._build_index()

    def _build_index(self):
        """Index all rubric links by remedy abbreviation."""
        for rubric_id, links in self.rep.rubric_to_remedies.items():
            for link in links:
                abbrev = link.get("abbrev")
                if abbrev:
                    self._remedy_rubric_index[abbrev][rubric_id] = link.get("weight", 1)

    def compare_remedies(self, remedy_abbrevs: List[str]) -> RemedyComparisonResult:
        """
        Compare two or more remedies.

        Returns RemedyComparisonResult with overlap, divergence, exclusives, and similarity.
        """
        if len(remedy_abbrevs) < 2:
            raise ValueError("Need at least 2 remedies to compare")

        # Resolve abbreviations (handle abbrev with/without dots)
        resolved = []
        for abbrev in remedy_abbrevs:
            remedy = self.rep.get_remedy_by_abbrev(abbrev)
            if remedy:
                resolved.append(remedy.get("abbrev", abbrev))
            else:
                # Try fuzzy match
                results = self.rep.search_remedies(abbrev, limit=1)
                if results:
                    resolved.append(results[0]["abbrev"])
                else:
                    resolved.append(abbrev)

        # --- Overlap: rubrics present in ALL remedies ---
        rubric_sets = [set(self._remedy_rubric_index.get(a, {}).keys()) for a in resolved]
        common_rubric_ids = set.intersection(*rubric_sets) if rubric_sets else set()
        overlap_rubrics = []
        for rid in sorted(common_rubric_ids):
            rubric = self.rep.get_rubric_by_id(rid)
            if rubric:
                entry = {"rubric_id": rid, "fullpath": rubric.get("fullpath"), "source": rubric.get("source")}
                for a in resolved:
                    entry[a] = self._remedy_rubric_index[a].get(rid, 0)
                overlap_rubrics.append(entry)

        # --- Exclusive rubrics per remedy ---
        exclusive: Dict[str, List[Dict]] = defaultdict(list)
        for i, a in enumerate(resolved):
            other_sets = [rubric_sets[j] for j in range(len(resolved)) if j != i]
            if other_sets:
                union_others = set.union(*other_sets)
            else:
                union_others = set()
            unique_ids = rubric_sets[i] - union_others
            for rid in sorted(unique_ids):
                rubric = self.rep.get_rubric_by_id(rid)
                if rubric:
                    exclusive[a].append({
                        "rubric_id": rid,
                        "fullpath": rubric.get("fullpath"),
                        "source": rubric.get("source"),
                        "weight": self._remedy_rubric_index[a].get(rid, 0),
                    })

        # --- Pairwise divergence: where one remedy outranks another ---
        pairwise = []
        for i in range(len(resolved)):
            for j in range(i + 1, len(resolved)):
                a, b = resolved[i], resolved[j]
                a_wins = []
                b_wins = []
                shared = rubric_sets[i] & rubric_sets[j]
                for rid in shared:
                    wa = self._remedy_rubric_index[a].get(rid, 0)
                    wb = self._remedy_rubric_index[b].get(rid, 0)
                    rubric = self.rep.get_rubric_by_id(rid)
                    if rubric and wa != wb:
                        entry = {
                            "rubric_id": rid,
                            "fullpath": rubric.get("fullpath"),
                            f"{a}_weight": wa,
                            f"{b}_weight": wb,
                        }
                        if wa > wb:
                            a_wins.append(entry)
                        else:
                            b_wins.append(entry)
                pairwise.append({
                    "remedy_a": a,
                    "remedy_b": b,
                    "a_advantage_count": len(a_wins),
                    "b_advantage_count": len(b_wins),
                    "a_advantages": sorted(a_wins, key=lambda x: x[f"{a}_weight"], reverse=True)[:10],
                    "b_advantages": sorted(b_wins, key=lambda x: x[f"{b}_weight"], reverse=True)[:10],
                })

        # --- Similarity matrix (Jaccard) ---
        similarity: Dict[str, Dict[str, float]] = defaultdict(dict)
        for i, a in enumerate(resolved):
            similarity[a][a] = 1.0
            for j in range(i + 1, len(resolved)):
                b = resolved[j]
                sa, sb = rubric_sets[i], rubric_sets[j]
                inter = len(sa & sb)
                uni = len(sa | sb)
                jaccard = inter / uni if uni else 0.0
                similarity[a][b] = round(jaccard, 3)
                similarity[b][a] = round(jaccard, 3)

        total_rubrics = {a: len(self._remedy_rubric_index.get(a, {})) for a in resolved}

        return RemedyComparisonResult(
            remedies=resolved,
            overlap_rubrics=overlap_rubrics,
            pairwise_divergence=pairwise,
            exclusive_rubrics=dict(exclusive),
            similarity_matrix=dict(similarity),
            total_rubrics=total_rubrics,
        )

    def diff_two(self, abbrev_a: str, abbrev_b: str) -> Dict:
        """Quick two-remedy diff."""
        result = self.compare_remedies([abbrev_a, abbrev_b])
        return asdict(result)


def compare_remedies_quick(abbrevs: List[str]) -> Dict:
    """Convenience function for quick comparison."""
    comp = RemedyComparator()
    return asdict(comp.compare_remedies(abbrevs))
