"""Tests for inter_rater_reliability.py (Module #69)"""

import pytest
from oorep.inter_rater_reliability import InterRaterReliability


class TestCohensKappa:

    def test_perfect_agreement(self):
        result = InterRaterReliability.cohens_kappa(["A", "B", "A"], ["A", "B", "A"])
        assert result["kappa"] == 1.0
        assert result["interpretation"] == "Almost perfect agreement"

    def test_no_agreement(self):
        result = InterRaterReliability.cohens_kappa(["A", "A", "B"], ["B", "B", "A"])
        # Negative kappa = less than chance
        assert result["kappa"] < 0

    def test_partial_agreement(self):
        result = InterRaterReliability.cohens_kappa(["A", "B", "A", "B"], ["A", "B", "B", "A"])
        assert 0 <= result["kappa"] <= 1


class TestFleissKappa:

    def test_perfect_agreement(self):
        result = InterRaterReliability.fleiss_kappa([
            ["A", "B", "A"],
            ["A", "B", "A"],
            ["A", "B", "A"],
        ])
        assert result["kappa"] == 1.0

    def test_partial_agreement(self):
        result = InterRaterReliability.fleiss_kappa([
            ["A", "B", "A"],
            ["A", "B", "A"],
            ["B", "B", "A"],
        ])
        assert 0 < result["kappa"] < 1


class TestICC:

    def test_high_icc(self):
        result = InterRaterReliability.icc_consistency([
            [1.0, 2.0, 3.0],
            [1.1, 2.1, 3.1],
            [0.9, 1.9, 2.9],
        ])
        assert result["icc"] > 0.9

    def test_low_icc(self):
        result = InterRaterReliability.icc_consistency([
            [1.0, 5.0, 3.0],
            [4.0, 2.0, 6.0],
            [7.0, 1.0, 9.0],
        ])
        assert result["icc"] < 0.5


class TestFeatureOverview:

    def test_overview(self):
        ov = InterRaterReliability().get_feature_overview()
        assert ov["feature_id"] == 69
        assert "cohens_kappa" in ov["supports"]
