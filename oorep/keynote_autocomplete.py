"""
Kent's Keynote Autocomplete — Feature #22

Trie-based autocomplete for rubric search with keynote boosting.
As the user types, suggest rubrics ranked by:
(a) prefix match,
(b) classical keynote frequency,
(c) usage history.

Usage:
    from oorep.keynote_autocomplete import KeynoteAutocompleteEngine
    engine = KeynoteAutocompleteEngine(rubric_list=[...], keynotes={"ARS": [...]})
    suggestions = engine.complete("anxi", top_n=5)
    suggestions = engine.complete_with_history("anxi", history=["anxiety evening"])
"""

from typing import Any, Dict, List, Optional
from collections import defaultdict


class KeynoteAutocompleteEngine:
    """
    Rubric autocomplete with multi-factor ranking.
    """

    def __init__(
        self,
        rubric_list: Optional[List[Dict[str, Any]]] = None,
        keynotes: Optional[Dict[str, List[str]]] = None,
        usage_history: Optional[List[str]] = None,
    ):
        self.rubrics: List[Dict[str, Any]] = rubric_list or []
        self.keynotes = keynotes or {}
        self.usage_history = list(usage_history or [])
        self.trie: Dict[str, Any] = {}
        self._build_trie()

    def _build_trie(self) -> None:
        """Build prefix trie from rubric fullpaths."""
        self.trie = {}
        for rubric in self.rubrics:
            path = rubric.get("fullpath", "") or rubric.get("text", "")
            tokens = path.lower().split(";")
            for token in tokens:
                parts = token.strip().lower().split()
                for part in parts:
                    node = self.trie
                    for char in part:
                        if char not in node:
                            node[char] = {}
                        node = node[char]
                    node.setdefault("__entries", []).append(rubric)

    def _trie_lookup(self, prefix: str) -> List[Dict]:
        """Find all entries matching a prefix."""
        node = self.trie
        for char in prefix.lower():
            if char not in node:
                return []
            node = node[char]

        results = []
        # Walk all leaves from this node
        stack = [node]
        while stack:
            cur = stack.pop()
            if "__entries" in cur:
                results.extend(cur["__entries"])
            for k, v in cur.items():
                if k != "__entries" and isinstance(v, dict):
                    stack.append(v)

        # Deduplicate by id
        seen = set()
        deduped = []
        for r in results:
            rid = r.get("id", r.get("rubric_id", str(hash(str(r)))))
            if rid not in seen:
                seen.add(rid)
                deduped.append(r)
        return deduped

    def _score_rubric(self, rubric: Dict, query: str, history: List[str]) -> float:
        """Score a rubric by: prefix match (1.0), keynote presence (1.5), history (0.5)."""
        path = (rubric.get("fullpath", "") or rubric.get("text", "")).lower()
        query_lc = query.lower()

        score = 0.0
        # Prefix match bonus
        if path.startswith(query_lc):
            score += 1.0
        elif query_lc in path:
            score += 0.5

        # Keyword match in parts
        parts = path.split(";")
        for part in parts:
            if query_lc in part.strip():
                score += 0.3

        # History bonus
        for hist in history:
            if query_lc in hist.lower():
                score += 0.2

        # Keynote bonus
        keynote_score = self._keynote_bonus(rubric)
        score += keynote_score

        return score

    def _keynote_bonus(self, rubric: Dict) -> float:
        """Add score if remedy in rubric has classical keynote frequency."""
        path = (rubric.get("fullpath", "") or rubric.get("text", "")).lower()
        bonus = 0.0
        for remedy, kws in self.keynotes.items():
            for kw in kws:
                kw_lc = kw.lower() if isinstance(kw, str) else kw.get("symptom", "").lower()
                if kw_lc and kw_lc in path:
                    bonus += 0.1
        return bonus

    # ── Public API ─────────────────────────────────────────────────────────────

    def complete(
        self,
        query: str,
        top_n: int = 10,
        include_history: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Autocomplete suggestions for a query prefix.
        Returns [{rubric_id, path, text, score, preview}, ...].
        """
        if not query or len(query.strip()) < 2:
            return []

        query = query.strip().lower()

        # 1. Trie lookup for prefix
        matches = self._trie_lookup(query)
        if not matches and len(self.rubrics) > 0:
            # Fallback: search all rubrics for substring
            matches = [
                r for r in self.rubrics
                if query in (r.get("fullpath", "") or r.get("text", "")).lower()
            ]

        history = self.usage_history[-20:] if include_history else []

        scored = []
        for r in matches:
            s = self._score_rubric(r, query, history)
            scored.append({
                "rubric_id": r.get("id", r.get("rubric_id", "")),
                "path": r.get("fullpath", r.get("text", "")),
                "text": r.get("text", ""),
                "score": round(s, 3),
                "preview": (r.get("fullpath", "") or r.get("text", ""))[:100],
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    def record_usage(self, rubric_text: str) -> None:
        """Record a rubric selection for ranking."""
        self.usage_history.append(rubric_text)

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 22,
            "feature_name": "Kent's Keynote Autocomplete",
            "cold_start_capable": True,
            "rubric_count": len(self.rubrics),
            "version": "1.0",
        }
