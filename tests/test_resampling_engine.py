"""Tests for resampling_engine.py (Module #73)"""

import pytest
from oorep.resampling_engine import ResamplingEngine


class TestBootstrap:

    def test_ci_contains_mean(self):
        data = [25.3, 22.1, 28.0, 24.5, 26.2, 23.8, 27.1, 25.0]
        result = ResamplingEngine.bootstrap_ci(data, statistic="mean", n_iterations=500, seed=42)
        assert result["ci_lower"] <= result["point_estimate"] <= result["ci_upper"]

    def test_reproducible(self):
        data = [1, 2, 3, 4, 5]
        r1 = ResamplingEngine.bootstrap_ci(data, n_iterations=200, seed=123)
        r2 = ResamplingEngine.bootstrap_ci(data, n_iterations=200, seed=123)
        assert r1["ci_lower"] == r2["ci_lower"]

    def test_empty_data(self):
        result = ResamplingEngine.bootstrap_ci([])
        assert "error" in result


class TestPermutation:

    def test_significant_difference(self):
        a = ["cured", "improved", "cured", "improved", "cured"]
        b = ["unchanged", "worsened", "unchanged", "worsened", "unchanged"]
        result = ResamplingEngine.permutation_test(a, b, n_iterations=500, seed=42)
        assert result["p_value"] < 0.05
        assert result["significant"] is True

    def test_no_difference(self):
        a = ["cured", "unchanged", "improved"]
        b = ["unchanged", "cured", "improved"]
        result = ResamplingEngine.permutation_test(a, b, n_iterations=500, seed=42)
        assert result["p_value"] >= 0.05 or result["observed_difference"] == 0


class TestCrossValidation:

    def test_kfold(self):
        data = list(range(20))
        def mock_model(train, test):
            return {"score": len(train) / 100}
        result = ResamplingEngine.cross_validation(data, mock_model, k=5, seed=42)
        assert len(result["fold_scores"]) == 5
        assert result["mean_score"] > 0

    def test_invalid_k(self):
        result = ResamplingEngine.cross_validation([1, 2], lambda t, te: {"score": 1}, k=1)
        assert "error" in result


class TestFeatureOverview:

    def test_overview(self):
        ov = ResamplingEngine().get_feature_overview()
        assert ov["feature_id"] == 73
        assert "bootstrap_ci" in ov["supports"]
