"""
Causal Inference for Remedy Effects — Module #119

Potential outcomes framework for estimating causal effects of remedies.
Uses propensity matching and inverse probability weighting.

Usage:
    from oorep.causal_remedy_effects import CausalRemedyEffects
    
    causal = CausalRemedyEffects()
    ate = causal.estimate_ate("Puls", "Ars", cases)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class CausalRemedyEffects:
    """
    Causal inference for remedy effectiveness.
    
    Estimates Average Treatment Effects (ATE) using:
    - Propensity score matching
    - Inverse probability weighting
    - Doubly robust estimation
    """
    
    def __init__(self):
        self.cases = []
    
    def add_case(self, remedy: str, outcome: float, 
                covariates: Dict[str, Any]):
        """
        Add a case to the dataset.
        
        Args:
            remedy: Remedy prescribed
            outcome: Outcome score (0-1)
            covariates: Case characteristics
        """
        self.cases.append({
            'remedy': remedy,
            'outcome': outcome,
            'covariates': covariates
        })
    
    def estimate_propensity_score(self, remedy: str, 
                                  covariates: Dict[str, Any]) -> float:
        """
        Estimate P(remedy | covariates) using logistic approximation.
        
        Args:
            remedy: Target remedy
            covariates: Case characteristics
            
        Returns:
            Propensity score
        """
        # Count similar cases
        total_cases = len(self.cases)
        if total_cases == 0:
            return 0.5
        
        remedy_cases = [c for c in self.cases if c['remedy'] == remedy]
        if not remedy_cases:
            return 0.01  # Very unlikely
        
        # Calculate similarity to each remedy case
        similarities = []
        for case in remedy_cases:
            sim = self._covariate_similarity(covariates, case['covariates'])
            similarities.append(sim)
        
        # Propensity = average similarity weighted by frequency
        avg_similarity = sum(similarities) / len(similarities)
        frequency = len(remedy_cases) / total_cases
        
        # Combine frequency and similarity
        propensity = 0.5 * frequency + 0.5 * avg_similarity
        
        return max(0.01, min(0.99, propensity))
    
    def _covariate_similarity(self, cov1: Dict, cov2: Dict) -> float:
        """Calculate similarity between two covariate sets."""
        keys = set(cov1.keys()) & set(cov2.keys())
        if not keys:
            return 0.5
        
        matches = sum(1 for k in keys if cov1[k] == cov2[k])
        return matches / len(keys)
    
    def find_matches(self, remedy1: str, remedy2: str,
                    caliper: float = 0.2) -> List[Tuple[Dict, Dict]]:
        """
        Find matched pairs of cases using propensity scores.
        
        Args:
            remedy1: First remedy
            remedy2: Second remedy
            caliper: Maximum propensity difference for matching
            
        Returns:
            List of (case1, case2) matched pairs
        """
        cases1 = [c for c in self.cases if c['remedy'] == remedy1]
        cases2 = [c for c in self.cases if c['remedy'] == remedy2]
        
        # Calculate propensity scores
        for case in cases1:
            case['propensity'] = self.estimate_propensity_score(remedy1, case['covariates'])
        
        for case in cases2:
            case['propensity'] = self.estimate_propensity_score(remedy2, case['covariates'])
        
        # Greedy matching
        matches = []
        used2 = set()
        
        for c1 in cases1:
            best_match = None
            best_diff = float('inf')
            
            for i2, c2 in enumerate(cases2):
                if i2 in used2:
                    continue
                
                diff = abs(c1['propensity'] - c2['propensity'])
                if diff < best_diff and diff <= caliper:
                    best_diff = diff
                    best_match = i2
            
            if best_match is not None:
                matches.append((c1, cases2[best_match]))
                used2.add(best_match)
        
        return matches
    
    def estimate_ate_matching(self, remedy1: str, remedy2: str) -> Dict:
        """
        Estimate ATE using propensity score matching.
        
        ATE = E[Y(1) - Y(0)]
        
        Args:
            remedy1: Treatment remedy
            remedy2: Control remedy
            
        Returns:
            ATE estimate with confidence interval
        """
        matches = self.find_matches(remedy1, remedy2)
        
        if not matches:
            return {'ate': None, 'se': None, 'n_matches': 0}
        
        differences = [m1['outcome'] - m2['outcome'] for m1, m2 in matches]
        
        ate = sum(differences) / len(differences)
        variance = sum((d - ate) ** 2 for d in differences) / len(differences)
        se = math.sqrt(variance / len(differences))
        
        return {
            'ate': ate,
            'se': se,
            'ci_lower': ate - 1.96 * se,
            'ci_upper': ate + 1.96 * se,
            'n_matches': len(matches)
        }
    
    def estimate_ate_ipw(self, remedy1: str, remedy2: str) -> Dict:
        """
        Estimate ATE using inverse probability weighting.
        
        Args:
            remedy1: Treatment remedy
            remedy2: Control remedy
            
        Returns:
            IPW ATE estimate
        """
        # IPW estimator
        treated_outcomes = []
        treated_weights = []
        control_outcomes = []
        control_weights = []
        
        for case in self.cases:
            if case['remedy'] == remedy1:
                ps = self.estimate_propensity_score(remedy1, case['covariates'])
                treated_outcomes.append(case['outcome'])
                treated_weights.append(1.0 / ps)
            elif case['remedy'] == remedy2:
                ps = self.estimate_propensity_score(remedy2, case['covariates'])
                control_outcomes.append(case['outcome'])
                control_weights.append(1.0 / ps)
        
        if not treated_outcomes or not control_outcomes:
            return {'ate': None, 'n_treated': len(treated_outcomes), 
                   'n_control': len(control_outcomes)}
        
        # Weighted means
        treated_mean = sum(o * w for o, w in zip(treated_outcomes, treated_weights))
        treated_mean /= sum(treated_weights)
        
        control_mean = sum(o * w for o, w in zip(control_outcomes, control_weights))
        control_mean /= sum(control_weights)
        
        ate = treated_mean - control_mean
        
        return {
            'ate': ate,
            'treated_mean': treated_mean,
            'control_mean': control_mean,
            'n_treated': len(treated_outcomes),
            'n_control': len(control_outcomes)
        }
    
    def get_balance_check(self, remedy1: str, remedy2: str) -> Dict:
        """
        Check covariate balance between remedy groups.
        
        Returns:
            Balance statistics
        """
        cases1 = [c for c in self.cases if c['remedy'] == remedy1]
        cases2 = [c for c in self.cases if c['remedy'] == remedy2]
        
        # Get all covariate keys
        all_keys = set()
        for c in cases1 + cases2:
            all_keys.update(c['covariates'].keys())
        
        balance = {}
        for key in all_keys:
            vals1 = [c['covariates'].get(key, 0) for c in cases1]
            vals2 = [c['covariates'].get(key, 0) for c in cases2]
            
            if vals1 and vals2:
                mean1 = sum(vals1) / len(vals1)
                mean2 = sum(vals2) / len(vals2)
                
                # Standardized mean difference
                pooled_sd = math.sqrt(
                    (sum((v - mean1) ** 2 for v in vals1) + 
                     sum((v - mean2) ** 2 for v in vals2)) / 
                    (len(vals1) + len(vals2))
                )
                
                smd = abs(mean1 - mean2) / pooled_sd if pooled_sd > 0 else 0
                
                balance[key] = {
                    'mean_treated': mean1,
                    'mean_control': mean2,
                    'smd': smd,
                    'balanced': smd < 0.1  # Standard threshold
                }
        
        return balance


def quick_ate(remedy1: str, remedy2: str, 
             cases: List[Dict]) -> Dict:
    """Quick static function for ATE estimation."""
    causal = CausalRemedyEffects()
    for case in cases:
        causal.add_case(case['remedy'], case['outcome'], case['covariates'])
    return causal.estimate_ate_matching(remedy1, remedy2)
