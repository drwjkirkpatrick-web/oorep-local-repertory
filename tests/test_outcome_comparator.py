"""Tests for outcome_comparator.py (Module #66)"""

import pytest
import sqlite3
from pathlib import Path
from oorep.outcome_comparator import OutcomeComparator


@pytest.fixture
def comparator(tmp_path: Path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id TEXT PRIMARY KEY, patient_id TEXT, remedy_abbrev TEXT,
            potency TEXT, status TEXT, outcome_score TEXT, prescribed_date TEXT
        )
    """)
    rows = [
        ("r1", "P1", "PULS", "30C", "done", "cured", "2025-01-01"), ("r2", "P1", "PULS", "200C", "done", "improved", "2025-01-15"),
        ("r3", "P2", "PULS", "1M", "done", "cured", "2025-02-01"), ("r4", "P3", "PULS", "30C", "done", "improved", "2025-02-15"),
        ("r5", "P4", "PULS", "200C", "done", "cured", "2025-03-01"), ("r6", "P5", "PULS", "30C", "done", "improved", "2025-03-15"),
        ("r7", "P6", "PULS", "1M", "done", "unchanged", "2025-04-01"), ("r8", "P7", "PULS", "200C", "done", "worsened", "2025-04-15"),
        ("r9", "P8", "ARS", "30C", "done", "cured", "2025-01-01"), ("r10", "P9", "ARS", "200C", "done", "improved", "2025-01-15"),
        ("r11", "P10", "ARS", "30C", "done", "unchanged", "2025-02-01"), ("r12", "P11", "ARS", "1M", "done", "worsened", "2025-02-15"),
    ]
    c.executemany("INSERT INTO prescriptions VALUES (?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    return OutcomeComparator(db_path=db)


class TestComparison:

    def test_basic_comparison(self, comparator):
        result = comparator.compare_remedies("PULS", "ARS", ["cured", "improved"])
        assert "mann_whitney_u" in result
        assert "odds_ratio" in result
        assert "cohens_d" in result
        assert result["n_a"] == 8
        assert result["n_b"] == 4

    def test_puls_higher_rate(self, comparator):
        result = comparator.compare_remedies("PULS", "ARS", ["cured", "improved"])
        assert result["positive_rate_a"] > result["positive_rate_b"]

    def test_cliffs_delta(self, comparator):
        result = comparator.compare_remedies("PULS", "ARS", ["cured", "improved"])
        assert "cliffs_delta" in result
        assert "cliffs_interpretation" in result

    def test_empty_remedy(self, comparator):
        result = comparator.compare_remedies("PULS", "UNKNOWN", ["cured"])
        assert "error" in result


class TestFeatureOverview:

    def test_overview(self, comparator):
        ov = comparator.get_feature_overview()
        assert ov["feature_id"] == 66
        assert "mann_whitney_u" in ov["supports"]
