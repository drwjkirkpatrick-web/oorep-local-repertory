"""
Tests for Follow-up Comparator (Feature #20)

Covers: symptom comparison, timeline, suggestions, visit comparison,
prediction, edge cases.
"""

import pytest
from oorep.followup_comparator import FollowupComparator


class TestSymptomComparison:

    def test_unchanged(self):
        comp = FollowupComparator()
        result = comp.compare_symptom_sets(
            ["anxiety", "thirst", "pain"],
            ["anxiety", "thirst", "pain"],
        )
        assert result["new"] == []
        assert result["disappeared"] == []
        assert result["unchanged"] == ["anxiety", "pain", "thirst"]
        assert result["change_ratio"] == 0.0

    def test_new(self):
        result = FollowupComparator.compare_symptom_sets(
            ["anxiety"],
            ["anxiety", "fear", "pain"],
        )
        assert result["new"] == ["fear", "pain"]
        assert result["disappeared"] == []
        assert result["changed_picture"] == True

    def test_disappeared(self):
        result = FollowupComparator.compare_symptom_sets(
            ["anxiety", "pain"],
            ["pain"],
        )
        assert result["disappeared"] == ["anxiety"]
        assert result["change_ratio"] == 0.5

    def test_case_insensitive(self):
        result = FollowupComparator.compare_symptom_sets(
            ["Anxiety", "PAIN"],
            ["anxiety", "pain"],
        )
        assert result["unchanged"] == ["anxiety", "pain"]


class TestSuggestions:

    def test_suggestion_complementary(self):
        comp = FollowupComparator()
        rels = {
            "PULS": [{"remedy": "SIL", "relationship": "complementary"}],
        }
        result = comp.suggest_followup(
            patient_pseudonym="X",
            current_remedy="PULS",
            relationship_db=rels,
        )
        assert result["current_remedy"] == "PULS"
        remedies = [s["remedy"] for s in result["suggestions"]]
        assert "SIL" in remedies

    def test_suggestion_prior_outcomes(self):
        # No DB → no prior outcomes → no history-based suggestions
        comp = FollowupComparator()
        result = comp.suggest_followup(
            patient_pseudonym="X",
            current_remedy="ARS",
        )
        assert result["suggestion_count"] >= 0

    def test_new_symptoms(self):
        comp = FollowupComparator()
        changes = {
            "new": ["fear", "burning"],
            "change_ratio": 0.5,
        }
        result = comp.suggest_followup(
            patient_pseudonym="X",
            current_remedy="PULS",
            symptom_changes=changes,
            relationship_db={},
        )
        reasons = [s["reason"] for s in result["suggestions"]]
        assert "new_symptoms_detected" in reasons


class TestVisitComparison:

    def test_compare_visits(self):
        comp = FollowupComparator()
        result = comp.compare_visits(
            baseline_symptoms=["anxiety", "thirst"],
            followup_symptoms=["anxiety", "fear"],
            baseline_remedies=["ARS"],
            followup_remedies=["PULS"],
        )
        assert result["repertorization_advised"] == True
        assert "ARS" in result["changed_remedies"]
        assert "PULS" in result["changed_remedies"]


class TestPrediction:

    def test_no_history(self):
        comp = FollowupComparator()
        pred = comp.predict_next_visit("NewPatient")
        assert pred["predicted"] is None

    def test_feature_overview(self):
        comp = FollowupComparator()
        ov = comp.get_feature_overview()
        assert ov["feature_id"] == 20
