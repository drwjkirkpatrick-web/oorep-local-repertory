"""
Tests for outcome_predictor_stats.py (Module #64)

Covers:
  - Schema initialization
  - ROC/AUC computation (pure Python)
  - Calibration analysis (equal-frequency binning)
  - Bootstrap CI on AUC
  - Full validation report
  - Edge cases: empty DB, single class, ties
"""

import pytest
import sqlite3
from pathlib import Path
from oorep.outcome_predictor_stats import OutcomePredictorStats


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_stats(tmp_path: Path):
    db = tmp_path / "test_feedback.db"
    stats = OutcomePredictorStats(db_path=db)
    return stats


@pytest.fixture
def populated_stats(tmp_path: Path):
    db = tmp_path / "test_feedback.db"
    stats = OutcomePredictorStats(db_path=db)
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    # Insert 20 prescriptions with varying scores and outcomes
    rows = [
        # High scores → positive outcomes
        ("rx1", "P1", "PULS", "30C", "completed", "cured", 0.9, 0.8, 0.95),
        ("rx2", "P1", "PULS", "200C", "completed", "improved", 0.85, 0.7, 0.88),
        ("rx3", "P2", "ARS", "6C", "completed", "cured", 0.8, 0.75, 0.82),
        ("rx4", "P2", "ARS", "30C", "completed", "improved", 0.78, 0.72, 0.79),
        ("rx5", "P3", "NAT_M", "30C", "completed", "cured", 0.92, 0.85, 0.91),
        ("rx6", "P3", "NAT_M", "200C", "completed", "improved", 0.88, 0.8, 0.87),
        ("rx7", "P4", "LACH", "200C", "completed", "cured", 0.75, 0.7, 0.76),
        ("rx8", "P4", "LACH", "1M", "completed", "improved", 0.7, 0.65, 0.71),
        ("rx9", "P5", "SULPH", "30C", "completed", "cured", 0.82, 0.78, 0.83),
        ("rx10", "P5", "SULPH", "200C", "completed", "improved", 0.79, 0.74, 0.80),
        # Medium scores → mixed
        ("rx11", "P6", "NUX_V", "30C", "completed", "improved", 0.55, 0.5, 0.58),
        ("rx12", "P6", "NUX_V", "200C", "completed", "unchanged", 0.5, 0.45, 0.52),
        ("rx13", "P7", "BRY", "30C", "completed", "improved", 0.6, 0.55, 0.62),
        ("rx14", "P7", "BRY", "200C", "completed", "unchanged", 0.52, 0.48, 0.53),
        # Low scores → negative
        ("rx15", "P8", "PHOS", "30C", "completed", "unchanged", 0.3, 0.25, 0.32),
        ("rx16", "P8", "PHOS", "200C", "completed", "worsened", 0.25, 0.2, 0.28),
        ("rx17", "P9", "MERC", "30C", "completed", "unchanged", 0.35, 0.3, 0.36),
        ("rx18", "P9", "MERC", "200C", "completed", "worsened", 0.2, 0.15, 0.22),
        ("rx19", "P10", "SIL", "30C", "completed", "worsened", 0.15, 0.1, 0.18),
        ("rx20", "P10", "SIL", "200C", "completed", "worsened", 0.1, 0.05, 0.12),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO prescriptions (prescription_id, patient_id, remedy_abbrev, potency, status, outcome_score, rubric_coverage, keynote_match, composite_score) VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return stats


# ── ROC / AUC ─────────────────────────────────────────────────────────────────

class TestROC:

    def test_roc_computation(self, populated_stats):
        roc = populated_stats.compute_roc("composite_score", ["cured", "improved"])
        assert "auc" in roc
        assert roc["auc"] > 0.5  # Should discriminate
        assert roc["auc"] <= 1.0
        assert len(roc["points"]) > 0
        assert roc["n_positive"] == 12  # 5 cured + 7 improved
        assert roc["n_negative"] == 8   # 4 unchanged + 4 worsened
        assert roc["n_total"] == 20

    def test_auc_interpretation(self, populated_stats):
        roc = populated_stats.compute_roc("composite_score", ["cured", "improved"])
        interp = roc["auc_interpretation"]
        assert interp in ["Fair discrimination", "Good discrimination", "Very good discrimination", "Excellent discrimination"]

    def test_roc_empty_db(self, fresh_stats):
        roc = fresh_stats.compute_roc("composite_score", ["cured", "improved"])
        assert "error" in roc
        assert roc["auc"] == 0.5

    def test_roc_single_class(self, tmp_path: Path):
        db = tmp_path / "single.db"
        stats = OutcomePredictorStats(db_path=db)
        conn = sqlite3.connect(str(db))
        c = conn.cursor()
        for i in range(5):
            c.execute(
                "INSERT INTO prescriptions (prescription_id, patient_id, remedy_abbrev, potency, status, outcome_score, composite_score) VALUES (?,?,?,?,?,?,?)",
                (f"rx{i}", f"P{i}", "PULS", "30C", "completed", "cured", 0.8),
            )
        conn.commit()
        conn.close()
        roc = stats.compute_roc("composite_score", ["cured"])
        assert "error" in roc
        assert "Only one outcome class" in roc["error"]

    def test_optimal_threshold_exists(self, populated_stats):
        roc = populated_stats.compute_roc("composite_score", ["cured", "improved"])
        assert "optimal_threshold" in roc
        assert roc["optimal_tpr"] > 0
        assert roc["optimal_fpr"] >= 0


# ── Calibration ──────────────────────────────────────────────────────────────

class TestCalibration:

    def test_calibration_bins(self, populated_stats):
        cal = populated_stats.calibration_analysis(5, "composite_score", ["cured", "improved"])
        assert "bins" in cal
        assert len(cal["bins"]) > 0
        assert "expected_calibration_error" in cal
        assert cal["expected_calibration_error"] >= 0

    def test_calibration_quality_label(self, populated_stats):
        cal = populated_stats.calibration_analysis(5, "composite_score", ["cured", "improved"])
        assert cal["calibration_quality"] in ["well-calibrated", "fair", "poor"]

    def test_calibration_empty(self, fresh_stats):
        cal = fresh_stats.calibration_analysis(5, "composite_score", ["cured", "improved"])
        assert "error" in cal


# ── Bootstrap CI ──────────────────────────────────────────────────────────────

class TestBootstrap:

    def test_bootstrap_ci(self, populated_stats):
        boot = populated_stats.bootstrap_auc("composite_score", 100, ["cured", "improved"], seed=42)
        assert "ci_95" in boot
        assert len(boot["ci_95"]) == 2
        assert boot["ci_95"][0] <= boot["ci_95"][1]
        assert boot["ci_95"][0] >= 0
        assert boot["ci_95"][1] <= 1
        assert "mean_auc" in boot
        assert "std_auc" in boot

    def test_bootstrap_reproducible(self, populated_stats):
        b1 = populated_stats.bootstrap_auc("composite_score", 50, ["cured", "improved"], seed=123)
        b2 = populated_stats.bootstrap_auc("composite_score", 50, ["cured", "improved"], seed=123)
        assert b1["mean_auc"] == b2["mean_auc"]
        assert b1["ci_95"] == b2["ci_95"]

    def test_bootstrap_empty(self, fresh_stats):
        boot = fresh_stats.bootstrap_auc("composite_score", 50, ["cured", "improved"])
        assert "error" in boot


# ── Full Report ─────────────────────────────────────────────────────────────

class TestFullReport:

    def test_full_report_structure(self, populated_stats):
        report = populated_stats.full_validation_report()
        assert "predictors" in report
        assert "summary" in report
        assert "predictor_ranking" in report
        assert "rubric_coverage" in report["predictors"]
        assert "keynote_match" in report["predictors"]
        assert "composite_score" in report["predictors"]
        assert report["summary"]["n_total"] == 20

    def test_predictor_ranking_order(self, populated_stats):
        report = populated_stats.full_validation_report()
        aucs = [p["auc"] for p in report["predictor_ranking"]]
        assert aucs == sorted(aucs, reverse=True)


# ── Feature Overview ─────────────────────────────────────────────────────────

class TestFeatureOverview:

    def test_overview(self, fresh_stats):
        ov = fresh_stats.get_feature_overview()
        assert ov["feature_id"] == 64
        assert ov["feature_name"] == "Outcome Predictor Statistics"
        assert ov["pure_python"] is True
        assert "roc_auc" in ov["supports"]
