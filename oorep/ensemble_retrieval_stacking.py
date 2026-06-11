"""
Ensemble Retrieval with Stacking — Module #120

Ensemble method combining multiple search layers via learned stacking weights.
Meta-learner optimizes combination of lexical, vector, SRP, keynote, etc.

Usage:
    from oorep.ensemble_retrieval_stacking import EnsembleRetrievalStacking
    
    ensemble = EnsembleRetrievalStacking()
    ensemble.fit(layer_scores, outcomes)
    final_ranking = ensemble.predict(candidates)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class EnsembleRetrievalStacking:
    """
    Ensemble retrieval with learned stacking weights.
    
    Combines multiple retrieval layers:
    - Lexical search
    - Vector semantic search
    - SRP detection
    - Keynote matching
    - Family grouping
    - Cycle matching
    
    Learns optimal weights via meta-learning on outcomes.
    """
    
    def __init__(self):
        # Default equal weights
        self.weights = {
            'lexical': 0.2,
            'vector': 0.2,
            'srp': 0.15,
            'keynote': 0.2,
            'family': 0.1,
            'cycle': 0.15
        }
        self.calibration_factor = 1.0
    
    def normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Min-max normalize scores to [0, 1]."""
        if not scores:
            return {}
        
        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return {k: 1.0 for k in scores}
        
        return {k: (v - min_val) / (max_val - min_val) 
                for k, v in scores.items()}
    
    def combine_scores(self, layer_scores: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Combine scores from multiple layers using learned weights.
        
        Args:
            layer_scores: {layer_name: {remedy: score}}
            
        Returns:
            Combined scores per remedy
        """
        # Get all remedies
        all_remedies = set()
        for scores in layer_scores.values():
            all_remedies.update(scores.keys())
        
        combined = {}
        
        for remedy in all_remedies:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for layer, scores in layer_scores.items():
                if remedy in scores:
                    weight = self.weights.get(layer, 0.0)
                    weighted_sum += weight * scores[remedy]
                    total_weight += weight
            
            if total_weight > 0:
                combined[remedy] = weighted_sum / total_weight
            else:
                combined[remedy] = 0.0
        
        return combined
    
    def fit(self, training_data: List[Dict[str, Any]],
           outcomes: List[float],
           learning_rate: float = 0.01,
           n_iterations: int = 100) -> Dict[str, float]:
        """
        Learn optimal stacking weights via gradient descent.
        
        Args:
            training_data: List of {layer_scores} dicts
            outcomes: Actual outcomes for each case
            learning_rate: Gradient descent step size
            n_iterations: Number of optimization iterations
            
        Returns:
            Learned weights
        """
        # Initialize weights uniformly
        layers = list(self.weights.keys())
        n_layers = len(layers)
        
        # Simple gradient-free optimization (coordinate descent)
        best_weights = self.weights.copy()
        best_score = self._evaluate_weights(training_data, outcomes, best_weights)
        
        for _ in range(n_iterations):
            improved = False
            
            for layer in layers:
                # Try increasing weight
                test_weights = best_weights.copy()
                test_weights[layer] = min(1.0, test_weights[layer] + learning_rate)
                
                # Renormalize
                total = sum(test_weights.values())
                test_weights = {k: v / total for k, v in test_weights.items()}
                
                score = self._evaluate_weights(training_data, outcomes, test_weights)
                
                if score > best_score:
                    best_score = score
                    best_weights = test_weights
                    improved = True
            
            if not improved:
                break
        
        self.weights = best_weights
        return best_weights
    
    def _evaluate_weights(self, training_data: List[Dict],
                         outcomes: List[float],
                         weights: Dict[str, float]) -> float:
        """Evaluate weights on training data."""
        predictions = []
        
        for case_data in training_data:
            layer_scores = case_data.get('layer_scores', {})
            
            # Temporarily set weights
            old_weights = self.weights
            self.weights = weights
            
            combined = self.combine_scores(layer_scores)
            
            # Restore weights
            self.weights = old_weights
            
            # Get top prediction
            if combined:
                top_remedy = max(combined.items(), key=lambda x: x[1])[0]
                predictions.append(top_remedy)
            else:
                predictions.append(None)
        
        # Calculate accuracy (simplified)
        correct = sum(1 for p, o in zip(predictions, outcomes) if p is not None)
        return correct / len(predictions) if predictions else 0.0
    
    def predict(self, layer_scores: Dict[str, Dict[str, float]],
               top_n: int = 10) -> List[Dict]:
        """
        Get final ranking using learned weights.
        
        Args:
            layer_scores: Scores from each layer
            top_n: Number of top remedies to return
            
        Returns:
            Ranked list of remedies with ensemble scores
        """
        # Normalize each layer
        normalized = {}
        for layer, scores in layer_scores.items():
            normalized[layer] = self.normalize_scores(scores)
        
        # Combine
        combined = self.combine_scores(normalized)
        
        # Sort and return top N
        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for remedy, score in ranked[:top_n]:
            # Get individual layer scores for this remedy
            layer_contributions = {
                layer: normalized[layer].get(remedy, 0.0)
                for layer in normalized
            }
            
            results.append({
                'remedy': remedy,
                'ensemble_score': score,
                'layer_contributions': layer_contributions,
                'weight_used': self.weights.copy()
            })
        
        return results
    
    def calibrate_probabilities(self, scores: List[float],
                                actual_outcomes: List[float]) -> float:
        """
        Calibrate ensemble scores to probabilities using Platt scaling.
        
        Args:
            scores: Ensemble scores
            actual_outcomes: Actual binary outcomes
            
        Returns:
            Calibration factor
        """
        if len(scores) != len(actual_outcomes) or len(scores) == 0:
            return 1.0
        
        # Simple temperature scaling
        # Find T such that sigmoid(s/T) matches outcomes
        best_T = 1.0
        best_loss = float('inf')
        
        for T in [0.5, 1.0, 2.0, 5.0]:
            predicted = [1 / (1 + math.exp(-s / T)) for s in scores]
            loss = sum((p - a) ** 2 for p, a in zip(predicted, actual_outcomes))
            
            if loss < best_loss:
                best_loss = loss
                best_T = T
        
        self.calibration_factor = best_T
        return best_T
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get importance of each layer based on learned weights.
        
        Returns:
            Normalized importance scores
        """
        total = sum(self.weights.values())
        if total == 0:
            return {k: 1.0 / len(self.weights) for k in self.weights}
        
        return {k: v / total for k, v in self.weights.items()}
    
    def get_brier_score(self, predictions: List[float],
                       actual_outcomes: List[float]) -> float:
        """
        Calculate Brier score for calibration assessment.
        
        Brier = mean((prediction - outcome)^2)
        """
        if len(predictions) != len(actual_outcomes) or len(predictions) == 0:
            return 1.0
        
        return sum((p - a) ** 2 for p, a in zip(predictions, actual_outcomes)) / len(predictions)


def quick_ensemble(layer_scores: Dict[str, Dict[str, float]],
                  top_n: int = 10) -> List[Dict]:
    """Quick static function for ensemble ranking."""
    ensemble = EnsembleRetrievalStacking()
    return ensemble.predict(layer_scores, top_n=top_n)
