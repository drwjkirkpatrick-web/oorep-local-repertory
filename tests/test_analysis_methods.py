"""
Tests for Pluggable Analysis Methods (Feature #13)
"""

import pytest
from typing import Any, Dict, List

from oorep.analysis_methods import (
    AnalysisMethod,
    AnalysisMethods,
    KentMethod,
    BoenninghausenMethod,
    BogerMethod,
    VithoulkasExpertSystem,
    MethodRegistry,
    MethodSwitcher,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_results() -> List[Dict[str, Any]]:
    """Standard repertorization results for four remedies across three rubrics."""
    return [
        {
            "abbrev": "Puls.",
            "matches": [
                {"rubric_id": 1, "rubric": "Mind; weeping", "weight": 3},
                {"rubric_id": 2, "rubric": "Head; pain", "weight": 2},
                {"rubric_id": 3, "rubric": "Stomach; nausea", "weight": 1},
            ],
        },
        {
            "abbrev": "Nux-v.",
            "matches": [
                {"rubric_id": 1, "rubric": "Mind; weeping", "weight": 2},
                {"rubric_id": 2, "rubric": "Head; pain", "weight": 3},
                {"rubric_id": 3, "rubric": "Stomach; nausea", "weight": 3},
            ],
        },
        {
            "abbrev": "Sulph.",
            "matches": [
                {"rubric_id": 1, "rubric": "Mind; weeping", "weight": 1},
                {"rubric_id": 2, "rubric": "Head; pain", "weight": 1},
                {"rubric_id": 3, "rubric": "Stomach; nausea", "weight": 1},
            ],
        },
        {
            "abbrev": "Lyc.",
            "matches": [
                {"rubric_id": 2, "rubric": "Head; pain", "weight": 3},
                {"rubric_id": 3, "rubric": "Stomach; nausea", "weight": 2},
            ],
        },
    ]


@pytest.fixture
def single_result() -> List[Dict[str, Any]]:
    return [
        {
            "abbrev": "Ars.",
            "matches": [
                {"rubric_id": 5, "rubric": "Generals; anxiety", "weight": 3},
            ],
        }
    ]


# ── Base class interface ─────────────────────────────────────────────────────

class TestAnalysisMethodInterface:

    def test_base_configure(self):
        class Dummy(AnalysisMethod):
            def score_repertorization(self, results, rubric_ids):
                return []
            def explain(self, remedy):
                return "dummy"
            def get_name(self):
                return "dummy"
        d = Dummy()
        d.configure({"foo": 1})
        assert d._params == {"foo": 1}

    def test_base_explain_not_implemented(self):
        # AnalysisMethod is abstract-ish but not formally abstract,
        # so instantiation is allowed in Python.
        obj = AnalysisMethod()
        with pytest.raises(NotImplementedError):
            obj.explain("")

    def test_base_score_repertorization_not_implemented(self):
        class Partial(AnalysisMethod):
            def explain(self, remedy):
                return "partial"
            def get_name(self):
                return "partial"
        p = Partial()
        with pytest.raises(NotImplementedError):
            p.score_repertorization([], [])

    def test_base_explain_not_implemented_directly(self):
        class Partial(AnalysisMethod):
            def score_repertorization(self, results, rubric_ids):
                return []
            def get_name(self):
                return "partial"
        p = Partial()
        with pytest.raises(NotImplementedError):
            p.explain("Ars.")

    def test_base_get_name_not_implemented_directly(self):
        class Partial(AnalysisMethod):
            def score_repertorization(self, results, rubric_ids):
                return []
            def explain(self, remedy):
                return "partial"
        p = Partial()
        with pytest.raises(NotImplementedError):
            p.get_name()


# ── KentMethod ───────────────────────────────────────────────────────────────

class TestKentMethod:

    def test_name(self):
        m = KentMethod()
        assert m.get_name() == "kent"

    def test_explain(self):
        m = KentMethod()
        e = m.explain("Puls.")
        assert "KentMethod" in e
        assert "Puls." in e

    def test_kent_scoring_hand_calculated(self, sample_results):
        m = KentMethod()
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Puls = 3+2+1 = 6
        # Nux-v = 2+3+3 = 8
        # Sulph = 1+1+1 = 3
        # Lyc = 3+2 = 5
        assert scores["Nux-v."] == 8.0
        assert scores["Puls."] == 6.0
        assert scores["Lyc."] == 5.0
        assert scores["Sulph."] == 3.0
        assert ranked[0]["abbrev"] == "Nux-v."

    def test_kent_configure_grade_map(self, sample_results):
        m = KentMethod()
        m.configure({"grade_map": {1: 1, 2: 4, 3: 9}})
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Puls = 9+4+1=14, Nux-v = 4+9+9=22, Sulph=3, Lyc=9+4=13
        assert scores["Nux-v."] == 22.0
        assert scores["Puls."] == 14.0

    def test_kent_single_remedy(self, single_result):
        m = KentMethod()
        ranked = m.score_repertorization(single_result, [5])
        assert len(ranked) == 1
        assert ranked[0]["method_score"] == 3.0

    def test_kent_empty_results(self):
        m = KentMethod()
        assert m.score_repertorization([], []) == []


# ── BoenninghausenMethod ───────────────────────────────────────────────────────

class TestBoenninghausenMethod:

    def test_name(self):
        m = BoenninghausenMethod()
        assert m.get_name() == "boenninghausen"

    def test_explain(self):
        m = BoenninghausenMethod()
        e = m.explain("Sulph.")
        assert "totality-of-symptoms" in e

    def test_sector_extraction(self):
        m = BoenninghausenMethod()
        assert m._extract_sector("Mind; weeping") == "mind"
        assert m._extract_sector("Head; pain; morning") == "head"
        assert m._extract_sector(None) == "unknown"
        assert m._extract_sector("") == "unknown"

    def test_boenninghausen_scoring_hand_calculated(self, sample_results):
        m = BoenninghausenMethod()
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        sectors = {r["abbrev"]: r["sector_count"] for r in ranked}
        # All default sector weights = 1.0
        # Puls appears in mind, head, stomach => sectors=3, base=3, bonus=2*(3-1)=4 => 7
        # Nux-v same => 7
        # Sulph same => 7
        # Lyc appears in head, stomach => sectors=2, base=2, bonus=2*(2-1)=2 => 4
        assert scores["Puls."] == 7.0
        assert scores["Nux-v."] == 7.0
        assert scores["Sulph."] == 7.0
        assert scores["Lyc."] == 4.0
        assert sectors["Puls."] == 3

    def test_boenninghausen_cross_sector_bonus(self, sample_results):
        m = BoenninghausenMethod()
        m.configure({"cross_sector_bonus": 5.0})
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Puls base=3 + bonus=5*2=13 => 16
        assert scores["Puls."] == 13.0
        assert scores["Lyc."] == 7.0  # base=2 + bonus=5*1=5 => 7

    def test_boenninghausen_custom_sector_weights(self):
        results = [
            {
                "abbrev": "A",
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind; anxiety", "weight": 1},
                    {"rubric_id": 2, "rubric": "Head; pain", "weight": 1},
                ],
            },
            {
                "abbrev": "B",
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind; anxiety", "weight": 1},
                    {"rubric_id": 3, "rubric": "Stomach; nausea", "weight": 1},
                ],
            },
        ]
        m = BoenninghausenMethod()
        m.configure({"sector_weights": {"mind": 3.0, "head": 1.0, "stomach": 1.0}})
        ranked = m.score_repertorization(results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # A: mind(3) + head(1) = 4 + bonus 2*(2-1)=2 = 6
        # B: mind(3) + stomach(1) = 4 + bonus 2*(2-1)=2 = 6
        assert scores["A"] == 6.0
        assert scores["B"] == 6.0

    def test_boenninghausen_empty_results(self):
        m = BoenninghausenMethod()
        assert m.score_repertorization([], []) == []


# ── BogerMethod ──────────────────────────────────────────────────────────────

class TestBogerMethod:

    def test_name(self):
        m = BogerMethod()
        assert m.get_name() == "boger"

    def test_explain(self):
        m = BogerMethod()
        e = m.explain("Sil.")
        assert "keynote" in e.lower()

    def test_boger_grade3_boost(self, sample_results):
        m = BogerMethod()
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Without keynotes:
        # Puls: 3*2 + 2*1 + 1*0.5 = 6+2+0.5=8.5
        # Nux-v: 2*1 + 3*2 + 3*2 = 2+6+6=14
        # Sulph: 1*0.5*3 = 1.5
        # Lyc: 3*2 + 2*1 = 8
        assert scores["Nux-v."] == 14.0
        assert scores["Puls."] == 8.5
        assert scores["Lyc."] == 8.0
        assert scores["Sulph."] == 1.5

    def test_boger_keynote_boost(self, sample_results):
        m = BogerMethod()
        m.configure({
            "keynote_rubric_ids": [1],
            "keynote_remedy_boost": {"Puls.": 2.0},
        })
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Puls: (3*2*1.5 keynote mult *2 rem_boost)=18 + (2*1*2 rem_boost)=4 + (1*0.5*2)=1 = 23
        # Nux-v: (2*1*1.5 keynote mult)=3 + (3*2)=6 + (3*2)=6 = 15
        assert scores["Puls."] == 23.0
        assert scores["Nux-v."] == 15.0

    def test_boger_configure_multipliers(self, sample_results):
        m = BogerMethod()
        m.configure({
            "grade3_multiplier": 1.0,
            "grade2_multiplier": 0.5,
            "grade1_multiplier": 0.25,
        })
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Puls: 3*1 + 2*0.5 + 1*0.25 = 3+1+0.25 = 4.25
        # Nux-v: 2*0.5 + 3*1 + 3*1 = 1+3+3 = 7
        assert scores["Nux-v."] == 7.0
        assert scores["Puls."] == 4.25

    def test_boger_empty_results(self):
        m = BogerMethod()
        assert m.score_repertorization([], []) == []


# ── VithoulkasExpertSystem ───────────────────────────────────────────────────

class TestVithoulkasExpertSystem:

    def test_name(self):
        m = VithoulkasExpertSystem()
        assert m.get_name() == "vithoulkas"

    def test_explain(self):
        m = VithoulkasExpertSystem()
        e = m.explain("Calc.")
        assert "level of health" in e.lower()

    def test_ves_totality_intensity_balance(self, sample_results):
        m = VithoulkasExpertSystem()
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        totality = {r["abbrev"]: r["ves_totality"] for r in ranked}
        intensity = {r["abbrev"]: r["ves_intensity"] for r in ranked}
        # Puls: totality=3, intensity=3 => composite=3+3=6, level=6 => lw=1.1
        #   total = 6*1.1 + 0.5 (exact alignment) = 7.1
        # Nux-v: totality=3, intensity=3 => same composite=6 => 6*1.1+0.5=7.1
        # Sulph: totality=3, intensity=1 => composite=3+1=4 => 4*1.1+0.5=4.9
        # Lyc: totality=2, intensity=3 => composite=2+3=5 => 5*1.1+0.5=6.0
        assert totality["Puls."] == 3
        assert intensity["Puls."] == 3
        assert totality["Lyc."] == 2
        assert intensity["Lyc."] == 3
        assert scores["Puls."] == pytest.approx(7.1)
        assert scores["Nux-v."] == pytest.approx(7.1)

    def test_ves_level_alignment_bonus(self):
        results = [
            {
                "abbrev": "Med.",
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind", "weight": 3},
                ],
            },
            {
                "abbrev": "Sulph.",
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind", "weight": 3},
                ],
            },
        ]
        m = VithoulkasExpertSystem()
        m.configure({
            "level_of_health": 4,
            "remedy_level_map": {"Med.": 4, "Sulph.": 10},
        })
        ranked = m.score_repertorization(results, [1])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Med: composite=1+3=4, level=4 => lw=1.0, alignment exact => +0.5 => 4.5
        # Sulph: composite=4, level=10 => lw=1.2, diff=6 => alignment=0.0 => 4.8
        assert scores["Med."] == pytest.approx(4.5)
        assert scores["Sulph."] == pytest.approx(4.8)

    def test_ves_configure_weights(self, sample_results):
        m = VithoulkasExpertSystem()
        m.configure({"totality_weight": 3.0, "intensity_weight": 0.5})
        ranked = m.score_repertorization(sample_results, [1, 2, 3])
        scores = {r["abbrev"]: r["method_score"] for r in ranked}
        # Puls: totality=3, intensity=3 => composite=9+1.5=10.5 => 10.5*1.1+0.5=12.05
        # Nux-v: same => 12.05
        # Sulph: totality=3, intensity=1 => composite=9+0.5=9.5 => 9.5*1.1+0.5=10.95
        # Lyc: totality=2, intensity=3 => composite=6+1.5=7.5 => 7.5*1.1+0.5=8.75
        assert scores["Puls."] == pytest.approx(12.05, rel=1e-2)
        assert scores["Lyc."] == pytest.approx(8.75, rel=1e-2)

    def test_ves_empty_results(self):
        m = VithoulkasExpertSystem()
        assert m.score_repertorization([], []) == []


