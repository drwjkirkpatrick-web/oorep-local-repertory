"""
Multi-Repertory Search — Feature #10

Search across multiple repertory corpora simultaneously with source tagging.
Load Kent, Boenninghausen, Boger, and private rubric sets;
search all in parallel; tag each result with its source corpus.

Usage:
    from oorep.multi_repertory import MultiRepertoryEngine

    engine = MultiRepertoryEngine({
        "kent": "data/kent_rubrics.json",
        "boenninghausen": "data/boenninghausen_rubrics.json",
    })

    results = engine.search_rubrics("anxiety evening")
    comparison = engine.compare_across_sources(12345)
    coverage = engine.get_coverage_by_source()
"""

import json
import re
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class MultiRepertoryEngine:
    """
    Multi-corpus repertory search with source tagging.
    """

    def __init__(self, corpora: Optional[Dict[str, str]] = None):
        """
        corpora: dict of {name: json_file_path}.
        """
        self.corpora: Dict[str, List[Dict[str, Any]]] = {}
        self.index: Dict[str, Dict[str, Dict]] = {}  # source -> rubric_id -> rubric

        if corpora:
            for name, path in corpora.items():
                self.load_corpus(name, path)

    def load_corpus(self, name: str, path: str) -> bool:
        """Load a single corpus. Returns True on success."""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return False

        # Normalize
        if isinstance(data, dict) and "rubrics" in data:
            rubrics = data["rubrics"]
        elif isinstance(data, list):
            rubrics = data
        elif isinstance(data, dict):
            # assume dict of rubric_id -> remedies
            rubrics = [
                {"id": rid, "fullpath": str(rid), "remedies": rems}
                for rid, rems in data.items()
            ]
        else:
            rubrics = []

        # Enrich with source
        for r in rubrics:
            r.setdefault("_source", name)

        self.corpora[name] = rubrics
        self.index[name] = {str(r.get("id", r.get("rubric_id", i))): r for i, r in enumerate(rubrics)}
        return True

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z]+", text.lower())

    def _matches(self, rubric: Dict, tokens: List[str]) -> int:
        """Count how many query tokens appear in fullpath or text."""
        haystack = " ".join([
            rubric.get("fullpath", ""),
            rubric.get("text", ""),
            " ".join(rubric.get("path_parts", [])),
        ]).lower()
        return sum(1 for t in tokens if t in haystack)

    # ── Search APIs ───────────────────────────────────────────────────────────

    def search_rubrics(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        top_n: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search across specified (or all) corpora.
        Returns list of {source, rubric_id, path, score, matched_tokens}.
        """
        tokens = self._tokenize(query)
        results = []
        srcs = sources or list(self.corpora.keys())

        for s in srcs:
            if s not in self.corpora:
                continue
            for rid, rubric in self.index.get(s, {}).items():
                m = self._matches(rubric, tokens)
                if m > 0:
                    results.append({
                        "source": s,
                        "rubric_id": rid,
                        "path": rubric.get("fullpath", "") or rubric.get("path", "") or rid,
                        "text": rubric.get("text", ""),
                        "matched_tokens": m,
                        "score": m,
                        "total_tokens": len(tokens),
                        "remedy_count": len(rubric.get("remedies", [])),
                    })

        results.sort(key=lambda x: (-x["score"], x["source"], x["rubric_id"]))
        return results[:top_n]

    def search_remedies(
        self,
        remedy: str,
        sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Find all rubrics containing a specific remedy across all sources."""
        results = []
        srcs = sources or list(self.corpora.keys())
        rem_up = remedy.upper().replace(".", "")

        for s in srcs:
            for rid, rubric in self.index.get(s, {}).items():
                rems = rubric.get("remedies", [])
                matched = []
                for r in rems:
                    abbrev = str(r.get("remedy", "")).upper().replace(".", "")
                    if abbrev == rem_up:
                        matched.append({
                            "remedy": r.get("remedy", ""),
                            "grade": r.get("grade", r.get("weight", 1)),
                        })
                if matched:
                    results.append({
                        "source": s,
                        "rubric_id": rid,
                        "path": rubric.get("fullpath", ""),
                        "text": rubric.get("text", ""),
                        "matches": matched,
                    })

        results.sort(key=lambda x: (-sum(m["grade"] for m in x["matches"]), x["source"]))
        return results

    # ── Comparison ──────────────────────────────────────────────────────────────────

    def compare_across_sources(
        self,
        rubric_id: str,
        sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Compare how a rubric is defined across different corpora."""
        srcs = sources or list(self.corpora.keys())
        matches = []
        for s in srcs:
            r = self.index.get(s, {}).get(str(rubric_id))
            if r:
                rems = r.get("remedies", [])
                # Normalize
                norm_rems = []
                for rem in rems:
                    norm_rems.append({
                        "remedy": rem.get("remedy", ""),
                        "grade": rem.get("grade", rem.get("weight", 1)),
                    })
                matches.append({
                    "source": s,
                    "rubric_id": rubric_id,
                    "path": r.get("fullpath", ""),
                    "text": r.get("text", ""),
                    "remedies": sorted(norm_rems, key=lambda x: x["remedy"]),
                    "remedy_count": len(norm_rems),
                })
        matches.sort(key=lambda x: x["source"])
        return matches

    def get_coverage_by_source(self) -> List[Dict[str, Any]]:
        """Per-source statistics."""
        stats = []
        for name, rubrics in self.corpora.items():
            total = len(rubrics)
            entries = sum(len(r.get("remedies", [])) for r in rubrics)
            unique_rems: Set[str] = set()
            for r in rubrics:
                for rem in r.get("remedies", []):
                    abbr = rem.get("remedy", "") if isinstance(rem, dict) else str(rem)
                    if abbr:
                        unique_rems.add(abbr.upper())
            stats.append({
                "source": name,
                "rubric_count": total,
                "remedy_entries": entries,
                "unique_remedies": len(unique_rems),
                "avg_remedies_per_rubric": round(entries / max(total, 1), 2),
            })
        stats.sort(key=lambda x: (-x["rubric_count"], x["source"]))
        return stats

    # ── Aggregate search ─────────────────────────────────────────────────────

    def search_all(
        self,
        queries: List[str],
        sources: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict]]:
        """
        Multi-query batch search.
        Returns {query: [results]}.
        """
        out = {}
        for q in queries:
            out[q] = self.search_rubrics(q, sources=sources, top_n=20)
        return out

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 10,
            "feature_name": "Multi-Repertory Search",
            "corpora_loaded": list(self.corpora.keys()),
            "cold_start_capable": True,
            "version": "1.0",
        }
