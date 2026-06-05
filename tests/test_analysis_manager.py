"""
Tests for analysis_manager.py — Feature #16
"""

import sys
import json
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oorep.analysis_manager import AnalysisManager


def _make_db() -> Path:
    fd = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    fd.close()
    return Path(fd.name)


def _count_rows(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ── Save / Create ────────────────────────────────────────────────────────────

def test_save_analysis_basic():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)

    a = mgr.save_analysis({
        "analysis_name": "Test Analysis",
        "symptoms": ["headache", "fever"],
        "results": [
            {"abbrev": "Ars", "score": 34.0, "match_count": 13},
            {"abbrev": "Sulph", "score": 32.0, "match_count": 14},
        ],
        "grade_mode": "full",
        "notes": "Initial run",
    })
    assert a["analysis_id"] is not None
    assert a["analysis_name"] == "Test Analysis"
    assert a["version"] == 1
    assert a["symptoms"] == ["headache", "fever"]
    assert len(a["results"]) == 2
    assert a["grade_mode"] == "full"
    assert a["notes"] == "Initial run"
    assert not a["is_baseline"]


def test_save_analysis_with_patient_and_consultation():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)

    a = mgr.save_analysis({
        "analysis_name": "MrsJ-Initial",
        "patient_pseudonym": "MrsJ2024",
        "consultation_id": "cons-123",
        "symptoms": ["anxiety"],
        "results": [{"abbrev": "Puls", "score": 20.0}],
    })
    assert a["patient_pseudonym"] == "MrsJ2024"
    assert a["consultation_id"] == "cons-123"
    assert a["version"] == 1


def test_save_analysis_missing_name_raises():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    try:
        mgr.save_analysis({"symptoms": ["x"]})
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "analysis_name is required" in str(e)


# ── Versioning ─────────────────────────────────────────────────────────────────

def test_auto_versioning_per_consultation():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)

    a1 = mgr.save_analysis({
        "analysis_name": "V1",
        "consultation_id": "cons-abc",
        "symptoms": ["a"],
        "results": [{"abbrev": "Ars", "score": 10}],
    })
    assert a1["version"] == 1

    a2 = mgr.save_analysis({
        "analysis_name": "V2",
        "consultation_id": "cons-abc",
        "symptoms": ["a", "b"],
        "results": [{"abbrev": "Ars", "score": 12}],
    })
    assert a2["version"] == 2

    a3 = mgr.save_analysis({
        "analysis_name": "Other",
        "consultation_id": "cons-xyz",
        "symptoms": ["c"],
        "results": [{"abbrev": "Puls", "score": 5}],
    })
    assert a3["version"] == 1  # different consultation resets


def test_version_1_without_consultation():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({
        "analysis_name": "Standalone",
        "symptoms": ["x"],
        "results": [],
    })
    assert a["version"] == 1


# ── Read ───────────────────────────────────────────────────────────────────────

def test_get_analysis():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({
        "analysis_name": "GetTest",
        "symptoms": ["y"],
        "results": [{"abbrev": "Nux", "score": 5}],
        "grade_weights": {"1": 1, "2": 3, "3": 6},
    })

    fetched = mgr.get_analysis(a["analysis_id"])
    assert fetched is not None
    assert fetched["analysis_name"] == "GetTest"
    assert fetched["grade_weights"] == {"1": 1, "2": 3, "3": 6}


def test_get_analysis_not_found():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    assert mgr.get_analysis("NONEXISTENT") is None


def test_list_analyses_by_patient():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    mgr.save_analysis({"analysis_name": "A1", "patient_pseudonym": "PT-A", "symptoms": [], "results": []})
    mgr.save_analysis({"analysis_name": "A2", "patient_pseudonym": "PT-A", "symptoms": [], "results": []})
    mgr.save_analysis({"analysis_name": "B1", "patient_pseudonym": "PT-B", "symptoms": [], "results": []})

    a_list = mgr.list_analyses(patient_pseudonym="PT-A")
    assert len(a_list) == 2
    assert all(a["patient_pseudonym"] == "PT-A" for a in a_list)


def test_list_analyses_baseline_only():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    mgr.save_analysis({"analysis_name": "Base", "patient_pseudonym": "PT-C", "symptoms": [], "results": [], "is_baseline": True})
    mgr.save_analysis({"analysis_name": "Other", "patient_pseudonym": "PT-C", "symptoms": [], "results": [], "is_baseline": False})

    baselines = mgr.list_analyses(patient_pseudonym="PT-C", baseline_only=True)
    assert len(baselines) == 1
    assert baselines[0]["analysis_name"] == "Base"


def test_get_baseline_for_consultation():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    mgr.save_analysis({
        "analysis_name": "Base1",
        "consultation_id": "cons-d",
        "symptoms": [],
        "results": [],
        "is_baseline": True,
        "version": 1,
    })
    mgr.save_analysis({
        "analysis_name": "Base2",
        "consultation_id": "cons-d",
        "symptoms": [],
        "results": [],
        "is_baseline": True,
        "version": 2,
    })

    baseline = mgr.get_baseline_for_consultation("cons-d")
    assert baseline is not None
    assert baseline["analysis_name"] == "Base2"  # latest baseline
    assert baseline["version"] == 2


