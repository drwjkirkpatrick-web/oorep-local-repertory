"""Tests for remedy_network_analysis.py (Module #65)"""

import pytest
from oorep.remedy_network_analysis import RemedyNetworkAnalyzer


@pytest.fixture
def analyzer():
    return RemedyNetworkAnalyzer()


class TestCentrality:

    def test_degree_centrality(self, analyzer):
        c = analyzer.compute_centrality("PULS")
        assert c is not None
        assert 0 <= c["degree"] <= 1
        assert c["degree"] > 0  # PULS has edges

    def test_betweenness_centrality(self, analyzer):
        c = analyzer.compute_centrality("SULPH")
        assert c["betweenness"] >= 0

    def test_closeness_centrality(self, analyzer):
        c = analyzer.compute_centrality("PULS")
        assert c["closeness"] >= 0

    def test_eigenvector_centrality(self, analyzer):
        c = analyzer.compute_centrality("PULS")
        assert c["eigenvector"] >= 0

    def test_pagerank(self, analyzer):
        c = analyzer.compute_centrality("PULS")
        assert c["pagerank"] > 0

    def test_all_centralities(self, analyzer):
        all_c = analyzer.all_centralities()
        assert len(all_c) == 10
        for node, metrics in all_c.items():
            assert "degree" in metrics
            assert "betweenness" in metrics

    def test_unknown_remedy(self, analyzer):
        assert analyzer.compute_centrality("UNKNOWN") is None


class TestCommunities:

    def test_detect_communities(self, analyzer):
        result = analyzer.detect_communities()
        assert "communities" in result
        assert result["community_count"] >= 1
        assert -1 <= result["modularity"] <= 1

    def test_node_labels_assigned(self, analyzer):
        result = analyzer.detect_communities()
        assert "node_labels" in result
        assert len(result["node_labels"]) == 10


class TestPaths:

    def test_shortest_path_exists(self, analyzer):
        path = analyzer.shortest_path("PULS", "SULPH")
        assert path is not None
        assert path["reachable"] is True
        assert len(path["path"]) > 0

    def test_shortest_path_direct(self, analyzer):
        path = analyzer.shortest_path("PULS", "NAT_M")
        assert path is not None
        assert path["distance"] == 1

    def test_shortest_path_unreachable(self, analyzer):
        # Create disconnected graph
        a = RemedyNetworkAnalyzer(graph_data={
            "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
            "edges": [{"source": "A", "target": "B", "weight": 1}]
        })
        path = a.shortest_path("A", "C")
        assert path["reachable"] is False

    def test_graph_diameter(self, analyzer):
        d = analyzer.graph_diameter()
        assert d >= 1

    def test_average_path_length(self, analyzer):
        apl = analyzer.average_path_length()
        assert apl > 0


class TestClustering:

    def test_local_clustering(self, analyzer):
        cc = analyzer.clustering_coefficient("SULPH")
        assert 0 <= cc <= 1

    def test_global_clustering(self, analyzer):
        gc = analyzer.global_clustering()
        assert 0 <= gc <= 1


class TestFeatureOverview:

    def test_overview(self, analyzer):
        ov = analyzer.get_feature_overview()
        assert ov["feature_id"] == 65
        assert "pagerank" in ov["supports"]
