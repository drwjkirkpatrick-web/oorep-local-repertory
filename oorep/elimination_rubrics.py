"""
Elimination Rubrics Logic — Feature #18

Structured elimination rubric engine.
Define rubrics that EXCLUDE remedies.
Support AND/OR/NOT logic for elimination criteria.
Integration with repertorization to produce 'ruled out' and 'ruled in' lists.

Usage:
    from oorep.elimination_rubrics import EliminationEngine
    engine = EliminationEngine(repertory_data)

    engine.add_elimination_rubric(
        symptom="thirst absent",
        exclude_rubric_key="thirst large quantities",
        exclude_remedies=["ARS", "PHOS"],
    )

    result = engine.apply_elimination(candidate_remedies, symptoms=["thirst absent"])
    # result = {"ruled_in": [...], "ruled_out": [...]}
"""

import re
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class EliminationEngine:
    """
    Elimination logic for homeopathic remedy selection.
    """

    def __init__(self, repertory_data: Optional[Dict[str, Any]] = None):
        self.repertory = repertory_data or {}
        self.elimination_rules: List[Dict[str, Any]] = []

    # ── Rule definition ───────────────────────────────────────────────────────

    def add_elimination_rubric(
        self,
        symptom: str,
        exclude_rubric_key: Optional[str] = None,
        exclude_remedies: Optional[List[str]] = None,
        exclude_kingdoms: Optional[List[str]] = None,
        exclude_families: Optional[List[str]] = None,
        logic: str = "and",
        weight: float = 1.0,
    ) -> None:
        """Register an elimination criterion."""
        self.elimination_rules.append({
            "symptom": symptom.lower(),
            "exclude_rubric_key": exclude_rubric_key.lower() if exclude_rubric_key else None,
            "exclude_remedies": set(r.upper().replace(".", "") for r in (exclude_remedies or [])),
            "exclude_kingdoms": set(k.lower() for k in (exclude_kingdoms or [])),
            "exclude_families": set(f.lower() for f in (exclude_families or [])),
            "logic": logic.lower(),
            "weight": weight,
        })

    def clear_rules(self) -> None:
        self.elimination_rules = []

    def list_rules(self) -> List[Dict[str, Any]]:
        return self.elimination_rules

    # ── Apply elimination ─────────────────────────────────────────────────────

    def apply_elimination(
        self,
        candidate_remedies: List[Dict[str, Any]],
        symptoms: List[str],
        taxonomy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Apply all elimination rules to candidate remedies.
        Returns: {ruled_in: [...], ruled_out: [...], elimination_reasons: {...}}.
        """
        ruled_in: List[Dict[str, Any]] = []
        ruled_out: List[Dict[str, Any]] = []
        reasons: Dict[str, List[str]] = defaultdict(list)

        for cand in candidate_remedies:
            remedy = (cand.get("remedy") or cand.get("abbrev", "")).upper().replace(".", "")
            if not remedy:
                continue

            eliminated = False
            for rule in self.elimination_rules:
                match = self._rule_matches(rule, symptoms, remedy, taxonomy)
                if match:
                    eliminated = True
                    reasons[remedy].append(
                        f"'{rule['symptom']}' -> excludes { ', '.join(sorted(rule['exclude_remedies'])) }"
                    )
                    break  # One elimination is enough

            if eliminated:
                ruled_out.append(cand)
            else:
                ruled_in.append(cand)

        return {
            "ruled_in": ruled_in,
            "ruled_out": ruled_out,
            "elimination_reasons": dict(reasons),
            "total_candidates": len(candidate_remedies),
            "ruled_out_count": len(ruled_out),
            "ruled_in_count": len(ruled_in),
        }

    def _rule_matches(
        self,
        rule: Dict[str, Any],
        symptoms: List[str],
        remedy: str,
        taxonomy: Optional[Dict],
    ) -> bool:
        """Check if a remedy matches an elimination condition."""
        symptom_match = rule["symptom"] in (s.lower() for s in symptoms)

        # Eliminate if symptom present AND remedy is in excluded set
        if not symptom_match:
            return False

        # Check remedy direct exclusion
        if remedy in rule["exclude_remedies"]:
            return True

        # Check taxonomy exclusions
        if taxonomy:
            tax = taxonomy.get(remedy, {})
            kingdom = (tax.get("kingdom", "") or "").lower()
            family = (tax.get("family", "") or "").lower()
            if kingdom in rule["exclude_kingdoms"] or family in rule["exclude_families"]:
                return True

        # Check repertory lookup by key
        if rule["exclude_rubric_key"] and self.repertory:
            for rubric_text, rems in self.repertory.items():
                if rule["exclude_rubric_key"] in rubric_text.lower():
                    if remedy in set(r.upper().replace(".", "") for r in (rems if isinstance(rems, list) else [])):
                        return True

        return False

    # ── Simpler API: eliminate by symptom list ────────────────────────────────

    def eliminate_by_symptoms(
        self,
        candidate_remedies: List[Dict[str, Any]],
        symptoms: List[str],
        taxonomy: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Shortcut: return only ruled-in remedies."""
        result = self.apply_elimination(candidate_remedies, symptoms, taxonomy)
        return result["ruled_in"]

    def explain_eliminations(self, elimination_result: Dict[str, Any]) -> List[str]:
        """Human-readable explanation."""
        lines = []
        for r in elimination_result.get("ruled_out", []):
            remedy = r.get("remedy", r.get("abbrev", "?"))
            reasons = elimination_result.get("elimination_reasons", {}).get(remedy.upper().replace(".", ""), [])
            if reasons:
                lines.append(f"{remedy}: eliminated because {reasons[0]}")
            else:
                lines.append(f"{remedy}: eliminated (unspecified reason)")
        return lines

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 18,
            "feature_name": "Elimination Rubrics UI Logic",
            "rule_types": ["remedy_exclusion", "kingdom_exclusion", "family_exclusion", "rubric_key_exclusion"],
            "cold_start_capable": True,
            "version": "1.0",
        }
