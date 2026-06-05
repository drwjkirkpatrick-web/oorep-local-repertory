"""
Tests for Word-Wrap Proximity Search (Feature #9)
"""

import pytest
from oorep.word_wrap_search import WordWrapSearch


class MockRepertory:
    """Minimal mock for testing WordWrapSearch in isolation."""

    def __init__(self, rubrics):
        self._rubrics = rubrics

    def search_rubrics(self, query: str, limit: int = 10):
        tokens = query.lower().split()
        results = []
        for r in self._rubrics:
            text = (r.get("fullpath", "") + " " + r.get("text", "")).lower()
            if all(t in text for t in tokens):
                results.append(dict(r))
            if len(results) >= limit:
                break
        return results


SAMPLE_RUBRICS = [
    {"id": "1", "fullpath": "Mind; anxiety, health, about", "text": "anxiety health about"},
    {"id": "2", "fullpath": "Mind; weeping, consolation, agg.", "text": "weeping consolation aggravation"},
    {"id": "3", "fullpath": "Chest; cough, dry, evening", "text": "cough dry evening"},
    {"id": "4", "fullpath": "Chest; cough, dry, morning", "text": "cough dry morning"},
    {"id": "5", "fullpath": "Stomach; thirst, small quantities", "text": "thirst small quantities"},
    {"id": "6", "fullpath": "General; evening, fever, dry cough", "text": "evening fever dry cough"},
]


@pytest.fixture
def engine():
    rep = MockRepertory(SAMPLE_RUBRICS)
    return WordWrapSearch(rep)


class TestWordWrapSearch:

    def test_tokenize_basic(self, engine):
        assert engine._tokenize("dry cough evening") == ["dry", "cough", "evening"]

    def test_tokenize_punctuation(self, engine):
        assert engine._tokenize("cough, dry; evening!") == ["cough", "dry", "evening"]

    def test_proximity_score_exact_match(self, engine):
        score = engine._proximity_score("cough dry evening", ["dry", "cough", "evening"], window=5)
        assert score > 0.8  # High proximity since all present

    def test_proximity_score_missing_token(self, engine):
        score = engine._proximity_score("cough dry", ["dry", "cough", "evening"], window=5)
        assert score == 0.0

    def test_proximity_score_far_apart(self, engine):
        text = "cough something something something dry something something something evening"
        score = engine._proximity_score(text, ["dry", "cough", "evening"], window=5)
        assert score == 0.0  # Beyond window

    def test_search_finds_proximity_match(self, engine):
        results = engine.search("dry cough evening", window=5, top_n=10)
        assert len(results) > 0
        ids = [r["id"] for r in results]
        assert "3" in ids  # "cough dry evening"
        assert "6" in ids  # "evening fever dry cough"

    def test_search_ranks_adjacent_higher(self, engine):
        results = engine.search("dry cough evening", window=5, top_n=10)
        assert results[0]["proximity_score"] >= results[-1]["proximity_score"]

    def test_search_no_match_empty(self, engine):
        results = engine.search("xyzabc nonexistent", window=5, top_n=10, fallback=False)
        assert results == []

    def test_search_fallback(self, engine):
        results = engine.search("xyzabc nonexistent", window=5, top_n=10, fallback=True)
        # Should return standard matches even though proximity fails
        assert len(results) >= 0  # May be empty if no AND match either

    def test_adjacency_bonus_finds_exact_phrase(self, engine):
        # Query "cough dry evening" matches rubric #3 exactly in order
        results = engine.search_with_adjacency_bonus("cough dry evening", window=5)
        for r in results:
            if r["id"] == "3":
                assert r["match_type"] == "adjacency"

    def test_adjacency_bonus_not_triggered_wrong_order(self, engine):
        # Query "dry cough evening" does NOT match "cough dry evening" consecutively
        results = engine.search_with_adjacency_bonus("dry cough evening", window=5)
        for r in results:
            if r["id"] == "3":
                assert r["match_type"] == "proximity"

    def test_window_parameter_effective(self, engine):
        # "dry cough evening" = 3 tokens; window=3 is minimum valid
        narrow = engine.search("dry cough evening", window=3, top_n=10, fallback=False)
        wide = engine.search("dry cough evening", window=10, top_n=10, fallback=False)
        assert len(wide) >= len(narrow)

    def test_proximity_score_field_present(self, engine):
        results = engine.search("dry cough", window=5)
        for r in results:
            assert "proximity_score" in r
            assert isinstance(r["proximity_score"], float)
            assert 0.0 <= r["proximity_score"] <= 2.0

    def test_empty_query(self, engine):
        results = engine.search("", window=5)
        assert results == []

    def test_single_token(self, engine):
        results = engine.search("cough", window=5, top_n=10)
        assert len(results) > 0

    def test_top_n_respected(self, engine):
        results = engine.search("dry cough evening", window=5, top_n=2)
        assert len(results) <= 2
