"""
Kent vs Boenninghausen Comparison — Benefit #46

Classical repertorization supports two dominant methodologies:

  - **Kent method**
      Grade-sum scoring: each remedy's total is the sum of its grades
      across all selected rubrics. Higher individual grades (3, 4) pull
      a remedy up strongly.

  - **Boenninghausen method**
      Totality-of-symptoms: every selected rubric carries equal weight.
      Remedies covering *more* rubrics rank higher regardless of grade.
      This highlights broad polychrest coverage.

This module runs both methods side-by-side, analyses where they diverge,
and recommends the more appropriate method based on symptom characteristics.

Usage:
    from oorep.kent_vs_boenninghausen import KentVsBoenninghausen

    tool = KentVsBoenninghausen()
    results = tool.compare_methods(rubric_ids=[12345, 67890, 11111])
    divergence = tool.analyze_divergence(results)
    recommendation = tool.recommend_method(symptoms=["fever", "thirst small quantities"])
"""

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .homeopathic_repertory import HomeopathicRepertory


class KentVsBoenninghausen:
    """
    Side-by-side Kent and Boenninghausen repertorization engine.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        """
        Args:
            repertory: Existing ``HomeopathicRepertory`` instance.
                       A new one is created lazily if None.
        """
        self._rep = repertory

    @property
    def rep(self) -> HomeopathicRepertory:
        """Lazy-load a repertory if none was supplied at init."""
        if self._rep is None:
            self._rep = HomeopathicRepertory()
        return self._rep

    # ── Core methods ───────────────────────────────────────────────────────────

    def kent_repertorize(self, rubric_ids: List[int], top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Classical Kent grade-sum repertorization.

        Args:
            rubric_ids: Selected rubric IDs (already reviewed/approved).
            top_n: Number of top remedies to return.

        Returns:
            List of remedy dicts with ``abbrev``, ``score`` (sum of grades),
            ``match_count``, ``matches``.
        """
        remedy_data: Dict[str, Dict[str, Any]] = {}
        for rid in rubric_ids:
            remedies = self.rep.get_remedies_for_rubric(rid)
            for rem in remedies:
                abbrev = rem["abbrev"]
                weight = rem.get("weight", 1)
                if abbrev not in remedy_data:
                    remedy_data[abbrev] = {"score": 0, "matches": [], "_rubric_ids": set()}
                remedy_data[abbrev]["score"] += weight
                remedy_data[abbrev]["_rubric_ids"].add(rid)
                rubric_full = self.rep.get_rubric_by_id(rid)
                remedy_data[abbrev]["matches"].append({
                    "rubric_id": rid,
                    "rubric": rubric_full.get("fullpath") if rubric_full else None,
                    "weight": weight,
                })

        sorted_results = sorted(
            remedy_data.items(), key=lambda x: x[1]["score"], reverse=True
        )

        out: List[Dict[str, Any]] = []
        for abbrev, data in sorted_results[:top_n]:
            out.append({
                "abbrev": abbrev,
                "score": data["score"],
                "match_count": len(data["_rubric_ids"]),
                "matches": data["matches"][:5],
            })
        return out

    def boenninghausen_repertorize(
        self, rubric_ids: List[int], top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Boenninghausen totality-of-symptoms repertorization.

        Each rubric contributes *equally* (weight = 1). The top remedies are
        those that appear in the greatest number of rubrics, regardless
        of classical grade.

        Args:
            rubric_ids: Selected rubric IDs.
            top_n: Number of top remedies to return.

        Returns:
            List of remedy dicts with ``abbrev``, ``score`` (rubric count),
            ``match_count``, ``matches``.
        """
        remedy_data: Dict[str, Dict[str, Any]] = {}
        for rid in rubric_ids:
            remedies = self.rep.get_remedies_for_rubric(rid)
            seen_abbrev = set()
            for rem in remedies:
                abbrev = rem["abbrev"]
                if abbrev in seen_abbrev:
                    continue
                seen_abbrev.add(abbrev)
                if abbrev not in remedy_data:
                    remedy_data[abbrev] = {"score": 0, "matches": [], "_rubric_ids": set()}
                # Equal weight per rubric = 1
                remedy_data[abbrev]["score"] += 1
                remedy_data[abbrev]["_rubric_ids"].add(rid)
                rubric_full = self.rep.get_rubric_by_id(rid)
                remedy_data[abbrev]["matches"].append({
                    "rubric_id": rid,
                    "rubric": rubric_full.get("fullpath") if rubric_full else None,
                    "weight": 1,
                })

        sorted_results = sorted(
            remedy_data.items(), key=lambda x: x[1]["score"], reverse=True
        )

        out: List[Dict[str, Any]] = []
        for abbrev, data in sorted_results[:top_n]:
            out.append({
                "abbrev": abbrev,
                "score": data["score"],
                "match_count": len(data["_rubric_ids"]),
                "matches": data["matches"][:5],
            })
        return out

    def compare_methods(
        self, rubric_ids: List[int], top_n: int = 20
    ) -> Dict[str, Any]:
        """
        Run BOTH Kent and Boenninghausen methods on the same rubric set
        and return unified results for comparison.

        Returns:
            Dict with keys::

                ``rubric_ids``,
                ``kent_results`` (list),
                ``boenninghausen_results`` (list),
                ``top_common`` (list of remedy abbrevs present in top 5 of both),
                ``top_kent_only``,
                ``top_boenninghausen_only``.
        """
        kent = self.kent_repertorize(rubric_ids, top_n=top_n)
        boen = self.boenninghausen_repertorize(rubric_ids, top_n=top_n)

        kent_top_set = {r["abbrev"] for r in kent[:5]}
        boen_top_set = {r["abbrev"] for r in boen[:5]}

        common = sorted(kent_top_set & boen_top_set)
        kent_only = sorted(kent_top_set - boen_top_set)
        boen_only = sorted(boen_top_set - kent_top_set)

        return {
            "rubric_ids": rubric_ids,
            "kent_results": kent,
            "boenninghausen_results": boen,
            "top_common": common,
            "top_kent_only": kent_only,
            "top_boenninghausen_only": boen_only,
        }

    # ── Divergence analysis ─────────────────────────────────────────────────

    def analyze_divergence(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Highlight where Kent and Boenninghausen disagree in the top ranks.

        Returns:
            Dict with human-readable narrative and structured data.
        """
        kent = results.get("kent_results", [])
        boen = results.get("boenninghausen_results", [])
        common = results.get("top_common", [])
        k_only = results.get("top_kent_only", [])
        b_only = results.get("top_boenninghausen_only", [])

        kent_map = {r["abbrev"]: r for r in kent}
        boen_map = {r["abbrev"]: r for r in boen}

        divergent_pairs: List[Dict[str, Any]] = []
        for rem in kent[:10]:
            abbrev = rem["abbrev"]
            if abbrev in common:
                continue
            boen_entry = boen_map.get(abbrev)
            if boen_entry:
                divergent_pairs.append({
                    "remedy": abbrev,
                    "kent_rank": self._index_of(kent, abbrev),
                    "boen_rank": self._index_of(boen, abbrev),
                    "kent_score": rem["score"],
                    "boen_score": boen_entry["score"],
                    "note": (
                        f"Stronger in Kent (grade-driven) because {abbrev} "
                        if rem["score"] > boen_entry["score"]
                        else f"Weaker in Kent despite broad coverage."
                    ),
                })

        narrative_parts = []
        if common:
            narrative_parts.append(
                f"Both methods agree on top remedies: {', '.join(common)}. "
                "These are robust polychrests with both high grades and broad coverage."
            )
        if k_only:
            narrative_parts.append(
                f"Kent-unique top remedies: {', '.join(k_only)}. "
                "These have high individual grades but may not cover every rubric."
            )
        if b_only:
            narrative_parts.append(
                f"Boenninghausen-unique top remedies: {', '.join(b_only)}. "
                "These appear in many rubrics with lower individual grades."
            )

        return {
            "common_top": common,
            "kent_only_top": k_only,
            "boenninghausen_only_top": b_only,
            "divergent_pairs": divergent_pairs,
            "narrative": " ".join(narrative_parts)
                or "Methods largely agree; no significant divergence detected.",
        }

    # ── Method recommendation heuristic ───────────────────────────────────────

    def recommend_method(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        Recommend Kent or Boenninghausen based on symptom characteristics.

        Heuristic rules:
          - Few symptoms (≤3) + very strange/rare/peculiar → Kent (SRP-driven).
          - Many symptoms, mixed layers, no single dominating symptom
            → Boenninghausen (totality).
          - Acute case with clear keynotes → Kent (grade emphasis).
          - Chronic constitutional case with many rubrics
            → Boenninghausen (broad coverage).
        """
        joined = " ".join(symptoms).lower()
        count = len(symptoms)

        # SRP-like keyword markers
        srp_markers = [
            "concomitant", "modalities", "as if", "never", "always",
            "peculiar", "strange", "unusual", "keynote", "characteristic",
            "pathognomonic",
        ]
        srp_score = sum(1 for m in srp_markers if m in joined)

        # Chronicity markers
        chronic_markers = [
            "chronic", "years", "long-standing", "constitutional", "since",
            "childhood", "hereditary", "family history", "slow onset",
        ]
        chronic_score = sum(1 for m in chronic_markers if m in joined)

        if count <= 3 and srp_score >= 2:
            method = "kent"
            rationale = (
                "Few symptoms with strong keynote / SRP character; "
                "Kent grade-sum scoring will emphasise the rare high-grade remedy."
            )
        elif count >= 6 and chronic_score >= 2:
            method = "boenninghausen"
            rationale = (
                "Many chronic symptoms; totality-of-symptoms (Boenninghausen) "
                "is more reliable when no single symptom dominates."
            )
        elif count <= 3:
            method = "kent"
            rationale = (
                "Small symptom set; high-grade individual rubrics carry more "
                "diagnostic weight than broad coverage."
            )
        else:
            method = "boenninghausen"
            rationale = (
                "Moderate-to-large symptom set without clear keynote dominance; "
                "recommend Boenninghausen for balanced totality coverage."
            )

        return {
            "recommended_method": method,
            "rationale": rationale,
            "symptom_count": count,
            "srp_score": srp_score,
            "chronic_score": chronic_score,
        }

    # ── Format converters ─────────────────────────────────────────────────────

    @staticmethod
    def convert_to_kent(rubric_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert a generic list of rubric-result dicts into the Kent
        grade-sum format (this is mainly a schema normaliser).

        Input items expected keys: ``abbrev``, ``score`` or ``grade_sum``,
        optionally ``matches``.
        """
        out: List[Dict[str, Any]] = []
        for r in rubric_results:
            item = {
                "abbrev": r.get("abbrev", r.get("remedy_abbrev", "?")),
                "score": r.get("score", r.get("grade_sum", 0)),
                "match_count": r.get("match_count", r.get("rubric_count", 0)),
                "matches": r.get("matches", []),
            }
            out.append(item)
        out.sort(key=lambda x: x["score"], reverse=True)
        return out

    @staticmethod
    def convert_to_boenninghausen(rubric_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert a generic list of rubric-result dicts into the
        Boenninghausen equal-weight format.

        Input items expected keys: ``abbrev``, ``rubric_count`` or ``score``,
        optionally ``matches``.
        """
        out: List[Dict[str, Any]] = []
        for r in rubric_results:
            # If the input already has a score, treat each rubric as 1 point
            raw_score = r.get("score", r.get("rubric_count", 0))
            # Normalise to rubric count if the score looks like a grade sum
            match_count = r.get("match_count", r.get("rubric_count", 0))
            item = {
                "abbrev": r.get("abbrev", r.get("remedy_abbrev", "?")),
                "score": match_count,
                "match_count": match_count,
                "matches": r.get("matches", []),
            }
            out.append(item)
        out.sort(key=lambda x: x["score"], reverse=True)
        return out

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _index_of(result_list: List[Dict[str, Any]], abbrev: str) -> int:
        """Return 1-based rank of a remedy in a result list, or 999 if absent."""
        for i, r in enumerate(result_list):
            if r["abbrev"] == abbrev:
                return i + 1
        return 999
