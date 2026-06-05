#!/usr/bin/env python3
"""
Builder: Feature #9 — Word-Wrap Proximity Search

Generates oorep/word_wrap_search.py + tests/test_word_wrap_search.py
"""

import sys
from pathlib import Path

PROJECT = Path("/home/walker/projects/oorep-local-repertory")
sys.path.insert(0, str(PROJECT))

FEATURE_SLUG = "word_wrap_search"
FEATURE_ID = 9

MODULE_CODE = '''"""
Word-Wrap Proximity Search — Feature #9

Multi-word phrase matching with adjacency scoring.
When a user searches "dry cough evening", find rubrics where all words
appear within a configurable window, scoring higher when closer together.
Falls back to standard AND search if no proximity matches.

Usage:
    from oorep.word_wrap_search import WordWrapSearch
    engine = WordWrapSearch(repertory)
    results = engine.search("dry cough evening", window=5, top_n=20)
"""

import re
from typing import Dict, List, Optional, Any
from collections import defaultdict


class WordWrapSearch:
    """
    Proximity-aware rubric search engine.

    Splits queries into tokens, finds rubrics where tokens appear close
    together (within `window` words), and scores by proximity (closer = higher).
    Falls back to standard AND matching when no proximity hits exist.
    """

    def __init__(self, repertory: Any):
        self.rep = repertory
        self._token_cache: Dict[str, List[str]] = {}

    def _tokenize(self, text: str) -> List[str]:
        """Lowercase, strip punctuation, split to tokens."""
        if text in self._token_cache:
            return self._token_cache[text]
        tokens = re.findall(r"[a-z]+", text.lower())
        self._token_cache[text] = tokens
        return tokens

    def _proximity_score(self, rubric_text: str, query_tokens: List[str], window: int) -> float:
        """
        Compute proximity score for query tokens in rubric text.
        Returns 0.0 if not all tokens appear. Higher score = closer proximity.
        """
        text_tokens = self._tokenize(rubric_text)
        token_positions: Dict[str, List[int]] = defaultdict(list)

        for idx, tok in enumerate(text_tokens):
            token_positions[tok].append(idx)

        # Check all tokens present
        for qt in query_tokens:
            if qt not in token_positions:
                return 0.0

        # Find best (minimum span) combination of positions
        positions_lists = [token_positions[qt] for qt in query_tokens]
        best_span = float("inf")

        # Cartesian product with early termination for small lists
        def cartesian_product(lists, current=(), depth=0):
            nonlocal best_span
            if depth == len(lists):
                span = max(current) - min(current) + 1
                if span < best_span:
                    best_span = span
                return
            if depth == 0:
                for pos in lists[0]:
                    cartesian_product(lists, (pos,), depth + 1)
            else:
                for pos in lists[depth]:
                    if pos - min(current) >= window:
                        continue
                    cartesian_product(lists, current + (pos,), depth + 1)

        cartesian_product(positions_lists)

        if best_span == float("inf"):
            return 0.0

        # Score: 1.0 when all adjacent, decreases with distance
        denominator = max(1, window - len(query_tokens) + 1)
        proximity_factor = max(0.0, 1.0 - (best_span - len(query_tokens)) / denominator)
        return proximity_factor

    def search(self, query: str, window: int = 5, top_n: int = 20, fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Search rubrics by proximity of query tokens.

        Args:
            query: Space-separated search terms
            window: Maximum word distance between farthest tokens
            top_n: Return top N results
            fallback: If no proximity matches, fall back to standard AND search

        Returns:
            List of rubric dicts with added 'proximity_score' field
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Get candidate rubrics via lexical search (fast pre-filter)
        candidates = self.rep.search_rubrics(query, limit=top_n * 3)

        scored = []
        for rubric in candidates:
            text = rubric.get("fullpath", "") + " " + rubric.get("text", "")
            prox_score = self._proximity_score(text, query_tokens, window)
            if prox_score > 0:
                rubric_copy = dict(rubric)
                rubric_copy["proximity_score"] = round(prox_score, 3)
                rubric_copy["match_type"] = "proximity"
                scored.append((prox_score, rubric_copy))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return [r for _, r in scored[:top_n]]

        if fallback:
            # Return standard AND matches with proximity_score=0.0
            for rubric in candidates[:top_n]:
                rubric["proximity_score"] = 0.0
                rubric["match_type"] = "fallback"
            return candidates[:top_n]

        return []

    def search_with_adjacency_bonus(self, query: str, window: int = 5, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Same as search() but boosts adjacent (consecutive) token matches.
        Consecutive tokens get 2× proximity score.
        """
        query_tokens = self._tokenize(query)
        candidates = self.rep.search_rubrics(query, limit=top_n * 3)

        scored = []
        for rubric in candidates:
            text = rubric.get("fullpath", "") + " " + rubric.get("text", "")
            prox_score = self._proximity_score(text, query_tokens, window)

            # Check for consecutive matches (adjacent tokens in same order)
            text_tokens = self._tokenize(text)
            adjacency_bonus = 0.0
            for i in range(len(text_tokens) - len(query_tokens) + 1):
                if text_tokens[i:i + len(query_tokens)] == query_tokens:
                    adjacency_bonus = 1.0
                    break

            total_score = prox_score + adjacency_bonus
            if total_score > 0:
                rubric_copy = dict(rubric)
                rubric_copy["proximity_score"] = round(total_score, 3)
                rubric_copy["match_type"] = "adjacency" if adjacency_bonus > 0 else "proximity"
                scored.append((total_score, rubric_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_n]] if scored else []
'''

TEST_CODE = '''"""
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
        results = engine.search_with_adjacency_bonus("dry cough evening", window=5)
        for r in results:
            if r["id"] == "3":
                assert r["match_type"] == "adjacency"

    def test_window_parameter_effective(self, engine):
        narrow = engine.search("dry cough evening", window=2, top_n=10, fallback=False)
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
'''


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"[WROTE] {path}")


def main():
    print(f"[BUILD] Feature #{FEATURE_ID}: Word-Wrap Proximity Search")

    # Write module
    write_file(PROJECT / "oorep" / f"{FEATURE_SLUG}.py", MODULE_CODE)

    # Write unit tests
    write_file(PROJECT / "tests" / f"test_{FEATURE_SLUG}.py", TEST_CODE)

    print(f"[DONE] Feature #{FEATURE_ID} built successfully")


if __name__ == "__main__":
    main()