# ── MethodRegistry ───────────────────────────────────────────────────────────

class TestMethodRegistry:

    def test_register_and_get(self):
        reg = MethodRegistry()
        k = KentMethod()
        reg.register(k)
        assert reg.get_method("kent") is k

    def test_unknown_method(self):
        reg = MethodRegistry()
        assert reg.get_method("unknown") is None

    def test_list_methods(self):
        reg = MethodRegistry()
        reg.register(KentMethod())
        reg.register(BoenninghausenMethod())
        items = reg.list_methods()
        assert len(items) == 2
        names = {i["name"] for i in items}
        assert names == {"kent", "boenninghausen"}
        for i in items:
            assert "description" in i
            assert "default_weight" in i

    def test_list_methods_default_weights(self):
        reg = MethodRegistry()
        reg.register(KentMethod())
        reg.register(BoenninghausenMethod())
        reg.register(VithoulkasExpertSystem())
        weights = {i["name"]: i["default_weight"] for i in reg.list_methods()}
        assert weights["kent"] == 0.30
        assert weights["boenninghausen"] == 0.20
        assert weights["vithoulkas"] == 0.35


# ── MethodSwitcher ───────────────────────────────────────────────────────────

class TestMethodSwitcher:

    def test_compare_all_methods(self, sample_results):
        reg = MethodRegistry()
        reg.register(KentMethod())
        reg.register(BoenninghausenMethod())
        switcher = MethodSwitcher(reg)
        comp = switcher.compare(sample_results, [1, 2, 3])
        assert "method_results" in comp
        assert "side_by_side" in comp
        assert "top_common" in comp
        assert "summary" in comp
        assert "kent" in comp["method_results"]
        assert "boenninghausen" in comp["method_results"]

    def test_compare_subset_methods(self, sample_results):
        reg = MethodRegistry()
        reg.register(KentMethod())
        reg.register(BoenninghausenMethod())
        reg.register(BogerMethod())
        switcher = MethodSwitcher(reg)
        comp = switcher.compare(sample_results, [1, 2, 3], methods=["kent", "boger"])
        assert set(comp["method_results"].keys()) == {"kent", "boger"}

    def test_compare_top_common(self, sample_results):
        reg = MethodRegistry()
        reg.register(KentMethod())
        reg.register(BoenninghausenMethod())
        switcher = MethodSwitcher(reg)
        comp = switcher.compare(sample_results, [1, 2, 3])
        # Kent top 5 includes Nux-v, Puls, Lyc, Sulph (all)
        # Boenninghausen top 5 includes Nux-v, Puls, Sulph, Lyc (all)
        # common should have at least some overlap
        assert isinstance(comp["top_common"], list)

    def test_compare_unknown_method(self, sample_results):
        reg = MethodRegistry()
        reg.register(KentMethod())
        switcher = MethodSwitcher(reg)
        with pytest.raises(ValueError, match="Unknown method"):
            switcher.compare(sample_results, [1, 2, 3], methods=["kent", "ves"])

    def test_compare_with_empty_registry(self, sample_results):
        switcher = MethodSwitcher(MethodRegistry())
        with pytest.raises(ValueError, match="No methods registered"):
            switcher.compare(sample_results, [1, 2, 3])

    def test_switcher_registry_property(self):
        reg = MethodRegistry()
        switcher = MethodSwitcher(reg)
        assert switcher.registry is reg


