"""
Bayesian Network of Rubric Dependencies (Module #127)

Models the conditional independence structure between rubrics using mutual
information and a simple Chow-Liu tree approximation. This reveals which
rubrics carry redundant information (one implies the other) and which
provide independent evidence (should both be asked).

Math:
    Mutual information: I(X; Y) = sum_{x, y} P(x, y) log(P(x, y) / (P(x) P(y)))
    Construct a complete graph with edge weights = I(rubric_i; rubric_j)
    Find the maximum spanning tree (Chow-Liu) → tree-structured Bayesian network
    For each rubric, compute its Markov blanket (parents + children) in the tree

Practical use:
    - If a parent rubric is present, child rubrics are partially redundant.
    - If a child rubric provides a lot of new information, it should be
      prioritized in case-taking.

Usage:
    from oorep.bayesian_rubric_network import BayesianRubricNetwork
    net = BayesianRubricNetwork()
    net.fit(case_database)
    report = net.rubric_neighborhood(rubric_id=101)
"""

from __future__ import annotations

import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class RubricNode:
    rubric_id: int
    rubric_text: str
    chapter: str
    frequency: float  # P(rubric=1) across the case database


@dataclass
class RubricEdge:
    rubric_a: int
    rubric_b: int
    mutual_information: float
    conditional_prob: float  # P(B=1 | A=1)


@dataclass
class NetworkReport:
    n_rubrics: int
    n_edges: int
    top_edges: List[RubricEdge]
    redundancy_pairs: List[Tuple[int, int, float]]  # (a, b, I)
    tree_structure: Dict[int, List[int]]  # parent rubric → child rubrics
    runtime_ms: float


