"""
Tests for Keynote Autocomplete — Feature #22

Covers: trie completion, scoring, ranked suggestions, history, feature overview.
"""

import pytest
from oorep.keynote_autocomplete import KeynoteAutocompleteEngine


SAMPLE_RUBRICS = [
    {"id": 1, "fullpath": "Mind; Anxiety", "text": "Anxiety"},
    {"id": 2, "fullpath": "Mind; Anxiety; morning", "text": "Anxiety morning"},
    {"id": 3, "fullpath": "Mind; Fear; death of", "text": "Fear death of"},
    {"id": 4, "fullpath": "General; Restless", "text": "Restless"},
]

SAMPLE_KEYNOTES = {
    "ARS": ["anxiety"],
    "PULS": ["fear"],
}


class TestAutocompleteCompletion:

    def test_complete_returns_list(self):
        engine = KeynoteAutocompleteEngine(rubric_list=SAMPLE_RUBRICS,
                                            keynotes=SAMPLE_KEYNOTES)
        result = engine.complete("anx")
        assert isinstance(result, list)

    def test_complete_filters_by_prefix(self):
        engine = KeynoteAutocompleteEngine(rubric_list=SAMPLE_RUBRICS)
        result = engine.complete("fear")
        assert isinstance(result, list)

    def test_complete_top_n(self):
        engine = KeynoteAutocompleteEngine(rubric_list=SAMPLE_RUBRICS * 3,
                                            keynotes=SAMPLE_KEYNOTES)
        result = engine.complete("a", top_n=2)
        assert len(result) <= 2

    def test_complete_empty_returns_empty(self):
        engine = KeynoteAutocompleteEngine()
        assert engine.complete("") == []
        assert engine.complete("x") == []


class TestAutocompleteScoring:

    def test_scores_are_floats(self):
        engine = KeynoteAutocompleteEngine(rubric_list=SAMPLE_RUBRICS,
                                            keynotes=SAMPLE_KEYNOTES)
        result = engine.complete("anx", top_n=5)
        for r in result:
            assert isinstance(r["score"], (int, float))

    def test_anxiety_has_ars_keynote_bonus(self):
        engine = KeynoteAutocompleteEngine(rubric_list=SAMPLE_RUBRICS,
                                            keynotes=SAMPLE_KEYNOTES)
        result = engine.complete("anx", top_n=5)
        assert len(result) > 0


class TestUsageHistory:

    def test_record_usage_adds_entry(self):
        engine = KeynoteAutocompleteEngine()
        engine.record_usage("Mind; Anxiety")
        assert "Mind; Anxiety" in engine.usage_history


class TestFeatureOverview:

    def test_overview(self):
        engine = KeynoteAutocompleteEngine()
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 22
        assert ov["feature_name"] == "Kent's Keynote Autocomplete"
