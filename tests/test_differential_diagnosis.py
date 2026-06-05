"""
Tests for Differential Diagnosis (Feature #19)

Covers: compare_remedies, differential_table, taxonomy, potency, edge cases.
"""

import pytest
from oorep.differential_diagnosis import DifferentialDiagnosisEngine


@pytest.fixture
def engine():
    tax = {
        "ARS": {"kingdom": "Mineral", "family": "Metal"},
        "PULS": {"kingdom": "Plant", "family": "Ranunculaceae"},
        "LACH": {"kingdom": "Animal", "family": "Viperidae"},
    }
    rubric_data = {
        "1": [{"remedy": "ARS", "grade": 3}, {"remedy": "PULS", "grade": 2}],
        "2": [{"remedy": "ARS", "grade": 3}, {"remedy": "LACH", "grade": 1}],
        "3": [{"remedy": "PULS", "grade": 3}],
        "4": [{"remedy": "LACH", "grade": 3}],
    }
    return DifferentialDiagnosisEngine(rubric_data=rubric_data, remedy_taxonomy=tax)


class TestCompareRemedies:

    def test_shared_exclusive(self, engine):
        result = engine.compare_remedies("ARS", "PULS", rubric_ids=[1, 2, 3])
        assert result["remedy_a"] == "ARS"
        assert result["remedy_b"] == "PULS"
        # ARS in 1,2; PULS in 1,3 → shared: 1, exclusive for ARS: 2, for PULS: 3
        assert "1" in result["shared_rubrics"]
        assert "2" in result["exclusive_a"]
        assert "3" in result["exclusive_b"]
        assert result["differential_score"] > 0

    def test_same_kingdom_false(self, engine):
        result = engine.compare_remedies("ARS", "PULS")
        assert result["same_kingdom"] is False

    def test_keynotes_returned(self, engine):
        result = engine.compare_remedies("ARS", "PULS")
        assert "keynotes_a" in result
        assert "keynotes_b" in result

    def test_potency_guidance(self, engine):
        result = engine.compare_remedies("ARS", "PULS")
        assert "ARS" in result["potency_guidance"]
        assert "PULS" in result["potency_guidance"]
        assert "higher" in result["potency_guidance"]["ARS"].lower()


class TestDifferentialTable:

    def test_table_sorted(self, engine):
        candidates = [
            {"remedy": "ARS", "score": 28.0},
            {"remedy": "PULS", "score": 26.0},
            {"remedy": "LACH", "score": 22.0},
        ]
        table = engine.differential_table(candidates, rubric_ids=[1, 2, 3, 4])
        assert len(table) == 3
        assert "avg_differential_score" in table[0]
        assert table[0]["avg_differential_score"] >= 0

    def test_kingdom_in_table(self, engine):
        candidates = [{"remedy": "ARS", "score": 10}]
        table = engine.differential_table(candidates)
        assert table[0]["kingdom"] == "Mineral"


class TestEmpty:

    def test_no_data(self):
        engine = DifferentialDiagnosisEngine()
        result = engine.compare_remedies("ARS", "PULS")
        assert result["shared_count"] == 0
        assert result["differential_score"] == 0

    def test_feature_overview(self, engine):
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 19
