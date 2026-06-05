"""
Tests for Pluggable Analysis Methods (Feature #13)
"""

import pytest
from oorep.analysis_methods import AnalysisMethods


class TestAnalysisMethods:

    def test_construction(self):
        engine = AnalysisMethods()
        assert engine is not None

    def test_process_returns_dict(self):
        engine = AnalysisMethods()
        result = engine.process()
        assert isinstance(result, dict)
        assert result["status"] == "stub"
        assert result["feature_id"] == 13

    def test_process_with_mock_repertory(self):
        class MockRep:
            pass
        engine = AnalysisMethods(MockRep())
        assert engine.rep is not None
