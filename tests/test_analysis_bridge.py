"""
Bridge integration tests for Analysis Manager — Feature #16
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "oorep-local-repertory"))
sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "clinic" / "oorep-hermes-bridge" / "scripts"))

from oorep_bridge import OOREPBridge
from oorep.analysis_manager import AnalysisManager


def test_bridge_analysis_save():
    bridge = OOREPBridge()
    ts = str(int(time.time()))[-6:]
    name = f"TestAnalysis_{ts}"
    result = bridge.handle(f"save analysis {name}")
    assert result["type"] == "analysis_save"
    assert "saved" in result["formatted"].lower()
    assert result["result"]["version"] == 1
    # Cleanup
    mgr = AnalysisManager()
    mgr.delete_analysis(result["result"]["analysis_id"])


def test_bridge_analysis_get():
    bridge = OOREPBridge()
    mgr = AnalysisManager()
    a = mgr.save_analysis({"analysis_name": "GetTest", "symptoms": [], "results": []})

    result = bridge.handle(f"get analysis {a['analysis_id']}")
    assert result["type"] == "analysis_get"
    assert result["result"]["analysis_name"] == "GetTest"

    mgr.delete_analysis(a["analysis_id"])


def test_bridge_analysis_list():
    bridge = OOREPBridge()
    mgr = AnalysisManager()
    ts = str(int(time.time()))[-6:]
    a = mgr.save_analysis({"analysis_name": f"ListTest_{ts}", "symptoms": [], "results": []})

    result = bridge.handle("list analyses")
    assert result["type"] == "analysis_list"
    assert any(a["analysis_name"] == f"ListTest_{ts}" for a in result["result"])

    mgr.delete_analysis(a["analysis_id"])


def test_bridge_analysis_compare():
    bridge = OOREPBridge()
    mgr = AnalysisManager()
    a = mgr.save_analysis({
        "analysis_name": "Before",
        "symptoms": ["x"],
        "results": [{"abbrev": "Ars", "score": 34.0}, {"abbrev": "Sulph", "score": 32.0}],
    })
    b = mgr.save_analysis({
        "analysis_name": "After",
        "symptoms": ["x", "y"],
        "results": [{"abbrev": "Ars", "score": 30.0}, {"abbrev": "Nux", "score": 15.0}],
    })

    result = bridge.handle(f"compare analyses {a['analysis_id']} and {b['analysis_id']}")
    assert result["type"] == "analysis_compare"
    assert "changed" in result["formatted"].lower() or "new" in result["formatted"].lower()

    mgr.delete_analysis(a["analysis_id"])
    mgr.delete_analysis(b["analysis_id"])


def test_bridge_analysis_delete():
    bridge = OOREPBridge()
    mgr = AnalysisManager()
    a = mgr.save_analysis({"analysis_name": "ToDelete", "symptoms": [], "results": []})

    result = bridge.handle(f"delete analysis {a['analysis_id']}")
    assert result["type"] == "analysis_delete"
    assert "deleted" in result["formatted"].lower()


def test_bridge_analysis_not_found():
    bridge = OOREPBridge()
    result = bridge.handle("get analysis NONEXISTENT12345")
    assert result["type"] == "analysis_get"
    assert "error" in result
    assert "not found" in result["formatted"].lower()


if __name__ == "__main__":
    tests = [
        test_bridge_analysis_save,
        test_bridge_analysis_get,
        test_bridge_analysis_list,
        test_bridge_analysis_compare,
        test_bridge_analysis_delete,
        test_bridge_analysis_not_found,
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
