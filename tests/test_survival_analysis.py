"""Tests for survival_analysis.py (Module #72)"""

import pytest
import sqlite3
from pathlib import Path
from oorep.survival_analysis import SurvivalAnalysis


@pytest.fixture
def sa(tmp_path: Path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE prescriptions (
            prescription_id TEXT, patient_id TEXT, remedy_abbrev TEXT,
            potency TEXT, status TEXT, outcome_score TEXT, prescribed_date TEXT
        )
    """)
    rows = [
        ("r1", "P1", "PULS", "30C", "done", "cured", "2025-01-01"),
        ("r2", "P2", "PULS", "200C", "improved", "improved", "2025-01-15"),
        ("r3", "P3", "PULS", "1M", "done", "unchanged", "2025-02-01"),
        ("r4", "P4", "ARS", "30C", "done", "cured", "2025-01-01"),
        ("r5", "P5", "ARS", "200C", "done", "worsened", "2025-02-01"),
    ]
    c.executemany("INSERT INTO prescriptions VALUES (?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    return SurvivalAnalysis(db_path=db)


class TestKaplanMeier:

    def test_curve_generated(self, sa):
        result = sa.kaplan_meier("PULS")
        assert "curve" in result
        assert len(result["curve"]) > 0
        assert result["curve"][0]["survival"] == 1.0

    def test_empty_remedy(self, sa):
        result = sa.kaplan_meier("UNKNOWN")
        assert "error" in result


class TestHazardRatio:

    def test_hazard_ratio(self, sa):
        result = sa.hazard_ratio("PULS", "ARS")
        assert "hazard_ratio" in result
        assert result["hazard_a"] >= 0
        assert result["hazard_b"] >= 0


class TestFeatureOverview:

    def test_overview(self, sa):
        ov = sa.get_feature_overview()
        assert ov["feature_id"] == 72
        assert "kaplan_meier" in ov["supports"]
