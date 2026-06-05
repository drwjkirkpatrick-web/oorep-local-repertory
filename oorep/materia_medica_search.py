"""
Full-Text Materia Medica Search — Feature #11

Extends existing materia_medica.py with TF-IDF indexing and repertory integration.
Search across remedy proving texts by symptom description;
return ranked remedy excerpts with highlighting.
Acts as secondary confirmation layer after repertorization.

Usage:
    from oorep.materia_medica_search import MateriaMedicaSearchEngine

    engine = MateriaMedicaSearchEngine(materia_medica=MateriaMedica())

    # Direct MM search
    hits = engine.search("burning anxiety", top_n=10)

    # Secondary confirmation of repertorization results
    confirmed = engine.confirm_repertorization(
        repertorization_results=[{"remedy": "Ars.", "score": 28}],
        symptom_set=["burning anxiety", "restless"],
    )
"""

import math
import re
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

import logging

LOG = logging.getLogger(__name__)


try:
    from .materia_medica import MateriaMedica
except Exception:
    from materia_medica import MateriaMedica


# ──────────────────────────────────────────────────────────────────────────────
# TF-IDF Index
# ──────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Simple word tokenization."""
    return re.findall(r"[a-z]+", text.lower())


class TfIdfIndex:
    """In-memory TF-IDF index over proving texts."""

    def __init__(self, docs: Optional[List[Dict[str, Any]]] = None):
        # docs: [{"remedy": "Ars.", "text": "...", "section": "mind", "author": "Kent", ...}, ...]
        self._docs: List[Dict[str, Any]] = docs or []
        self._tokens: List[List[str]] = []
        self._df: Dict[str, int] = {}  # document frequency
        self._doc_tf: List[Dict[str, int]] = []
        self._idf: Dict[str, float] = {}
        self._remedy_to_doc_ids: Dict[str, Set[int]] = defaultdict(set)
        self._built = False

    def add_document(self, doc: Dict[str, Any]) -> None:
        self._docs.append(doc)
        self._built = False

    def _build(self) -> None:
        if self._built:
            return
        self._tokens = []
        self._df = {}
        self._doc_tf = []
        self._remedy_to_doc_ids = defaultdict(set)

        for i, doc in enumerate(self._docs):
            text = doc.get("text", "") + " " + doc.get("section", "") + " " + doc.get("author", "")
            tokens = _tokenize(text)
            self._tokens.append(tokens)
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self._doc_tf.append(tf)
            for t in set(tokens):
                self._df[t] = self._df.get(t, 0) + 1
            rem = doc.get("remedy", "").upper()
            if rem:
                self._remedy_to_doc_ids[rem].add(i)

        N = max(len(self._docs), 1)
        self._idf = {t: math.log(N / (df + 1)) + 1 for t, df in self._df.items()}
        self._built = True

    def score_document(self, doc_id: int, query_tokens: List[str]) -> float:
        """TF-IDF score for a single document against query tokens."""
        self._build()
        if doc_id < 0 or doc_id >= len(self._tokens):
            return 0.0
        tf = self._doc_tf[doc_id]
        s = sum(
            tf.get(t, 0) * self._idf.get(t, 1.0)
            for t in query_tokens
        )
        # Normalize by doc length
        doc_len = len(self._tokens[doc_id])
        if doc_len > 0:
            s = s / math.sqrt(doc_len)
        return s

    def query(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Query the index. Returns list of {doc_index, score}."""
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        self._build()
        scored = []
        for i in range(len(self._docs)):
            s = self.score_document(i, query_tokens)
            if s > 0:
                scored.append({"doc_index": i, "score": round(s, 4)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    def get_doc(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self._docs):
            return self._docs[index]
        return None

    def get_remedy_documents(self, remedy: str) -> List[int]:
        self._build()
        return sorted(self._remedy_to_doc_ids.get(remedy.upper(), set()))


# ──────────────────────────────────────────────────────────────────────────────
# MateriaMedicaSearchEngine
# ──────────────────────────────────────────────────────────────────────────────

class MateriaMedicaSearchEngine:
    """
    Advanced materia medica search with TF-IDF ranking,
    highlighting, and repertory confirmation layer.
    """

    def __init__(self, materia_medica: Optional[MateriaMedica] = None):
        self.mm = materia_medica or MateriaMedica()
        self._index: Optional[TfIdfIndex] = None
        self._init_index()

    def _init_index(self) -> None:
        """Build TF-IDF index from all materia medica entries."""
        try:
            docs = self.mm.list_remedies()
        except Exception:
            docs = []
        self._index = TfIdfIndex()
        for entry in docs:
            # entry: {remedy_abbrev, text, author, section}
            self._index.add_document(entry)

    # ── Public API ──────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_n: int = 10,
        remedy_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        TF-IDF search over proving texts.
        Returns: [{remedy: str, text: str, author: str, section: str,
                    score: float, highlights: [str]}, ...]
        """
        if self._index is None:
            return []

        self._index._build()

        # If remedy_filter is set, only search that remedy's documents
        if remedy_filter:
            doc_ids = self._index.get_remedy_documents(remedy_filter)
            query_tokens = _tokenize(query)
            scored = []
            for i in doc_ids:
                s = self._index.score_document(i, query_tokens)
                if s > 0:
                    scored.append({"doc_index": i, "score": round(s, 4)})
            scored.sort(key=lambda x: x["score"], reverse=True)
        else:
            scored = self._index.query(query, top_n)

        results = []
        for item in scored[:top_n]:
            doc = self._index.get_doc(item["doc_index"])
            if doc is None:
                continue
            highlighted = self._highlight(doc.get("text", ""), query)
            results.append({
                "remedy": doc.get("remedy", ""),
                "text": doc.get("text", ""),
                "author": doc.get("author", ""),
                "section": doc.get("section", ""),
                "score": item["score"],
                "highlights": highlighted,
                "text_length": len(doc.get("text", "")),
            })

        return results

    def _highlight(self, text: str, query: str) -> List[str]:
        """Return snippets with matched words emphasized."""
        query_tokens = set(_tokenize(query))
        sentences = re.split(r"(?&lt;=[.!?])\\s+", text)
        snippets = []
        for s in sentences:
            st = s.strip()
            if not st:
                continue
            tokens = set(_tokenize(st))
            if tokens & query_tokens:
                snippets.append(st[:160] + ("..." if len(st) > 160 else ""))
        snippets.sort(key=lambda x: sum(1 for t in query_tokens if t in x.lower()), reverse=True)
        return snippets[:3]

    def get_remedy_text(
        self,
        remedy_abbrev: str,
        author: Optional[str] = None,
        section: Optional[str] = None,
    ) -> Optional[str]:
        try:
            entries = self.mm.get_proving_text(remedy_abbrev, author=author, section=section)
            if isinstance(entries, list):
                text = "; ".join(e.get("text", "") for e in entries)
            else:
                text = entries
        except Exception:
            text = None
        return text

    def confirm_repertorization(
        self,
        repertorization_results: List[Dict[str, Any]],
        symptom_set: List[str],
        top_mm_hits: int = 3,
    ) -> Dict[str, Any]:
        """
        Secondary confirmation layer.
        Re-queries materia medica for each symptom against top-N remedies.
        Returns confirmation scoring that boosts remedies with strong MM support.
        """
        if not repertorization_results or not symptom_set:
            return {"confirmed": [], "skipped": True}

        confirmations = []
        for rep in repertorization_results[:5]:
            remedy = rep.get("remedy", "")
            rep_score = rep.get("score", 0.0)

            # Search MM for each symptom
            mm_scores = []
            for sym in symptom_set:
                hits = self.search(sym, top_n=top_mm_hits, remedy_filter=remedy)
                if hits:
                    mm_scores.append(max(h["score"] for h in hits))

            avg_mm_score = sum(mm_scores) / max(len(mm_scores), 1) if mm_scores else 0.0
            boosted_score = rep_score * (1.0 + 0.2 * avg_mm_score)

            confirmations.append({
                "remedy": remedy,
                "original_score": rep_score,
                "mm_support_avg": round(avg_mm_score, 4),
                "boosted_score": round(boosted_score, 4),
                "highlights": mm_scores,
            })

        confirmations.sort(key=lambda x: x["boosted_score"], reverse=True)
        return {
            "confirmed": confirmations,
            "symptom_set": symptom_set,
            "method": "TF-IDF confirmation layer",
        }

    def search_rubrics_with_fallback(
        self,
        query: str,
        repertory_engine: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search MM first; if no results, fall back to rubric search.
        """
        mm_results = self.search(query, top_n=10)
        if mm_results or repertory_engine is None:
            return mm_results
        try:
            rubric_results = repertory_engine.search_rubrics(query)
        except Exception:
            rubric_results = []
        return [
            {"remedy": r.get("remedy", ""), "text": r.get("text", ""),
             "author": "rubric", "section": "rubric_fallback", "score": 0.0,
             "highlights": [], "fallback": True}
            for r in rubric_results[:10]
        ]

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 11,
            "feature_name": "Full-Text Materia Medica Search",
            "indexing": "TF-IDF",
            "cold_start_capable": True,
            "integration": ["materia_medica.py", "repertorization confirmation"],
            "version": "1.0",
        }
