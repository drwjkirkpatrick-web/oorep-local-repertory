"""
Pluggable Analysis Methods — Feature #13

Formalize Vithoulkas Expert System (VES), Kent, Boenninghausen, and Boger as
pluggable analysis method plugins. Create AnalysisMethod base class with
method-specific scoring, weighting, and remedy ranking. Allow runtime switching
between methods. Integrate with master_score_engine.py.

Usage:
    from oorep.analysis_methods import (
        AnalysisMethod, KentMethod, BoenninghausenMethod,
        BogerMethod, VithoulkasExpertSystem,
        MethodRegistry, MethodSwitcher, AnalysisMethods,
    )

    registry = MethodRegistry()
    registry.register(KentMethod())
    registry.register(BoenninghausenMethod())

    switcher = MethodSwitcher(registry)
    comparison = switcher.compare(results, rubric_ids)
"""

from typing import Any, Dict, List, Optional

# Local imports with fallback patterns
try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory  # type: ignore[import-not-found]

try:
    from .kent_vs_boenninghausen import KentVsBoenninghausen
except Exception:
    from kent_vs_boenninghausen import KentVsBoenninghausen  # type: ignore[import-not-found]

try:
    from .master_score_engine import MasterScoreEngine
except Exception:
    from master_score_engine import MasterScoreEngine  # type: ignore[import-not-found]


