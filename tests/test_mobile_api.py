"""
Tests for Mobile-Responsive API Layer (Feature #27)
"""

import pytest
from oorep.mobile_api import MobileApi


class TestMobileApi:

    def test_construction(self):
        engine = MobileApi()
        assert engine is not None

    def test_process_returns_dict(self):
        engine = MobileApi()
        result = engine.process()
        assert isinstance(result, dict)
        assert result["status"] == "stub"
        assert result["feature_id"] == 27

    def test_process_with_mock_repertory(self):
        class MockRep:
            pass
        engine = MobileApi(MockRep())
        assert engine.rep is not None
