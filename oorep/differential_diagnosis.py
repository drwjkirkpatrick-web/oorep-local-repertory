"""
Differential Diagnosis Engine — Feature #19

Given a set of candidate remedies from repertorization, produce a differential
diagnosis table: shared rubrics (supports both), exclusive rubrics (differentiates),
keynotes present/absent, kingdom/family patterns, potency guidance, and a ranked
'differential score' based on discriminating power.

Usage:
    from oorep.differential_diagnosis import DifferentialDiagnosisEngine
    engine = DifferentialDiagnosisEngine()

    result = engine.compare_remedies("ARS", "PULS", rubric_ids=[1,2,3])
    diags = engine.differential_table(candidates=[...], top_n=5)
"""

import math
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class DifferentialDiagnosisEngine:
    """
    Multi-way differential diagnosis for homeopathic remedies.
    """

    def __init__(
        self,
        rubric_data: Optional[Dict[str, List[Dict]]] = None,
        materia_medica: Optional[Dict[str, List[str]]] = None,
        remedy_taxonomy: Optional[Dict[str, Any]] = None,
    ):
        self.rubric_data = rubric_data or {}
        self.mm_keynotes = materia_medica or {}
        self.taxonomy = remedy_taxonomy or {}

    # ── Core comparison ────────────────────────────────────────────────────

    def compare_remedies(
        self,
        remedy_a: str,
        remedy_b: str,
        rubric_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Detailed head-to-head comparison.
        Returns: {shared_rubrics, exclusive_a, exclusive_b, differential_score, keynotes}.
        """
        a = self._get_remedy_rubric_ids(remedy_a)
        b = self._get_remedy_rubric_ids(remedy_b)

        if rubric_ids:
            target = set(str(r) for r in rubric_ids)
            a = a & target
            b = b & target

        shared = sorted(list(a & b))
        exclusive_a = sorted(list(a - b))
        exclusive_b = sorted(list(b - a))

        # Differential score: more exclusive rubrics = stronger differentiation
        total = max(len(a), len(b), 1)
        differentiation = (len(exclusive_a) + len(exclusive_b)) / total
        base_score = differentiation * 10  # scale to useful range

        # Keynote comparison
        ka = self._get_keynotes(remedy_a)
        kb = self._get_keynotes(remedy_b)

        # Kingdom/family comparison
        tax_a = self.taxonomy.get(remedy_a.upper(), {})
        tax_b = self.taxonomy.get(remedy_b.upper(), {})
        same_kingdom = tax_a.get("kingdom", "") == tax_b.get("kingdom", "")

        return {
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "shared_rubrics": shared,
            "shared_count": len(shared),
            "exclusive_a": exclusive_a,
            "exclusive_a_count": len(exclusive_a),
            "exclusive_b": exclusive_b,
            "exclusive_b_count": len(exclusive_b),
            "differential_score": round(base_score, 3),
            "keynotes_a": ka,
            "keynotes_b": kb,
            "same_kingdom": same_kingdom,
            "potency_guidance" : {
                remedy_a: self._potency_hint(remedy_a),
                remedy_b: self._potency_hint(remedy_b),
            },
        }

    # ── Multi-way differential table ───────────────────────────────────────

    def differential_table(
        self,
        candidates: List[Dict[str, Any]],
        rubric_ids: Optional[List[int]] = None,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate full differential table for N candidates.
        Returns list of rows sorted by differential_score desc.
        """
        top = candidates[:top_n]
        rows = []
        for i, cand in enumerate(top):
            remedy = cand.get("remedy", cand.get("abbrev", ""))
            scores = []
            for j, other in enumerate(top):
                if i == j:
                    continue
                other_name = other.get("remedy", other.get("abbrev", ""))
                comp = self.compare_remedies(remedy, other_name, rubric_ids=rubric_ids)
                scores.append(comp["differential_score"])

            avg_diff = sum(scores) / max(len(scores), 1) if scores else 0.0
            rubric_count = len(self._get_remedy_rubric_ids(remedy) & (set(str(r) for r in rubric_ids) if rubric_ids else self._get_remedy_rubric_ids(remedy)))

            rows.append({
                "remedy": remedy,
                "repertorization_score": cand.get("score", 0.0),
                "avg_differential_score": round(avg_diff, 3),
                "distinctive_rubric_count": self._distinctive_rubric_count(remedy, top),
                "kingdom": (self.taxonomy.get(remedy.upper(), {}) or {}).get("kingdom", "Unknown"),
                "family": (self.taxonomy.get(remedy.upper(), {}) or {}).get("family", "Unknown"),
            })

        rows.sort(key=lambda x: x["avg_differential_score"], reverse=True)
        return rows

    def _distinctive_rubric_count(
        self,
        remedy: str,
        all_candidates: List[Dict[str, Any]],
    ) -> int:
        """Count rubrics unique to this remedy among candidates."""
        own = self._get_remedy_rubric_ids(remedy)
        others: Set[str] = set()
        for c in all_candidates:
            other = c.get("remedy", c.get("abbrev", ""))
            if other != remedy:
                others |= self._get_remedy_rubric_ids(other)
        return len(own - others)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_remedy_rubric_ids(self, remedy: str) -> Set[str]:
        """Find all rubric IDs containing this remedy."""
        result: Set[str] = set()
        rem_norm = remedy.upper().replace(".", "")
        for rid, remedies in self.rubric_data.items():
            if not isinstance(remedies, list):
                continue
            for r in remedies:
                abbrev = (r.get("remedy", "") if isinstance(r, dict) else str(r)).upper().replace(".", "")
                if abbrev == rem_norm:
                    result.add(str(rid))
        return result

    def _get_keynotes(self, remedy: str) -> List[str]:
        """Return keynotes for a remedy."""
        return self.mm_keynotes.get(remedy.upper(), self.mm_keynotes.get(remedy, []))

    def _potency_hint(self, remedy: str) -> str:
        """Simple potency guidance based on kingdom."""
        tax = self.taxonomy.get(remedy.upper(), {})
        kingdom = tax.get("kingdom", "").lower()
        if kingdom == "mineral":
            return "Higher potencies (200C-1M); chronic deep conditions."
        elif kingdom == "animal":
            return "Medium-high (30C-200C); intense symptoms."
        elif kingdom == "plant":
            return "Lower-medium (6C-30C); acute/chronic boundary."
        else:
            return "Start low (6C-30C), observe response."

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 19,
            "feature_name": "Differential Diagnosis Engine",
            "cold_start_capable": True,
            "version": "1.0",
        }
