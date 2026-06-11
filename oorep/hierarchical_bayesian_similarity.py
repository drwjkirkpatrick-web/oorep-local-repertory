"""
Hierarchical Bayesian Remedy Similarity — Module #115

Hierarchical Bayesian model for remedy similarity using kingdom/family
taxonomy as priors. Network-informed remedy recommendations.

Usage:
    from oorep.hierarchical_bayesian_similarity import HierarchicalBayesianSimilarity
    
    model = HierarchicalBayesianSimilarity()
    similar = model.get_similar_remedies("Puls", top_n=5)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class HierarchicalBayesianSimilarity:
    """
    Hierarchical Bayesian model for remedy similarity.
    
    Uses taxonomic hierarchy (kingdom -> family -> remedy) as a prior
    for similarity, combined with observed co-occurrence data.
    """
    
    def __init__(self):
        # Taxonomy priors
        self.kingdom_similarity = {
            ('plant', 'plant'): 0.8,
            ('mineral', 'mineral'): 0.8,
            ('animal', 'animal'): 0.8,
            ('plant', 'mineral'): 0.3,
            ('plant', 'animal'): 0.3,
            ('mineral', 'animal'): 0.3,
        }
        
        # Default remedy taxonomy
        self.remedy_taxonomy = {
            'Puls': {'kingdom': 'plant', 'family': 'Ranunculaceae'},
            'Ars': {'kingdom': 'mineral', 'family': 'Arsenic'},
            'Nux-v': {'kingdom': 'plant', 'family': 'Loganiaceae'},
            'Lach': {'kingdom': 'animal', 'family': 'Viperidae'},
            'Sil': {'kingdom': 'mineral', 'family': 'Silica'},
            'Calc': {'kingdom': 'mineral', 'family': 'Calcarea'},
            'Phos': {'kingdom': 'mineral', 'family': 'Phosphorus'},
            'Sulph': {'kingdom': 'mineral', 'family': 'Sulphur'},
            'Nat-m': {'kingdom': 'mineral', 'family': 'Natrum'},
            'Bry': {'kingdom': 'plant', 'family': 'Cucurbitaceae'},
        }
        
        # Observed co-occurrence data
        self.cooccurrence_counts = defaultdict(lambda: defaultdict(int))
        self.outcome_pairs = defaultdict(lambda: defaultdict(list))
    
    def set_taxonomy(self, remedy: str, kingdom: str, family: str):
        """Set taxonomy for a remedy."""
        self.remedy_taxonomy[remedy] = {'kingdom': kingdom, 'family': family}
    
    def record_cooccurrence(self, remedy1: str, remedy2: str, 
                           outcome: Optional[float] = None):
        """
        Record that two remedies co-occurred in a case.
        
        Args:
            remedy1: First remedy
            remedy2: Second remedy
            outcome: Optional outcome score for this pair
        """
        # Ensure consistent ordering
        pair = tuple(sorted([remedy1, remedy2]))
        self.cooccurrence_counts[pair[0]][pair[1]] += 1
        
        if outcome is not None:
            self.outcome_pairs[pair[0]][pair[1]].append(outcome)
    
    def get_taxonomic_similarity(self, remedy1: str, remedy2: str) -> float:
        """
        Calculate taxonomic similarity between two remedies.
        
        Returns:
            Similarity score (0-1)
        """
        tax1 = self.remedy_taxonomy.get(remedy1, {})
        tax2 = self.remedy_taxonomy.get(remedy2, {})
        
        if not tax1 or not tax2:
            return 0.5
        
        # Same remedy
        if remedy1 == remedy2:
            return 1.0
        
        # Same family
        if tax1.get('family') == tax2.get('family'):
            return 0.9
        
        # Same kingdom
        k1 = tax1.get('kingdom', '')
        k2 = tax2.get('kingdom', '')
        if k1 <= k2:
            kingdom_pair = (k1, k2)
        else:
            kingdom_pair = (k2, k1)
        return self.kingdom_similarity.get(kingdom_pair, 0.3)
    
    def get_observed_similarity(self, remedy1: str, remedy2: str) -> float:
        """
        Calculate observed similarity from co-occurrence data.
        
        Returns:
            Similarity score (0-1)
        """
        pair = tuple(sorted([remedy1, remedy2]))
        count = self.cooccurrence_counts[pair[0]][pair[1]]
        
        if count == 0:
            return 0.0
        
        # Get average outcome for this pair
        outcomes = self.outcome_pairs[pair[0]][pair[1]]
        if outcomes:
            avg_outcome = sum(outcomes) / len(outcomes)
            return avg_outcome * min(count / 5, 1.0)  # Scale by frequency
        
        return min(count / 10, 1.0)  # Just frequency-based
    
    def calculate_similarity(self, remedy1: str, remedy2: str,
                            prior_weight: float = 0.3) -> float:
        """
        Calculate hierarchical Bayesian similarity.
        
        similarity = (1 - w) * observed + w * taxonomic_prior
        
        Args:
            remedy1: First remedy
            remedy2: Second remedy
            prior_weight: Weight for taxonomic prior (0-1)
            
        Returns:
            Similarity score (0-1)
        """
        if remedy1 == remedy2:
            return 1.0
        
        tax_sim = self.get_taxonomic_similarity(remedy1, remedy2)
        obs_sim = self.get_observed_similarity(remedy1, remedy2)
        
        # Bayesian combination
        similarity = (1 - prior_weight) * obs_sim + prior_weight * tax_sim
        
        return similarity
    
    def get_similar_remedies(self, remedy: str, 
                            candidates: Optional[List[str]] = None,
                            top_n: int = 5,
                            prior_weight: float = 0.3) -> List[Dict]:
        """
        Get most similar remedies using hierarchical Bayesian model.
        
        Args:
            remedy: Reference remedy
            candidates: List of candidate remedies (None = all known)
            top_n: Number of similar remedies to return
            prior_weight: Weight for taxonomic prior
            
        Returns:
            List of similar remedies with scores
        """
        if candidates is None:
            candidates = list(self.remedy_taxonomy.keys())
        
        if remedy in candidates:
            candidates = [c for c in candidates if c != remedy]
        
        similarities = []
        for candidate in candidates:
            sim = self.calculate_similarity(remedy, candidate, prior_weight)
            tax_sim = self.get_taxonomic_similarity(remedy, candidate)
            obs_sim = self.get_observed_similarity(remedy, candidate)
            
            # Get co-occurrence count
            pair = tuple(sorted([remedy, candidate]))
            count = self.cooccurrence_counts[pair[0]][pair[1]]
            
            similarities.append({
                'remedy': candidate,
                'similarity': sim,
                'taxonomic_similarity': tax_sim,
                'observed_similarity': obs_sim,
                'cooccurrence_count': count,
                'prior_weight': prior_weight
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_n]
    
    def recommend_by_similarity(self, remedy: str,
                                 outcome_threshold: float = 0.7) -> List[Dict]:
        """
        Recommend remedies based on successful similar remedies.
        
        Args:
            remedy: Reference remedy
            outcome_threshold: Minimum average outcome for recommendation
            
        Returns:
            Recommended remedies with evidence
        """
        similar = self.get_similar_remedies(remedy, top_n=10)
        
        recommendations = []
        for sim in similar:
            pair = tuple(sorted([remedy, sim['remedy']]))
            outcomes = self.outcome_pairs[pair[0]][pair[1]]
            
            if outcomes:
                avg_outcome = sum(outcomes) / len(outcomes)
                if avg_outcome >= outcome_threshold:
                    recommendations.append({
                        **sim,
                        'avg_outcome': avg_outcome,
                        'n_cases': len(outcomes)
                    })
        
        recommendations.sort(key=lambda x: x['avg_outcome'], reverse=True)
        return recommendations
    
    def get_network_stats(self) -> Dict:
        """Get statistics about the similarity network."""
        total_pairs = 0
        observed_pairs = 0
        
        for r1 in self.cooccurrence_counts:
            for r2 in self.cooccurrence_counts[r1]:
                total_pairs += 1
                if self.cooccurrence_counts[r1][r2] > 0:
                    observed_pairs += 1
        
        return {
            'total_remedies': len(self.remedy_taxonomy),
            'total_pairs': total_pairs,
            'observed_pairs': observed_pairs,
            'coverage': observed_pairs / total_pairs if total_pairs > 0 else 0
        }


def quick_similar(remedy: str, top_n: int = 5) -> List[Dict]:
    """Quick static function for similar remedies."""
    model = HierarchicalBayesianSimilarity()
    return model.get_similar_remedies(remedy, top_n=top_n)
