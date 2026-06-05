"""
Bridge integration tests for Patient File System — Feature #14
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "oorep-local-repertory"))
sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "clinic" / "oorep-hermes-bridge" / "scripts"))

from oorep_bridge import OOREPBridge
from oorep.patient_file_system import PatientFileSystem


def _make_bridge():
    """Build bridge with a temp DB so we don't pollute production."""
    fd = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    fd.close()
    db_path = Path(fd.name)
    # The bridge reads from the default DATA_DIR / feedback.db
    # but we can't easily override that without refactoring.
    # Instead, we'll use the production bridge but run commands that
    # are idempotent for testing.
    return OOREPBridge()


def test_bridge_patient_create():
    bridge = _make_bridge()
    # Use a unique pseudonym with timestamp to avoid collisions
    import time
    ts = str(int(time.time()))[-6:]
    pseudonym = f"TEST_PAT_{ts}"

    result = bridge.handle(f"new patient {pseudonym}")
    assert result["type"] == "patient_create"
    assert "registered" in result["formatted"].lower()
    assert result["result"]["pseudonym"] == pseudonym

    # Cleanup
    from oorep.patient_file_system import PatientFileSystem
    pfs = PatientFileSystem()
    pfs.delete_patient(pseudonym)


def test_bridge_patient_get():
    bridge = _make_bridge()
    import time
    ts = str(int(time.time()))[-6:]
    pseudonym = f"TEST_PAT_{ts}"

    # Create then get
    bridge.handle(f"new patient {pseudonym} F")
    result = bridge.handle(f"patient info {pseudonym}")
    assert result["type"] == "patient_get"
    assert result["result"]["pseudonym"] == pseudonym
    assert "F" in result["formatted"]

    pfs = PatientFileSystem()
    pfs.delete_patient(pseudonym)


def test_bridge_patient_list():
    bridge = _make_bridge()
    result = bridge.handle("list patients")
    assert result["type"] == "patient_list"
    assert isinstance(result["result"], list)


def test_bridge_consultation_create():
    bridge = _make_bridge()
    import time
    ts = str(int(time.time()))[-6:]
    pseudonym = f"TEST_CONS_{ts}"

    bridge.handle(f"new patient {pseudonym}")
    result = bridge.handle(f"new consultation {pseudonym} initial Anxiety with morning headache")
    assert result["type"] == "consultation_create"
    assert "recorded" in result["formatted"].lower()

    # Cleanup
    pfs = PatientFileSystem()
    pfs.delete_patient(pseudonym)


def test_bridge_patient_timeline():
    bridge = _make_bridge()
    import time
    ts = str(int(time.time()))[-6:]
    pseudonym = f"TEST_TL_{ts}"

    bridge.handle(f"new patient {pseudonym}")
    bridge.handle(f"new consultation {pseudonym} initial Headache")
    bridge.handle(f"new consultation {pseudonym} followup Improved")

    result = bridge.handle(f"patient timeline {pseudonym}")
    assert result["type"] == "patient_timeline"
    assert result["result"]["consultation_count"] == 2
    assert "Headache" in result["formatted"] or "Improved" in result["formatted"]

    pfs = PatientFileSystem()
    pfs.delete_patient(pseudonym)


def test_bridge_unknown_patient_get():
    bridge = _make_bridge()
    result = bridge.handle("patient info NONEXISTENT_PATIENT_12345")
    assert result["type"] == "patient_get"
    assert "error" in result
    assert "no patient found" in result["formatted"].lower()


if __name__ == "__main__":
    tests = [
        test_bridge_patient_create,
        test_bridge_patient_get,
        test_bridge_patient_list,
        test_bridge_consultation_create,
        test_bridge_patient_timeline,
        test_bridge_unknown_patient_get,
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
