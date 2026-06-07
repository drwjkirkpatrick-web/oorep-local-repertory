"""Tests for case_complexity_scorer.py (Module #68)"""

import pytest
from oorep.case_complexity_scorer import CaseComplexityScorer


@pytest.fixture
def scorer():
    return CaseComplexityScorer()


class TestScoring:

    def test_simple_case(self, scorer):
        result = scorer.score_case(["headache", "thirst", "irritability"])
        assert 0 <= result["complexity_score"] <= 1
        assert "components" in result

    def test_empty_symptoms(self, scorer):
        result = scorer.score_case([])
        assert result["complexity_score"] == 0

    def test_high_complexity(self, scorer):
        # Vague, overlapping symptoms
        result = scorer.score_case([
            "something is wrong",
            "not feeling well",
            "generally unwell",
        ])
        assert result["complexity_score"] > 0.3

    def test_coverage_ratio(self, scorer):
        result = scorer.score_case(["anxiety", "insomnia"], rubric_matches=[1])
        assert result["components"]["coverage_ratio"] == 0.5

    def test_entropy_increases_with_diversity(self, scorer):
        diverse = scorer.score_case(["burning pain", "restless anxiety", "fear of death"])
        similar = scorer.score_case(["pain", "painful", "hurts"])
        assert diverse["components"]["symptom_entropy"] >= similar["components"]["symptom_entropy"]


class TestFeatureOverview:

    def test_overview(self, scorer):
        ov = scorer.get_feature_overview()
        assert ov["feature_id"] == 68
