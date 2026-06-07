"""
Repertory PCA — Dimensionality Reduction on Remedy-Rubric Matrix (Module #67)

Pure Python SVD + PCA on the remedy-rubric matrix. Produces:
  - Principal components (latent remedy dimensions)
  - Variance explained per component
  - 2D/3D projections for visualization
  - Remedy loadings on each component

Dashboard visual: Scatter plot of remedies in PC1-PC2 space, colored by kingdom

Usage:
    from oorep.repertory_pca import RepertoryPCA
    pca = RepertoryPCA(data_dir="data")
    components = pca.fit(n_components=10)
    projection = pca.project_2d()
"""

import math
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class RepertoryPCA:
    """
    PCA via SVD on the remedy-rubric matrix (remedies × rubrics).
    Pure Python — no numpy/scipy dependency.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path.home() / "projects" / "oorep-local-repertory" / "data"
        self.matrix: List[List[float]] = []
        self.remedy_ids: List[str] = []
        self.mean: List[float] = []
        self.std: List[float] = []
        self.U: List[List[float]] = []   # Remedy × component
        self.S: List[float] = []         # Singular values
        self.Vt: List[List[float]] = []  # Component × rubric
        self.explained_variance: List[float] = []

    def _load_matrix(self) -> None:
        """Load remedy-rubric matrix from JSON or build small demo."""
        path = self.data_dir / "remedy_rubric_matrix.json"
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
            self.matrix = data["matrix"]
            self.remedy_ids = data["remedy_ids"]
        else:
            # Demo: 8 remedies × 6 rubrics
            self.remedy_ids = ["PULS", "NAT_M", "ARS", "LACH", "SULPH", "NUX_V", "BRY", "PHOS"]
            # Each row = rubric grades for that remedy (0=absent, 1-3=grade)
            self.matrix = [
                [3, 2, 0, 1, 0, 2],   # PULS
                [0, 3, 2, 0, 1, 1],   # NAT_M
                [2, 0, 3, 2, 0, 0],   # ARS
                [1, 0, 2, 3, 0, 1],   # LACH
                [0, 1, 0, 0, 3, 2],   # SULPH
                [0, 0, 1, 0, 2, 3],   # NUX_V
                [1, 2, 0, 0, 1, 0],   # BRY
                [0, 0, 0, 1, 2, 1],   # PHOS
            ]

    def _standardize(self) -> List[List[float]]:
        """Z-score standardize columns."""
        n_rows = len(self.matrix)
        n_cols = len(self.matrix[0]) if self.matrix else 0
        if n_rows == 0 or n_cols == 0:
            return []

        self.mean = [0.0] * n_cols
        self.std = [1.0] * n_cols

        for j in range(n_cols):
            col = [self.matrix[i][j] for i in range(n_rows)]
            self.mean[j] = sum(col) / n_rows
            variance = sum((x - self.mean[j]) ** 2 for x in col) / n_rows
            self.std[j] = math.sqrt(variance) if variance > 0 else 1.0

        standardized = []
        for i in range(n_rows):
            row = [(self.matrix[i][j] - self.mean[j]) / self.std[j] for j in range(n_cols)]
            standardized.append(row)
        return standardized

    def _transpose(self, M: List[List[float]]) -> List[List[float]]:
        return [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]

    def _dot(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication."""
        n = len(A)
        m = len(B[0])
        p = len(B)
        C = [[0.0] * m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                s = 0.0
                for k in range(p):
                    s += A[i][k] * B[k][j]
                C[i][j] = s
        return C

    def _power_iteration(self, M: List[List[float]], k: int, iterations: int = 50) -> Tuple[List[List[float]], List[float]]:
        """
        Power iteration for top-k eigenvectors of symmetric matrix M.
        Returns (eigenvectors, eigenvalues).
        """
        n = len(M)
        vecs = []
        vals = []

        for _ in range(k):
            # Random init
            vec = [random.random() for _ in range(n)]
            # Normalize
            norm = math.sqrt(sum(v ** 2 for v in vec))
            vec = [v / norm for v in vec]

            for _ in range(iterations):
                # M @ vec
                new_vec = [sum(M[i][j] * vec[j] for j in range(n)) for i in range(n)]
                norm = math.sqrt(sum(v ** 2 for v in new_vec))
                if norm == 0:
                    break
                vec = [v / norm for v in new_vec]

            # Rayleigh quotient for eigenvalue
            Mv = [sum(M[i][j] * vec[j] for j in range(n)) for i in range(n)]
            val = sum(vec[i] * Mv[i] for i in range(n))

            vecs.append(vec)
            vals.append(val)

            # Deflate
            for i in range(n):
                for j in range(n):
                    M[i][j] -= val * vec[i] * vec[j]

        return vecs, vals

    def fit(self, n_components: int = 5) -> Dict[str, Any]:
        """
        Fit PCA on remedy-rubric matrix.
        """
        random.seed(42)

        self._load_matrix()
        X = self._standardize()
        n_rows = len(X)
        n_cols = len(X[0]) if X else 0
        if n_rows == 0 or n_cols == 0:
            return {"error": "Empty matrix"}

        # Compute covariance: X^T @ X / n
        Xt = self._transpose(X)
        cov = self._dot(Xt, X)
        for i in range(n_cols):
            for j in range(n_cols):
                cov[i][j] /= n_rows

        # Eigen-decomposition of covariance
        k = min(n_components, n_cols)
        eig_vecs, eig_vals = self._power_iteration(
            [[cov[i][j] for j in range(n_cols)] for i in range(n_cols)],
            k,
        )

        # Sort by eigenvalue descending
        sorted_pairs = sorted(zip(eig_vals, eig_vecs), key=lambda x: x[0], reverse=True)
        eig_vals = [p[0] for p in sorted_pairs]
        eig_vecs = [p[1] for p in sorted_pairs]

        # Vt = eigenvectors (component × feature)
        self.Vt = eig_vecs
        # S = sqrt(eigenvalues)
        self.S = [math.sqrt(max(0, v)) for v in eig_vals]
        # U = X @ V @ S^-1 (remedy × component)
        self.U = []
        for i in range(n_rows):
            row = []
            for c in range(k):
                proj = sum(X[i][j] * eig_vecs[c][j] for j in range(n_cols))
                row.append(proj / self.S[c] if self.S[c] > 0 else 0)
            self.U.append(row)

        # Explained variance
        total_var = sum(eig_vals)
        self.explained_variance = [v / total_var if total_var else 0 for v in eig_vals]

        return {
            "n_components": k,
            "n_remedies": n_rows,
            "n_rubrics": n_cols,
            "explained_variance": [round(v, 4) for v in self.explained_variance],
            "cumulative_variance": [round(sum(self.explained_variance[:i+1]), 4) for i in range(k)],
            "singular_values": [round(s, 4) for s in self.S],
        }

    def project_2d(self) -> List[Dict[str, Any]]:
        """Return 2D projection for visualization."""
        if not self.U:
            return []
        return [
            {"remedy": self.remedy_ids[i], "x": round(self.U[i][0], 4), "y": round(self.U[i][1], 4)}
            for i in range(len(self.remedy_ids))
        ]

    def project_3d(self) -> List[Dict[str, Any]]:
        """Return 3D projection."""
        if not self.U or len(self.U[0]) < 3:
            return []
        return [
            {"remedy": self.remedy_ids[i], "x": round(self.U[i][0], 4),
             "y": round(self.U[i][1], 4), "z": round(self.U[i][2], 4)}
            for i in range(len(self.remedy_ids))
        ]

    def get_loadings(self, component: int = 0, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top rubric loadings for a component."""
        if not self.Vt or component >= len(self.Vt):
            return []
        loadings = [(j, abs(self.Vt[component][j])) for j in range(len(self.Vt[component]))]
        loadings.sort(key=lambda x: x[1], reverse=True)
        return [
            {"rubric_index": idx, "loading": round(val, 4)}
            for idx, val in loadings[:top_n]
        ]

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 67,
            "feature_name": "Repertory PCA",
            "version": "1.0",
            "supports": ["pca", "svd", "2d_projection", "3d_projection", "loadings", "explained_variance"],
            "pure_python": True,
        }
