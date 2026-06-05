"""
Master Score Engine — Feature #6

Composite repertorization scoring that unifies multiple analysis philosophies
into a single tunable Master Score. Each sub-scorer runs independently, scores
are normalized to [0,1], then weighted and composited.

Sub-scorers included:
  - Kent (classical grade-sum)
  - Boenninghausen (totality / equal-weight coverage)
  - SRP boost (strange-rare-peculiar symptom detection)
  - Rarity bonus (small/rare remedy surfacing)
  - Kingdom affinity (kingdom/family grouping bonus)

Usage:
    from oorep.master_score_engine import MasterScoreEngine

    engine = MasterScoreEngine()
    results = engine.repertorize(
        rubric_ids=[12345, 67890, 11111],
        symptoms=["head pain morning", "worse from consolation"],
        weights={"kent": 0.30, "boenninghausen": 0.20, "srp": 0.25,
                 "rarity": 0.15, "kingdom": 0.10},
        top_n=20,
    )
    # results[0] = {"abbrev": "Puls.", "master_score": 0.87,
    #               "sub_scores": {"kent": 0.92, "boenninghausen": 0.71, ...},
    #               ...}

Classical integrity: The Master Score is used ONLY for ranking. Remedy grades
(1/2/3) and rubric links remain untouched. The score is a composite convenience,
not a replacement for classical analysis.
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

# Local imports with fallback patterns
try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory

try:
    from .kent_vs_boenninghausen import KentVsBoenninghausen
except Exception:
    from kent_vs_boenninghausen import KentVsBoenninghausen

try:
    from .srp_detector import SRPDetector
except Exception:
    from srp_detector import SRPDetector

try:
    from .rare_remedy_triangulator import RareRemedyTriangulator
except Exception:
    from rare_remedy_triangulator import RareRemedyTriangulator

try:
    from .kingdom_taxonomy import KingdomTaxonomy
except Exception:
    from kingdom_taxonomy import KingdomTaxonomy


@dataclass
class SubScoreResult:
    """Normalized sub-score from a single scoring philosophy."""
    scorer_name: str
    raw_score: float
    normalized_score: float  # 0.0–1.0 within this scorer's output
    rank: int  # 1-based rank within this scorer
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MasterScoreResult:
    """Final composite result for a single remedy."""
    abbrev: str
    remedy_name: str
    master_score: float
    sub_scores: Dict[str, SubScoreResult]
    rank: int
    match_count: int
    grade_distribution: Dict[int, int]
    matches: List[Dict[str, Any]]
    confidence: float  # 0.0–1.0, based on sub-score agreement


class MasterScoreEngine:
    """
    Composite repertorization engine unifying Kent, Boenninghausen,
    SRP, rarity, and kingdom scoring.
    """

    # Default weight vector — tunable per case
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "kent": 0.30,
        "boenninghausen": 0.20,
        "srp": 0.25,
        "rarity": 0.15,
        "kingdom": 0.10,
    }

    # Valid scorer names
    VALID_SCORERS = frozenset(DEFAULT_WEIGHTS.keys())

    def __init__(
        self,
        repertory: Optional[HomeopathicRepertory] = None,
        kvb: Optional[KentVsBoenninghausen] = None,
        srp_detector: Optional[SRPDetector] = None,
        rarity_triangulator: Optional[RareRemedyTriangulator] = None,
        taxonomy: Optional[KingdomTaxonomy] = None,
    ):
        self.rep = repertory
        self._kvb = kvb
        self._srp = srp_detector
        self._rarity = rarity_triangulator
        self._taxonomy = taxonomy
        # Lazy-loaded components
        self.__kvb: Optional[KentVsBoenninghausen] = None
        self.__srp: Optional[SRPDetector] = None
        self.__rarity: Optional[RareRemedyTriangulator] = None
        self.__taxonomy: Optional[KingdomTaxonomy] = None

    # ── Lazy property accessors ────────────────────────────────────────────────

    @property
    def rep(self) -> HomeopathicRepertory:
        if self._rep is None:
            self._rep = HomeopathicRepertory()
        return self._rep

    @rep.setter
    def rep(self, value: Optional[HomeopathicRepertory]):
        self._rep = value

    @property
    def kvb(self) -> KentVsBoenninghausen:
        if self.__kvb is None:
            self.__kvb = self._kvb or KentVsBoenninghausen(self.rep)
        return self.__kvb

    @property
    def srp(self) -> SRPDetector:
        if self.__srp is None:
            self.__srp = self._srp or SRPDetector()
        return self.__srp

    @property
    def rarity(self) -> RareRemedyTriangulator:
        if self.__rarity is None:
            self.__rarity = self._rarity or RareRemedyTriangulator(repertory=self.rep)
        return self.__rarity

    @property
    def taxonomy(self) -> KingdomTaxonomy:
        if self.__taxonomy is None:
            self.__taxonomy = self._taxonomy or KingdomTaxonomy()
        return self.__taxonomy

    # ── Public API ─────────────────────────────────────────────────────────────

    def repertorize(
        self,
        rubric_ids: List[int],
        symptoms: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_n: int = 20,
        include_raw: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Run composite Master Score repertorization.

        Args:
            rubric_ids: Selected rubric IDs (already reviewed/approved).
            symptoms: Original symptom texts (for SRP detection and
                      kingdom inference). Optional.
            weights: Per-scorer weight dict. Must sum to ~1.0.
                     Defaults to DEFAULT_WEIGHTS.
            top_n: Number of top remedies to return.
            include_raw: If True, include raw (non-normalized) sub-scores
                         in output for debugging.

        Returns:
            List of result dicts sorted by master_score descending.
            Each dict contains:
                - abbrev, remedy_name, master_score, rank
                - sub_scores: {scorer_name: {normalized, raw, rank, details}}
                - confidence: inter-scorer agreement metric
                - match_count, grade_distribution, matches
        """
        weights = self._normalize_weights(weights or dict(self.DEFAULT_WEIGHTS))
        symptoms = symptoms or []

        # ── Step 1: Run each sub-scorer ──────────────────────────────────────
        raw_results: Dict[str, List[Dict[str, Any]]] = {}

        if weights.get("kent", 0) > 0:
            raw_results["kent"] = self.kvb.kent_repertorize(rubric_ids, top_n=max(top_n, 50))
        if weights.get("boenninghausen", 0) > 0:
            raw_results["boenninghausen"] = self.kvb.boenninghausen_repertorize(rubric_ids, top_n=max(top_n, 50))
        if weights.get("srp", 0) > 0 and symptoms:
            raw_results["srp"] = self._run_srp_scorer(rubric_ids, symptoms, top_n=max(top_n, 50))
        if weights.get("rarity", 0) > 0 and symptoms:
            raw_results["rarity"] = self._run_rarity_scorer(rubric_ids, symptoms, top_n=max(top_n, 50))
        if weights.get("kingdom", 0) > 0:
            raw_results["kingdom"] = self._run_kingdom_scorer(rubric_ids, symptoms, top_n=max(top_n, 50))

        # ── Step 2: Gather all remedy abbreviations seen by any scorer ───────
        all_abbrevs: set = set()
        for scorer_results in raw_results.values():
            all_abbrevs.update(r["abbrev"] for r in scorer_results)

        if not all_abbrevs:
            return []

        # ── Step 3: Normalize each scorer's scores to [0, 1] ─────────────────
        normalized: Dict[str, Dict[str, float]] = {}
        ranks: Dict[str, Dict[str, int]] = {}

        for scorer_name, results in raw_results.items():
            scores = {r["abbrev"]: float(r["score"]) for r in results}
            norm_scores = self._normalize_scores(scores)
            rank_map = {r["abbrev"]: i + 1 for i, r in enumerate(results)}
            normalized[scorer_name] = norm_scores
            ranks[scorer_name] = rank_map

        # ── Step 4: Composite master score per remedy ────────────────────────
        master_data: Dict[str, Dict[str, Any]] = {}
        for abbrev in all_abbrevs:
            master_data[abbrev] = {
                "sub_scores": {},
                "master_score": 0.0,
                "match_count": 0,
                "grade_distribution": {1: 0, 2: 0, 3: 0},
                "matches": [],
            }

        for scorer_name, weight in weights.items():
            if weight <= 0 or scorer_name not in raw_results:
                continue
            for result in raw_results[scorer_name]:
                abbrev = result["abbrev"]
                norm = normalized[scorer_name].get(abbrev, 0.0)
                master_data[abbrev]["sub_scores"][scorer_name] = {
                    "normalized": round(norm, 4),
                    "raw": round(float(result["score"]), 4),
                    "rank": ranks[scorer_name].get(abbrev, 999),
                    "details": result.get("matches", [])[:3] if include_raw else {},
                }
                master_data[abbrev]["master_score"] += weight * norm
                # Aggregate match data from Kent (most detailed)
                if scorer_name == "kent" and "matches" in result:
                    master_data[abbrev]["matches"] = result["matches"][:5]
                    master_data[abbrev]["match_count"] = result.get("match_count", 0)
                    # Compute grade distribution from Kent matches
                    gd: Dict[int, int] = {1: 0, 2: 0, 3: 0}
                    for m in result.get("matches", []):
                        w = m.get("weight", 1)
                        if w in gd:
                            gd[w] += 1
                    master_data[abbrev]["grade_distribution"] = gd

        # ── Step 5: Compute confidence (inter-scorer agreement) ───────────────
        for abbrev, data in master_data.items():
            sub_scores_list = [
                s["normalized"]
                for s in data["sub_scores"].values()
            ]
            if len(sub_scores_list) >= 2:
                # Coefficient of variation inverse: lower spread = higher confidence
                mean = sum(sub_scores_list) / len(sub_scores_list)
                if mean > 0:
                    variance = sum((s - mean) ** 2 for s in sub_scores_list) / len(sub_scores_list)
                    std = math.sqrt(variance)
                    cv = std / mean
                    confidence = max(0.0, min(1.0, 1.0 - cv))
                else:
                    confidence = 0.0
            else:
                confidence = 0.5
            data["confidence"] = round(confidence, 3)

        # ── Step 6: Sort and format ─────────────────────────────────────────
        sorted_items = sorted(
            master_data.items(),
            key=lambda x: (x[1]["master_score"], x[1]["confidence"]),
            reverse=True,
        )

        out: List[Dict[str, Any]] = []
        for rank, (abbrev, data) in enumerate(sorted_items[:top_n], start=1):
            remedy = self.rep.get_remedy_by_abbrev(abbrev)
            remedy_name = remedy.get("name", "") if remedy else ""
            item: Dict[str, Any] = {
                "abbrev": abbrev,
                "remedy_name": remedy_name,
                "master_score": round(data["master_score"], 4),
                "rank": rank,
                "confidence": data["confidence"],
                "match_count": data["match_count"],
                "grade_distribution": data["grade_distribution"],
                "sub_scores": data["sub_scores"],
            }
            if include_raw:
                item["_raw_sub_scores"] = {
                    k: {"raw": v["raw"], "normalized": v["normalized"], "rank": v["rank"]}
                    for k, v in data["sub_scores"].items()
                }
            if data["matches"]:
                item["matches"] = data["matches"]
            out.append(item)

        return out

    def compare_methods(
        self,
        rubric_ids: List[int],
        symptoms: Optional[List[str]] = None,
        top_n: int = 20,
    ) -> Dict[str, Any]:
        """
        Run all methods independently AND composite, then compare them.

        Returns a dict with:
            - master_results: composite top-N
            - kent_results: Kent-only top-N
            - boenninghausen_results: Boenninghausen-only top-N
            - method_agreement: which remedies appear in all top-5s
            - divergence_analysis: narrative + structured data
        """
        master = self.repertorize(
            rubric_ids=rubric_ids,
            symptoms=symptoms,
            weights=self.DEFAULT_WEIGHTS,
            top_n=top_n,
        )
        kent_only = self.kvb.kent_repertorize(rubric_ids, top_n=top_n)
        boen_only = self.kvb.boenninghausen_repertorize(rubric_ids, top_n=top_n)

        master_top = {r["abbrev"] for r in master[:5]}
        kent_top = {r["abbrev"] for r in kent_only[:5]}
        boen_top = {r["abbrev"] for r in boen_only[:5]}

        all_three = sorted(master_top & kent_top & boen_top)
        master_only = sorted(master_top - kent_top - boen_top)
        kent_only_top = sorted(kent_top - master_top)
        boen_only_top = sorted(boen_top - master_top)

        # Rank correlation: Spearman-like for top-10
        master_rank = {r["abbrev"]: i for i, r in enumerate(master[:10])}
        kent_rank = {r["abbrev"]: i for i, r in enumerate(kent_only[:10])}
        boen_rank = {r["abbrev"]: i for i, r in enumerate(boen_only[:10])}

        common_in_top10 = sorted(
            set(master_rank.keys()) & set(kent_rank.keys()) & set(boen_rank.keys())
        )
        rank_diffs = []
        for abbrev in common_in_top10:
            mk = master_rank[abbrev]
            kk = kent_rank[abbrev]
            bk = boen_rank[abbrev]
            rank_diffs.append({
                "remedy": abbrev,
                "master_rank": mk + 1,
                "kent_rank": kk + 1,
                "boen_rank": bk + 1,
                "master_vs_kent": mk - kk,
                "master_vs_boen": mk - bk,
            })

        narrative_parts = []
        if all_three:
            narrative_parts.append(
                f"All methods agree on: {', '.join(all_three)}. "
                "These are robust candidates across all scoring philosophies."
            )
        if master_only:
            narrative_parts.append(
                f"Master Score uniquely highlights: {', '.join(master_only)}. "
                "These benefited from SRP/rarity/kingdom composite weighting."
            )
        if kent_only_top:
            narrative_parts.append(
                f"Kent-only top remedies: {', '.join(kent_only_top)}. "
                "High-grade individual rubrics but possibly narrow coverage."
            )
        if boen_only_top:
            narrative_parts.append(
                f"Boenninghausen-only top remedies: {', '.join(boen_only_top)}. "
                "Broad coverage but possibly lower individual grades."
            )

        return {
            "master_results": master[:top_n],
            "kent_results": kent_only[:top_n],
            "boenninghausen_results": boen_only[:top_n],
            "method_agreement": {
                "all_three": all_three,
                "master_only": master_only,
                "kent_only": kent_only_top,
                "boen_only": boen_only_top,
            },
            "divergence_analysis": {
                "common_top10": common_in_top10,
                "rank_shifts": rank_diffs,
                "narrative": " ".join(narrative_parts)
                    or "Methods largely agree on top candidates.",
            },
        }

    # ── Sub-scorer implementations ─────────────────────────────────────────────

    def _run_srp_scorer(
        self,
        rubric_ids: List[int],
        symptoms: List[str],
        top_n: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        SRP-enhanced Kent scoring: apply per-symptom SRP boost multipliers.
        Returns results in same format as kent_repertorize.
        """
        # Analyze symptoms for SRP markers
        srp_weights = self.srp.get_srp_weights_for_repertorization(symptoms)
        # Map symptoms to rubric IDs (best effort: use order)
        # In practice, rubric_ids and symptoms should be 1:1
        symptom_for_rubric: Dict[int, str] = {}
        for i, rid in enumerate(rubric_ids):
            if i < len(symptoms):
                symptom_for_rubric[rid] = symptoms[i]

        remedy_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"score": 0.0, "matches": [], "_rubric_ids": set()}
        )
        for rid in rubric_ids:
            remedies = self.rep.get_remedies_for_rubric(rid)
            symptom_text = symptom_for_rubric.get(rid, "")
            srp_boost = srp_weights.get(symptom_text, 1.0)
            for rem in remedies:
                abbrev = rem["abbrev"]
                weight = rem.get("weight", 1)
                boosted = weight * srp_boost
                remedy_data[abbrev]["score"] += boosted
                remedy_data[abbrev]["_rubric_ids"].add(rid)
                rubric_full = self.rep.get_rubric_by_id(rid)
                remedy_data[abbrev]["matches"].append({
                    "rubric_id": rid,
                    "rubric": rubric_full.get("fullpath") if rubric_full else None,
                    "weight": weight,
                    "srp_boost": srp_boost,
                })

        sorted_results = sorted(
            remedy_data.items(), key=lambda x: x[1]["score"], reverse=True
        )
        out: List[Dict[str, Any]] = []
        for abbrev, data in sorted_results[:top_n]:
            out.append({
                "abbrev": abbrev,
                "score": round(data["score"], 2),
                "match_count": len(data["_rubric_ids"]),
                "matches": data["matches"][:5],
            })
        return out

    def _run_rarity_scorer(
        self,
        rubric_ids: List[int],
        symptoms: List[str],
        top_n: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Rarity scorer: small remedies that cover the rubric set get a bonus.
        Uses Kent base + rarity quotient scaling.
        """
        # Base Kent scores
        kent_results = self.kvb.kent_repertorize(rubric_ids, top_n=top_n)
        if not kent_results:
            return []

        # Get rarity signals for the symptom set
        try:
            rare_signals = self.rarity.triangulate(symptoms, top_n=top_n * 2)
        except Exception:
            rare_signals = []
        rarity_bonus: Dict[str, float] = {
            s.remedy_abbrev: s.rarity_quotient for s in rare_signals
        }

        out: List[Dict[str, Any]] = []
        for r in kent_results:
            abbrev = r["abbrev"]
            base_score = float(r["score"])
            bonus = rarity_bonus.get(abbrev, 0.0)
            # Rarity score = base Kent score + rarity quotient bonus
            # Small remedies with rare rubric coverage get pushed up
            score = base_score + (bonus * 3.0)  # Scale bonus to match Kent range
            out.append({
                "abbrev": abbrev,
                "score": round(score, 2),
                "match_count": r.get("match_count", 0),
                "matches": r.get("matches", []),
            })
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:top_n]

    def _run_kingdom_scorer(
        self,
        rubric_ids: List[int],
        symptoms: Optional[List[str]] = None,
        top_n: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Kingdom affinity scorer: boost remedies in the inferred kingdom.
        Kingdom inference is naive keyword matching from symptoms.
        """
        inferred_kingdom = self._infer_kingdom(symptoms or [])
        kent_results = self.kvb.kent_repertorize(rubric_ids, top_n=top_n)
        if not kent_results:
            return []

        out: List[Dict[str, Any]] = []
        for r in kent_results:
            abbrev = r["abbrev"]
            base_score = float(r["score"])
            tags = self.taxonomy.get_tags(abbrev)
            kingdom_match = 0.0
            if inferred_kingdom and tags:
                if tags.get("kingdom") == inferred_kingdom:
                    kingdom_match = 1.0
                elif tags.get("family") and inferred_kingdom in str(tags.get("family")).lower():
                    kingdom_match = 0.5
            # Kingdom score = base + affinity bonus (0-3 points)
            score = base_score + (kingdom_match * 3.0)
            out.append({
                "abbrev": abbrev,
                "score": round(score, 2),
                "match_count": r.get("match_count", 0),
                "matches": r.get("matches", []),
                "_kingdom_match": kingdom_match,
            })
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:top_n]

    def _infer_kingdom(self, symptoms: List[str]) -> Optional[str]:
        """Naive kingdom inference from symptom keywords."""
        text = " ".join(symptoms).lower()
        plant_markers = ["plant", "flower", "tree", "root", "leaf", "growing", "bloom",
                         "herb", "botanical", "vegetable", "wood", "green"]
        animal_markers = ["animal", "bite", "sting", "snake", "spider", "insect",
                          "bird", "fish", "mammal", "venom", "poison", "crawl",
                          "fly", "swim", "hunt", "prey"]
        mineral_markers = ["metal", "salt", "crystal", "rock", "stone", "ore",
                           "mineral", "element", "chemical", "compound", "acid",
                           "alkali", "oxide", "carbonate"]
        p_score = sum(1 for m in plant_markers if m in text)
        a_score = sum(1 for m in animal_markers if m in text)
        m_score = sum(1 for m in mineral_markers if m in text)
        scores = [("plant", p_score), ("animal", a_score), ("mineral", m_score)]
        best = max(scores, key=lambda x: x[1])
        return best[0] if best[1] >= 2 else None

    # ── Static utilities ───────────────────────────────────────────────────────

    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights sum to 1.0."""
        total = sum(weights.values())
        if total == 0:
            return dict(MasterScoreEngine.DEFAULT_WEIGHTS)
        return {k: v / total for k, v in weights.items()}

    @staticmethod
    def _normalize_scores(score_map: Dict[str, float]) -> Dict[str, float]:
        """Normalize a score dict to [0, 1]."""
        if not score_map:
            return {}
        values = list(score_map.values())
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            return {k: 1.0 for k in score_map}
        return {k: (v - min_v) / (max_v - min_v) for k, v in score_map.items()}

    @staticmethod
    def get_available_scorers() -> List[str]:
        return sorted(MasterScoreEngine.VALID_SCORERS)

    def get_scorer_description(self, scorer_name: str) -> str:
        descriptions = {
            "kent": "Classical grade-sum scoring (Kent method). Emphasizes high-grade individual rubrics.",
            "boenninghausen": "Totality-of-symptoms scoring (Boenninghausen method). Equal weight per rubric; broad coverage wins.",
            "srp": "Strange-Rare-Peculiar boost. Symptoms with SRP markers receive 1.5–3× multipliers.",
            "rarity": "Rare remedy bonus. Small remedies with rare-rubric coverage receive additive bonus.",
            "kingdom": "Kingdom affinity scoring. Remedies matching inferred kingdom (Plant/Animal/Mineral) get boosted.",
        }
        return descriptions.get(scorer_name, "Unknown scorer.")


# ── Convenience function ─────────────────────────────────────────────────────

def master_repertorize(
    rubric_ids: List[int],
    symptoms: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """One-shot composite repertorization."""
    engine = MasterScoreEngine()
    return engine.repertorize(
        rubric_ids=rubric_ids,
        symptoms=symptoms,
        weights=weights,
        top_n=top_n,
    )
