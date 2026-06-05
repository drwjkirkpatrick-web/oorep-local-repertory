"""
Advanced Remedy Relationships V2 — Feature #25

Enhanced remedy relationships: directional graphs, strength scoring,
temporal sequencing. Complementary → follow-up → antidotal chains.
Network analysis: PageRank-style 'central remedies' in the graph.

Usage:
    from oorep.remedy_relationships_v2 import RemedyGraphEngine
    engine = RemedyGraphEngine(db_path="data/feedback.db")

    chain = engine.get_chain("PULS", depth=3)
    pagerank = engine.central_remedies(top_n=10)
    similar = engine.similar_to("ARS", method="network", top_n=5)
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class RemedyGraphEngine:
    """
    Remedy relationship graph with network analysis.
    """

    # Classical relationship strength (from materia medica)
    CLASSICAL_RELATIONSHIPS: Dict[str, List[Dict]] = {
        "PULS": [{"remedy": "SIL", "rel": "complementary", "strength": 0.8},
                  {"remedy": "COFF", "rel": "antidote", "strength": 0.6}],
        "ARS": [{"remedy": "NUX-V", "rel": "complementary", "strength": 0.7},
                 {"remedy": "CARB-V", "rel": "follows", "strength": 0.5}],
        "NUX-V": [{"remedy": "PULS", "rel": "antidote", "strength": 0.7},
                   {"remedy": "COFF", "rel": "antidote", "strength": 0.6}],
        "SIL": [{"remedy": "PULS", "rel": "complementary", "strength": 0.8},
                 {"remedy": "MERC", "rel": "inimical", "strength": 0.9}],
        "LYC": [{"remedy": "CAUST", "rel": "follows", "strength": 0.7},
                 {"remedy": "GRAPH", "rel": "complementary", "strength": 0.6}],
        "SULPH": [{"remedy": "LYC", "rel": "follows", "strength": 0.7},
                   {"remedy": "ARS", "rel": "complementary", "strength": 0.5}],
    }

    def __init__(self, db_path: Optional[str] = None, relationship_data: Optional[Dict] = None):
        self.db_path = db_path
        self.edges: Dict[str, List[Dict]] = {}
        self._load_relationships(relationship_data)

    def _load_relationships(self, data: Optional[Dict] = None) -> None:
        """Load graph edges from data or defaults."""
        self.edges = defaultdict(list)
        base = self.CLASSICAL_RELATIONSHIPS if data is None else data
        for rem, targets in base.items():
            self.edges[rem.upper().replace(".", "")] = targets
        if self.db_path:
            self._load_from_db()

    def _load_from_db(self) -> None:
        """Load additional edges from feedback.db."""
        if not self.db_path:
            return
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            "SELECT remedy_a, remedy_b, rel_type, source FROM remedy_relationships"
        )
        for a, b, rel_type, source in c.fetchall():
            self.edges[a.upper().replace(".", "")].append({
                "remedy": b.upper().replace(".", ""),
                "rel": rel_type.lower(),
                "strength": 0.5,
                "source": source,
            })
        conn.close()

    # ── Graph traversal ────────────────────────────────────────────────────

    def get_chain(self, remedy: str, depth: int = 3) -> Dict[str, Any]:
        """
        Follow the relationship chain from a remedy.
        Returns: {remedy, chain: [{remedy, rel, strength, depth}, ...]}.
        """
        rem = remedy.upper().replace(".", "")
        visited: Set[str] = set()
        chain: List[Dict] = []

        def walk(r: str, d: int):
            if d > depth or r in visited or not self.edges.get(r):
                return
            visited.add(r)
            for edge in self.edges.get(r, []):
                target = edge.get("remedy", "")
                if target not in visited:
                    chain.append({
                        "remedy": target,
                        "rel": edge.get("rel", ""),
                        "strength": edge.get("strength", 0.0),
                        "depth": d,
                    })
                    walk(target, d + 1)

        walk(rem, 1)
        return {"root": remedy, "chain": chain}

    def similar_to(
        self,
        remedy: str,
        method: str = "network",  # or "classical"
        rel_types: Optional[List[str]] = None,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find remedies related to the given one."""
        rem = remedy.upper().replace(".", "")
        edges = self.edges.get(rem, [])
        if rel_types:
            filtered = [e for e in edges if e.get("rel", "").lower() in rel_types]
        else:
            filtered = edges

        scored = []
        for e in filtered:
            scored.append({
                "remedy": e.get("remedy", ""),
                "relationship": e.get("rel", ""),
                "strength": e.get("strength", 0.0),
                "source": e.get("source", "classical"),
            })
        scored.sort(key=lambda x: x["strength"], reverse=True)
        return scored[:top_n]

    def find_follow_up(self, remedy: str) -> Optional[Dict[str, Any]]:
        """Find the primary follow-up or complementary remedy."""
        edges = self.edges.get(remedy.upper().replace(".", ""), [])
        for rel_type in ["follows", "complementary"]:
            for e in edges:
                if e.get("rel", "").lower() == rel_type:
                    return {
                        "remedy": e.get("remedy", ""),
                        "relationship": rel_type,
                        "strength": e.get("strength", 0.0),
                    }
        return None

    def get_all_edges(self, remedy: str) -> List[Dict[str, Any]]:
        """All outgoing edges for a remedy."""
        return self.edges.get(remedy.upper().replace(".", ""), [])

    # ── Network analysis ───────────────────────────────────────────────────

    def central_remedies(self, top_n: int = 10, iterations: int = 20) -> List[Dict[str, Any]]:
        """
        PageRank-style centrality on the remedy relationship graph.
        Returns top remedies ranked by graph centrality.
        """
        nodes: Set[str] = set(self.edges.keys())
        for targets in self.edges.values():
            for t in targets:
                nodes.add(t.get("remedy", ""))
        nodes = {n for n in nodes if n}
        if not nodes:
            return []

        # Initialize scores
        scores: Dict[str, float] = {n: 1.0 / len(nodes) for n in nodes}
        damping = 0.85

        for _ in range(iterations):
            new_scores: Dict[str, float] = {}
            for n in nodes:
                incoming = 0.0
                for src, edges in self.edges.items():
                    for e in edges:
                        if e.get("remedy", "") == n:
                            outdegree = max(len(self.edges.get(src, [])), 1)
                            incoming += scores.get(src, 0.0) * e.get("strength", 0.5) / outdegree
                new_scores[n] = (1 - damping) / len(nodes) + damping * incoming
            scores = new_scores

        ranked = sorted(
            [{"remedy": k, "centrality": round(v, 6)} for k, v in scores.items()],
            key=lambda x: x["centrality"],
            reverse=True,
        )
        return ranked[:top_n]

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 25,
            "feature_name": "Advanced Remedy Relationships",
            "graph_nodes": len(self.edges),
            "edge_types": ["complementary", "antidote", "follows", "inimical"],
            "cold_start_capable": True,
            "version": "1.0",
        }
