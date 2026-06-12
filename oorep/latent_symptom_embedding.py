"""
Latent Symptom Embedding Distance (Module #124)

Projects symptoms and remedies into a shared low-dimensional latent space
via Truncated SVD on the remedy-rubric grade matrix. The case is represented
as a weighted sum of rubric vectors, and remedies are ranked by cosine
similarity to the case vector.

This complements the lexical/grade-based repertorization by capturing
"hidden" semantic relationships between rubrics that share remedies.

Math:
    Build matrix M[remedy × rubric] with entries = max grade
    Truncated SVD: M ≈ U_k Σ_k V_k^T  (k components)
    Embed each rubric as column of V_k Σ_k (low-dim)
    Embed each remedy as row of U_k Σ_k
    Embed a case as sum over observed rubric embeddings, weighted by grade
    Rank remedies by cosine(remedy_vec, case_vec)

Pure-Python implementation of Truncated SVD via power iteration with
orthogonal deflation — no NumPy/SciPy dependency.

Usage:
    from oorep.latent_symptom_embedding import LatentSymptomEmbedder
    embedder = LatentSymptomEmbedder(n_components=20)
    embedder.fit()
    result = embedder.rank_remedies(case_rubric_ids=[101, 102, 103])
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class EmbedderResult:
    n_components: int
    explained_variance: float
    n_remedies: int
    n_rubrics: int
    case_remedy_scores: List[Tuple[str, float]]  # abbrev, cosine similarity
    top_recommendation: Optional[str]
    runtime_ms: float


class LatentSymptomEmbedder:
    """
    SVD-based latent embedding of remedies and rubrics (pure Python).
    """

    def __init__(
        self,
        n_components: int = 20,
        repertory: Optional[HomeopathicRepertory] = None,
        seed: int = 42,
        n_iter: int = 20,
    ):
        self.n_components = n_components
        self.rep = repertory or HomeopathicRepertory()
        self.seed = seed
        self.n_iter = n_iter
        self._fitted = False
        self._remedy_index: Dict[str, int] = {}
        self._rubric_index: Dict[int, int] = {}
        self._remedy_vecs: Dict[str, List[float]] = {}
        self._rubric_vecs: Dict[int, List[float]] = {}
        self._explained_variance: float = 0.0
        self._n_remedies = 0
        self._n_rubrics = 0

    def _build_sparse_matrix(self) -> Tuple[int, int, Dict[Tuple[int, int], float]]:
        """Build the sparse remedy × rubric grade matrix."""
        remedy_to_idx: Dict[str, int] = {}
        rubric_to_idx: Dict[int, int] = {}
        sparse: Dict[Tuple[int, int], float] = {}

        for rubric_id, links in self.rep.rubric_to_remedies.items():
            for link in links:
                abbrev = link.get("abbrev")
                grade = link.get("grade", 1)
                if not abbrev:
                    continue
                if abbrev not in remedy_to_idx:
                    remedy_to_idx[abbrev] = len(remedy_to_idx)
                if rubric_id not in rubric_to_idx:
                    rubric_to_idx[rubric_id] = len(rubric_to_idx)
                r = remedy_to_idx[abbrev]
                c = rubric_to_idx[rubric_id]
                sparse[(r, c)] = max(sparse.get((r, c), 0.0), float(grade))

        return len(remedy_to_idx), len(rubric_to_idx), sparse

    def _power_iteration(
        self,
        M_dense: List[List[float]],
        k: int,
    ) -> Tuple[List[List[float]], List[List[float]], List[float]]:
        """
        Compute top-k left and right singular vectors of M via power
        iteration with deflation. Returns (U, V, singular_values) where
        U is (n_remedies × k), V is (n_rubrics × k), and singular_values
        is a length-k list.
        """
        rng = random.Random(self.seed)
        n_remedies = len(M_dense)
        n_rubrics = len(M_dense[0]) if n_remedies else 0
        U: List[List[float]] = []
        V: List[List[float]] = []
        singular_values: List[float] = []

        for _ in range(k):
            # Initial random v
            v = [rng.gauss(0, 1) for _ in range(n_rubrics)]
            v = self._normalize(v)
            u: List[float] = []
            for _it in range(self.n_iter):
                # u = M v
                u = [sum(M_dense[r][j] * v[j] for j in range(n_rubrics)) for r in range(n_remedies)]
                u = self._normalize(u)
                # v = M^T u
                v_new = [0.0] * n_rubrics
                for r in range(n_remedies):
                    row_coeff = u[r]
                    row = M_dense[r]
                    for j in range(n_rubrics):
                        v_new[j] += row[j] * row_coeff
                v = self._normalize(v_new)
            # Compute singular value = u^T M v
            Mv = [sum(M_dense[r][j] * v[j] for j in range(n_rubrics)) for r in range(n_remedies)]
            sigma = sum(u_r * Mv_r for u_r, Mv_r in zip(u, Mv)) if u else 0.0
            sigma = max(0.0, sigma)  # numerical safety
            U.append(u)
            V.append(v)
            singular_values.append(sigma)
            # Deflate: M = M - sigma * u v^T
            for r in range(n_remedies):
                row = M_dense[r]
                coeff = sigma * u[r]
                for j in range(n_rubrics):
                    row[j] -= coeff * v[j]

        return U, V, singular_values

    @staticmethod
    def _normalize(v: List[float]) -> List[float]:
        n = math.sqrt(sum(x * x for x in v))
        if n < 1e-12:
            return v
        return [x / n for x in v]

    def fit(self) -> "LatentSymptomEmbedder":
        """Build the SVD embedding from the remedy × rubric grade matrix."""
        n_remedies, n_rubrics, sparse = self._build_sparse_matrix()
        self._n_remedies = n_remedies
        self._n_rubrics = n_rubrics

        k = min(self.n_components, max(1, min(n_remedies, n_rubrics) - 1))
        if k <= 0 or n_remedies == 0 or n_rubrics == 0:
            self._fitted = True
            return self

        # Build dense matrix
        M = [[0.0] * n_rubrics for _ in range(n_remedies)]
        for (r, c), v in sparse.items():
            M[r][c] = v

        # Truncated SVD
        U, V, sigma = self._power_iteration(M, k)

        # Save indices
        idx_to_remedy = {idx: abbrev for abbrev, idx in self._remedy_index.items()}
        # Rebuild remedy_index (we lost it, recover from sparse structure)
        # (Actually, _build_sparse_matrix only returned the matrix, not the indices.)
        # So we re-derive:
        remedy_to_idx: Dict[str, int] = {}
        rubric_to_idx: Dict[int, int] = {}
        for rubric_id, links in self.rep.rubric_to_remedies.items():
            for link in links:
                abbrev = link.get("abbrev")
                if not abbrev:
                    continue
                if abbrev not in remedy_to_idx:
                    remedy_to_idx[abbrev] = len(remedy_to_idx)
                if rubric_id not in rubric_to_idx:
                    rubric_to_idx[rubric_id] = len(rubric_to_idx)
        self._remedy_index = remedy_to_idx
        self._rubric_index = rubric_to_idx

        # Embed: U * diag(sigma), V * diag(sigma) so cosine is meaningful
        for i, abbrev in enumerate(remedy_to_idx):
            if i < len(U):
                self._remedy_vecs[abbrev] = [U[i][j] * sigma[j] for j in range(k)]
        for j, rubric_id in enumerate(rubric_to_idx):
            if j < len(V):
                self._rubric_vecs[rubric_id] = [V[j][i] * sigma[i] for i in range(k)]

        # Explained variance = sum(sigma_i^2) / total_variance
        total_var = sum(v * v for v in sparse.values())
        captured_var = sum(s * s for s in sigma)
        self._explained_variance = captured_var / total_var if total_var > 0 else 0.0
        self._fitted = True
        return self

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1e-9
        nb = math.sqrt(sum(x * x for x in b)) or 1e-9
        return dot / (na * nb)

    def rank_remedies(
        self,
        case_rubric_ids: List[int],
        case_grades: Optional[List[int]] = None,
        top_k: int = 10,
    ) -> EmbedderResult:
        """
        Rank remedies by cosine similarity to a case vector.

        The case vector is a grade-weighted sum of rubric embeddings.
        """
        import time
        t0 = time.time()
        if not self._fitted:
            self.fit()

        if not case_grades:
            case_grades = [3] * len(case_rubric_ids)

        k = self.n_components
        case_vec = [0.0] * k
        for rubric_id, grade in zip(case_rubric_ids, case_grades):
            rvec = self._rubric_vecs.get(rubric_id)
            if rvec:
                for i in range(min(k, len(rvec))):
                    case_vec[i] += rvec[i] * grade

        sims: List[Tuple[str, float]] = []
        for abbrev, rvec in self._remedy_vecs.items():
            sims.append((abbrev, self._cosine(case_vec, rvec)))
        sims.sort(key=lambda x: x[1], reverse=True)

        return EmbedderResult(
            n_components=k,
            explained_variance=self._explained_variance,
            n_remedies=len(self._remedy_vecs),
            n_rubrics=len(self._rubric_index),
            case_remedy_scores=sims[:top_k],
            top_recommendation=sims[0][0] if sims else None,
            runtime_ms=(time.time() - t0) * 1000,
        )


# ── Quick function ─────────────────────────────────────────────────────────

def quick_embed(rubric_ids: List[int], n_components: int = 20) -> EmbedderResult:
    """Quick helper: rank remedies by latent embedding similarity."""
    embedder = LatentSymptomEmbedder(n_components=n_components)
    embedder.fit()
    return embedder.rank_remedies(rubric_ids)
