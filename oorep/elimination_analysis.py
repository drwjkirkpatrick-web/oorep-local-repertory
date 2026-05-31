"""
Elimination Analysis

Given target remedy and repertorization rubric results, determine which rubrics
the remedy does NOT cover (eliminators) or where coverage is weak (grade 1
excluders). This helps practitioners justify why a remedy is not the simillimum.

Usage:
    from oorep.elimination_analysis import EliminationAnalyzer
    ea = EliminationAnalyzer()
    eliminators = ea.find_eliminators(rubric_results, target_remedy="Kali-c.")
    report = ea.generate_elimination_report(rubric_results, remedy="Kali-c.")
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class EliminationAnalyzer:
    """
    Analyze repertorization results to support remedy elimination reasoning.

    The analyzer looks at which rubrics in the case are *not* represented by
    the target remedy, and which rubrics have only grade-1 coverage (partial
    or weak association).
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None, db_path: Optional[str] = None):
        self.rep = repertory or HomeopathicRepertory()
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _abbrev_match(self, abbrev_a: str, abbrev_b: str) -> bool:
        """Case-insensitive abbreviation comparison, stripping trailing dots."""
        a = abbrev_a.strip().lower().rstrip(".")
        b = abbrev_b.strip().lower().rstrip(".")
        return a == b

    def _rubric_weight_for_remedy(self, rubric_id: int, target_abbrev: str) -> Optional[int]:
        """
        Return the remedy weight (grade) for a target remedy in a rubric,
        or None if absent.
        """
        remedies = self.rep.get_remedies_for_rubric(rubric_id)
        for rem in remedies:
            if self._abbrev_match(rem.get("abbrev", ""), target_abbrev):
                return rem.get("weight", 1)
        return None

    def _gather_case_rubric_ids(self, rubric_results: List[Dict]) -> set:
        """Collect all unique rubric IDs from repertorization results."""
        ids = set()
        for entry in rubric_results:
            for match in entry.get("matches", []):
                rid = match.get("rubric_id")
                if rid is not None:
                    ids.add(rid)
        return ids

    # ── Public API ───────────────────────────────────────────────────────────

    def find_eliminators(self, rubric_results: List[Dict], target_remedy: str) -> List[Dict]:
        """
        Find which rubrics from the case the target remedy does NOT cover at all.

        Args:
            rubric_results: Output from HomeopathicRepertory.repertorize().
            target_remedy: Remedy abbreviation (e.g. "Kali-c.").

        Returns:
            List of dicts with rubric_id, rubric_fullpath, source,
            matched_symptom, and coverage rationale.
        """
        case_rubric_ids = self._gather_case_rubric_ids(rubric_results)
        eliminators = []
        for rid in case_rubric_ids:
            weight = self._rubric_weight_for_remedy(rid, target_remedy)
            if weight is not None:
                continue
            rubric = self.rep.get_rubric_by_id(rid)
            # Retrieve the symptom text from the first match that includes this rubric
            symptom_text = ""
            for entry in rubric_results:
                for match in entry.get("matches", []):
                    if match.get("rubric_id") == rid:
                        symptom_text = match.get("query_symptom", "")
                        break
                if symptom_text:
                    break
            eliminators.append({
                "rubric_id": rid,
                "rubric_fullpath": rubric.get("fullpath") if rubric else "?",
                "source": rubric.get("source") if rubric else "?",
                "matched_symptom": symptom_text,
                "rationale": f"{target_remedy} does not appear in this rubric.",
            })
        return eliminators

    def find_excluders(self, rubric_results: List[Dict], target_remedy: str) -> List[Dict]:
        """
        Find rubrics where the target remedy is present but only with
        grade 1 (weak/partial coverage).

        In classical homeopathy, grade-1 presence in a heavy symptom rubric
        may indicate only partial fit — useful for differential reasoning.

        Args:
            rubric_results: Output from HomeopathicRepertory.repertorize().
            target_remedy: Remedy abbreviation.

        Returns:
            List of dicts with rubric_id, rubric_fullpath, weight,
            top_grade_in_rubric, and rationale.
        """
        case_rubric_ids = self._gather_case_rubric_ids(rubric_results)
        excluders = []
        for rid in case_rubric_ids:
            weight = self._rubric_weight_for_remedy(rid, target_remedy)
            if weight is None or weight > 1:
                continue
            rubric = self.rep.get_rubric_by_id(rid)
            # Find the maximum grade for *any* remedy in this rubric
            remedies = self.rep.get_remedies_for_rubric(rid)
            top_grade = max((r.get("weight", 1) for r in remedies), default=1)
            symptom_text = ""
            for entry in rubric_results:
                for match in entry.get("matches", []):
                    if match.get("rubric_id") == rid:
                        symptom_text = match.get("query_symptom", "")
                        break
                if symptom_text:
                    break
            excluders.append({
                "rubric_id": rid,
                "rubric_fullpath": rubric.get("fullpath") if rubric else "?",
                "source": rubric.get("source") if rubric else "?",
                "matched_symptom": symptom_text,
                "target_weight": weight,
                "top_grade_in_rubric": top_grade,
                "rationale": (
                    f"{target_remedy} has only grade {weight} in this rubric "
                    f"(top grade = {top_grade}), suggesting weak coverage."
                ),
            })
        return excluders

    def generate_elimination_report(self, rubric_results: List[Dict], remedy: str) -> Dict:
        """
        Generate a structured elimination report for a target remedy.

        Args:
            rubric_results: Output from HomeopathicRepertory.repertorize().
            remedy: Target remedy abbreviation.

        Returns:
            Dict with keys:
                remedy: str
                total_case_rubrics: int
                present_rubrics: int
                missing_rubrics: int
                weak_coverage_rubrics: int
                eliminators: list
                excluders: list
                summary: str
        """
        case_rubric_ids = self._gather_case_rubric_ids(rubric_results)
        total = len(case_rubric_ids)
        eliminators = self.find_eliminators(rubric_results, remedy)
        excluders = self.find_excluders(rubric_results, remedy)
        present = total - len(eliminators)
        weak = len(excluders)
        summary = (
            f"{remedy} covers {present}/{total} case rubrics. "
            f"Missing: {len(eliminators)}; weak (grade 1): {weak}."
        )
        return {
            "remedy": remedy,
            "total_case_rubrics": total,
            "present_rubrics": present,
            "missing_rubrics": len(eliminators),
            "weak_coverage_rubrics": weak,
            "eliminators": eliminators,
            "excluders": excluders,
            "summary": summary,
        }

    def rank_remedies_by_coverage(self, rubric_results: List[Dict], candidate_abbrevs: List[str]) -> List[Dict]:
        """
        Rank candidate remedies by coverage depth (fewest eliminators, most strong grades).

        Convenience for comparing multiple candidates quickly.
        """
        ranked = []
        for abbrev in candidate_abbrevs:
            report = self.generate_elimination_report(rubric_results, abbrev)
            # Score: present rubrics + (strong rubrics count implicitly via weak)
            # Lower missing + weak = better candidate
            score = report["present_rubrics"] - report["weak_coverage_rubrics"]
            ranked.append({
                "remedy": abbrev,
                "score": score,
                **report,
            })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
