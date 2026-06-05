"""
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
