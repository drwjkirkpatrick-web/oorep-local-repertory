"""
Tests for Full-Text Materia Medica Search (Feature #11)
"""

import pytest
from oorep.materia_medica_search import MateriaMedicaSearch


class TestMateriaMedicaSearch:

    def test_construction(self):
        engine = MateriaMedicaSearch()
        assert engine is not None

    def test_process_returns_dict(self):
        engine = MateriaMedicaSearch()
        result = engine.process()
        assert isinstance(result, dict)
        assert result["status"] == "stub"
        assert result["feature_id"] == 11

    def test_process_with_mock_repertory(self):
        class MockRep:
            pass
        engine = MateriaMedicaSearch(MockRep())
        assert engine.rep is not None
