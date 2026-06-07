"""Tests for power_analysis.py (Module #71)"""

import pytest
from oorep.power_analysis import PowerAnalysis


@pytest.fixture
def pa():
    return PowerAnalysis()


class TestSampleSize:

    def test_basic_calculation(self, pa):
        result = pa.sample_size_proportion(0.3, 0.6, alpha=0.05, power=0.8)
        assert result["sample_size_per_group"] is not None
        assert result["sample_size_per_group"] > 0

    def test_higher_power_needs_more(self, pa):
        r1 = pa.sample_size_proportion(0.3, 0.6, power=0.8)
        r2 = pa.sample_size_proportion(0.3, 0.6, power=0.9)
        assert r2["sample_size_per_group"] >= r1["sample_size_per_group"]


class TestPowerCalculation:

    def test_power_increases_with_n(self, pa):
        p1 = pa.power_for_proportion(20, 0.3, 0.6)
        p2 = pa.power_for_proportion(100, 0.3, 0.6)
        assert p2["achievable_power"] > p1["achievable_power"]

    def test_power_bounded(self, pa):
        p = pa.power_for_proportion(50, 0.3, 0.6)
        assert 0 <= p["achievable_power"] <= 1


class TestMDE:

    def test_mde_decreases_with_n(self, pa):
        m1 = pa.minimum_detectable_effect(30, 0.3)
        m2 = pa.minimum_detectable_effect(100, 0.3)
        assert m2["minimum_detectable_difference"] < m1["minimum_detectable_difference"]


class TestPowerCurve:

    def test_curve_length(self, pa):
        curve = pa.power_curve(0.3, 0.6)
        assert len(curve) > 0
        assert all(0 <= p["power"] <= 1 for p in curve)


class TestFeatureOverview:

    def test_overview(self, pa):
        ov = pa.get_feature_overview()
        assert ov["feature_id"] == 71
        assert "sample_size" in ov["supports"]
