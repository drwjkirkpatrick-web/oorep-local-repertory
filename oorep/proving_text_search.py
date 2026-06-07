"""
Proving Text Search — Full Materia Medica Text Search

Search inside proving texts, not just rubric headings.
"Where does Hahnemann describe fear of dogs?" → finds proving text.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProvingTextSearch:
    """
    Full-text search over materia medica / proving texts.
    Currently a scaffold — requires proving text corpus.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.corpus_path = self.data_dir / "proving_texts.json"
        self.index_path = self.data_dir / "proving_text_index.json"
        self._corpus: Dict[str, Any] = {}
        self._index: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self):
        if self.corpus_path.exists():
            with open(self.corpus_path, "r", encoding="utf-8") as f:
                self._corpus = json.load(f)
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                self._index = json.load(f)

    def search(self, query: str, author: Optional[str] = None,
               remedy: Optional[str] = None, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Search proving texts for a phrase.
        """
        if not self._corpus:
            return [{"note": "No proving text corpus loaded. This is a scaffold.", "query": query}]

        query_lower = query.lower()
        results = []
        for remedy_name, sections in self._corpus.items():
            if remedy and remedy != remedy_name:
                continue
            for section in sections:
                text = section.get("text", "").lower()
                if query_lower in text:
                    results.append({
                        "remedy": remedy_name,
                        "author": section.get("author", "unknown"),
                        "section": section.get("section", ""),
                        "text_preview": section.get("text", "")[:300] + "...",
                        "relevance": text.count(query_lower),
                    })

        results.sort(key=lambda x: -x["relevance"])
        return results[:top_n]

    def index_corpus(self, corpus: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Index a proving text corpus for fast search."""
        self._corpus = corpus
        # Build inverted index: word → [{remedy, section_idx}]
        index: Dict[str, List[Dict[str, Any]]] = {}
        for remedy, sections in corpus.items():
            for i, section in enumerate(sections):
                text = section.get("text", "").lower()
                words = set(text.split())
                for word in words:
                    if len(word) > 3:
                        index.setdefault(word, []).append({"remedy": remedy, "section": i})

        self._index = index
        with open(self.corpus_path, "w", encoding="utf-8") as f:
            json.dump(corpus, f, indent=2)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

        return {"n_remedies": len(corpus), "n_indexed_words": len(index)}

    def get_remedy_texts(self, remedy: str) -> List[Dict[str, Any]]:
        return self._corpus.get(remedy, [])

    def get_corpus_stats(self) -> Dict[str, Any]:
        if not self._corpus:
            return {"note": "No corpus loaded"}
        total_sections = sum(len(s) for s in self._corpus.values())
        authors = set()
        for sections in self._corpus.values():
            for s in sections:
                authors.add(s.get("author", "unknown"))
        return {
            "n_remedies": len(self._corpus),
            "total_sections": total_sections,
            "authors": sorted(authors),
            "index_size": len(self._index),
        }
