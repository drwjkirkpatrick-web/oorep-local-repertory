"""
Tests for patient_file_system.py — Feature #14
"""

import sys
import json
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oorep.patient_file_system import PatientFileSystem


# ── Helpers ────────────────────────────────────────────────────────────────

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


# ── Patient CRUD ───────────────────────────────────────────────────────────

def test_create_and_get_patient():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)

    p = pfs.create_patient({
        "pseudonym": "PT-001",
        "gender": "F",
        "date_of_birth": "1985-03-15",
        "notes": "Test patient",
        "contact_consent": True,
    })
    assert p["pseudonym"] == "PT-001"
    assert p["gender"] == "F"
    assert p["contact_consent"] is True
    assert p["status"] == "active"

    fetched = pfs.get_patient("PT-001")
    assert fetched is not None
    assert fetched["pseudonym"] == "PT-001"
    assert fetched["notes"] == "Test patient"


def test_get_patient_not_found():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    assert pfs.get_patient("NONEXISTENT") is None


def test_create_patient_missing_pseudonym_raises():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    try:
        pfs.create_patient({"gender": "M"})
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "pseudonym is required" in str(e)


def test_update_patient():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-002", "notes": "Old notes"})

    updated = pfs.update_patient("PT-002", {"notes": "New notes", "status": "inactive"})
    assert updated is not None
    assert updated["notes"] == "New notes"
    assert updated["status"] == "inactive"


def test_update_patient_not_found():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    try:
        pfs.update_patient("MISSING", {"notes": "x"})
        assert False, "Expected KeyError"
    except KeyError:
        pass


def test_list_patients():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-A", "status": "active"})
    pfs.create_patient({"pseudonym": "PT-B", "status": "inactive"})

    all_patients = pfs.list_patients()
    assert len(all_patients) == 2

    active = pfs.list_patients(status="active")
    assert len(active) == 1
    assert active[0]["pseudonym"] == "PT-A"


def test_delete_patient_cascades_consultations():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-DEL"})
    pfs.create_consultation({
        "patient_pseudonym": "PT-DEL",
        "chief_complaint": "Headache",
    })
    assert _count_rows(db, "consultations") == 1

    deleted = pfs.delete_patient("PT-DEL")
    assert deleted is True
    assert _count_rows(db, "patients") == 0
    assert _count_rows(db, "consultations") == 0  # CASCADE


# ── Consultation CRUD ─────────────────────────────────────────────────────

def test_create_consultation():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-003"})

    c = pfs.create_consultation({
        "patient_pseudonym": "PT-003",
        "consultation_type": "initial",
        "chief_complaint": "Anxiety with morning headache",
        "practitioner_id": "DrW",
        "clipboard_ids": ["clip-1", "clip-2"],
        "analysis_snapshot": {"top_remedy": "Ars", "score": 34.0},
        "next_visit_date": "2024-07-01",
    })
    assert c["consultation_id"] is not None
    assert c["patient_pseudonym"] == "PT-003"
    assert c["consultation_type"] == "initial"
    assert c["chief_complaint"] == "Anxiety with morning headache"
    assert c["clipboard_ids"] == ["clip-1", "clip-2"]
    assert c["analysis_snapshot"]["top_remedy"] == "Ars"
    assert c["next_visit_date"] == "2024-07-01"


def test_create_consultation_missing_patient_raises():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    try:
        pfs.create_consultation({"patient_pseudonym": "MISSING"})
        assert False, "Expected KeyError"
    except KeyError as e:
        assert "MISSING" in str(e)


def test_get_consultation():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-004"})
    c1 = pfs.create_consultation({"patient_pseudonym": "PT-004", "chief_complaint": "Fever"})

    fetched = pfs.get_consultation(c1["consultation_id"])
    assert fetched is not None
    assert fetched["chief_complaint"] == "Fever"


def test_list_consultations_by_patient():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-005"})
    pfs.create_consultation({"patient_pseudonym": "PT-005", "consultation_type": "initial"})
    pfs.create_consultation({"patient_pseudonym": "PT-005", "consultation_type": "followup"})

    all_consults = pfs.list_consultations(patient_pseudonym="PT-005")
    assert len(all_consults) == 2

    initial = pfs.list_consultations(patient_pseudonym="PT-005", consult_type="initial")
    assert len(initial) == 1
    assert initial[0]["consultation_type"] == "initial"


def test_update_consultation():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-006"})
    c = pfs.create_consultation({
        "patient_pseudonym": "PT-006",
        "chief_complaint": "Old complaint",
    })

    updated = pfs.update_consultation(c["consultation_id"], {
        "chief_complaint": "Updated complaint",
        "outcome_notes": "Resolved",
        "clipboard_ids": ["clip-3"],
    })
    assert updated is not None
    assert updated["chief_complaint"] == "Updated complaint"
    assert updated["outcome_notes"] == "Resolved"
    assert updated["clipboard_ids"] == ["clip-3"]


def test_delete_consultation():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-007"})
    c = pfs.create_consultation({"patient_pseudonym": "PT-007"})
    assert pfs.delete_consultation(c["consultation_id"]) is True
    assert pfs.get_consultation(c["consultation_id"]) is None


# ── Timeline ─────────────────────────────────────────────────────────────────

def test_patient_timeline():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-008"})
    pfs.create_consultation({
        "patient_pseudonym": "PT-008",
        "consultation_type": "initial",
        "chief_complaint": "Cough",
        "prescription_id": "rx-1",
    })
    pfs.create_consultation({
        "patient_pseudonym": "PT-008",
        "consultation_type": "followup",
        "chief_complaint": "Follow-up cough",
    })

    timeline = pfs.get_patient_timeline("PT-008")
    assert timeline["patient"]["pseudonym"] == "PT-008"
    assert timeline["consultation_count"] == 2
    assert timeline["prescription_count"] == 1
    assert timeline["days_in_practice"] is not None
    assert len(timeline["consultations"]) == 2
    # Initial should be first (newest first)
    assert timeline["consultations"][0]["consultation_type"] in ("initial", "followup")


def test_chief_complaints_history():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-009"})
    pfs.create_consultation({"patient_pseudonym": "PT-009", "chief_complaint": "Headache"})
    pfs.create_consultation({"patient_pseudonym": "PT-009", "chief_complaint": "Fatigue"})

    cc = pfs.get_patient_chief_complaints("PT-009")
    assert "Headache" in cc
    assert "Fatigue" in cc


# ── last_seen update ─────────────────────────────────────────────────────────

def test_last_seen_updated_on_consultation():
    db = _make_db()
    pfs = PatientFileSystem(db_path=db)
    pfs.create_patient({"pseudonym": "PT-010"})
    before = pfs.get_patient("PT-010")["last_seen"]

    # Force a slight delay so timestamps differ
    import time
    time.sleep(0.01)

    pfs.create_consultation({"patient_pseudonym": "PT-010"})
    after = pfs.get_patient("PT-010")["last_seen"]
    assert after >= before


if __name__ == "__main__":
    tests = [
        test_create_and_get_patient,
        test_get_patient_not_found,
        test_create_patient_missing_pseudonym_raises,
        test_update_patient,
        test_update_patient_not_found,
        test_list_patients,
        test_delete_patient_cascades_consultations,
        test_create_consultation,
        test_create_consultation_missing_patient_raises,
        test_get_consultation,
        test_list_consultations_by_patient,
        test_update_consultation,
        test_delete_consultation,
        test_patient_timeline,
        test_chief_complaints_history,
        test_last_seen_updated_on_consultation,
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
            failed += 1
    print(f"\n{passed}/{len(tests)} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
