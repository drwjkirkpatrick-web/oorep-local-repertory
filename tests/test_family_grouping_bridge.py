"""
Test Family Grouping Bridge Integration

Tests NL routing for family grouping commands through OOREPBridge.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path.home() / "projects" / "oorep-local-repertory"))
_BRIDGE_DIR = Path.home() / ".hermes" / "skills" / "clinic" / "oorep-hermes-bridge" / "scripts"
sys.path.insert(0, str(_BRIDGE_DIR))

from oorep_bridge import OOREPBridge


@pytest.fixture(scope="module")
def bridge():
    return OOREPBridge()


# ── Family Group routing ─────────────────────────────────────────────────────

def test_bridge_family_group_routing(bridge):
    result = bridge.handle("family group anxiety restlessness")
    assert result["type"] == "family_group"
    assert "result" in result
    assert "formatted" in result


def test_bridge_kingdom_group_routing(bridge):
    result = bridge.handle("kingdom group anxiety restlessness")
    assert result["type"] == "kingdom_group"
    assert "result" in result


# ── Filter Kingdom routing ──────────────────────────────────────────────────

def test_bridge_filter_kingdom_plant(bridge):
    result = bridge.handle("filter kingdom plant anxiety restlessness")
    assert result["type"] == "filter_kingdom"
    assert result["kingdom"] == "plant"


def test_bridge_filter_kingdom_mineral(bridge):
    result = bridge.handle("filter kingdom mineral anxiety restlessness")
    assert result["type"] == "filter_kingdom"
    assert result["kingdom"] == "mineral"


# ── Family/Kingdom Compare routing ───────────────────────────────────────────

def test_bridge_compare_families_routing(bridge):
    result = bridge.handle("compare families Solanaceae and Ranunculaceae")
    assert result["type"] == "compare_families"
    assert "family_a" in result
    assert result["family_a"] == "Solanaceae"


def test_bridge_compare_kingdoms_routing(bridge):
    result = bridge.handle("compare kingdoms plant and mineral")
    assert result["type"] == "compare_kingdoms"
    assert result["kingdom_a"] == "plant"
    assert result["kingdom_b"] == "mineral"


# ── Family Summary / List routing ────────────────────────────────────────────

def test_bridge_family_summary_routing(bridge):
    result = bridge.handle("family summary Solanaceae")
    assert result["type"] == "family_summary"
    assert "result" in result


def test_bridge_list_families_routing(bridge):
    result = bridge.handle("list families")
    assert result["type"] == "list_families"
    assert "result" in result


# ── Enrich taxonomy routing ─────────────────────────────────────────────────

def test_bridge_enrich_taxonomy_routing(bridge):
    result = bridge.handle("enrich taxonomy anxiety restlessness")
    assert result["type"] == "enrich_taxonomy"
    assert "result" in result


# ── Formatted output checks ─────────────────────────────────────────────────

def test_bridge_family_group_formatted(bridge):
    result = bridge.handle("family group anxiety restlessness")
    formatted = result["formatted"]
    assert "Family" in formatted or "family" in formatted


def test_bridge_family_summary_formatted(bridge):
    result = bridge.handle("family summary Solanaceae")
    formatted = result["formatted"]
    assert "Solanaceae" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
