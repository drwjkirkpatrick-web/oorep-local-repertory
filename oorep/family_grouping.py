"""
Family Grouping Engine — Feature #7

Groups repertorization results by kingdom, family, and group; filters by
taxonomic criteria; and provides family-level scoring (e.g., "Solanaceae as a
family scores highest across these rubrics").

Integrates with:
  - HomeopathicRepertory (repertorization data)
  - KingdomTaxonomy (classification tags)
  - MasterScoreEngine (optional composite scoring within families)

Usage:
    from oorep.family_grouping import FamilyGroupingEngine

    engine = FamilyGroupingEngine()

    # Filter existing repertorization to Plant remedies only
    plant_results = engine.filter_by_kingdom(results, kingdom="plant")

    # Group a rubric set by family and score families
    family_scores = engine.group_by_family(rubric_ids=[12345, 67890])

    # Get all remedies in a family
    solanaceae = engine.get_family_remedies("Solanaceae")

    # Compare two families on the same rubric set
    comp = engine.compare_families("Solanaceae", "Ranunculaceae", rubric_ids=[12345, 67890])
"""

import json
import math
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory

try:
    from .kingdom_taxonomy import KingdomTaxonomy
except Exception:
    from kingdom_taxonomy import KingdomTaxonomy

try:
    from .master_score_engine import MasterScoreEngine
except Exception:
    from master_score_engine import MasterScoreEngine


@dataclass
class FamilyScoreResult:
    """Family-level scoring result."""
    family: str
    kingdom: str
    remedy_count: int
    total_score: float
    avg_score: float
    max_score: float
    top_remedy: str
    coverage_ratio: float  # fraction of rubrics covered by at least one family member
    remedies: List[Dict[str, Any]]


@dataclass
class KingdomScoreResult:
    """Kingdom-level scoring result."""
    kingdom: str
    remedy_count: int
    total_score: float
    avg_score: float
    families: List[str]
    coverage_ratio: float


