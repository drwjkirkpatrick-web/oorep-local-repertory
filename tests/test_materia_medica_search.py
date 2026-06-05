"""
Tests for Full-Text Materia Medica Search — Feature #11

Covers: TF-IDF search, remedy filtering, confirmation layer, highlighting.
"""

import pytest
from oorep.materia_medica_search import MateriaMedicaSearchEngine, TfIdfIndex


SAMPLE_DOCS = [
    {"remedy": "ARS", "text": "Anxiety with restlessness. Burning pains.", "author": "Kent", "section": "mind"},
    {"remedy": "PULS", "text": "Fear of death. Tearful anxiety.", "author": "Kent", "section": "mind"},
    {"remedy": "ARS", "text": "Burning in throat. Thirst for sips.", "author": "Kent", "section": "throat"},
    {"remedy": "NUX", "text": "Irritability. Over-sensitiveness.", "author": "Hahnemann", "section": "mind"},
]


@pytest.fixture
def populated_engine():
    idx = TfIdfIndex(docs=SAMPLE_DOCS)
    engine = MateriaMedicaSearchEngine.__new__(MateriaMedicaSearchEngine)
    engine.mm = None
    engine._index = idx
    return engine


class TestTfIdfIndex:

    def test_query_returns_results(self):
        idx = TfIdfIndex(docs=SAMPLE_DOCS)
        results = idx.query("anxiety", top_n=10)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_query_scores_positive(self):
        idx = TfIdfIndex(docs=SAMPLE_DOCS)
        results = idx.query("anxiety", top_n=10)
        assert all(r["score"] > 0 for r in results)

    def test_unknown_query_returns_empty(self):
        idx = TfIdfIndex(docs=SAMPLE_DOCS)
        results = idx.query("xyz_nonexistent")
        assert results == []

    def test_remedy_documents_filter(self):
        idx = TfIdfIndex(docs=SAMPLE_DOCS)
        doc_ids = idx.get_remedy_documents("ARS")
        assert len(doc_ids) == 2
        texts = [idx.get_doc(i)["text"] for i in doc_ids]
        assert any("Anxiety" in t for t in texts)


class TestMateriaMedicaSearchEngine:

    def test_search_returns_list(self, populated_engine):
        results = populated_engine.search("anxiety")
        assert isinstance(results, list)

    def test_search_has_highlights(self, populated_engine):
        results = populated_engine.search("anxiety", top_n=5)
        for r in results:
            assert isinstance(r["highlights"], list)

    def test_remedy_filter(self, populated_engine):
        results = populated_engine.search("burning", remedy_filter="ARS")
        assert all(r["remedy"].upper() == "ARS" for r in results)

    def test_confirm_repertorization(self, populated_engine):
        reps = [{"remedy": "ARS", "score": 20}]
        symptoms = ["anxiety"]
        result = populated_engine.confirm_repertorization(reps, symptoms)
        assert "confirmed" in result
        assert result["confirmed"][0]["remedy"] == "ARS"

    def test_confirm_repertorization_skip(self, populated_engine):
        result = populated_engine.confirm_repertorization([], ["anxiety"])
        assert result["skipped"] is True

    def test_confirm_repertorization_empty_symptoms(self, populated_engine):
        result = populated_engine.confirm_repertorization([{"remedy": "ARS", "score": 10}], [])
        assert result["skipped"] is True


class TestHighlight:

    def test_highlight_returns_snippets(self, populated_engine):
        text = "Anxiety. Restlessness. Fear of death."
        hl = populated_engine._highlight(text, "anxiety")
        assert isinstance(hl, list)
        assert any("Anxiety" in h for h in hl)


class TestFeatureOverview:

    def test_overview(self, populated_engine):
        ov = populated_engine.get_feature_overview()
        assert ov["feature_id"] == 11
        assert ov["feature_name"] == "Full-Text Materia Medica Search"
        assert ov["indexing"] == "TF-IDF"
