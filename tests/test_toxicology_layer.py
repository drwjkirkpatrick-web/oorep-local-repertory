"""
Tests for Toxicology Layer (Feature #23)

Covers: inimical pairs, antidotes, DB checks, conflicts, empty.
"""

import pytest
from oorep.toxicology_layer import ToxicologyLayer


class TestInimicalPairs:

    def test_ars_ign_inimical(self):
        layer = ToxicologyLayer()
        result = layer.check_safety("ARS", "X", prior_remedies=["IGN"])
        assert result["severity"] == "high"
        assert not result["safe"]
        assert any(a["type"] == "inimical" for a in result["alerts"])

    def test_nux_v_coff_inimical(self):
        layer = ToxicologyLayer()
        result = layer.check_safety("NUX-V", "X", prior_remedies=["COFF"])
        assert result["severity"] == "high"

    def test_no_conflict(self):
        layer = ToxicologyLayer()
        result = layer.check_safety("PULS", "X", prior_remedies=["SIL"])
        assert result["severity"] == "none"
        assert result["safe"]

    def test_antidote_pair(self):
        layer = ToxicologyLayer()
        result = layer.check_safety("NUX-V", "X", prior_remedies=["PULS"])
        assert any(a["type"] == "antidote" for a in result["alerts"])

    def test_find_conflicts_in_list(self):
        layer = ToxicologyLayer()
        # ARS-IGN inimical, PHOS-CAUST inimical, NUX-V-COFF antidotes
        conflicts = layer.find_conflicts(["ARS", "IGN", "PHOS", "CAUST", "NUX-V", "COFF"])
        types = [c["type"] for c in conflicts]
        assert "inimical" in types
        assert "antidote" in types

    def test_get_antidotes(self):
        layer = ToxicologyLayer()
        ants = layer.get_antidotes("ARS")
        assert "NUX-V" in ants

    def test_add_interaction(self):
        layer = ToxicologyLayer()
        layer.add_interaction("A", "B", "inimical")
        # Should now be in inimical pairs
        result = layer.check_safety("A", "X", prior_remedies=["B"])
        assert result["severity"] == "high"

    def test_empty_prior(self):
        layer = ToxicologyLayer()
        result = layer.check_safety("ARS", "X")
        assert result["severity"] == "none"

    def test_feature_overview(self):
        layer = ToxicologyLayer()
        ov = layer.get_feature_overview()
        assert ov["feature_id"] == 23
        assert ov["cold_start_capable"] is True