# ── Update ─────────────────────────────────────────────────────────────────────

def test_update_analysis_name_and_notes():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({"analysis_name": "Old", "symptoms": [], "results": []})

    updated = mgr.update_analysis(a["analysis_id"], {
        "analysis_name": "New",
        "notes": "Updated note",
        "is_baseline": True,
    })
    assert updated is not None
    assert updated["analysis_name"] == "New"
    assert updated["notes"] == "Updated note"
    assert updated["is_baseline"] is True


def test_update_analysis_not_found():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    try:
        mgr.update_analysis("MISSING", {"analysis_name": "X"})
        assert False, "Expected KeyError"
    except KeyError:
        pass


def test_update_analysis_disallows_results():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({"analysis_name": "X", "symptoms": [], "results": []})
    try:
        mgr.update_analysis(a["analysis_id"], {"results": [{"abbrev": "Ars"}]})
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "allowed fields" in str(e).lower()


# ── Delete ─────────────────────────────────────────────────────────────────────

def test_delete_analysis():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({"analysis_name": "ToDelete", "symptoms": [], "results": []})
    assert mgr.delete_analysis(a["analysis_id"]) is True
    assert mgr.get_analysis(a["analysis_id"]) is None


def test_delete_analysis_not_found():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    assert mgr.delete_analysis("MISSING") is False


# ── Compare ───────────────────────────────────────────────────────────────────

def test_compare_analyses_basic():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({
        "analysis_name": "Before",
        "symptoms": ["x"],
        "results": [
            {"abbrev": "Ars", "score": 34.0},
            {"abbrev": "Sulph", "score": 32.0},
            {"abbrev": "Puls", "score": 20.0},
        ],
    })
    b = mgr.save_analysis({
        "analysis_name": "After",
        "symptoms": ["x", "y"],
        "results": [
            {"abbrev": "Ars", "score": 30.0},
            {"abbrev": "Sulph", "score": 35.0},
            {"abbrev": "Nux", "score": 15.0},
        ],
    })

    diff = mgr.compare_analyses(a["analysis_id"], b["analysis_id"])
    assert diff["analysis_a"]["name"] == "Before"
    assert diff["analysis_b"]["name"] == "After"

    # Ars changed (score 34 -> 30, rank 1 -> 1)
    ars = next((c for c in diff["changed"] if c["abbrev"] == "Ars"), None)
    assert ars is not None
    assert ars["score_delta"] == -4.0

    # Sulph changed (score 32 -> 35)
    sulph = next((c for c in diff["changed"] if c["abbrev"] == "Sulph"), None)
    assert sulph is not None
    assert sulph["score_delta"] == 3.0

    # Puls dropped
    assert any(d["abbrev"] == "Puls" for d in diff["dropped_remedies"])

    # Nux new
    assert any(n["abbrev"] == "Nux" for n in diff["new_remedies"])


def test_compare_analyses_not_found():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    try:
        mgr.compare_analyses("MISSING-A", "MISSING-B")
        assert False, "Expected KeyError"
    except KeyError as e:
        assert "MISSING" in str(e)


# ── JSON serialization round-trip ────────────────────────────────────────────

def test_json_roundtrip():
    db = _make_db()
    mgr = AnalysisManager(db_path=db)
    a = mgr.save_analysis({
        "analysis_name": "JSONTest",
        "symptoms": ["a", "b", "c"],
        "results": [{"abbrev": "Ars", "score": 34.0, "matches": [{"rubric": "Headache", "weight": 3}]}],
        "grade_mode": "classical",
        "grade_weights": {1: 1, 2: 3, 3: 6},
        "clipboard_ids": ["clip-1", "clip-2"],
        "is_baseline": True,
        "notes": "Test note",
    })

    fetched = mgr.get_analysis(a["analysis_id"])
    assert fetched is not None
    assert fetched["symptoms"] == ["a", "b", "c"]
    assert fetched["results"][0]["abbrev"] == "Ars"
    assert fetched["grade_weights"] == {"1": 1, "2": 3, "3": 6}  # JSON string keys
    assert fetched["clipboard_ids"] == ["clip-1", "clip-2"]
    assert fetched["is_baseline"] is True
    assert fetched["notes"] == "Test note"


if __name__ == "__main__":
    tests = [
        test_save_analysis_basic,
        test_save_analysis_with_patient_and_consultation,
        test_save_analysis_missing_name_raises,
        test_auto_versioning_per_consultation,
        test_version_1_without_consultation,
        test_get_analysis,
        test_get_analysis_not_found,
        test_list_analyses_by_patient,
        test_list_analyses_baseline_only,
        test_get_baseline_for_consultation,
        test_update_analysis_name_and_notes,
        test_update_analysis_not_found,
        test_update_analysis_disallows_results,
        test_delete_analysis,
        test_delete_analysis_not_found,
        test_compare_analyses_basic,
        test_compare_analyses_not_found,
        test_json_roundtrip,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{passed}/{len(tests)} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
