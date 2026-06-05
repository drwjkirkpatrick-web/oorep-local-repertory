"""
Tests for Patient Outcome Prediction (Feature #28)

Covers:
  - Construction with/without DB
  - Cold-start prediction (no prescription history)
  - Prediction with synthetic DB records
  - Bayesian score decomposition
  - Track record queries
  - Outcome recording (learning)
  - Edge cases: empty candidates, unknown remedies
  - Confidence thresholds
"""

import json
import os
import pytest
import sqlite3
import tempfile
from pathlib import Path

from oorep.outcome_prediction import OutcomePredictionEngine


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def empty_db_path(tmp_path: Path) -> Path:
    """A fresh empty SQLite database at the correct schema."""
    db = tmp_path / "test_feedback.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id TEXT PRIMARY KEY,
            patient_id TEXT,
            remedy_abbrev TEXT,
            potency TEXT,
            status TEXT,
            outcome_score TEXT,
            prescribed_date TEXT,
            final_notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    return db


@pytest.fixture
def populated_db_path(tmp_path: Path) -> Path:
    """Database with a few fake prescription outcomes."""
    db = tmp_path / "test_feedback.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id TEXT PRIMARY KEY,
            patient_id TEXT,
            remedy_abbrev TEXT,
            potency TEXT,
            status TEXT,
            outcome_score TEXT,
            prescribed_date TEXT,
            final_notes TEXT
        )
        """
    )
    rows = [
        ("rx-1", "TestPatient", "PULS", "30C", "active", "improved", "2025-01-01", "Better mood"),
        ("rx-2", "TestPatient", "PULS", "200C", "completed", "cured", "2025-02-01", "Fully resolved"),
        ("rx-3", "TestPatient", "ARS", "6C", "completed", "unchanged", "2025-03-01", "No change"),
        ("rx-4", "OtherPatient", "PULS", "30C", "completed", "improved", "2025-01-15", "Good result"),
        ("rx-5", "OtherPatient", "LACH", "200C", "completed", "worsened", "2025-02-15", "Aggravation"),
    ]
    c.executemany(
        "INSERT INTO prescriptions VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return db


@pytest.fixture
def remedy_keynotes(tmp_path: Path) -> Path:
    json_file = tmp_path / "keynotes.json"
    data = {
        "PULS": [
            {"symptom": "changeable mood", "intensity": 3},
            {"symptom": "weeping disposition", "intensity": 3},
            {"symptom": "thirstless", "intensity": 2},
        ],
        "ARS": [
            {"symptom": "restless anxiety", "intensity": 3},
            {"symptom": "burning pains relieved by heat", "intensity": 3},
            {"symptom": "fear of death", "intensity": 3},
        ],
        "LACH": [
            {"symptom": "intense jealousy", "intensity": 3},
            {"symptom": "left-sided complaints", "intensity": 2},
        ],
    }
    with open(json_file, "w") as f:
        json.dump(data, f)
    return json_file


@pytest.fixture
def rubric_data(tmp_path: Path) -> Path:
    json_file = tmp_path / "rubrics.json"
    data = {
        "rubrics": [
            {
                "id": 1,
                "path": "Mind; Anxiety; evening; rest; amel.",
                "text": "Anxiety in the evening ameliorated by rest",
                "remedies": [{"remedy": "ARS", "grade": 3}, {"remedy": "PULS", "grade": 2}],
            },
            {
                "id": 2,
                "path": "Mind; Weeping; mood; changeable",
                "text": "Weeping with changeable mood",
                "remedies": [{"remedy": "PULS", "grade": 3}],
            },
            {
                "id": 3,
                "path": "Mind; Fear; death; of",
                "text": "Fear of death",
                "remedies": [{"remedy": "ARS", "grade": 3}, {"remedy": "AUR", "grade": 2}],
            },
        ]
    }
    with open(json_file, "w") as f:
        json.dump(data, f)
    return json_file


# ──────────────────────────────────────────────────────────────────────────────
# Construction
# ──────────────────────────────────────────────────────────────────────────────

class TestConstruction:

    def test_no_args(self):
        engine = OutcomePredictionEngine()
        assert engine is not None
        assert engine.repertory_json is None

    def test_with_paths(self, empty_db_path, rubric_data, remedy_keynotes):
        engine = OutcomePredictionEngine(
            db_path=empty_db_path,
            repertory_json=rubric_data,
            materia_medica_json=remedy_keynotes,
        )
        assert str(engine.db_path) == str(empty_db_path)
        assert engine.repertory_json == rubric_data

    # ── Patient history (cold start) ──────────────────────────────────────────

    def test_cold_start_no_history(self, empty_db_path):
        engine = OutcomePredictionEngine(db_path=empty_db_path)
        hist = engine.get_patient_history("Unknown")
        assert hist["prescriptions"] == []
        assert hist["overall_pattern"] == "no_history"

    def test_track_record_no_data(self, empty_db_path):
        engine = OutcomePredictionEngine(db_path=empty_db_path)
        track = engine.get_remedy_track_record("PULS")
        assert track["total_uses"] == 0
        assert track["avg_outcome"] is None


# ──────────────────────────────────────────────────────────────────────────────
# Prediction (cold start = DB empty, no prescription history)
# ──────────────────────────────────────────────────────────────────────────────

class TestColdStartPrediction:

    def test_predict_empty_candidates(self, empty_db_path, rubric_data, remedy_keynotes):
        engine = OutcomePredictionEngine(
            db_path=empty_db_path,
            repertory_json=rubric_data,
            materia_medica_json=remedy_keynotes,
        )
        result = engine.predict(
            patient_pseudonym="NewPatient",
            candidate_remedies=[],
            symptom_set=["anxiety", "restlessness"],
        )
        assert result == []

    def test_predict_no_db_no_keynotes(self):
        """Without DB or keynotes, still returns neutral scores."""
        engine = OutcomePredictionEngine()
        candidates = [
            {"remedy": "PULS", "score": 25.0},
            {"remedy": "ARS", "score": 22.0},
        ]
        result = engine.predict(
            patient_pseudonym="NewPatient",
            candidate_remedies=candidates,
            symptom_set=["anxiety"],
        )
        assert len(result) == 2
        for r in result:
            assert 0.0 <= r["outcome_likelihood"] <= 1.0
            assert r["confidence"] == "low"  # No historical data
            assert "components" in r

    def test_predict_with_rubric_and_keynote_data(self, empty_db_path, rubric_data, remedy_keynotes):
        engine = OutcomePredictionEngine(
            db_path=empty_db_path,
            repertory_json=rubric_data,
            materia_medica_json=remedy_keynotes,
        )
        candidates = [
            {"remedy": "ARS", "score": 28.0},
            {"remedy": "PULS", "score": 26.0},
        ]
        result = engine.predict(
            patient_pseudonym="NewPatient",
            candidate_remedies=candidates,
            symptom_set=["fear of death", "restless anxiety"],  # ARS keynotes
        )
        # ARS should rank higher due to keynote coverage
        assert result[0]["remedy"] == "ARS"
        assert result[0]["components"]["keynote_coverage"] > 0.3

    def test_rubric_coverage_boosts_grade3(self, empty_db_path, rubric_data, remedy_keynotes):
        """Ensure grade-3 rubric matches boost the rubric_coverage score."""
        engine = OutcomePredictionEngine(
            db_path=empty_db_path,
            repertory_json=rubric_data,
            materia_medica_json=remedy_keynotes,
        )
        # ARS has grade 3 in "fear of death" rubric
        candidates = [
            {"remedy": "ARS", "score": 20.0},
            {"remedy": "AUR", "score": 20.0},  # grade 2 in same rubric
        ]
        result = engine.predict(
            patient_pseudonym="X",
            candidate_remedies=candidates,
            symptom_set=["fear of death"],
        )
        ars = next(r for r in result if r["remedy"] == "ARS")
        aur = next(r for r in result if r["remedy"] == "AUR")
        assert ars["components"]["rubric_coverage"] >= aur["components"]["rubric_coverage"]

    def test_patient_history_score_with_prior_positive(self, populated_db_path, remedy_keynotes):
        engine = OutcomePredictionEngine(
            db_path=populated_db_path,
            materia_medica_json=remedy_keynotes,
        )
        candidates = [{"remedy": "PULS", "score": 20.0}]
        result = engine.predict(
            patient_pseudonym="TestPatient",
            candidate_remedies=candidates,
            symptom_set=["changeable mood"],
        )
        pul = result[0]
        # TestPatient had improved + cured with PULS → history should be > 0.5
        assert pul["components"]["patient_history"] > 0.5
        assert pul["track_record"]["total_uses"] == 3

    def test_patient_history_score_with_negative(self, populated_db_path, remedy_keynotes):
        engine = OutcomePredictionEngine(
            db_path=populated_db_path,
            materia_medica_json=remedy_keynotes,
        )
        candidates = [{"remedy": "ARS", "score": 20.0}]
        result = engine.predict(
            patient_pseudonym="TestPatient",
            candidate_remedies=candidates,
            symptom_set=["restless anxiety"],
        )
        ars = result[0]
        # TestPatient had 'unchanged' with ARS → history should be low
        assert ars["components"]["patient_history"] < 0.5


# ──────────────────────────────────────────────────────────────────────────────
# Track record
# ──────────────────────────────────────────────────────────────────────────────

class TestTrackRecord:

    def test_puls_track_record_aggregates_all_patients(self, populated_db_path):
        engine = OutcomePredictionEngine(db_path=populated_db_path)
        track = engine.get_remedy_track_record("PULS")
        assert track["total_uses"] == 3
        assert track["avg_outcome"] > 0.5  # improved + cured + improved
        assert track["success_rate"] > 0.5

    def test_lach_negative_track_record(self, populated_db_path):
        engine = OutcomePredictionEngine(db_path=populated_db_path)
        track = engine.get_remedy_track_record("LACH")
        assert track["total_uses"] == 1
        assert track["avg_outcome"] < 0.5  # worsened


# ──────────────────────────────────────────────────────────────────────────────
# Learning (outcome recording)
# ──────────────────────────────────────────────────────────────────────────────

class TestLearning:

    def test_record_outcome_updates_db(self, populated_db_path):
        engine = OutcomePredictionEngine(db_path=populated_db_path)
        ok = engine.record_outcome(
            patient_pseudonym="TestPatient",
            remedy="PULS",
            outcome="worsened",
            notes="Aggravation after repeat",
        )
        # SQLite UPDATE ... LIMIT 1 is not valid — our code uses subquery or LIMIT
        assert ok is True  # Should succeed with our implementation

        conn = sqlite3.connect(str(populated_db_path))
        c = conn.cursor()
        c.execute(
            "SELECT outcome_score, final_notes FROM prescriptions WHERE patient_id=? AND remedy_abbrev=? ORDER BY prescribed_date DESC LIMIT 1",
            ("TestPatient", "PULS"),
        )
        row = c.fetchone()
        conn.close()
        # The most recent PULS should have been updated
        assert row is not None
        assert "Aggravation" in (row[1] or "")

    def test_record_outcome_no_db(self):
        engine = OutcomePredictionEngine()  # No DB
        ok = engine.record_outcome("X", "PULS", "improved")
        assert ok is False


# ──────────────────────────────────────────────────────────────────────────────
# Feature overview
# ──────────────────────────────────────────────────────────────────────────────

class TestFeatureOverview:

    def test_overview_returns_dict(self):
        engine = OutcomePredictionEngine()
        overview = engine.get_feature_overview()
        assert overview["feature_id"] == 28
        assert overview["interpretable"] is True
        assert overview["cold_start_capable"] is True