class BayesianRubricNetwork:
    """
    Chow-Liu tree approximation of the rubric dependency structure.
    """

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory()
        self.cases: List[Set[int]] = []  # Each case = set of rubric ids

    def fit(self, case_database: List[List[int]]) -> "BayesianRubricNetwork":
        """Fit the network from a database of past cases (each = list of rubric ids)."""
        self.cases = [set(case) for case in case_database]
        return self

    def _mutual_information(
        self,
        rubric_a: int,
        rubric_b: int,
    ) -> float:
        """
        Compute mutual information I(A; B) in bits from case data.
        I(A; B) = sum P(a, b) log2( P(a, b) / (P(a) P(b)) )
        """
        n = len(self.cases)
        if n == 0:
            return 0.0
        # Joint counts
        n11 = sum(1 for c in self.cases if rubric_a in c and rubric_b in c)
        n10 = sum(1 for c in self.cases if rubric_a in c and rubric_b not in c)
        n01 = sum(1 for c in self.cases if rubric_a not in c and rubric_b in c)
        n00 = n - n11 - n10 - n01
        # Marginals
        pa1 = (n11 + n10) / n
        pb1 = (n11 + n01) / n
        # MI
        mi = 0.0
        for count, pa, pb in [
            (n11, pa1, pb1),
            (n10, pa1, 1 - pb1),
            (n01, 1 - pa1, pb1),
            (n00, 1 - pa1, 1 - pb1),
        ]:
            if count == 0:
                continue
            pab = count / n
            denom = pa * pb
            if denom > 0:
                mi += pab * math.log2(pab / denom)
        return mi

    def _build_complete_graph(
        self,
        rubric_ids: List[int],
    ) -> List[RubricEdge]:
        """Compute MI for all pairs in the rubric id list."""
        edges: List[RubricEdge] = []
        n = len(rubric_ids)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = rubric_ids[i], rubric_ids[j]
                mi = self._mutual_information(a, b)
                if mi < 0.001:
                    continue
                # Conditional probability P(B=1 | A=1)
                p_b_given_a = sum(
                    1 for c in self.cases if a in c and b in c
                ) / max(1, sum(1 for c in self.cases if a in c))
                edges.append(
                    RubricEdge(
                        rubric_a=a,
                        rubric_b=b,
                        mutual_information=mi,
                        conditional_prob=p_b_given_a,
                    )
                )
        return edges

    @staticmethod
    def _maximum_spanning_tree(
        nodes: List[int],
        edges: List[RubricEdge],
    ) -> Dict[int, List[int]]:
        """
        Kruskal's algorithm for maximum spanning tree (Chow-Liu).
        Returns adjacency list (parent → [children]).
        """
        # Sort edges by MI descending
        sorted_edges = sorted(edges, key=lambda e: e.mutual_information, reverse=True)
        # Union-Find
        parent_uf: Dict[int, int] = {n: n for n in nodes}
        rank: Dict[int, int] = {n: 0 for n in nodes}

        def find(x: int) -> int:
            while parent_uf[x] != x:
                parent_uf[x] = parent_uf[parent_uf[x]]
                x = parent_uf[x]
            return x

        def union(x: int, y: int) -> bool:
            rx, ry = find(x), find(y)
            if rx == ry:
                return False
            if rank[rx] < rank[ry]:
                rx, ry = ry, rx
            parent_uf[ry] = rx
            if rank[rx] == rank[ry]:
                rank[rx] += 1
            return True

        adjacency: Dict[int, List[int]] = {n: [] for n in nodes}
        n_edges_added = 0
        for edge in sorted_edges:
            if union(edge.rubric_a, edge.rubric_b):
                adjacency[edge.rubric_a].append(edge.rubric_b)
                adjacency[edge.rubric_b].append(edge.rubric_a)
                n_edges_added += 1
                if n_edges_added >= len(nodes) - 1:
                    break

        return adjacency

    def fit_and_build(
        self,
        rubric_ids: Optional[List[int]] = None,
        top_n_edges: int = 20,
    ) -> NetworkReport:
        """
        Build the Bayesian network from the case database.
        """
        import time
        t0 = time.time()
        # Default: take top 50 most-frequent rubrics
        if rubric_ids is None:
            freq: Counter = Counter()
            for case in self.cases:
                for rid in case:
                    freq[rid] += 1
            rubric_ids = [rid for rid, _ in freq.most_common(50)]
        if not rubric_ids:
            return NetworkReport(
                n_rubrics=0, n_edges=0,
                top_edges=[], redundancy_pairs=[],
                tree_structure={}, runtime_ms=0.0,
            )

        # Build complete graph (MI for all pairs)
        edges = self._build_complete_graph(rubric_ids)
        edges.sort(key=lambda e: e.mutual_information, reverse=True)

        # Chow-Liu tree
        tree = self._maximum_spanning_tree(rubric_ids, edges)

        # Top redundancy pairs: high MI, conditional prob near 0 or 1
        redundancy: List[Tuple[int, int, float]] = []
        for edge in edges:
            if edge.mutual_information > 0.05 and (
                edge.conditional_prob > 0.85 or edge.conditional_prob < 0.15
            ):
                redundancy.append((edge.rubric_a, edge.rubric_b, edge.mutual_information))
        redundancy.sort(key=lambda x: x[2], reverse=True)

        return NetworkReport(
            n_rubrics=len(rubric_ids),
            n_edges=len(edges),
            top_edges=edges[:top_n_edges],
            redundancy_pairs=redundancy[:10],
            tree_structure=tree,
            runtime_ms=(time.time() - t0) * 1000,
        )

    def rubric_neighborhood(
        self,
        rubric_id: int,
        tree: Dict[int, List[int]],
    ) -> List[int]:
        """Return the immediate neighbors of a rubric in the Chow-Liu tree."""
        return tree.get(rubric_id, [])


# ── Quick function ─────────────────────────────────────────────────────────

def quick_network(
    case_database: List[List[int]],
    rubric_ids: Optional[List[int]] = None,
) -> NetworkReport:
    """Quick helper: build a Bayesian rubric network from case data."""
    net = BayesianRubricNetwork()
    net.fit(case_database)
    return net.fit_and_build(rubric_ids)
