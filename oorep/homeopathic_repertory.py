"""
Homeopathic Repertory (OOREP)
Local searchable repertory based on OOREP data.

Usage:
    from homeopathic_repertory import HomeopathicRepertory

    rep = HomeopathicRepertory()

    # Search rubrics by symptom (lexical)
    results = rep.search_rubrics("headache morning")

    # Hybrid search (lexical + vector retrieval)
    results = rep.search_rubrics_hybrid("headache morning")

    # Get remedies for a rubric
    remedies = rep.get_remedies_for_rubric(rubric_id=12345)

    # Search remedies by name
    remedies = rep.search_remedies("arsenic")

    # Repertorization (multi-symptom analysis)
    results = rep.repertorize(["head pain morning", "thirst small quantities"])
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

try:
    from .oorep_vector_search import OORepVectorSearch
except Exception:
    try:
        from oorep_vector_search import OORepVectorSearch
    except Exception:
        OORepVectorSearch = None


class HomeopathicRepertory:
    """Local searchable homeopathic repertory."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the repertory.

        Args:
            data_dir: Path to data directory. Defaults to same directory as this file.
        """
        if data_dir is None:
            # Grouped project layout: references/oorep/*.py + references/data/*.json.
            data_dir = Path(__file__).resolve().parent.parent / "data"
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir

        # Load remedies (small file, load into memory)
        with open(data_dir / "remedies.json", "r", encoding="utf-8") as f:
            self.remedies = {r["id"]: r for r in json.load(f)}

        with open(data_dir / "remedies_by_abbrev.json", "r", encoding="utf-8") as f:
            self.remedies_by_abbrev = json.load(f)

        # Load search index
        with open(data_dir / "rubric_search_index.json", "r", encoding="utf-8") as f:
            self.search_index = json.load(f)

        with open(data_dir / "rubrics.json", "r", encoding="utf-8") as f:
            rubrics_list = json.load(f)
            # OOREP has duplicate numeric rubric IDs across sources (e.g. publicum/kent-de).
            # Keep the full list count for stats, while retaining the legacy id->rubric map
            # for remedy lookup compatibility.
            self.rubrics_list = rubrics_list
            self.rubrics = {r["id"]: r for r in rubrics_list}

        with open(data_dir / "rubric_to_remedies.json", "r", encoding="utf-8") as f:
            self.rubric_to_remedies = json.load(f)

        # Convert string keys back to integers
        self.rubric_to_remedies = {int(k): v for k, v in self.rubric_to_remedies.items()}

        self._rubric_count = len(self.rubrics_list)
        self._remedy_count = len(self.remedies)

        # Optional vector search backend
        self._vector = None
        if OORepVectorSearch is not None:
            try:
                self._vector = OORepVectorSearch(str(self.data_dir))
            except Exception:
                self._vector = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w.lower() for w in (text or "").split() if len(w) > 2]

    @staticmethod
    def _normalize_scores(score_map: Dict[int, float]) -> Dict[int, float]:
        if not score_map:
            return {}
        values = list(score_map.values())
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            return {k: 1.0 for k in score_map.keys()}
        span = max_v - min_v
        return {k: (v - min_v) / span for k, v in score_map.items()}

    def get_stats(self) -> Dict:
        """Return repertory statistics."""
        total_links = sum(len(rems) for rems in self.rubric_to_remedies.values())
        return {
            "remedies": self._remedy_count,
            "rubrics": self._rubric_count,
            "remedy_rubric_links": total_links,
        }

    def search_remedies(self, query: str, limit: int = 20) -> List[Dict]:
        """Search remedies by name or abbreviation."""
        query = query.lower()
        results = []

        for remedy in self.remedies.values():
            name = remedy.get("name", "").lower()
            abbrev = remedy.get("abbrev", "").lower()

            if query in name or query in abbrev:
                results.append(remedy)
                if len(results) >= limit:
                    break

        return results

    def get_remedy_by_abbrev(self, abbrev: str) -> Optional[Dict]:
        """Get remedy by abbreviation (e.g., 'Ars.' or 'Arsenicum')."""
        return self.remedies_by_abbrev.get(abbrev)

    def get_remedy_by_id(self, remedy_id: int) -> Optional[Dict]:
        """Get remedy by ID."""
        return self.remedies.get(remedy_id)

    def _search_rubrics_lexical(self, query: str, limit: int = 50) -> List[Dict]:
        query_words = self._tokenize(query)
        if not query_words:
            return []

        rubric_scores = defaultdict(float)

        for word in query_words:
            if word in self.search_index:
                for rubric_id in self.search_index[word]:
                    rubric_scores[rubric_id] += 1.0

            # Partial matches
            for idx_word, idx_ids in self.search_index.items():
                if word in idx_word or idx_word in word:
                    for rubric_id in idx_ids:
                        rubric_scores[rubric_id] += 0.5

        sorted_results = sorted(rubric_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for rubric_id, score in sorted_results[:limit]:
            if rubric_id in self.rubrics:
                rubric = self.rubrics[rubric_id].copy()
                rubric["_match_score"] = score
                results.append(rubric)

        return results

    def search_rubrics(self, query: str, limit: int = 50) -> List[Dict]:
        """Backwards-compatible lexical rubric search."""
        return self._search_rubrics_lexical(query=query, limit=limit)

    def build_vector_index(self, source: Optional[str] = None, dim: int = 384, dtype: str = "float16") -> Dict:
        """Build local vector index for rubric semantic search.

        Args:
            source: Optional source filter. Use None or "" for all OOREP rubrics.
            dim: Vector dimensions.
            dtype: Stored matrix dtype.
        """
        if self._vector is None:
            raise RuntimeError("Vector backend not available")
        return self._vector.build_index(source_filter=source or None, dim=dim, dtype=dtype)

    def search_rubrics_vector(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search rubrics using local vector similarity.

        Returns rubric dictionaries with `id`, metadata, and `_vector_score`.
        """
        if self._vector is None:
            return []

        try:
            raw = self._vector.search(query, top_k=limit)
        except FileNotFoundError:
            self._vector.build_index(source_filter="publicum", dim=384, dtype="float16")
            raw = self._vector.search(query, top_k=limit)

        out: List[Dict] = []
        for row in raw:
            rubric_id = int(row.get("rubric_id"))
            # Use the vector row's own fullpath/source. Numeric rubric IDs collide
            # between OOREP sources, so looking up by id alone can silently swap
            # the matched rubric text/source.
            legacy = self.rubrics.get(rubric_id, {})
            item = legacy.copy()
            item["id"] = rubric_id
            item["fullpath"] = row.get("fullpath") or legacy.get("fullpath")
            item["source"] = row.get("source") or legacy.get("source")
            item["_vector_score"] = float(row.get("score", 0.0))
            out.append(item)
        return out

    def search_rubrics_hybrid(
        self,
        query: str,
        limit: int = 50,
        lexical_k: int = 200,
        vector_k: int = 200,
        lexical_weight: float = 0.35,
        vector_weight: float = 0.55,
        overlap_weight: float = 0.10,
    ) -> List[Dict]:
        """
        Hybrid retrieval (lexical + vector + token overlap).

        Important: this only ranks rubric candidates. It does NOT alter remedy grades.
        """
        query_tokens = set(self._tokenize(query))
        lexical = self._search_rubrics_lexical(query, limit=max(limit, lexical_k))
        vector = self.search_rubrics_vector(query, limit=max(limit, vector_k))

        by_id: Dict[int, Dict] = {}
        lexical_scores: Dict[int, float] = {}
        vector_scores: Dict[int, float] = {}

        for r in lexical:
            rid = int(r["id"])
            by_id[rid] = r
            lexical_scores[rid] = float(r.get("_match_score", 0.0))

        for r in vector:
            rid = int(r["id"])
            by_id[rid] = by_id.get(rid, r)
            vector_scores[rid] = float(r.get("_vector_score", 0.0))

        # If vector is unavailable for this query, avoid penalizing lexical-only ranking.
        if not vector_scores:
            lexical_weight = 0.90
            vector_weight = 0.0
            overlap_weight = 0.10

        norm_lex = self._normalize_scores(lexical_scores)
        norm_vec = self._normalize_scores(vector_scores)

        scored: List[Dict] = []
        for rid, rubric in by_id.items():
            fullpath_tokens = set(self._tokenize(rubric.get("fullpath", "")))
            overlap = (len(query_tokens & fullpath_tokens) / len(query_tokens)) if query_tokens else 0.0

            l = norm_lex.get(rid, 0.0)
            v = norm_vec.get(rid, 0.0)
            h = (lexical_weight * l) + (vector_weight * v) + (overlap_weight * overlap)

            item = rubric.copy()
            item["_lexical_score"] = l
            item["_vector_score"] = v
            item["_overlap_score"] = overlap
            item["_hybrid_score"] = h
            scored.append(item)

        scored.sort(key=lambda x: x.get("_hybrid_score", 0.0), reverse=True)
        return scored[:limit]

    def get_rubric_by_id(self, rubric_id: int) -> Optional[Dict]:
        """Get rubric by ID."""
        return self.rubrics.get(rubric_id)

    def get_remedies_for_rubric(self, rubric_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Get all remedies with grades for a specific rubric."""
        links = self.rubric_to_remedies.get(rubric_id, [])

        results = []
        for link in links:
            remedy_id = link.get("remedy_id")
            weight = link.get("weight", 1)

            remedy = self.remedies.get(remedy_id)
            if remedy:
                results.append(
                    {
                        "remedy_id": remedy_id,
                        "abbrev": remedy.get("abbrev"),
                        "name": remedy.get("name"),
                        "weight": weight,
                    }
                )

        results.sort(key=lambda x: x["weight"], reverse=True)
        if limit:
            results = results[:limit]
        return results

    def get_rubrics_for_remedy(self, remedy_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Get all rubrics associated with a specific remedy."""
        results = []

        for rubric_id, links in self.rubric_to_remedies.items():
            for link in links:
                if link.get("remedy_id") == remedy_id:
                    rubric = self.rubrics.get(rubric_id)
                    if rubric:
                        results.append(
                            {
                                "rubric_id": rubric_id,
                                "fullpath": rubric.get("fullpath"),
                                "source": rubric.get("source"),
                                "weight": link.get("weight", 1),
                            }
                        )
                    break

        results.sort(key=lambda x: x["weight"], reverse=True)
        if limit:
            results = results[:limit]
        return results

    def _retrieve_rubrics(self, symptom: str, retrieval: str = "hybrid", rubrics_per_symptom: int = 10) -> List[Dict]:
        mode = (retrieval or "hybrid").strip().lower()
        if mode == "lexical":
            return self.search_rubrics(symptom, limit=rubrics_per_symptom)
        if mode == "vector":
            return self.search_rubrics_vector(symptom, limit=rubrics_per_symptom)
        return self.search_rubrics_hybrid(symptom, limit=rubrics_per_symptom)

    def repertorize(
        self,
        symptoms: List[str],
        top_n: int = 20,
        retrieval: str = "hybrid",
        rubrics_per_symptom: int = 10,
        use_clinical_mapper: bool = True,
    ) -> List[Dict]:
        """
        Perform repertorization with classical grade-based scoring.

        By default, case symptoms are routed through ClinicalRubricMapper first:
        patient-friendly language is normalized/expanded, no-remedy rubrics are
        filtered out, and candidate rubrics remain reviewable. Set
        use_clinical_mapper=False only for legacy/direct repertory behavior.

        Retrieval strategy picks rubric candidates. Final remedy score is strictly
        the sum of classical remedy grades across selected rubrics.
        """
        remedy_scores = defaultdict(lambda: {"score": 0, "matches": [], "_rubric_ids": set()})

        mapper = None
        if use_clinical_mapper:
            try:
                try:
                    from .clinical_rubric_mapper import ClinicalRubricMapper
                except Exception:
                    from clinical_rubric_mapper import ClinicalRubricMapper

                mapper = ClinicalRubricMapper(self)
            except Exception:
                mapper = None

        for symptom in symptoms:
            if mapper is not None:
                candidates = mapper.suggest_candidates(
                    symptom,
                    limit=rubrics_per_symptom,
                    retrieval=retrieval,
                    require_remedies=True,
                )
                rubrics = [
                    {
                        "id": c["rubric_id"],
                        "fullpath": c.get("rubric"),
                        "source": c.get("source"),
                        "query_expanded": c.get("query_expanded"),
                        "review_status": c.get("review_status"),
                        "retrieval_score": c.get("retrieval_score"),
                    }
                    for c in candidates
                ]
            else:
                rubrics = self._retrieve_rubrics(
                    symptom,
                    retrieval=retrieval,
                    rubrics_per_symptom=rubrics_per_symptom,
                )

            seen_rubrics = set()
            for rubric in rubrics:
                rubric_id = int(rubric["id"])
                if rubric_id in seen_rubrics:
                    continue
                seen_rubrics.add(rubric_id)

                remedies = self.get_remedies_for_rubric(rubric_id)
                scored_remedies_for_rubric = set()
                for rem in remedies:
                    abbrev = rem["abbrev"]
                    if abbrev in scored_remedies_for_rubric:
                        continue
                    scored_remedies_for_rubric.add(abbrev)
                    weight = rem["weight"]

                    # Classical repertory logic preserved here:
                    # remedy grade drives the score; retrieval score is not multiplied in.
                    remedy_scores[abbrev]["score"] += weight
                    remedy_scores[abbrev]["remedy_name"] = rem["name"]
                    remedy_scores[abbrev]["_rubric_ids"].add(rubric_id)
                    remedy_scores[abbrev]["matches"].append(
                        {
                            "query_symptom": symptom,
                            "query_expanded": rubric.get("query_expanded"),
                            "rubric_id": rubric_id,
                            "rubric": rubric.get("fullpath"),
                            "source": rubric.get("source"),
                            "review_status": rubric.get("review_status"),
                            "weight": weight,
                        }
                    )

        sorted_results = sorted(remedy_scores.items(), key=lambda x: x[1]["score"], reverse=True)

        results = []
        for abbrev, data in sorted_results[:top_n]:
            results.append(
                {
                    "abbrev": abbrev,
                    "name": data["remedy_name"],
                    "score": data["score"],
                    "match_count": len(data["_rubric_ids"]),
                    "matches": data["matches"][:5],
                }
            )

        return results


# Convenience function for quick lookup
def quick_search(symptom: str, limit: int = 10) -> List[Dict]:
    """Quick lexical search for rubrics matching a symptom."""
    rep = HomeopathicRepertory()
    return rep.search_rubrics(symptom, limit=limit)


if __name__ == "__main__":
    print("Loading repertory...")
    rep = HomeopathicRepertory()

    stats = rep.get_stats()
    print("\nRepertory loaded:")
    print(f"  Remedies: {stats['remedies']:,}")
    print(f"  Rubrics: {stats['rubrics']:,}")
    print(f"  Links: {stats['remedy_rubric_links']:,}")

    print("\n\nTest: Search remedies 'arsenic':")
    for r in rep.search_remedies("arsenic", limit=5):
        print(f"  {r['abbrev']}: {r['name']}")

    print("\n\nTest: Hybrid rubric search 'headache morning':")
    for r in rep.search_rubrics_hybrid("headache morning", limit=5):
        print(f"  {r['fullpath']}  [hybrid={r.get('_hybrid_score', 0):.3f}]")

    print("\n\nTest: Repertorization 'fever, thirst' (hybrid retrieval, classical grades):")
    for r in rep.repertorize(["fever", "thirst"], top_n=5, retrieval="hybrid"):
        print(f"  {r['abbrev']} ({r['name']}): score {r['score']}")
