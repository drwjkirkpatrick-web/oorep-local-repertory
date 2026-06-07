"""Tests for reverse_repertorization.py"""
import pytest
from oorep.reverse_repertorization import ReverseRepertorization

@pytest.fixture
def rev():
    return ReverseRepertorization()

class TestReverseRepertorization:
    def test_query_returns_structure(self, rev):
        result = rev.query("PULS", top_n=5)
        assert "remedy" in result
        if "error" not in result:
            assert "by_chapter" in result
        else:
            assert result["error"] == "No rubric data"

    def test_grade_label(self, rev):
        assert rev._grade_label(3) == "bold"
        assert rev._grade_label(2) == "italic"
        assert rev._grade_label(1) == "regular"

    def test_compare_structure(self, rev):
        result = rev.compare_two_remedies("PULS", "SULPH")
        assert result["remedy_a"] == "PULS"
        assert result["remedy_b"] == "SULPH"
        assert "similarity" in result

    def test_compare_no_data(self, rev):
        result = rev.compare_two_remedies("UNKNOWN1", "UNKNOWN2")
        assert result["a_total"] == 0
        assert result["b_total"] == 0
