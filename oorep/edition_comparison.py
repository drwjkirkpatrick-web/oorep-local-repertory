"""
Comparative Repertory Edition Analysis — Feature #29

Compare rubric definitions, remedy grades, and rubric coverage across
different repertory editions (Kent 1st vs Kent 2nd, Synthesis vs OOREP).
Highlight added/removed/grade-changed rubrics. Track edition drift over time.

Usage:
    from oorep.edition_comparison import EditionComparisonEngine

    engine = EditionComparisonEngine(
        editions={
            "kent_1st": "data/kent_1st_rubrics.json",
            "kent_2nd": "data/kent_2nd_rubrics.json",
            "synthesis":  "data/synthesis_rubrics.json",
        }
    )

    # Compare two editions
    diff = engine.compare("kent_1st", "kent_2nd")

    # Find rubrics that changed grade for a remedy
    changes = engine.grade_changes("ARS", baseline="kent_1st", target="kent_2nd")

    # Get coverage report
    coverage = engine.coverage_report("kent_1st")

    # Edition drift (how much has the repertory changed)
    drift = engine.edition_drift("kent_1st", "kent_2nd")
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict, field


# ──────────────────────────────────────────────────────────────────────────────
# Data classes for type safety and clean serialization
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RubricDiff:
    """Difference in a single rubric between two editions."""
    rubric_id: str
    path: str
    change_type: str  # 'added', 'removed', 'grade_changed', 'text_changed', 'unchanged'
    baseline_grade: Optional[int] = None
    target_grade: Optional[int] = None
    baseline_remedies: int = 0
    target_remedies: int = 0
    remedy_diffs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CoverageEntry:
    """Coverage statistics for one edition."""
    edition: str
    total_rubrics: int
    total_remedy_entries: int
    avg_remedies_per_rubric: float
    unique_remedies: int
    max_grade3_count: int
    max_grade2_count: int
    max_grade1_count: int


@dataclass
class DriftMetrics:
    """Quantified edition drift between two editions."""
    baseline_edition: str
    target_edition: str
    jaccard_similarity: float       # overlap of rubric IDs
    weighted_similarity: float      # weighted by remedy counts
    grade_consistency: float      # fraction of shared rubrics with same max grade
    coverage_delta: float           # absolute difference in total entries
    added_rubrics: int
    removed_rubrics: int
    grade_changed_rubrics: int
    total_drift_score: float        # composite 0-1


# ──────────────────────────────────────────────────────────────────────────────
# Edition comparison engine
# ──────────────────────────────────────────────────────────────────────────────

class EditionComparisonEngine:
    """
    Multi-edition repertory comparison engine.

    Supports any number of editions loaded from JSON files.
    Each edition JSON should be a list of rubric dicts or a dict with
    a "rubrics" key. Each rubric dict needs at minimum:
        - "id" (str or int)
        - "fullpath" or "path" (str)
        - "remedies": [{"remedy": str, "grade": int}, ...]
    """

    def __init__(self, editions: Dict[str, str]):
        """
        Parameters
        ----------
        editions: dict[str, str]
            Mapping edition name -> file path.
        """
        self.edition_paths = editions
        self._data: Dict[str, Dict[str, Any]] = {}
        self._rubric_index: Dict[str, Dict[str, Any]] = {}

    # ── Data loading ────────────────────────────────────────────────────────

    def load_edition(self, name: str) -> Dict[str, Any]:
        """Load and index a single edition."""
        if name in self._rubric_index:
            return self._rubric_index[name]

        path = self.edition_paths.get(name)
        if not path:
            raise ValueError(f"Edition '{name}' not registered")

        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        # Normalize to list of rubric dicts
        rubric_list: List[Dict]
        if isinstance(raw, dict) and "rubrics" in raw:
            rubric_list = raw["rubrics"]
        elif isinstance(raw, list):
            rubric_list = raw
        else:
            rubric_list = []

        # Index by rubric ID for fast lookup
        index: Dict[str, Dict] = {}
        for r in rubric_list:
            rid = str(r.get("id", r.get("rubric_id", "")))
            if not rid:
                continue
            index[rid] = {
                "id": rid,
                "path": r.get("fullpath", r.get("path", "")),
                "text": r.get("text", ""),
                "remedies": r.get("remedies", []),
                "source": r.get("source", name),
            }

        self._rubric_index[name] = index
        return index

    def get_rubric(self, edition: str, rubric_id: str) -> Optional[Dict]:
        """Fetch a specific rubric from an edition."""
        index = self.load_edition(edition)
        return index.get(rubric_id)

    # ── Comparison ────────────────────────────────────────────────────────────

    def compare(
        self,
        baseline: str,
        target: str,
        remedies_of_interest: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Full comparison between two editions.

        Returns structured diff with added, removed, grade-changed, and unchanged rubrics.
        """
        base = self.load_edition(baseline)
        tgt = self.load_edition(target)

        base_ids = set(base.keys())
        tgt_ids = set(tgt.keys())

        added = tgt_ids - base_ids
        removed = base_ids - tgt_ids
        shared = base_ids & tgt_ids

        added_list: List[RubricDiff] = []
        removed_list: List[RubricDiff] = []
        grade_changed_list: List[RubricDiff] = []
        unchanged_list: List[RubricDiff] = []

        for rid in sorted(added):
            r = tgt[rid]
            added_list.append(RubricDiff(
                rubric_id=rid,
                path=r["path"],
                change_type="added",
                target_remedies=len(r["remedies"]),
            ))

        for rid in sorted(removed):
            r = base[rid]
            removed_list.append(RubricDiff(
                rubric_id=rid,
                path=r["path"],
                change_type="removed",
                baseline_remedies=len(r["remedies"]),
            ))

        for rid in sorted(shared):
            b = base[rid]
            t = tgt[rid]
            same = self._rubric_equal(b, t, remedies_of_interest)
            if same:
                unchanged_list.append(RubricDiff(
                    rubric_id=rid,
                    path=b["path"],
                    change_type="unchanged",
                    baseline_remedies=len(b["remedies"]),
                    target_remedies=len(t["remedies"]),
                ))
            else:
                rd = self._compute_remedy_diff(b, t, remedies_of_interest)
                grade_changed_list.append(RubricDiff(
                    rubric_id=rid,
                    path=b["path"],
                    change_type="grade_changed",
                    baseline_remedies=len(b["remedies"]),
                    target_remedies=len(t["remedies"]),
                    remedy_diffs=rd,
                ))

        # Summary counts
        total = len(added) + len(removed) + len(shared)
        return {
            "baseline": baseline,
            "target": target,
            "remedies_filtered": remedies_of_interest,
            "total_rubrics_baseline": len(base),
            "total_rubrics_target": len(tgt),
            "added": [asdict(x) for x in added_list],
            "removed": [asdict(x) for x in removed_list],
            "grade_changed": [asdict(x) for x in grade_changed_list],
            "unchanged": [asdict(x) for x in unchanged_list],
            "summary": {
                "added_count": len(added),
                "removed_count": len(removed),
                "grade_changed_count": len(grade_changed_list),
                "unchanged_count": len(unchanged_list),
                "drift_percent": round(
                    (len(added) + len(removed) + len(grade_changed_list)) / max(total, 1) * 100, 2
                ),
            },
        }

    def grade_changes(
        self,
        remedy: str,
        baseline: str,
        target: str,
    ) -> List[Dict[str, Any]]:
        """Return all rubrics where `remedy` changed grade between editions."""
        base = self.load_edition(baseline)
        tgt = self.load_edition(target)
        shared = set(base.keys()) & set(tgt.keys())

        changes = []
        for rid in shared:
            b_grade = self._remedy_grade(base[rid], remedy)
            t_grade = self._remedy_grade(tgt[rid], remedy)
            if b_grade != t_grade:
                changes.append({
                    "rubric_id": rid,
                    "path": base[rid]["path"],
                    "baseline_grade": b_grade,
                    "target_grade": t_grade,
                    "change": f"{b_grade or '-'} → {t_grade or '-'}",
                })
        return changes

    def coverage_report(self, edition: str) -> Dict[str, Any]:
        """Statistical coverage analysis for a single edition."""
        if edition not in self.edition_paths:
            return {"edition": edition, "error": "Edition not registered"}
        idx = self.load_edition(edition)
        if not idx:
            return {"edition": edition, "error": "Empty or missing data"}

        total_rubrics = len(idx)
        total_entries = 0
        unique_remedies: Set[str] = set()
        grade_counts = {1: 0, 2: 0, 3: 0}

        for rubric in idx.values():
            for rem in rubric.get("remedies", []):
                total_entries += 1
                abbrev = rem.get("remedy", "")
                if abbrev:
                    unique_remedies.add(abbrev.upper())
                g = rem.get("grade", 1)
                if g in grade_counts:
                    grade_counts[g] += 1

        avg_remedies = total_entries / max(total_rubrics, 1)

        entry = CoverageEntry(
            edition=edition,
            total_rubrics=total_rubrics,
            total_remedy_entries=total_entries,
            avg_remedies_per_rubric=round(avg_remedies, 2),
            unique_remedies=len(unique_remedies),
            max_grade3_count=grade_counts[3],
            max_grade2_count=grade_counts[2],
            max_grade1_count=grade_counts[1],
        )
        return asdict(entry)

    def edition_drift(self, baseline: str, target: str) -> Dict[str, Any]:
        """
        Quantified drift metrics between two editions.
        """
        base = self.load_edition(baseline)
        tgt = self.load_edition(target)

        base_ids = set(base.keys())
        tgt_ids = set(tgt.keys())
        shared = base_ids & tgt_ids
        union = base_ids | tgt_ids

        # Jaccard similarity (rubric overlap)
        jaccard = len(shared) / max(len(union), 1)

        # Weighted similarity (remedy entry overlap)
        shared_entries = 0
        base_entries = sum(len(b["remedies"]) for b in base.values())
        tgt_entries = sum(len(t["remedies"]) for t in tgt.values())
        for rid in shared:
            base_rems = {r["remedy"]: r["grade"] for r in base[rid]["remedies"]}
            tgt_rems = {r["remedy"]: r["grade"] for r in tgt[rid]["remedies"]}
            shared_rems = set(base_rems.keys()) & set(tgt_rems.keys())
            shared_entries += len(shared_rems)
        total_entries = max(base_entries, tgt_entries, 1)
        weighted_sim = shared_entries / total_entries

        # Grade consistency: fraction of shared rubrics where max grade is same
        consistent = 0
        for rid in shared:
            b_max = max((r["grade"] for r in base[rid]["remedies"]), default=0)
            t_max = max((r["grade"] for r in tgt[rid]["remedies"]), default=0)
            if b_max == t_max:
                consistent += 1
        grade_consistency = consistent / max(len(shared), 1)

        # Coverage delta
        coverage_delta = abs(base_entries - tgt_entries) / max(base_entries, 1)

        # Per-rubric changes
        added = len(tgt_ids - base_ids)
        removed = len(base_ids - tgt_ids)
        grade_changed = 0
        for rid in shared:
            if not self._rubric_equal(base[rid], tgt[rid]):
                grade_changed += 1

        # Total drift score (inverse of similarity, normalized 0-1)
        total_drift = min(1.0, (1 - jaccard) + coverage_delta + (1 - grade_consistency)) / 3

        return asdict(DriftMetrics(
            baseline_edition=baseline,
            target_edition=target,
            jaccard_similarity=round(jaccard, 4),
            weighted_similarity=round(weighted_sim, 4),
            grade_consistency=round(grade_consistency, 4),
            coverage_delta=round(coverage_delta, 4),
            added_rubrics=added,
            removed_rubrics=removed,
            grade_changed_rubrics=grade_changed,
            total_drift_score=round(total_drift, 4),
        ))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _remedy_grade(rubric: Dict, remedy: str) -> Optional[int]:
        """Return grade of a specific remedy in a rubric, or None."""
        for r in rubric.get("remedies", []):
            if r.get("remedy", "").upper() == remedy.upper():
                return r.get("grade")
        return None

    @staticmethod
    def _rubric_equal(
        base: Dict,
        target: Dict,
        remedies_filter: Optional[List[str]] = None,
    ) -> bool:
        """Check if two rubric entries are functionally equal (same remedy grades)."""
        base_rems = {r["remedy"]: r["grade"] for r in base.get("remedies", [])}
        tgt_rems = {r["remedy"]: r["grade"] for r in target.get("remedies", [])}

        if remedies_filter:
            filt = set(r.upper() for r in remedies_filter)
            base_rems = {k: v for k, v in base_rems.items() if k.upper() in filt}
            tgt_rems = {k: v for k, v in tgt_rems.items() if k.upper() in filt}

        return base_rems == tgt_rems

    @staticmethod
    def _compute_remedy_diff(
        base: Dict,
        target: Dict,
        remedies_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Compute per-remedy diffs between two rubric versions."""
        base_rems = {r["remedy"]: r["grade"] for r in base.get("remedies", [])}
        tgt_rems = {r["remedy"]: r["grade"] for r in target.get("remedies", [])}

        if remedies_filter:
            filt = set(r.upper() for r in remedies_filter)
            base_rems = {k: v for k, v in base_rems.items() if k.upper() in filt}
            tgt_rems = {k: v for k, v in tgt_rems.items() if k.upper() in filt}

        all_rems = set(base_rems.keys()) | set(tgt_rems.keys())
        diffs = []
        for rem in sorted(all_rems):
            b = base_rems.get(rem)
            t = tgt_rems.get(rem)
            if b != t:
                diffs.append({
                    "remedy": rem,
                    "baseline_grade": b,
                    "target_grade": t,
                    "change": "added" if b is None else ("removed" if t is None else "grade_changed"),
                })
        return diffs

    def get_feature_overview(self) -> Dict[str, Any]:
        """Feature metadata for integration dashboards."""
        return {
            "feature_id": 29,
            "feature_name": "Comparative Repertory Edition Analysis",
            "supported_comparisons": ["rubric_diff", "grade_changes", "coverage_report", "drift_metrics"],
            "cold_start_capable": True,
            "interpretable": True,
            "version": "1.0",
        }