class AnalysisMethod:
    """
    Abstract-ish base class for pluggable analysis methods.
    """

    def __init__(self) -> None:
        self._params: Dict[str, Any] = {}

    def configure(self, params: Dict[str, Any]) -> None:
        """
        Configure method-specific parameters at runtime.

        Args:
            params: Dictionary of parameter names to values.
        """
        self._params.update(params)

    def score_repertorization(
        self, results: List[Dict[str, Any]], rubric_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank a repertorization result list using this method's philosophy.

        Args:
            results: Repertorization results, each dict at minimum having
                ``abbrev`` and optionally ``matches`` with ``weight``,
                ``rubric_id``, and ``rubric``.
            rubric_ids: The selected rubric IDs used in the repertorization.

        Returns:
            Re-ranked remedy list sorted by this method's score, descending.
            Each item is a copy of the input item with added
            ``method_score`` and ``method_name`` keys.
        """
        raise NotImplementedError("Subclasses must implement score_repertorization")

    def explain(self, remedy: str) -> str:
        """
        Return a human-readable rationale for why a remedy was ranked.

        Args:
            remedy: Remedy abbreviation.

        Returns:
            Explanation string.
        """
        raise NotImplementedError("Subclasses must implement explain")

    def get_name(self) -> str:
        """
        Return the registered name of this analysis method.

        Returns:
            Method name string.
        """
        raise NotImplementedError("Subclasses must implement get_name")


# ── Kent method ──────────────────────────────────────────────────────────────


class KentMethod(AnalysisMethod):
    """
    Classical Kent grade-sum scoring.

    Each remedy's total is the sum of its grades across selected rubrics.
    Grades are valued as 1, 2, 3 (and optionally 4). All rubrics are weighted
    equally at the rubric level; grade differences drive the ranking.
    """

    def __init__(self) -> None:
        super().__init__()
        self._grade_map: Dict[int, int] = {1: 1, 2: 2, 3: 3, 4: 4}

    def configure(self, params: Dict[str, Any]) -> None:
        super().configure(params)
        if "grade_map" in params:
            self._grade_map = dict(params["grade_map"])

    def score_repertorization(
        self, results: List[Dict[str, Any]], rubric_ids: List[int]
    ) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for item in results:
            matches = item.get("matches", [])
            total = 0
            for m in matches:
                weight = int(m.get("weight", 1))
                total += self._grade_map.get(weight, weight)
            new_item: Dict[str, Any] = dict(item)
            new_item["method_score"] = float(total)
            new_item["method_name"] = self.get_name()
            scored.append(new_item)
        scored.sort(key=lambda x: x["method_score"], reverse=True)
        return scored

    def explain(self, remedy: str) -> str:
        return (
            f"KentMethod ranks {remedy} by classical grade-sum: each rubric's "
            f"grade (1–3) is added directly. Higher individual grades pull the "
            f"remedy upward strongly."
        )

    def get_name(self) -> str:
        return "kent"


# ── Boenninghausen method ─────────────────────────────────────────────────────


class BoenninghausenMethod(AnalysisMethod):
    """
    Boenninghausen totality-of-symptoms method.

    Each selected rubric carries equal weight (1 point per rubric).
    Remedies covering more rubrics rank higher regardless of grade.
    Cross-sector coverage is emphasized: appearing in many different
    anatomical / functional sectors yields a bonus.
    """

    # Default sector weights — can be overridden via configure()
    DEFAULT_SECTOR_WEIGHTS: Dict[str, float] = {
        "mind": 1.0,
        "head": 1.0,
        "eye": 1.0,
        "ears": 1.0,
        "nose": 1.0,
        "face": 1.0,
        "mouth": 1.0,
        "throat": 1.0,
        "stomach": 1.0,
        "abdomen": 1.0,
        "rectum": 1.0,
        "bladder": 1.0,
        "urinary": 1.0,
        "male": 1.0,
        "female": 1.0,
        "respiration": 1.0,
        "chest": 1.0,
        "back": 1.0,
        "extremities": 1.0,
        "sleep": 1.0,
        "dreams": 1.0,
        "chill": 1.0,
        "fever": 1.0,
        "perspiration": 1.0,
        "skin": 1.0,
        "generals": 1.0,
    }

    def __init__(self) -> None:
        super().__init__()
        self._sector_weights: Dict[str, float] = dict(self.DEFAULT_SECTOR_WEIGHTS)
        self._cross_sector_bonus: float = 2.0

    def configure(self, params: Dict[str, Any]) -> None:
        super().configure(params)
        if "sector_weights" in params:
            self._sector_weights = dict(params["sector_weights"])
        if "cross_sector_bonus" in params:
            self._cross_sector_bonus = float(params["cross_sector_bonus"])

    @staticmethod
    def _extract_sector(rubric_path: Optional[str]) -> str:
        """
        Derive a sector name from a rubric full path.

        Returns:
            Lower-case sector keyword.
        """
        if not rubric_path:
            return "unknown"
        parts = [p.strip().lower() for p in rubric_path.split(";")]
        if not parts:
            return "unknown"
        first = parts[0]
        synonyms: Dict[str, str] = {
            "eyes": "eye",
            "ears": "ear",
            "nose & smell": "nose",
            "face & jaw": "face",
            "teeth": "mouth",
            "tongue": "mouth",
            "stomach & digestion": "stomach",
            "liver & gallbladder": "abdomen",
            "kidneys": "urinary",
            "urinary organs": "urinary",
            "male genitalia": "male",
            "female genitalia": "female",
            "respiratory system": "respiration",
            "chest & lungs": "chest",
            "back & spine": "back",
            "limbs": "extremities",
            "sleep & dreams": "sleep",
            "perspiration & sweat": "perspiration",
            "generalities": "generals",
        }
        return synonyms.get(first, first)

    def score_repertorization(
        self, results: List[Dict[str, Any]], rubric_ids: List[int]
    ) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for item in results:
            matches = item.get("matches", [])
            unique_rubric_ids: set = set()
            sectors_seen: set = set()
            base_score = 0.0
            for m in matches:
                rid = m.get("rubric_id")
                if rid is not None and rid not in unique_rubric_ids:
                    unique_rubric_ids.add(rid)
                    rubric_path = m.get("rubric")
                    sector = self._extract_sector(rubric_path)
                    sectors_seen.add(sector)
                    sector_w = self._sector_weights.get(sector, 1.0)
                    base_score += 1.0 * sector_w

            sector_count = len(sectors_seen)
            bonus = self._cross_sector_bonus * max(0, sector_count - 1)
            total = base_score + bonus

            new_item: Dict[str, Any] = dict(item)
            new_item["method_score"] = float(total)
            new_item["method_name"] = self.get_name()
            new_item["sector_count"] = sector_count
            new_item["sectors"] = sorted(sectors_seen)
            scored.append(new_item)
        scored.sort(key=lambda x: x["method_score"], reverse=True)
        return scored

    def explain(self, remedy: str) -> str:
        return (
            f"BoenninghausenMethod ranks {remedy} by totality-of-symptoms: "
            f"each rubric contributes equally regardless of grade. "
            f"Cross-sector coverage adds a bonus for broad polychrest action."
        )

    def get_name(self) -> str:
        return "boenninghausen"


# ── Boger method ─────────────────────────────────────────────────────────────


class BogerMethod(AnalysisMethod):
    """
    Boger keynote-emphasis method.

    Gives higher weight to grade-3 rubrics that are keynotes for the remedy.
    Keynotes are configured via ``keynote_rubric_ids`` and
    ``keynote_remedy_boost``.
    """

    def __init__(self) -> None:
        super().__init__()
        self._keynote_rubric_ids: set = set()
        self._keynote_remedy_boost: Dict[str, float] = {}
        self._grade3_multiplier: float = 2.0
        self._grade2_multiplier: float = 1.0
        self._grade1_multiplier: float = 0.5

    def configure(self, params: Dict[str, Any]) -> None:
        super().configure(params)
        if "keynote_rubric_ids" in params:
            self._keynote_rubric_ids = set(params["keynote_rubric_ids"])
        if "keynote_remedy_boost" in params:
            self._keynote_remedy_boost = dict(params["keynote_remedy_boost"])
        for key in ("grade3_multiplier", "grade2_multiplier", "grade1_multiplier"):
            if key in params:
                setattr(self, f"_{key}", float(params[key]))

    def score_repertorization(
        self, results: List[Dict[str, Any]], rubric_ids: List[int]
    ) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for item in results:
            abbrev = item.get("abbrev", "")
            matches = item.get("matches", [])
            total = 0.0
            keynote_hits = 0
            for m in matches:
                weight = int(m.get("weight", 1))
                if weight >= 3:
                    mult = self._grade3_multiplier
                elif weight == 2:
                    mult = self._grade2_multiplier
                else:
                    mult = self._grade1_multiplier

                rid = m.get("rubric_id")
                if rid is not None and rid in self._keynote_rubric_ids:
                    mult = mult * 1.5
                    keynote_hits += 1

                rem_boost = self._keynote_remedy_boost.get(abbrev, 1.0)
                total += weight * mult * rem_boost

            new_item: Dict[str, Any] = dict(item)
            new_item["method_score"] = float(total)
            new_item["method_name"] = self.get_name()
            new_item["keynote_hits"] = keynote_hits
            scored.append(new_item)
        scored.sort(key=lambda x: x["method_score"], reverse=True)
        return scored

    def explain(self, remedy: str) -> str:
        return (
            f"BogerMethod ranks {remedy} by keynote emphasis: grade-3 rubrics "
            f"are multiplied and keynotes receive an extra boost. This surfaces "
            f"remedies with strong characteristic symptoms."
        )

    def get_name(self) -> str:
        return "boger"


# ── Vithoulkas Expert System (VES) ───────────────────────────────────────────


class VithoulkasExpertSystem(AnalysisMethod):
    """
    Vithoulkas Expert System (VES).

    Balances totality (number of rubrics covered) with intensity
    (highest grade present). Uses a ``level_of_health`` concept:
    remedies whose "energy level" aligns with the patient's configured
    level of health receive an additional weight.
    """

    # Default level-of-health mapping (simplified 1–12 scale)
    DEFAULT_LEVEL_WEIGHTS: Dict[int, float] = {
        1: 1.0,
        2: 1.0,
        3: 1.0,
        4: 1.0,
        5: 1.1,
        6: 1.1,
        7: 1.1,
        8: 1.1,
        9: 1.2,
        10: 1.2,
        11: 1.2,
        12: 1.2,
    }

    def __init__(self) -> None:
        super().__init__()
        self._totality_weight: float = 1.0
        self._intensity_weight: float = 1.0
        self._level_of_health: int = 6
        self._level_weights: Dict[int, float] = dict(self.DEFAULT_LEVEL_WEIGHTS)
        self._remedy_level_map: Dict[str, int] = {}

    def configure(self, params: Dict[str, Any]) -> None:
        super().configure(params)
        if "totality_weight" in params:
            self._totality_weight = float(params["totality_weight"])
        if "intensity_weight" in params:
            self._intensity_weight = float(params["intensity_weight"])
        if "level_of_health" in params:
            self._level_of_health = int(params["level_of_health"])
        if "level_weights" in params:
            self._level_weights = dict(params["level_weights"])
        if "remedy_level_map" in params:
            self._remedy_level_map = dict(params["remedy_level_map"])

    def score_repertorization(
        self, results: List[Dict[str, Any]], rubric_ids: List[int]
    ) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for item in results:
            abbrev = item.get("abbrev", "")
            matches = item.get("matches", [])
            unique_rids: set = set()
            max_grade = 0
            for m in matches:
                rid = m.get("rubric_id")
                if rid is not None:
                    unique_rids.add(rid)
                weight = int(m.get("weight", 1))
                if weight > max_grade:
                    max_grade = weight

            totality = len(unique_rids)
            intensity = max_grade
            composite = (
                self._totality_weight * totality
                + self._intensity_weight * intensity
            )

            level = self._remedy_level_map.get(abbrev, self._level_of_health)
            lw = self._level_weights.get(level, 1.0)
            patient_level = self._level_of_health
            level_diff = abs(level - patient_level)
            if level_diff == 0:
                alignment_bonus = 0.5
            elif level_diff <= 2:
                alignment_bonus = 0.25
            elif level_diff <= 4:
                alignment_bonus = 0.1
            else:
                alignment_bonus = 0.0

            total = composite * lw + alignment_bonus

            new_item: Dict[str, Any] = dict(item)
            new_item["method_score"] = float(total)
            new_item["method_name"] = self.get_name()
            new_item["ves_totality"] = totality
            new_item["ves_intensity"] = intensity
            new_item["ves_level"] = level
            scored.append(new_item)
        scored.sort(key=lambda x: x["method_score"], reverse=True)
        return scored

    def explain(self, remedy: str) -> str:
        return (
            f"VithoulkasExpertSystem balances totality and intensity for "
            f"{remedy}, then adjusts for the patient's level of health. "
            f"Remedies aligned with the patient's vitality state score higher."
        )

    def get_name(self) -> str:
        return "vithoulkas"


# ── Method Registry ──────────────────────────────────────────────────────────


class MethodRegistry:
    """
    Registry for pluggable analysis methods.
    """

    def __init__(self) -> None:
        self._methods: Dict[str, AnalysisMethod] = {}

    def register(self, method: AnalysisMethod) -> None:
        """
        Register an analysis method instance by its ``get_name()``.
        """
        name = method.get_name()
        self._methods[name] = method

    def get_method(self, name: str) -> Optional[AnalysisMethod]:
        """
        Retrieve a registered method by name.

        Returns:
            The method instance, or ``None`` if not found.
        """
        return self._methods.get(name)

    def list_methods(self) -> List[Dict[str, Any]]:
        """
        List all registered methods with metadata.

        Returns:
            List of dicts with keys ``name``, ``description``,
            and ``default_weight``.
        """
        out: List[Dict[str, Any]] = []
        for name, method in self._methods.items():
            desc = method.explain("")
            weight = 1.0
            if isinstance(method, KentMethod):
                weight = 0.30
            elif isinstance(method, BoenninghausenMethod):
                weight = 0.20
            elif isinstance(method, BogerMethod):
                weight = 0.15
            elif isinstance(method, VithoulkasExpertSystem):
                weight = 0.35
            out.append({
                "name": name,
                "description": desc,
                "default_weight": weight,
            })
        out.sort(key=lambda x: x["name"])
        return out


# ── Method Switcher ───────────────────────────────────────────────────────────


class MethodSwitcher:
    """
    Runs a repertorization through multiple methods and returns a
    side-by-side comparison.
    """

    def __init__(self, registry: Optional[MethodRegistry] = None) -> None:
        self._registry = registry or MethodRegistry()

    @property
    def registry(self) -> MethodRegistry:
        return self._registry

    def compare(
        self,
        results: List[Dict[str, Any]],
        rubric_ids: List[int],
        methods: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run the same repertorization results through multiple analysis
        methods and return a side-by-side comparison.

        Args:
            results: Base repertorization results (e.g. from Kent scoring).
            rubric_ids: Selected rubric IDs.
            methods: List of method names to compare. If None, uses all
                registered methods.

        Returns:
            Dict with keys:
                ``method_results`` – {method_name: [ranked results]},
                ``side_by_side`` – list of {abbrev, scores: {method: score}},
                ``top_common`` – remedies in top-5 of every method,
                ``summary`` – human-readable narrative.
        """
        if methods is None:
            methods = sorted(self._registry._methods.keys())
            if not methods:
                raise ValueError("No methods registered in registry")

        method_results: Dict[str, List[Dict[str, Any]]] = {}
        for name in methods:
            method = self._registry.get_method(name)
            if method is None:
                raise ValueError(f"Unknown method: {name}")
            ranked = method.score_repertorization(results, rubric_ids)
            method_results[name] = ranked

        all_abbrevs: set = set()
        for ranked in method_results.values():
            all_abbrevs.update(r.get("abbrev", "") for r in ranked)

        side_by_side: List[Dict[str, Any]] = []
        for abbrev in sorted(all_abbrevs):
            scores: Dict[str, Any] = {}
            ranks: Dict[str, int] = {}
            for name, ranked in method_results.items():
                score = 0.0
                rank = 999
                for i, r in enumerate(ranked):
                    if r.get("abbrev") == abbrev:
                        score = r.get("method_score", 0.0)
                        rank = i + 1
                        break
                scores[name] = score
                ranks[name] = rank
            side_by_side.append({
                "abbrev": abbrev,
                "scores": scores,
                "ranks": ranks,
            })

        top_sets: List[set] = []
        for _, ranked in method_results.items():
            top_sets.append({r.get("abbrev", "") for r in ranked[:5]})
        common = set.intersection(*top_sets) if top_sets else set()

        parts: List[str] = []
        for name, ranked in method_results.items():
            if ranked:
                top = ranked[0].get("abbrev", "")
                parts.append(f"{name} top: {top}")
        summary = "; ".join(parts) if parts else "No results to compare."

        return {
            "method_results": method_results,
            "side_by_side": side_by_side,
            "top_common": sorted(common),
            "summary": summary,
        }


# ── Backward-compatible convenience class ─────────────────────────────────────


class AnalysisMethods:
    """
    Convenience wrapper exposing the pluggable analysis method engine.
    Backward-compatible with the original Feature #13 stub API.
    """

    def __init__(self, repertory: Optional[Any] = None) -> None:
        self.rep = repertory
        self._registry = MethodRegistry()
        self._switcher = MethodSwitcher(self._registry)
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._registry.register(KentMethod())
        self._registry.register(BoenninghausenMethod())
        self._registry.register(BogerMethod())
        self._registry.register(VithoulkasExpertSystem())

    def process(
        self,
        results: Optional[List[Dict[str, Any]]] = None,
        rubric_ids: Optional[List[int]] = None,
        method: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Main entry point. Backward-compatible with Feature #13 stub.

        Args:
            results: Repertorization results to analyse.
            rubric_ids: Selected rubric IDs.
            method: If given, run only this method; otherwise run comparison.
            **kwargs: Passed through to configure() if a method is specified.

        Returns:
            Result dict.
        """
        if results is None:
            return {
                "status": "ready",
                "feature_id": 13,
                "feature_name": "Pluggable Analysis Methods",
                "available_methods": self._registry.list_methods(),
            }

        rubric_ids = rubric_ids or []
        if method:
            m = self._registry.get_method(method)
            if m is None:
                return {
                    "status": "error",
                    "message": f"Unknown method: {method}",
                }
            if kwargs:
                m.configure(kwargs)
            ranked = m.score_repertorization(results, rubric_ids)
            return {
                "status": "ok",
                "method": method,
                "results": ranked,
            }
        else:
            comparison = self._switcher.compare(results, rubric_ids)
            return {
                "status": "ok",
                "comparison": comparison,
            }
