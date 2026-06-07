"""Tests for duplicate_remedy_detector.py"""
import pytest
from oorep.duplicate_remedy_detector import DuplicateRemedyDetector

@pytest.fixture
def detector(tmp_path):
    return DuplicateRemedyDetector(db_path=str(tmp_path / "remedy_relationships.db"))

class TestDuplicateDetector:
    def test_add_and_history(self, detector):
        detector.add_prescription("case_1", "PULS", "30C", "2026-01-01")
        hist = detector.get_prescription_history("case_1")
        assert len(hist) == 1
        assert hist[0]["remedy"] == "PULS"

    def test_antidote_warning(self, detector):
        detector.add_prescription("case_1", "NUX-V", "30C", "2026-01-01")
        check = detector.check_interactions("case_1", "PULS")
        assert check["safe"] is False
        assert any(w["type"] == "antidote" for w in check["warnings"])

    def test_complementary_info(self, detector):
        detector.add_prescription("case_1", "SULPH", "30C", "2026-01-01")
        check = detector.check_interactions("case_1", "NUX-V")
        assert any(w["type"] == "complementary" for w in check["warnings"])

    def test_safe_no_history(self, detector):
        check = detector.check_interactions("case_new", "PULS")
        assert check["safe"] is True
