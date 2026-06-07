"""Tests for posology_scheduler.py"""
import pytest
from oorep.posology_scheduler import PosologyScheduler

@pytest.fixture
def ps():
    return PosologyScheduler()

class TestPosology:
    def test_acute_recommendation(self, ps):
        r = ps.recommend("acute", "average")
        assert r["recommended_potency"] == "30C"
        assert "max_doses" in r

    def test_chronic_recommendation(self, ps):
        r = ps.recommend("chronic", "average", previous_potency="30C", outcome="no_change")
        assert "recommended_potency" in r

    def test_lm_recommendation(self, ps):
        r = ps.recommend("LM_series", previous_potency="")
        assert r["recommended_potency"] == "LM1"

    def test_validate_prescription(self, ps):
        v = ps.validate_prescription("PULS", "30C", "acute")
        assert v["valid"] is True

    def test_potency_ladder(self, ps):
        ladder = ps.potency_ladder("centesimal")
        assert "30C" in ladder
        assert "200C" in ladder