# ── AnalysisMethods convenience wrapper ────────────────────────────────────────

class TestAnalysisMethods:

    def test_construction(self):
        engine = AnalysisMethods()
        assert engine is not None
        assert engine._registry is not None
        assert engine._switcher is not None

    def test_process_returns_dict(self):
        engine = AnalysisMethods()
        result = engine.process()
        assert isinstance(result, dict)
        assert result["status"] == "ready"
        assert result["feature_id"] == 13
        assert "available_methods" in result

    def test_process_kent_method(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(sample_results, rubric_ids=[1, 2, 3], method="kent")
        assert result["status"] == "ok"
        assert result["method"] == "kent"
        assert isinstance(result["results"], list)
        assert result["results"][0]["method_name"] == "kent"

    def test_process_boenninghausen_method(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(
            sample_results, rubric_ids=[1, 2, 3], method="boenninghausen"
        )
        assert result["status"] == "ok"
        assert result["method"] == "boenninghausen"

    def test_process_boger_method(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(
            sample_results, rubric_ids=[1, 2, 3], method="boger"
        )
        assert result["status"] == "ok"

    def test_process_vithoulkas_method(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(
            sample_results, rubric_ids=[1, 2, 3], method="vithoulkas"
        )
        assert result["status"] == "ok"

    def test_process_unknown_method(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(
            sample_results, rubric_ids=[1, 2, 3], method="nonexistent"
        )
        assert result["status"] == "error"
        assert "nonexistent" in result["message"]

    def test_process_comparison(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(sample_results, rubric_ids=[1, 2, 3])
        assert result["status"] == "ok"
        assert "comparison" in result
        comp = result["comparison"]
        assert "method_results" in comp

    def test_process_with_mock_repertory(self):
        class MockRep:
            pass
        engine = AnalysisMethods(MockRep())
        assert engine.rep is not None

    def test_process_configure_kwargs(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(
            sample_results,
            rubric_ids=[1, 2, 3],
            method="kent",
            grade_map={1: 1, 2: 10, 3: 100},
        )
        assert result["status"] == "ok"
        # Scores should reflect custom grade_map (we just ensure no crash)
        assert len(result["results"]) == 4

    def test_process_empty_results(self):
        engine = AnalysisMethods()
        result = engine.process([], rubric_ids=[1, 2, 3], method="kent")
        assert result["status"] == "ok"
        assert result["results"] == []

    def test_process_empty_rubric_ids(self, sample_results):
        engine = AnalysisMethods()
        result = engine.process(sample_results, rubric_ids=[], method="kent")
        assert result["status"] == "ok"

    def test_integration_all_methods_runnable(self, sample_results):
        engine = AnalysisMethods()
        for name in ["kent", "boenninghausen", "boger", "vithoulkas"]:
            res = engine.process(sample_results, rubric_ids=[1, 2, 3], method=name)
            assert res["status"] == "ok"
            assert len(res["results"]) == 4


# ── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_kent_missing_weight_defaults(self):
        results = [
            {"abbrev": "X", "matches": [{"rubric_id": 1, "rubric": "Mind"}]},
        ]
        m = KentMethod()
        ranked = m.score_repertorization(results, [1])
        assert ranked[0]["method_score"] == 1.0

    def test_boenninghausen_duplicate_rubric_ids_same_remedy(self):
        results = [
            {
                "abbrev": "X",
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind; a", "weight": 3},
                    {"rubric_id": 1, "rubric": "Mind; a duplicate", "weight": 2},
                ],
            },
        ]
        m = BoenninghausenMethod()
        ranked = m.score_repertorization(results, [1])
        # Only unique rubric_id should count
        assert ranked[0]["method_score"] == 1.0  # one rubric, no bonus

    def test_boger_no_matches(self):
        results = [{"abbrev": "Z", "matches": []}]
        m = BogerMethod()
        ranked = m.score_repertorization(results, [1])
        assert ranked[0]["method_score"] == 0.0
        assert ranked[0]["keynote_hits"] == 0

    def test_ves_no_matches(self):
        results = [{"abbrev": "Z", "matches": []}]
        m = VithoulkasExpertSystem()
        ranked = m.score_repertorization(results, [1])
        assert ranked[0]["method_score"] == 0.5  # alignment exact at level 6
        assert ranked[0]["ves_totality"] == 0
        assert ranked[0]["ves_intensity"] == 0

    def test_registry_overwrite(self):
        reg = MethodRegistry()
        k1 = KentMethod()
        k2 = KentMethod()
        reg.register(k1)
        reg.register(k2)
        assert reg.get_method("kent") is k2
