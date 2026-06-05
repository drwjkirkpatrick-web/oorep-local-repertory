"""
Tests for Multi-Repertory Search (Feature #10)

Covers: loading, search_rubrics, search_remedies, compare_across_sources,
coverage, aggregate search, missing source, edge cases.
"""

import json
import pytest
from pathlib import Path

from oorep.multi_repertory import MultiRepertoryEngine


@pytest.fixture
def corpus_files(tmp_path: Path):
    """Create two fake edition JSON files."""
    kent = tmp_path / "kent.json"
    boen = tmp_path / "boen.json"

    with open(kent, "w") as f:
        json.dump([
            {"id": 1, "fullpath": "Mind; Anxiety", "remedies": [
                {"remedy": "ARS", "grade": 3}, {"remedy": "PULS", "grade": 2}
            ]},
            {"id": 2, "fullpath": "Stomach; Thirst", "remedies": [
                {"remedy": "ARS", "grade": 3}, {"remedy": "LACH", "grade": 1}
            ]},
        ], f)

    with open(boen, "w") as f:
        json.dump([
            {"id": 1, "fullpath": "Mind; Anxiety", "remedies": [
                {"remedy": "ARS", "grade": 3}, {"remedy": "PULS", "grade": 1}
            ]},
            {"id": 3, "fullpath": "Head; Pain", "remedies": [
                {"remedy": "BELL", "grade": 3}
            ]},
        ], f)

    return {"kent": str(kent), "boen": str(boen)}


@pytest.fixture
def engine(corpus_files) -> MultiRepertoryEngine:
    return MultiRepertoryEngine(corpus_files)


class TestMultiRepertorySearch:

    def test_search_single_term(self, engine):
        results = engine.search_rubrics("anxiety")
        assert len(results) >= 2  # kent + boen
        sources = {r["source"] for r in results}
        assert "kent" in sources
        assert "boen" in sources

    def test_search_top_n(self, engine):
        results = engine.search_rubrics("anxiety", top_n=1)
        assert len(results) == 1

    def test_search_source_filter(self, engine):
        results = engine.search_rubrics("anxiety", sources=["kent"])
        assert len(results) == 1
        assert results[0]["source"] == "kent"

    def test_search_no_match(self, engine):
        results = engine.search_rubrics("zyxunknown")
        assert results == []

    def test_search_remedies(self, engine):
        results = engine.search_remedies("ARS")
        # Kent: ARS in 1 (Anxiety), 2 (Thirst). Boen: ARS in 1 (Anxiety)
        assert len(results) == 3
        ids = {r["rubric_id"] for r in results}
        assert "1" in ids
        assert "2" in ids

    def test_search_remedies_grade(self, engine):
        results = engine.search_remedies("ARS")
        for r in results:
            assert all(m["grade"] == 3 for m in r["matches"])

    def test_search_remedies_none(self, engine):
        results = engine.search_remedies("ZZZ")
        assert results == []

    def test_compare_across_sources(self, engine):
        comp = engine.compare_across_sources(1)
        assert len(comp) == 2
        sources = {c["source"] for c in comp}
        assert "kent" in sources
        assert "boen" in sources

    def test_compare_missing(self, engine):
        comp = engine.compare_across_sources(99)
        assert comp == []

    def test_coverage(self, engine):
        cov = engine.get_coverage_by_source()
        assert len(cov) == 2
        names = {c["source"] for c in cov}
        assert "kent" in names
        assert names == {"kent", "boen"}
        assert cov[0]["rubric_count"] >= 1
        assert cov[0]["remedy_entries"] > 0

    def test_search_all(self, engine):
        results = engine.search_all(["anxiety", "pain"])
        assert "anxiety" in results
        assert "pain" in results
        assert len(results["pain"]) >= 1

    def test_load_bad_json(self):
        e = MultiRepertoryEngine({"bad": "/tmp/nonexistent_file_123.json"})
        assert "bad" not in e.corpora

    def test_load_dict_format(self, tmp_path: Path):
        path = tmp_path / "dict_corpus.json"
        with open(path, "w") as f:
            json.dump({
                "rubrics": [
                    {"id": 100, "fullpath": "Mind; Anxiety", "remedies": [{"remedy": "ARS", "grade": 3}]}
                ]
            }, f)
        e = MultiRepertoryEngine({"dict_corp": str(path)})
        assert "dict_corp" in e.corpora
        assert len(e.corpora["dict_corp"]) == 1

    def test_search_empty_query(self, engine):
        results = engine.search_rubrics("")
        assert results == []

    def test_feature_overview(self, engine):
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 10
        assert "kent" in ov["corpora_loaded"]
