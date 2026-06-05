"""
Tests for Elimination Rubrics (Feature #18)

Covers: rule construction, elimination, taxonomy-based, explain, edge cases.
"""

import pytest
from oorep.elimination_rubrics import EliminationEngine


@pytest.fixture
def engine():
    return EliminationEngine()


@pytest.fixture
def candidates():
    return [
        {"remedy": "ARS"},
        {"remedy": "PULS"},
        {"remedy": "LACH"},
        {"remedy": "SULPH"},
    ]


class TestEliminationRules:

    def test_add_rule(self, engine):
        engine.add_elimination_rubric(symptom="thirst absent", exclude_remedies=["ARS", "PHOS"])
        assert len(engine.list_rules()) == 1
        rule = engine.list_rules()[0]
        assert rule["symptom"] == "thirst absent"

    def test_eliminate_remedy(self, engine, candidates):
        engine.add_elimination_rubric(symptom="thirst absent", exclude_remedies=["ARS"])
        result = engine.apply_elimination(candidates, symptoms=["thirst absent"])
        assert result["ruled_out_count"] == 1
        assert result["ruled_in_count"] == 3
        ruled_out = [r["remedy"] for r in result["ruled_out"]]
        assert "ARS" in ruled_out

    def test_no_match_no_elimination(self, engine, candidates):
        engine.add_elimination_rubric(symptom="thirst absent", exclude_remedies=["ARS"])
        result = engine.apply_elimination(candidates, symptoms=["no thirst issue"])
        assert result["ruled_out_count"] == 0
        assert result["ruled_in_count"] == 4

    def test_empty_candidates(self, engine):
        engine.add_elimination_rubric(symptom="x", exclude_remedies=["ARS"])
        result = engine.apply_elimination([], symptoms=["x"])
        assert result["ruled_out_count"] == 0

    def test_taxonomy_exclusion(self, engine, candidates):
        engine.add_elimination_rubric(symptom="animal fear", exclude_kingdoms=["animal"])
        tax = {
            "ARS": {"kingdom": "Mineral"},
            "PULS": {"kingdom": "Plant"},
            "LACH": {"kingdom": "Animal"},
            "SULPH": {"kingdom": "Mineral"},
        }
        result = engine.apply_elimination(candidates, symptoms=["animal fear"], taxonomy=tax)
        ruled_out = [r["remedy"] for r in result["ruled_out"]]
        assert "LACH" in ruled_out
        assert "ARS" not in ruled_out

    def test_explain(self, engine, candidates):
        engine.add_elimination_rubric(symptom="thirst absent", exclude_remedies=["ARS"])
        result = engine.apply_elimination(candidates, symptoms=["thirst absent"])
        lines = engine.explain_eliminations(result)
        assert any("ARS" in l for l in lines)

    def test_clear_rules(self, engine):
        engine.add_elimination_rubric(symptom="x", exclude_remedies=["ARS"])
        engine.clear_rules()
        assert engine.list_rules() == []

    def test_shortcut(self, engine, candidates):
        engine.add_elimination_rubric(symptom="thirst absent", exclude_remedies=["ARS"])
        ruled_in = engine.eliminate_by_symptoms(candidates, symptoms=["thirst absent"])
        assert len(ruled_in) == 3

    def test_family_exclusion(self, engine, candidates):
        engine.add_elimination_rubric(symptom="snake", exclude_families=["Viperidae"])
        tax = {"LACH": {"family": "Viperidae"}, "ARS": {"family": "Metal"}}
        result = engine.apply_elimination(candidates, symptoms=["snake"], taxonomy=tax)
        ruled_out = [r["remedy"] for r in result["ruled_out"]]
        assert "LACH" in ruled_out

    def test_feature_overview(self, engine):
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 18
        assert "rule_types" in ov
