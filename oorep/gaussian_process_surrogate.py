"""
Gaussian Process Surrogate for Remedy Selection — Module #118

Gaussian Process surrogate model for optimizing remedy selection.
Treats remedy selection as Bayesian optimization over a latent space.

Usage:
    from oorep.gaussian_process_surrogate import GaussianProcessSurrogate
    
    gp = GaussianProcessSurrogate()
    gp.fit(latent_representations, outcomes)
    next_best = gp.suggest_next_remedy(candidates)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
import random


class GaussianProcessSurrogate:
    """
    Gaussian Process surrogate for remedy selection.
    
    Models the relationship between remedy latent representations
    and outcomes for Bayesian optimization.
    """
    
    def __init__(self, length_scale: float = 1.0, 
                 noise_variance: float = 0.1,
                 signal_variance: float = 1.0):
        """
        Initialize GP with RBF kernel.
        
        Args:
            length_scale: RBF kernel length scale
            noise_variance: Observation noise
            signal_variance: Signal variance
        """
        self.length_scale = length_scale
        self.noise_variance = noise_variance
        self.signal_variance = signal_variance
        
        self.X_train = []  # Training points (latent representations)
        self.y_train = []  # Training outcomes
        self.K_inv = None  # Inverse kernel matrix
    
    def rbf_kernel(self, x1: List[float], x2: List[float]) -> float:
        """
        RBF (squared exponential) kernel.
        
        k(x1, x2) = sigma^2 * exp(-||x1 - x2||^2 / (2 * l^2))
        """
        if len(x1) != len(x2):
            return 0.0
        
        sq_dist = sum((a - b) ** 2 for a, b in zip(x1, x2))
        return self.signal_variance * math.exp(-sq_dist / (2 * self.length_scale ** 2))
    
    def fit(self, X: List[List[float]], y: List[float]):
        """
        Fit GP to training data.
        
        Args:
            X: List of latent representations (each is a vector)
            y: List of outcomes
        """
        self.X_train = X
        self.y_train = y
        
        # Build kernel matrix
        n = len(X)
        if n == 0:
            return
        
        K = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                K[i][j] = self.rbf_kernel(X[i], X[j])
                if i == j:
                    K[i][j] += self.noise_variance
        
        # Compute inverse (simplified - in practice use Cholesky)
        self.K_inv = self._matrix_inverse(K)
    
    def _matrix_inverse(self, matrix: List[List[float]]) -> List[List[float]]:
        """Compute matrix inverse (simplified for small matrices)."""
        n = len(matrix)
        if n == 0:
            return []
        
        # For simplicity, use Gaussian elimination
        # Augment with identity
        aug = [row + [1.0 if i == j else 0.0 for j in range(n)] 
               for i, row in enumerate(matrix)]
        
        # Forward elimination
        for i in range(n):
            # Pivot
            pivot = aug[i][i]
            if abs(pivot) < 1e-10:
                pivot = 1e-10
            
            for j in range(2 * n):
                aug[i][j] /= pivot
            
            for k in range(i + 1, n):
                factor = aug[k][i]
                for j in range(2 * n):
                    aug[k][j] -= factor * aug[i][j]
        
        # Back substitution
        for i in range(n - 1, -1, -1):
            for k in range(i):
                factor = aug[k][i]
                for j in range(2 * n):
                    aug[k][j] -= factor * aug[i][j]
        
        # Extract inverse
        return [row[n:] for row in aug]
    
    def predict(self, x: List[float]) -> Tuple[float, float]:
        """
        Predict mean and variance at point x.
        
        Args:
            x: Query point (latent representation)
            
        Returns:
            (mean, variance) tuple
        """
        if not self.X_train or self.K_inv is None:
            return 0.5, self.signal_variance  # Prior
        
        # Compute kernel vector
        k_star = [self.rbf_kernel(x, xi) for xi in self.X_train]
        
        # Predictive mean: k_star^T @ K_inv @ y
        mean = sum(
            k_star[i] * sum(self.K_inv[i][j] * self.y_train[j] 
                          for j in range(len(self.y_train)))
            for i in range(len(k_star))
        )
        
        # Predictive variance
        k_star_star = self.rbf_kernel(x, x) + self.noise_variance
        
        # k_star^T @ K_inv @ k_star
        variance_reduction = sum(
            k_star[i] * sum(self.K_inv[i][j] * k_star[j]
                          for j in range(len(k_star)))
            for i in range(len(k_star))
        )
        
        variance = k_star_star - variance_reduction
        variance = max(variance, 0.0)  # Ensure non-negative
        
        return mean, variance
    
    def upper_confidence_bound(self, x: List[float], 
                               exploration_factor: float = 2.0) -> float:
        """
        Calculate UCB acquisition function.
        
        UCB(x) = mu(x) + beta * sigma(x)
        
        Args:
            x: Query point
            exploration_factor: Beta parameter for UCB
            
        Returns:
            UCB score
        """
        mean, variance = self.predict(x)
        return mean + exploration_factor * math.sqrt(variance)
    
    def suggest_next_remedy(self, candidates: List[Dict],
                           exploration_factor: float = 2.0) -> Optional[Dict]:
        """
        Suggest next remedy to try using UCB.
        
        Args:
            candidates: List of candidate remedies with 'latent' key
            exploration_factor: UCB exploration parameter
            
        Returns:
            Best candidate according to UCB
        """
        if not candidates:
            return None
        
        best_candidate = None
        best_ucb = -float('inf')
        
        for candidate in candidates:
            latent = candidate.get('latent')
            if latent is None:
                continue
            
            ucb = self.upper_confidence_bound(latent, exploration_factor)
            
            if ucb > best_ucb:
                best_ucb = ucb
                best_candidate = candidate
        
        if best_candidate:
            mean, var = self.predict(best_candidate.get('latent', []))
            return {
                **best_candidate,
                'predicted_mean': mean,
                'predicted_variance': var,
                'ucb_score': best_ucb
            }
        
        return candidates[0] if candidates else None
    
    def optimize_hyperparameters(self, X: List[List[float]], 
                                  y: List[float],
                                  n_iterations: int = 10) -> Dict[str, float]:
        """
        Optimize GP hyperparameters via grid search.
        
        Args:
            X: Training points
            y: Training outcomes
            n_iterations: Grid search iterations
            
        Returns:
            Optimal hyperparameters
        """
        best_likelihood = -float('inf')
        best_params = {'length_scale': self.length_scale,
                      'noise_variance': self.noise_variance}
        
        # Grid search over hyperparameters
        for ls in [0.5, 1.0, 2.0, 5.0]:
            for nv in [0.01, 0.1, 0.5]:
                self.length_scale = ls
                self.noise_variance = nv
                self.fit(X, y)
                
                # Calculate log marginal likelihood (simplified)
                # In practice, use proper GP likelihood
                likelihood = -sum((yi - 0.5) ** 2 for yi in y)
                
                if likelihood > best_likelihood:
                    best_likelihood = likelihood
                    best_params = {'length_scale': ls, 'noise_variance': nv}
        
        # Restore best parameters
        self.length_scale = best_params['length_scale']
        self.noise_variance = best_params['noise_variance']
        self.fit(X, y)
        
        return best_params


def quick_gp_predict(X_train: List[List[float]], y_train: List[float],
                    x_query: List[float]) -> Tuple[float, float]:
    """Quick static function for GP prediction."""
    gp = GaussianProcessSurrogate()
    gp.fit(X_train, y_train)
    return gp.predict(x_query)
