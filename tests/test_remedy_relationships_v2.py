"""
Tests for Advanced Remedy Relationships V2 (Feature #25)

Covers: chain, similar_to, follow-up, PageRank centrality, edge loading.
"""

import pytest
from oorep.remedy_relationships_v2 import RemedyGraphEngine


class TestRemedyGraphChain:

    def test_chain_depth_2(self):
        engine = RemedyGraphEngine()
        chain = engine.get_chain("PULS", depth=2)
        assert chain["root"] == "PULS"
        assert len(chain["chain"]) > 0
        assert any(c["remedy"] == "SIL" for c in chain["chain"])

    def test_chain_no_data(self):
        engine = RemedyGraphEngine(relationship_data={})
        chain = engine.get_chain("PULS", depth=2)
        assert chain["chain"] == []

    def test_chain_unknown_remedy(self):
        engine = RemedyGraphEngine()
        chain = engine.get_chain("ZZZ", depth=2)
        assert chain["chain"] == []


class TestSimilarTo:

    def test_similar_by_rel_type(self):
        engine = RemedyGraphEngine()
        sim = engine.similar_to("PULS", rel_types=["complementary"])
        assert any(s["remedy"] == "SIL" for s in sim)

    def test_similar_no_rel_types(self):
        engine = RemedyGraphEngine()
        sim = engine.similar_to("PULS", top_n=10)
        assert len(sim) > 0


class TestFollowUp:

    def test_find_follow_up(self):
        engine = RemedyGraphEngine()
        fu = engine.find_follow_up("LYC")
        assert fu is not None
        assert fu["relationship"] in ["follows", "complementary"]

    def test_find_follow_up_none(self):
        engine = RemedyGraphEngine()
        fu = engine.find_follow_up("ZZZ")
        assert fu is None


class TestCentrality:

    def test_central_remedies(self):
        engine = RemedyGraphEngine()
        central = engine.central_remedies(top_n=10)
        assert len(central) > 0
        assert all("centrality" in c for c in central)

    def test_centrality_ranks(self):
        engine = RemedyGraphEngine()
        central = engine.central_remedies(top_n=5)
        for i in range(len(central) - 1):
            assert central[i]["centrality"] >= central[i + 1]["centrality"]


class TestEdges:

    def test_get_all_edges(self):
        engine = RemedyGraphEngine()
        edges = engine.get_all_edges("PULS")
        assert len(edges) > 0

    def test_empty_edges(self):
        engine = RemedyGraphEngine()
        edges = engine.get_all_edges("ZZZ")
        assert edges == []


class TestFeatureOverview:

    def test_overview(self):
        engine = RemedyGraphEngine()
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 25
        assert "graph_nodes" in ov
