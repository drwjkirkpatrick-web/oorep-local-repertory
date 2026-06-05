"""
Tests for Kent's Keynote Autocomplete (Feature #22)
"""

import pytest
from oorep.keynote_autocomplete import KeynoteAutocomplete


class TestKeynoteAutocomplete:

    def test_construction(self):
        engine = KeynoteAutocomplete()
        assert engine is not None

    def test_process_returns_dict(self):
        engine = KeynoteAutocomplete()
        result = engine.process()
        assert isinstance(result, dict)
        assert result["status"] == "stub"
        assert result["feature_id"] == 22

    def test_process_with_mock_repertory(self):
        class MockRep:
            pass
        engine = KeynoteAutocomplete(MockRep())
        assert engine.rep is not None
