"""
Tests for Miasm Tracking (Feature #24)

Covers: classification, suggestion, progression, affinity.
"""

import pytest
from oorep.miasm_tracking import MiasmTracker


class TestClassification:

    def test_psora_hints(self):
        tracker = MiasmTracker()
        scores = tracker.classify_symptoms(["itching all over", "dry skin"])
        assert "psora" in scores
        assert scores["psora"] > 0

    def test_psora_vs_sycosis(self):
        tracker = MiasmTracker()
        scores = tracker.classify_symptoms(["warts", "condylomata", "itching"])
        # Warts/condylomata → sycosis score should be higher
        assert scores["sycosis"] >= scores["psora"]

    def test_patient_classify(self):
        tracker = MiasmTracker()
        result = tracker.classify_patient(["warts", "overproduction"])
        assert result["primary"] == "sycosis"
        assert result["symptoms_analyzed"] == 2
        assert 90 <= result["primary_percentage"] <= 100

    def test_known_miasm_preserved(self):
        tracker = MiasmTracker()
        result = tracker.classify_patient(["itching"], known_miasm="psora")
        assert result["known_miasm"] == "psora"


class TestSuggestions:

    def test_suggest_psora(self):
        tracker = MiasmTracker()
        remedies = tracker.suggest_remedies("psora")
        assert len(remedies) > 0
        assert any(r["remedy"] == "SULPH" for r in remedies)

    def test_suggest_unknown(self):
        tracker = MiasmTracker()
        remedies = tracker.suggest_remedies("fictional")
        assert remedies == []


class TestAffinity:

    def test_sulph_affinity(self):
        tracker = MiasmTracker()
        aff = tracker.remedy_miasm_affinity("SULPH")
        assert "psora" in aff

    def test_unknown_remedy(self):
        tracker = MiasmTracker()
        aff = tracker.remedy_miasm_affinity("ZZZ")
        assert aff == []


class TestTimeline:

    def test_track_progression(self):
        tracker = MiasmTracker()
        history = [
            {"date": "2024-01", "symptoms": ["itching"], "known_miasm": "psora"},
            {"date": "2024-03", "symptoms": ["warts"], "known_miasm": "sycosis"},
            {"date": "2024-06", "symptoms": ["ulceration"], "known_miasm": "syphilis"},
        ]
        timeline = tracker.track_over_time("X", history)
        assert len(timeline) == 3
        assert timeline[1]["delta"]["shift"] == "psora -> sycosis"
        assert timeline[2]["delta"]["shift"] == "sycosis -> syphilis"


class TestOverview:

    def test_overview(self):
        tracker = MiasmTracker()
        ov = tracker.get_feature_overview()
        assert ov["feature_id"] == 24
        assert "anti_miasmatic_count" in ov
