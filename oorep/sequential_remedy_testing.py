"""
Sequential Testing for Remedy Selection — Module #117

Sequential Probability Ratio Test (SPRT) for early stopping in remedy selection.
Stops repertorization when a remedy is significantly better than alternatives.

Usage:
    from oorep.sequential_remedy_testing import SequentialRemedyTesting
    
    tester = SequentialRemedyTesting(alpha=0.05, beta=0.1)
    decision = tester.test_rubric_by_rubric(rubrics, remedies)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class SPRTDecision:
    """Result from SPRT test."""
    decision: str  # 'accept', 'reject', or 'continue'
    top_remedy: Optional[str]
    runner_up: Optional[str]
    log_likelihood_ratio: float
    rubrics_tested: int
    stopping_boundary: float


class SequentialRemedyTesting:
    """
    Sequential Probability Ratio Test for remedy selection.
    
    Tests hypotheses sequentially as rubrics are added:
    H0: Remedy A is not better than Remedy B
    H1: Remedy A is significantly better than Remedy B
    """
    
    def __init__(self, alpha: float = 0.05, beta: float = 0.1,
                 delta: float = 0.2):
        """
        Initialize SPRT.
        
        Args:
            alpha: Type I error rate (false positive)
            beta: Type II error rate (false negative)
            delta: Minimum detectable effect size
        """
        self.alpha = alpha
        self.beta = beta
        self.delta = delta
        
        # Calculate boundaries
        self.A = math.log((1 - beta) / alpha)  # Upper boundary (accept H1)
        self.B = math.log(beta / (1 - alpha))   # Lower boundary (accept H0)
    
    def calculate_log_likelihood(self, score_diff: float, n: int) -> float:
        """
        Calculate log-likelihood ratio for score difference.
        
        Args:
            score_diff: Difference in scores between top two remedies
            n: Number of rubrics tested so far
            
        Returns:
            Log-likelihood ratio
        """
        if n == 0:
            return 0.0
        
        # Simplified LLR calculation
        # Under H1: score_diff ~ N(delta, sigma^2)
        # Under H0: score_diff ~ N(0, sigma^2)
        sigma = 1.0  # Assumed standard deviation
        
        ll_h1 = -((score_diff - self.delta) ** 2) / (2 * sigma ** 2)
        ll_h0 = -(score_diff ** 2) / (2 * sigma ** 2)
        
        return ll_h1 - ll_h0
    
    def test_rubric_by_rubric(self, rubrics: List[Dict],
                              remedies: List[Dict],
                              min_rubrics: int = 3,
                              max_rubrics: int = 20) -> SPRTDecision:
        """
        Test remedies sequentially as rubrics are added.
        
        Args:
            rubrics: List of rubrics to test
            remedies: List of candidate remedies with scores
            min_rubrics: Minimum rubrics before stopping
            max_rubrics: Maximum rubrics to test
            
        Returns:
            SPRT decision
        """
        cumulative_llr = 0.0
        
        for i, rubric in enumerate(rubrics[:max_rubrics]):
            # Update remedy scores with this rubric
            # (Simplified - would integrate with actual repertorization)
            
            if i < min_rubrics:
                continue
            
            # Get top two remedies
            sorted_remedies = sorted(remedies, key=lambda x: x.get('score', 0), reverse=True)
            
            if len(sorted_remedies) < 2:
                continue
            
            top = sorted_remedies[0]
            runner = sorted_remedies[1]
            
            score_diff = top.get('score', 0) - runner.get('score', 0)
            
            # Update LLR
            llr = self.calculate_log_likelihood(score_diff, i + 1)
            cumulative_llr += llr
            
            # Check boundaries
            if cumulative_llr >= self.A:
                return SPRTDecision(
                    decision='accept',
                    top_remedy=top.get('remedy'),
                    runner_up=runner.get('remedy'),
                    log_likelihood_ratio=cumulative_llr,
                    rubrics_tested=i + 1,
                    stopping_boundary=self.A
                )
            elif cumulative_llr <= self.B:
                return SPRTDecision(
                    decision='reject',
                    top_remedy=None,
                    runner_up=runner.get('remedy'),
                    log_likelihood_ratio=cumulative_llr,
                    rubrics_tested=i + 1,
                    stopping_boundary=self.B
                )
        
        # Reached max rubrics without decision
        sorted_remedies = sorted(remedies, key=lambda x: x.get('score', 0), reverse=True)
        return SPRTDecision(
            decision='continue',
            top_remedy=sorted_remedies[0].get('remedy') if sorted_remedies else None,
            runner_up=sorted_remedies[1].get('remedy') if len(sorted_remedies) > 1 else None,
            log_likelihood_ratio=cumulative_llr,
            rubrics_tested=min(max_rubrics, len(rubrics)),
            stopping_boundary=self.A
        )
    
    def get_sample_size_estimate(self, effect_size: Optional[float] = None) -> Dict:
        """
        Estimate required sample size for given effect size.
        
        Args:
            effect_size: Expected effect size (None = use self.delta)
            
        Returns:
            Sample size estimates
        """
        delta = effect_size or self.delta
        
        # Approximate sample size formula for SPRT
        # E[N] ≈ (A * (1 - beta) + B * alpha) / delta^2
        expected_n = (self.A * (1 - self.beta) + self.B * self.alpha) / (delta ** 2)
        
        # Maximum sample size (conservative)
        max_n = self.A / (delta ** 2)
        
        return {
            'expected_sample_size': max(1, int(expected_n)),
            'max_sample_size': max(1, int(max_n)),
            'alpha': self.alpha,
            'beta': self.beta,
            'delta': delta
        }
    
    def get_power_curve(self, effect_sizes: Optional[List[float]] = None) -> List[Dict]:
        """
        Calculate power at different effect sizes.
        
        Returns:
            List of {effect_size, power} dicts
        """
        if effect_sizes is None:
            effect_sizes = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
        
        curve = []
        for delta in effect_sizes:
            # Approximate power formula
            # Power ≈ Phi((A - delta * E[N]) / sqrt(E[N]))
            # Simplified here
            sample_info = self.get_sample_size_estimate(delta)
            expected_n = sample_info['expected_sample_size']
            
            # Simplified power calculation
            power = min(1.0, max(0.0, 1 - self.beta + delta * 0.5))
            
            curve.append({
                'effect_size': delta,
                'power': power,
                'expected_sample_size': expected_n
            })
        
        return curve


def quick_sprt_test(rubrics: List[Dict], remedies: List[Dict],
                   alpha: float = 0.05) -> SPRTDecision:
    """Quick static function for SPRT testing."""
    tester = SequentialRemedyTesting(alpha=alpha)
    return tester.test_rubric_by_rubric(rubrics, remedies)
