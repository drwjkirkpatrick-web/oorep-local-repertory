"""
Test Master Score Bridge Integration

Tests the natural-language routing for master score commands through OOREPBridge.
Uses real data but bounded rubric counts to stay within Jetson limits.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path.home() / "projects" / "oorep-local-repertory"))

# Bridge lives in skills directory
_BRIDGE_DIR = Path.home() / ".hermes" / "skills" / "clinic" / "oorep-hermes-bridge" / "scripts"
sys.path.insert(0, str(_BRIDGE_DIR))

from oorep_bridge import OOREPBridge


@pytest.fixture(scope="module")
def bridge():
    """Module-scoped bridge (expensive to init)."""
    return OOREPBridge()


# ── Master Score command routing ─────────────────────────────────────────────

def test_bridge_master_score_routing(bridge):
    result = bridge.handle("master score anxiety restlessness")
    assert result["type"] == "master_score"
    assert "result" in result
    assert "formatted" in result
    assert result["result"] is not None
    assert len(result["result"]) > 0


def test_bridge_master_score_alias_composite(bridge):
    result = bridge.handle("composite dry cough hoarseness")
    assert result["type"] == "master_score"
    assert result["result"] is not None


def test_bridge_master_compare_routing(bridge):
    result = bridge.handle("compare methods anxiety restlessness thirst")
    assert result["type"] == "master_compare"
    assert "result" in result
    assert "kent_results" in result["result"]
    assert "boenninghausen_results" in result["result"]
    assert "master_results" in result["result"]


def test_bridge_master_weights_routing(bridge):
    result = bridge.handle("master weights")
    assert result["type"] == "master_weights"
    assert "result" in result
    assert "kent" in result["result"]
    assert "boenninghausen" in result["result"]


# ── Output format validation ───────────────────────────────────────────────

def test_bridge_master_score_formatted(bridge):
    result = bridge.handle("master score anxiety restlessness")
    formatted = result["formatted"]
    assert "Master Score" in formatted or "master_score" in formatted
    assert "🎯" in formatted or any(r.get("abbrev") in formatted for r in result["result"][:3])


def test_bridge_master_compare_formatted(bridge):
    result = bridge.handle("compare methods anxiety restlessness")
    formatted = result["formatted"]
    assert "Method Comparison" in formatted or "Kent" in formatted or "Boenninghausen" in formatted


# ── Edge cases ─────────────────────────────────────────────────────────────

def test_bridge_master_score_empty_symptoms(bridge):
    result = bridge.handle("master score")
    # With no symptoms, the regex may not match; fallback routes to repertorize
    # or returns unknown. Either is acceptable.
    assert result["type"] in ("master_score", "repertorize", "unknown")


def test_bridge_master_score_nonsense(bridge):
    result = bridge.handle("master score xyz123qwerty")
    # Should return empty results or handle gracefully
    assert result["type"] == "master_score"


# ── Integration: master vs regular repertorize ─────────────────────────────

def test_bridge_master_differs_from_regular(bridge):
    master = bridge.handle("master score anxiety restlessness")
    regular = bridge.handle("repertorize anxiety restlessness")
    assert master["type"] == "master_score"
    assert regular["type"] == "repertorize"
    # Master should include sub-scores; regular should not
    if master["result"] and regular["result"]:
        assert "sub_scores" in master["result"][0]
        assert "sub_scores" not in regular["result"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
