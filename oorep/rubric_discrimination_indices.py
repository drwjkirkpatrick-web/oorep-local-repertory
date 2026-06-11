"""
Rubric Discrimination Indices — Module #114

Classical test theory metrics for rubric quality assessment.
Calculates item-total correlations, KR-20 reliability, and discrimination power.

Usage:
    from oorep.rubric_discrimination_indices import RubricDiscriminationIndices
    
    rdi = RubricDiscriminationIndices()
    indices = rdi.calculate_indices(rubric_remedy_matrix)
    reliability = rdi.kr20_reliability(rubric_remedy_matrix)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class RubricDiscriminationIndices:
    """
    Classical test theory metrics for rubric discrimination.
    
    Measures how well each rubric discriminates between remedies
    using item-total correlation and point-biserial correlation.
    """
    
    def __init__(self):
        pass
    
    def point_biserial_correlation(self, rubric_scores: List[float],
                                    total_scores: List[float]) -> float:
        """
        Calculate point-biserial correlation between rubric and total scores.
        
        Args:
            rubric_scores: Scores on this rubric (0 or 1 for binary)
            total_scores: Total scores across all rubrics
            
        Returns:
            Point-biserial correlation coefficient
        """
        if len(rubric_scores) != len(total_scores) or len(rubric_scores) == 0:
            return 0.0
        
        n = len(rubric_scores)
        
        # Group by rubric score
        group1 = [total_scores[i] for i in range(n) if rubric_scores[i] > 0]
        group0 = [total_scores[i] for i in range(n) if rubric_scores[i] == 0]
        
        if not group1 or not group0:
            return 0.0
        
        mean1 = sum(group1) / len(group1)
        mean0 = sum(group0) / len(group0)
        
        # Pooled standard deviation
        all_scores = total_scores
        mean_all = sum(all_scores) / len(all_scores)
        variance = sum((s - mean_all) ** 2 for s in all_scores) / len(all_scores)
        sd = math.sqrt(variance)
        
        if sd == 0:
            return 0.0
        
        p = len(group1) / n
        q = len(group0) / n
        
        return ((mean1 - mean0) / sd) * math.sqrt(p * q)
    
    def item_total_correlation(self, rubric_matrix: Dict[str, Dict[str, float]],
                                rubric_name: str) -> float:
        """
        Calculate item-total correlation for a specific rubric.
        
        Args:
            rubric_matrix: {rubric: {remedy: score}}
            rubric_name: Name of rubric to calculate for
            
        Returns:
            Item-total correlation
        """
        if rubric_name not in rubric_matrix:
            return 0.0
        
        # Get all remedies
        all_remedies = set()
        for rubric_scores in rubric_matrix.values():
            all_remedies.update(rubric_scores.keys())
        
        remedies = sorted(all_remedies)
        
        # Calculate total scores (without target rubric)
        total_without = []
        rubric_scores_list = []
        
        for remedy in remedies:
            total = sum(
                rubric_matrix[r].get(remedy, 0) 
                for r in rubric_matrix if r != rubric_name
            )
            total_without.append(total)
            rubric_scores_list.append(rubric_matrix[rubric_name].get(remedy, 0))
        
        return self.point_biserial_correlation(rubric_scores_list, total_without)
    
    def kr20_reliability(self, rubric_matrix: Dict[str, Dict[str, float]]) -> float:
        """
        Calculate Kuder-Richardson 20 reliability coefficient.
        
        KR-20 = (k / (k-1)) * (1 - (sum(p*q) / variance))
        
        Args:
            rubric_matrix: {rubric: {remedy: score}}
            
        Returns:
            KR-20 reliability coefficient (0-1)
        """
        if not rubric_matrix:
            return 0.0
        
        k = len(rubric_matrix)
        if k < 2:
            return 0.0
        
        # Get all remedies
        all_remedies = set()
        for rubric_scores in rubric_matrix.values():
            all_remedies.update(rubric_scores.keys())
        
        remedies = sorted(all_remedies)
        n = len(remedies)
        
        if n == 0:
            return 0.0
        
        # Calculate total scores
        total_scores = []
        for remedy in remedies:
            total = sum(rubric_scores.get(remedy, 0) for rubric_scores in rubric_matrix.values())
            total_scores.append(total)
        
        # Variance of total scores
        mean_total = sum(total_scores) / len(total_scores)
        variance = sum((t - mean_total) ** 2 for t in total_scores) / len(total_scores)
        
        if variance == 0:
            return 0.0
        
        # Sum of p*q for each rubric
        pq_sum = 0.0
        for rubric_scores in rubric_matrix.values():
            scores = [rubric_scores.get(r, 0) for r in remedies]
            if scores:
                p = sum(1 for s in scores if s > 0) / len(scores)
                q = 1 - p
                pq_sum += p * q
        
        kr20 = (k / (k - 1)) * (1 - (pq_sum / variance))
        return max(0.0, min(1.0, kr20))
    
    def calculate_indices(self, rubric_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Dict]:
        """
        Calculate all discrimination indices for all rubrics.
        
        Args:
            rubric_matrix: {rubric: {remedy: score}}
            
        Returns:
            Dict of indices per rubric
        """
        indices = {}
        
        for rubric_name in rubric_matrix:
            item_total = self.item_total_correlation(rubric_matrix, rubric_name)
            
            # Calculate difficulty (proportion of remedies with score > 0)
            scores = list(rubric_matrix[rubric_name].values())
            difficulty = sum(1 for s in scores if s > 0) / len(scores) if scores else 0
            
            # Calculate discrimination (top vs bottom 27%)
            sorted_remedies = sorted(
                rubric_matrix[rubric_name].items(),
                key=lambda x: x[1],
                reverse=True
            )
            n = len(sorted_remedies)
            if n >= 4:
                top_27 = int(n * 0.27) + 1
                top_scores = [s for _, s in sorted_remedies[:top_27]]
                bottom_scores = [s for _, s in sorted_remedies[-top_27:]]
                discrimination = (sum(top_scores) / len(top_scores) - 
                                sum(bottom_scores) / len(bottom_scores)) if top_scores and bottom_scores else 0
            else:
                discrimination = 0
            
            indices[rubric_name] = {
                'item_total_correlation': item_total,
                'difficulty': difficulty,
                'discrimination': discrimination,
                'n_remedies': len(scores)
            }
        
        return indices
    
    def flag_poor_rubrics(self, rubric_matrix: Dict[str, Dict[str, float]],
                          min_correlation: float = 0.1) -> List[str]:
        """
        Identify rubrics with poor discrimination.
        
        Args:
            rubric_matrix: {rubric: {remedy: score}}
            min_correlation: Minimum acceptable item-total correlation
            
        Returns:
            List of rubric names flagged as poor
        """
        indices = self.calculate_indices(rubric_matrix)
        return [
            rubric for rubric, stats in indices.items()
            if stats['item_total_correlation'] < min_correlation
        ]


def quick_indices(rubric_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Dict]:
    """Quick static function for discrimination indices."""
    rdi = RubricDiscriminationIndices()
    return rdi.calculate_indices(rubric_matrix)