class FamilyGroupingEngine:
    """
    Family grouping and kingdom filtering for repertorization.
    """

    def __init__(
        self,
        repertory: Optional[HomeopathicRepertory] = None,
        taxonomy: Optional[KingdomTaxonomy] = None,
        master_engine: Optional[MasterScoreEngine] = None,
    ):
        self._rep = repertory
        self._taxonomy = taxonomy
        self._master = master_engine
        # Lazy loaded
        self.__rep: Optional[HomeopathicRepertory] = None
        self.__taxonomy: Optional[KingdomTaxonomy] = None
        self.__master: Optional[MasterScoreEngine] = None

    @property
    def rep(self) -> HomeopathicRepertory:
        if self.__rep is None:
            self.__rep = self._rep or HomeopathicRepertory()
        return self.__rep

    @property
    def taxonomy(self) -> KingdomTaxonomy:
        if self.__taxonomy is None:
            self.__taxonomy = self._taxonomy or KingdomTaxonomy()
        return self.__taxonomy

    @property
    def master(self) -> Optional[MasterScoreEngine]:
        if self.__master is None and self._master is not False:
            try:
                self.__master = self._master or MasterScoreEngine(repertory=self.rep)
            except Exception:
                self.__master = None
        return self.__master

    # ── Filtering ──────────────────────────────────────────────────────────────

    def filter_by_kingdom(
        self,
        results: List[Dict[str, Any]],
        kingdom: str,
    ) -> List[Dict[str, Any]]:
        """Filter repertorization results to remedies of a given kingdom."""
        kingdom = kingdom.lower().strip()
        filtered = []
        for r in results:
            abbrev = r.get("abbrev", "")
            tags = self.taxonomy.get_tags(abbrev)
            if tags and tags.get("kingdom") == kingdom:
                filtered.append(r)
        return filtered

    def filter_by_family(
        self,
        results: List[Dict[str, Any]],
        family: str,
    ) -> List[Dict[str, Any]]:
        """Filter repertorization results to remedies of a given family."""
        filtered = []
        for r in results:
            abbrev = r.get("abbrev", "")
            tags = self.taxonomy.get_tags(abbrev)
            if tags and tags.get("family") == family:
                filtered.append(r)
        return filtered

    def filter_by_group(
        self,
        results: List[Dict[str, Any]],
        group: str,
    ) -> List[Dict[str, Any]]:
        """Filter repertorization results to remedies of a given group."""
        filtered = []
        for r in results:
            abbrev = r.get("abbrev", "")
            tags = self.taxonomy.get_tags(abbrev)
            if tags and tags.get("group") == group:
                filtered.append(r)
        return filtered

    # ── Family-level scoring ─────────────────────────────────────────────────

    def group_by_family(
        self,
        rubric_ids: List[int],
        symptoms: Optional[List[str]] = None,
        top_n: int = 10,
        use_master_score: bool = False,
    ) -> List[FamilyScoreResult]:
        """
        Score families (not individual remedies) across a rubric set.

        For each family, the score is the sum of the highest-grade remedy
        in that family per rubric. This gives families credit for having
        *any* member cover a rubric, while still rewarding multiple members.
        """
        # Get base remedy scores
        if use_master_score and self.master is not None:
            remedy_results = self.master.repertorize(
                rubric_ids=rubric_ids,
                symptoms=symptoms,
                top_n=50,
            )
        else:
            # Simple Kent scoring
            remedy_data: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {"score": 0.0, "matches": [], "_rubric_ids": set()}
            )
            for rid in rubric_ids:
                remedies = self.rep.get_remedies_for_rubric(rid)
                for rem in remedies:
                    abbrev = rem["abbrev"]
                    weight = rem.get("weight", 1)
                    remedy_data[abbrev]["score"] += weight
                    remedy_data[abbrev]["_rubric_ids"].add(rid)
                    rubric_full = self.rep.get_rubric_by_id(rid)
                    remedy_data[abbrev]["matches"].append({
                        "rubric_id": rid,
                        "rubric": rubric_full.get("fullpath") if rubric_full else None,
                        "weight": weight,
                    })
            remedy_results = [
                {
                    "abbrev": abbrev,
                    "score": data["score"],
                    "match_count": len(data["_rubric_ids"]),
                    "matches": data["matches"][:5],
                }
                for abbrev, data in remedy_data.items()
            ]
            remedy_results.sort(key=lambda x: x["score"], reverse=True)

        # Group by family
        family_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "kingdom": "",
                "remedy_scores": {},
                "rubric_ids": set(),
                "remedy_count": 0,
            }
        )

        for r in remedy_results:
            abbrev = r["abbrev"]
            tags = self.taxonomy.get_tags(abbrev)
            if not tags or not tags.get("family"):
                continue
            family = tags["family"]
            kingdom = tags.get("kingdom", "")
            fd = family_data[family]
            fd["kingdom"] = kingdom
            fd["remedy_count"] += 1
            fd["remedy_scores"][abbrev] = r["score"]
            for m in r.get("matches", []):
                fd["rubric_ids"].add(m.get("rubric_id", 0))

        # Build FamilyScoreResult objects
        results: List[FamilyScoreResult] = []
        for family, data in family_data.items():
            scores = list(data["remedy_scores"].values())
            if not scores:
                continue
            total = sum(scores)
            avg = total / len(scores)
            max_score = max(scores)
            top_remedy = max(data["remedy_scores"].items(), key=lambda x: x[1])[0]
            coverage = len(data["rubric_ids"]) / len(rubric_ids) if rubric_ids else 0.0

            # Build remedy detail list
            remedy_details = []
            for abbrev, score in sorted(data["remedy_scores"].items(), key=lambda x: x[1], reverse=True):
                rem = self.rep.get_remedy_by_abbrev(abbrev)
                remedy_details.append({
                    "abbrev": abbrev,
                    "name": rem.get("name", "") if rem else "",
                    "score": score,
                })

            results.append(FamilyScoreResult(
                family=family,
                kingdom=data["kingdom"],
                remedy_count=data["remedy_count"],
                total_score=round(total, 2),
                avg_score=round(avg, 2),
                max_score=round(max_score, 2),
                top_remedy=top_remedy,
                coverage_ratio=round(coverage, 3),
                remedies=remedy_details,
            ))

        results.sort(key=lambda x: (x.total_score, x.coverage_ratio), reverse=True)
        return results[:top_n]

    def group_by_kingdom(
        self,
        rubric_ids: List[int],
        symptoms: Optional[List[str]] = None,
        top_n: int = 10,
        use_master_score: bool = False,
    ) -> List[KingdomScoreResult]:
        """
        Score kingdoms across a rubric set.
        """
        family_results = self.group_by_family(
            rubric_ids=rubric_ids,
            symptoms=symptoms,
            top_n=100,
            use_master_score=use_master_score,
        )

        kingdom_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total_score": 0.0, "remedy_count": 0, "families": set(), "rubric_ids": set()}
        )

        for fr in family_results:
            kd = kingdom_data[fr.kingdom]
            kd["total_score"] += fr.total_score
            kd["remedy_count"] += fr.remedy_count
            kd["families"].add(fr.family)
            for rem in fr.remedies:
                for m in rem.get("matches", []):
                    kd["rubric_ids"].add(m.get("rubric_id", 0))

        results: List[KingdomScoreResult] = []
        for kingdom, data in kingdom_data.items():
            count = data["remedy_count"]
            total = data["total_score"]
            avg = total / count if count > 0 else 0.0
            coverage = len(data["rubric_ids"]) / len(rubric_ids) if rubric_ids else 0.0
            results.append(KingdomScoreResult(
                kingdom=kingdom,
                remedy_count=count,
                total_score=round(total, 2),
                avg_score=round(avg, 2),
                families=sorted(data["families"]),
                coverage_ratio=round(coverage, 3),
            ))

        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_n]

    # ── Family queries ───────────────────────────────────────────────────────

    def get_family_remedies(self, family: str) -> List[Dict[str, Any]]:
        """Return all remedies belonging to a botanical/zoological family."""
        abbrevs = self.taxonomy.query(family=family)
        results = []
        for abbrev in abbrevs:
            rem = self.rep.get_remedy_by_abbrev(abbrev)
            tags = self.taxonomy.get_tags(abbrev)
            if rem:
                results.append({
                    "abbrev": abbrev,
                    "name": rem.get("name", ""),
                    "kingdom": tags.get("kingdom") if tags else None,
                    "family": tags.get("family") if tags else None,
                    "group": tags.get("group") if tags else None,
                })
        return results

    def get_kingdom_remedies(self, kingdom: str) -> List[Dict[str, Any]]:
        """Return all remedies belonging to a kingdom."""
        abbrevs = self.taxonomy.query(kingdom=kingdom)
        results = []
        for abbrev in abbrevs:
            rem = self.rep.get_remedy_by_abbrev(abbrev)
            tags = self.taxonomy.get_tags(abbrev)
            if rem:
                results.append({
                    "abbrev": abbrev,
                    "name": rem.get("name", ""),
                    "kingdom": tags.get("kingdom") if tags else None,
                    "family": tags.get("family") if tags else None,
                    "group": tags.get("group") if tags else None,
                })
        return results

    # ── Family comparison ────────────────────────────────────────────────────

    def compare_families(
        self,
        family_a: str,
        family_b: str,
        rubric_ids: List[int],
        symptoms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare two families on the same rubric set.
        Returns overlap, unique rubrics, and score breakdown.
        """
        # Get remedies in each family
        a_remedies = self.get_family_remedies(family_a)
        b_remedies = self.get_family_remedies(family_b)
        a_abbrevs = {r["abbrev"] for r in a_remedies}
        b_abbrevs = {r["abbrev"] for r in b_remedies}

        # Score each family
        a_rubric_scores: Dict[int, float] = {}
        b_rubric_scores: Dict[int, float] = {}

        for rid in rubric_ids:
            remedies = self.rep.get_remedies_for_rubric(rid)
            a_max = 0.0
            b_max = 0.0
            for rem in remedies:
                abbrev = rem["abbrev"]
                weight = rem.get("weight", 1)
                if abbrev in a_abbrevs:
                    a_max = max(a_max, weight)
                if abbrev in b_abbrevs:
                    b_max = max(b_max, weight)
            a_rubric_scores[rid] = a_max
            b_rubric_scores[rid] = b_max

        a_total = sum(a_rubric_scores.values())
        b_total = sum(b_rubric_scores.values())
        a_covered = sum(1 for s in a_rubric_scores.values() if s > 0)
        b_covered = sum(1 for s in b_rubric_scores.values() if s > 0)

        overlap_rids = [rid for rid in rubric_ids if a_rubric_scores[rid] > 0 and b_rubric_scores[rid] > 0]
        a_only_rids = [rid for rid in rubric_ids if a_rubric_scores[rid] > 0 and b_rubric_scores[rid] == 0]
        b_only_rids = [rid for rid in rubric_ids if b_rubric_scores[rid] > 0 and a_rubric_scores[rid] == 0]

        return {
            "family_a": family_a,
            "family_b": family_b,
            "a_total_score": round(a_total, 2),
            "b_total_score": round(b_total, 2),
            "a_coverage": f"{a_covered}/{len(rubric_ids)}",
            "b_coverage": f"{b_covered}/{len(rubric_ids)}",
            "overlap_count": len(overlap_rids),
            "a_only_count": len(a_only_rids),
            "b_only_count": len(b_only_rids),
            "winner": family_a if a_total > b_total else family_b if b_total > a_total else "tie",
            "margin": round(abs(a_total - b_total), 2),
        }

    def compare_kingdoms(
        self,
        kingdom_a: str,
        kingdom_b: str,
        rubric_ids: List[int],
    ) -> Dict[str, Any]:
        """Compare two kingdoms on the same rubric set."""
        a_remedies = self.get_kingdom_remedies(kingdom_a)
        b_remedies = self.get_kingdom_remedies(kingdom_b)
        a_abbrevs = {r["abbrev"] for r in a_remedies}
        b_abbrevs = {r["abbrev"] for r in b_remedies}

        a_total = 0.0
        b_total = 0.0
        a_covered = 0
        b_covered = 0
        overlap = 0

        for rid in rubric_ids:
            remedies = self.rep.get_remedies_for_rubric(rid)
            a_has = any(rem["abbrev"] in a_abbrevs for rem in remedies)
            b_has = any(rem["abbrev"] in b_abbrevs for rem in remedies)
            if a_has:
                a_covered += 1
                a_total += max(rem["weight"] for rem in remedies if rem["abbrev"] in a_abbrevs)
            if b_has:
                b_covered += 1
                b_total += max(rem["weight"] for rem in remedies if rem["abbrev"] in b_abbrevs)
            if a_has and b_has:
                overlap += 1

        return {
            "kingdom_a": kingdom_a,
            "kingdom_b": kingdom_b,
            "a_total_score": round(a_total, 2),
            "b_total_score": round(b_total, 2),
            "a_coverage": f"{a_covered}/{len(rubric_ids)}",
            "b_coverage": f"{b_covered}/{len(rubric_ids)}",
            "overlap_count": overlap,
            "winner": kingdom_a if a_total > b_total else kingdom_b if b_total > a_total else "tie",
            "margin": round(abs(a_total - b_total), 2),
        }

    # ── Integration helpers ──────────────────────────────────────────────────

    def enrich_results_with_taxonomy(
        self,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Add kingdom/family/group tags to each remedy result dict."""
        enriched = []
        for r in results:
            abbrev = r.get("abbrev", "")
            tags = self.taxonomy.get_tags(abbrev)
            item = dict(r)
            if tags:
                item["_taxonomy"] = {
                    "kingdom": tags.get("kingdom"),
                    "family": tags.get("family"),
                    "group": tags.get("group"),
                    "sub_group": tags.get("sub_group"),
                    "column": tags.get("column"),
                }
            else:
                item["_taxonomy"] = None
            enriched.append(item)
        return enriched

    def get_family_summary(self, family: str) -> Dict[str, Any]:
        """Return a summary of a family: remedies, kingdom, related families."""
        remedies = self.get_family_remedies(family)
        if not remedies:
            return {"family": family, "error": "Family not found"}
        kingdom = remedies[0].get("kingdom", "unknown")
        # Find related families in same kingdom
        related = self.taxonomy.get_families(kingdom=kingdom)
        related = [f for f in related if f != family]
        return {
            "family": family,
            "kingdom": kingdom,
            "remedy_count": len(remedies),
            "remedies": remedies,
            "related_families": related[:10],
        }

    def list_all_families(self) -> List[str]:
        """Return all unique families in the taxonomy database."""
        return self.taxonomy.get_families()

    def list_all_kingdoms(self) -> List[str]:
        """Return all unique kingdoms."""
        counts = self.taxonomy.get_kingdom_counts()
        return sorted(counts.keys())


# ── Convenience functions ────────────────────────────────────────────────────

def group_by_family(
    rubric_ids: List[int],
    symptoms: Optional[List[str]] = None,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """One-shot family grouping."""
    engine = FamilyGroupingEngine()
    results = engine.group_by_family(rubric_ids=rubric_ids, symptoms=symptoms, top_n=top_n)
    return [
        {
            "family": r.family,
            "kingdom": r.kingdom,
            "remedy_count": r.remedy_count,
            "total_score": r.total_score,
            "avg_score": r.avg_score,
            "top_remedy": r.top_remedy,
            "coverage_ratio": r.coverage_ratio,
            "remedies": r.remedies,
        }
        for r in results
    ]
