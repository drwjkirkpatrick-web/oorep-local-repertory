"""Tests for meta_analysis_engine.py (Module #70)"""

import pytest
from oorep.meta_analysis_engine import MetaAnalysisEngine


@pytest.fixture
def ma():
    return MetaAnalysisEngine()


@pytest.fixture
def studies():
    return [
        {"study": "Clinic A", "n": 30, "positive": 22},
        {"study": "Clinic B", "n": 25, "positive": 18},
        {"study": "Clinic C", "n": 20, "positive": 15},
    ]


class TestFixedEffect:

    def test_pooled_proportion(self, ma, studies):
        result = ma.fixed_effect(studies)
        assert 0 < result["pooled_proportion"] < 1
        assert len(result["ci_95"]) == 2

    def test_ci_order(self, ma, studies):
        result = ma.fixed_effect(studies)
        assert result["ci_95"][0] < result["ci_95"][1]


class TestRandomEffects:

    def test_heterogeneity(self, ma, studies):
        result = ma.random_effects(studies)
        assert "heterogeneity" in result
        assert "I_squared" in result["heterogeneity"]

    def test_ci_present(self, ma, studies):
        result = ma.random_effects(studies)
        assert result["ci_95"][0] < result["ci_95"][1]


class TestFeatureOverview:

    def test_overview(self, ma):
        ov = ma.get_feature_overview()
        assert ov["feature_id"] == 70
        assert "random_effects" in ov["supports"]
