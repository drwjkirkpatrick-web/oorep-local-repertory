"""Tests for case_similarity_search.py"""
import pytest
from oorep.case_similarity_search import CaseSimilaritySearch

@pytest.fixture
def css(tmp_path):
    return CaseSimilaritySearch(data_dir=str(tmp_path))

class TestCaseSimilarity:
    def test_index_and_find(self, css):
        css.index_case("case_1", [1, 2, 3, 4, 5], "PULS", "cured")
        css.index_case("case_2", [1, 2, 3, 10, 11], "SULPH", "improved")
        similar = css.find_similar([1, 2, 3, 99], top_n=5)
        assert len(similar) >= 1

    def test_what_worked(self, css):
        css.index_case("case_1", [1, 2], "PULS", "cured")
        css.index_case("case_2", [1, 3], "PULS", "cured")
        css.index_case("case_3", [2, 3], "SULPH", "cured")
        worked = css.get_what_worked([1, 2, 3], outcome_filter="cured")
        assert len(worked) >= 1
        assert worked[0]["remedy"] == "PULS"

    def test_practice_stats(self, css):
        css.index_case("c1", [1], "A", "cured")
        stats = css.get_practice_stats()
        assert stats["total_cases"] == 1
