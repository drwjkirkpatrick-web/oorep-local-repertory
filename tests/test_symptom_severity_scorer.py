"""Tests for symptom_severity_scorer.py"""
import pytest
from oorep.symptom_severity_scorer import SymptomSeverityScorer

@pytest.fixture
def scorer(tmp_path):
    return SymptomSeverityScorer(data_dir=str(tmp_path))

class TestSeverity:
    def test_set_and_get(self, scorer):
        scorer.set_severity("case_1", 123, 8, "intense morning headache")
        s = scorer.get_severity("case_1", 123)
        assert s["severity"] == 8
        assert round(s["multiplier"], 2) == 1.67

    def test_invalid_severity(self, scorer):
        with pytest.raises(ValueError):
            scorer.set_severity("case_1", 123, 11)

    def test_weighted_scores(self, scorer):
        scorer.set_severity("case_1", 123, 10)
        base = [{"remedy": "PULS", "score": 30.0}]
        result = scorer.compute_weighted_scores("case_1", base)
        assert result[0]["severity_weighted_score"] > 30.0

    def test_summary(self, scorer):
        scorer.set_severity("case_1", 100, 5)
        scorer.set_severity("case_1", 200, 7)
        summary = scorer.case_severity_summary("case_1")
        assert summary["n_rated"] == 2
        assert summary["avg_severity"] == 6.0
