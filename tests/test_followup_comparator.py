"""
Tests for Follow-up Remedy Comparator (Feature #20)
"""

import pytest
from oorep.followup_comparator import FollowupComparator


class TestFollowupComparator:

    def test_construction(self):
        engine = FollowupComparator()
        assert engine is not None

    def test_process_returns_dict(self):
        engine = FollowupComparator()
        result = engine.process()
        assert isinstance(result, dict)
        assert result["status"] == "stub"
        assert result["feature_id"] == 20

    def test_process_with_mock_repertory(self):
        class MockRep:
            pass
        engine = FollowupComparator(MockRep())
        assert engine.rep is not None
