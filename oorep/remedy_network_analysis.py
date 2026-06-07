"""
Remedy Network Analysis — Graph Centrality & Community Detection (Module #65)

Analyzes the remedy relationship graph from remedy_relationships_v2.py using:
  - Degree, betweenness, closeness, eigenvector centrality
  - Community detection via label propagation
  - Path length and diameter metrics
  - PageRank-style influence ranking

Pure Python. Dashboard visual: Force-directed network graph with
community-colored nodes, centrality-sized nodes.

Usage:
    from oorep.remedy_network_analysis import RemedyNetworkAnalyzer
    analyzer = RemedyNetworkAnalyzer(data_dir="data")
    
    centrality = analyzer.compute_centrality("PULS")
    communities = analyzer.detect_communities()
    pagerank = analyzer.pagerank()
    paths = analyzer.shortest_path("PULS", "NAT_M")
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class CentralityMetrics:
    degree: float
    betweenness: float
    closeness: float
    eigenvector: float
    pagerank: float


class RemedyNetworkAnalyzer:
    """
    Graph analysis engine for remedy relationship networks.
    """

    def __init__(self, data_dir: Optional[str] = None, graph_data: Optional[Dict[str, Any]] = None):
        self.data_dir = Path(data_dir) if data_dir else Path.home() / "projects" / "oorep-local-repertory" / "data"
        
        if graph_data:
            self.graph = graph_data
        else:
            self.graph = self._load_default_graph()

        self._adj: Dict[str, Set[str]] = defaultdict(set)
        self._weights: Dict[Tuple[str, str], float] = {}
        self._build_adjacency()

    def _load_default_graph(self) -> Dict[str, Any]:
        """Load from remedy_relationships.json or build minimal classical graph."""
        path = self.data_dir / "remedy_relationships.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        # Minimal classical graph for testing
        return {
            "nodes": [
                {"id": "PULS", "label": "Pulsatilla"},
                {"id": "NAT_M", "label": "Natrum Muriaticum"},
                {"id": "ARS", "label": "Arsenicum Album"},
                {"id": "LACH", "label": "Lachesis"},
                {"id": "SULPH", "label": "Sulphur"},
                {"id": "NUX_V", "label": "Nux Vomica"},
                {"id": "BRY", "label": "Bryonia"},
                {"id": "PHOS", "label": "Phosphorus"},
                {"id": "MERC", "label": "Mercurius"},
                {"id": "SIL", "label": "Silicea"},
            ],
            "edges": [
                {"source": "PULS", "target": "NAT_M", "type": "complementary", "weight": 0.9},
                {"source": "PULS", "target": "SULPH", "type": "follows_well", "weight": 0.8},
                {"source": "ARS", "target": "NAT_M", "type": "inimical", "weight": 0.7},
                {"source": "ARS", "target": "LACH", "type": "antidote", "weight": 0.6},
                {"source": "SULPH", "target": "NUX_V", "type": "complementary", "weight": 0.85},
                {"source": "SULPH", "target": "BRY", "type": "follows_well", "weight": 0.75},
                {"source": "NUX_V", "target": "BRY", "type": "complementary", "weight": 0.9},
                {"source": "PHOS", "target": "MERC", "type": "inimical", "weight": 0.65},
                {"source": "PHOS", "target": "SIL", "type": "antidote", "weight": 0.55},
                {"source": "MERC", "target": "SIL", "type": "follows_well", "weight": 0.7},
                {"source": "LACH", "target": "SULPH", "type": "complementary", "weight": 0.8},
                {"source": "NAT_M", "target": "BRY", "type": "follows_well", "weight": 0.6},
            ],
        }

    def _build_adjacency(self) -> None:
        """Build adjacency list and weight map."""
        for node in self.graph.get("nodes", []):
            nid = node["id"]
            if nid not in self._adj:
                self._adj[nid] = set()

        for edge in self.graph.get("edges", []):
            s = edge["source"]
            t = edge["target"]
            w = edge.get("weight", 1.0)
            self._adj[s].add(t)
            self._adj[t].add(s)
            self._weights[(s, t)] = w
            self._weights[(t, s)] = w

    @property
    def nodes(self) -> List[str]:
        return list(self._adj.keys())

    @property
    def edge_count(self) -> int:
        return len(self.graph.get("edges", []))

    # ── Centrality ────────────────────────────────────────────────────────────

    def compute_centrality(self, remedy: str) -> Optional[Dict[str, float]]:
        """Compute all centrality metrics for a single remedy."""
        if remedy not in self._adj:
            return None

        degree = self._degree_centrality(remedy)
        betweenness = self._betweenness_centrality(remedy)
        closeness = self._closeness_centrality(remedy)
        eigenvector = self._eigenvector_centrality().get(remedy, 0)
        pagerank = self.pagerank().get(remedy, 0)

        return {
            "degree": round(degree, 4),
            "betweenness": round(betweenness, 4),
            "closeness": round(closeness, 4),
            "eigenvector": round(eigenvector, 4),
            "pagerank": round(pagerank, 4),
        }

    def all_centralities(self) -> Dict[str, Dict[str, float]]:
        """Compute centrality for all remedies."""
        eigen = self._eigenvector_centrality()
        pr = self.pagerank()
        result = {}
        for node in self.nodes:
            result[node] = {
                "degree": round(self._degree_centrality(node), 4),
                "betweenness": round(self._betweenness_centrality(node), 4),
                "closeness": round(self._closeness_centrality(node), 4),
                "eigenvector": round(eigen.get(node, 0), 4),
                "pagerank": round(pr.get(node, 0), 4),
            }
        return result

    def _degree_centrality(self, node: str) -> float:
        n = len(self.nodes)
        if n <= 1:
            return 0.0
        return len(self._adj[node]) / (n - 1)

    def _betweenness_centrality(self, target_node: str) -> float:
        """Normalized betweenness via shortest-path counting."""
        n = len(self.nodes)
        if n <= 2:
            return 0.0

        total = 0
        between = 0
        for s in self.nodes:
            for t in self.nodes:
                if s == t or s == target_node or t == target_node:
                    continue
                paths = self._all_shortest_paths(s, t)
                if not paths:
                    continue
                total += 1
                through_target = sum(1 for p in paths if target_node in p)
                between += through_target / len(paths)

        denom = (n - 1) * (n - 2) / 2
        return between / denom if denom else 0

    def _all_shortest_paths(self, start: str, end: str) -> List[List[str]]:
        """BFS to find all shortest paths."""
        if start == end:
            return [[start]]
        if start not in self._adj or end not in self._adj:
            return []

        queue = deque([(start, [start])])
        shortest_len = None
        all_paths = []
        visited_at_depth: Dict[str, int] = {start: 0}

        while queue:
            node, path = queue.popleft()
            depth = len(path) - 1

            if shortest_len is not None and depth >= shortest_len:
                continue

            for neighbor in self._adj[node]:
                if neighbor in path:
                    continue
                new_path = path + [neighbor]
                if neighbor == end:
                    if shortest_len is None:
                        shortest_len = len(new_path)
                    all_paths.append(new_path)
                else:
                    if neighbor not in visited_at_depth or visited_at_depth[neighbor] >= depth + 1:
                        visited_at_depth[neighbor] = depth + 1
                        queue.append((neighbor, new_path))

        return all_paths

    def _closeness_centrality(self, node: str) -> float:
        """Harmonic closeness (handles disconnected graphs)."""
        n = len(self.nodes)
        if n <= 1:
            return 0.0

        total_distance = 0
        reachable = 0
        distances = self._bfs_distances(node)
        for other, dist in distances.items():
            if other != node and dist < float("inf"):
                total_distance += 1 / dist
                reachable += 1

        return total_distance / (n - 1) if n > 1 else 0

    def _bfs_distances(self, start: str) -> Dict[str, float]:
        """BFS distance from start to all nodes."""
        dist = {n: float("inf") for n in self.nodes}
        dist[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in self._adj[node]:
                if dist[neighbor] == float("inf"):
                    dist[neighbor] = dist[node] + 1
                    queue.append(neighbor)
        return dist

    def _eigenvector_centrality(self, iterations: int = 100, tolerance: float = 1e-6) -> Dict[str, float]:
        """Power iteration for eigenvector centrality."""
        nodes = self.nodes
        n = len(nodes)
        if n == 0:
            return {}

        x = {node: 1.0 / n for node in nodes}
        for _ in range(iterations):
            x_new = {node: 0.0 for node in nodes}
            for node in nodes:
                for neighbor in self._adj[node]:
                    x_new[node] += x[neighbor] * self._weights.get((node, neighbor), 1.0)

            norm = math.sqrt(sum(v ** 2 for v in x_new.values()))
            if norm == 0:
                break
            x_new = {k: v / norm for k, v in x_new.items()}

            if all(abs(x_new[k] - x[k]) < tolerance for k in nodes):
                break
            x = x_new

        return x

    def pagerank(self, damping: float = 0.85, iterations: int = 100, tolerance: float = 1e-6) -> Dict[str, float]:
        """PageRank on remedy relationship graph."""
        nodes = self.nodes
        n = len(nodes)
        if n == 0:
            return {}

        pr = {node: 1.0 / n for node in nodes}
        out_degrees = {node: len(self._adj[node]) for node in nodes}

        for _ in range(iterations):
            pr_new = {}
            for node in nodes:
                rank = (1 - damping) / n
                for neighbor in self._adj[node]:
                    if out_degrees[neighbor] > 0:
                        rank += damping * pr[neighbor] * self._weights.get((neighbor, node), 1.0) / out_degrees[neighbor]
                pr_new[node] = rank

            norm = sum(pr_new.values())
            if norm > 0:
                pr_new = {k: v / norm for k, v in pr_new.items()}

            if all(abs(pr_new[k] - pr[k]) < tolerance for k in nodes):
                break
            pr = pr_new

        return pr

    # ── Community Detection ─────────────────────────────────────────────────────

    def detect_communities(self, iterations: int = 50) -> Dict[str, Any]:
        """
        Label propagation community detection.
        Fast, near-linear, no parameters needed.
        """
        nodes = self.nodes
        if not nodes:
            return {"communities": [], "modularity": 0}

        # Initialize each node with unique label
        labels = {node: i for i, node in enumerate(nodes)}

        for _ in range(iterations):
            changed = False
            for node in nodes:
                neighbor_labels = defaultdict(float)
                for neighbor in self._adj[node]:
                    weight = self._weights.get((node, neighbor), 1.0)
                    neighbor_labels[labels[neighbor]] += weight

                if neighbor_labels:
                    best_label = max(neighbor_labels.items(), key=lambda x: x[1])[0]
                    if best_label != labels[node]:
                        labels[node] = best_label
                        changed = True

            if not changed:
                break

        # Group by label
        communities: Dict[int, List[str]] = defaultdict(list)
        for node, label in labels.items():
            communities[label].append(node)

        community_list = [
            {"id": i, "nodes": nodes, "size": len(nodes)}
            for i, nodes in communities.items()
        ]

        modularity = self._compute_modularity(labels)

        return {
            "community_count": len(community_list),
            "communities": community_list,
            "modularity": round(modularity, 4),
            "node_labels": labels,
        }

    def _compute_modularity(self, labels: Dict[str, int]) -> float:
        """Newman modularity for label assignment."""
        m = sum(len(self._adj[n]) for n in self.nodes) / 2
        if m == 0:
            return 0

        mod = 0.0
        for node in self.nodes:
            for neighbor in self._adj[node]:
                if labels[node] == labels[neighbor]:
                    ki = len(self._adj[node])
                    kj = len(self._adj[neighbor])
                    mod += 1 - (ki * kj) / (2 * m)

        return mod / (2 * m)

    # ── Path Analysis ─────────────────────────────────────────────────────────

    def shortest_path(self, start: str, end: str) -> Optional[Dict[str, Any]]:
        """Shortest path between two remedies."""
        if start not in self._adj or end not in self._adj:
            return None

        distances = self._bfs_distances(start)
        dist = distances.get(end, float("inf"))
        if dist == float("inf"):
            return {"path": [], "distance": None, "reachable": False}

        # Reconstruct path by backtracking from end
        path = [end]
        current = end
        while current != start:
            for neighbor in self._adj[current]:
                if distances.get(neighbor, float("inf")) == distances[current] - 1:
                    path.append(neighbor)
                    current = neighbor
                    break

        path.reverse()
        return {
            "path": path,
            "distance": len(path) - 1,
            "reachable": True,
        }

    def graph_diameter(self) -> int:
        """Longest shortest path (diameter)."""
        max_dist = 0
        for node in self.nodes:
            dists = self._bfs_distances(node)
            for other, d in dists.items():
                if d < float("inf") and other != node:
                    max_dist = max(max_dist, d)
        return int(max_dist)

    def average_path_length(self) -> float:
        """Average shortest path between all connected pairs."""
        total = 0
        count = 0
        for node in self.nodes:
            dists = self._bfs_distances(node)
            for other, d in dists.items():
                if other != node and d < float("inf"):
                    total += d
                    count += 1
        return total / count if count else 0

    def clustering_coefficient(self, node: str) -> float:
        """Local clustering coefficient."""
        neighbors = list(self._adj[node])
        k = len(neighbors)
        if k < 2:
            return 0.0

        triangles = 0
        for i in range(k):
            for j in range(i + 1, k):
                if neighbors[j] in self._adj[neighbors[i]]:
                    triangles += 1

        return 2 * triangles / (k * (k - 1))

    def global_clustering(self) -> float:
        """Average local clustering coefficient."""
        coeffs = [self.clustering_coefficient(n) for n in self.nodes]
        return sum(coeffs) / len(coeffs) if coeffs else 0

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 65,
            "feature_name": "Remedy Network Analysis",
            "version": "1.0",
            "supports": [
                "degree_centrality", "betweenness_centrality", "closeness_centrality",
                "eigenvector_centrality", "pagerank", "community_detection",
                "shortest_path", "graph_diameter", "clustering_coefficient",
            ],
            "pure_python": True,
        }
