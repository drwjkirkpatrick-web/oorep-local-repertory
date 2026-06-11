"""
Cross-Validated Symptom Weight Learning — Module #116

Learn optimal symptom weights via k-fold cross-validation on historical outcomes.
Uses grid search to find weights that maximize remedy prediction accuracy.

Usage:
    from oorep.cv_symptom_weights import CVSymptomWeightLearner
    
    learner = CVSymptomWeightLearner()
    optimal_weights = learner.learn_weights(symptom_cases, outcomes, n_folds=5)
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class CVSymptomWeightLearner:
    """
    Cross-validated symptom weight learning.
    
    Uses k-fold cross-validation to find symptom weights
    that maximize remedy prediction accuracy on historical cases.
    """
    
    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        random.seed(random_seed)
    
    def create_folds(self, cases: List[Dict], n_folds: int = 5) -> List[Tuple[List[Dict], List[Dict]]]:
        """
        Create k folds for cross-validation.
        
        Returns:
            List of (train_set, test_set) tuples
        """
        # Shuffle cases
        shuffled = cases.copy()
        random.shuffle(shuffled)
        
        fold_size = len(shuffled) // n_folds
        folds = []
        
        for i in range(n_folds):
            start = i * fold_size
            end = start + fold_size if i < n_folds - 1 else len(shuffled)
            
            test_set = shuffled[start:end]
            train_set = shuffled[:start] + shuffled[end:]
            
            folds.append((train_set, test_set))
        
        return folds
    
    def score_case(self, case: Dict, weights: Dict[str, float]) -> float:
        """
        Score a case using current weights.
        
        Args:
            case: Dict with 'symptoms' and 'correct_remedy'
            weights: Symptom weight dict
            
        Returns:
            Score for this case
        """
        symptoms = case.get('symptoms', [])
        score = sum(weights.get(s, 1.0) for s in symptoms)
        return score
    
    def evaluate_weights(self, train_cases: List[Dict],
                        test_cases: List[Dict],
                        weights: Dict[str, float]) -> Dict:
        """
        Evaluate symptom weights on test set.
        
        Returns:
            Evaluation metrics
        """
        correct = 0
        total = 0
        
        for case in test_cases:
            # Get predicted remedy (simplified - would use actual repertorization)
            predicted = self.predict_remedy(case, weights, train_cases)
            actual = case.get('correct_remedy')
            
            if predicted == actual:
                correct += 1
            total += 1
        
        accuracy = correct / total if total > 0 else 0.0
        
        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total
        }
    
    def predict_remedy(self, case: Dict, weights: Dict[str, float],
                      train_cases: List[Dict]) -> Optional[str]:
        """
        Predict remedy for a case using weighted symptoms.
        
        Simplified version - finds most similar training case.
        """
        case_symptoms = set(case.get('symptoms', []))
        
        best_match = None
        best_score = -1
        
        for train_case in train_cases:
            train_symptoms = set(train_case.get('symptoms', []))
            
            # Weighted Jaccard similarity
            intersection = case_symptoms & train_symptoms
            union = case_symptoms | train_symptoms
            
            if not union:
                continue
            
            weighted_intersection = sum(weights.get(s, 1.0) for s in intersection)
            weighted_union = sum(weights.get(s, 1.0) for s in union)
            
            similarity = weighted_intersection / weighted_union if weighted_union > 0 else 0
            
            if similarity > best_score:
                best_score = similarity
                best_match = train_case
        
        return best_match.get('correct_remedy') if best_match else None
    
    def learn_weights(self, cases: List[Dict],
                     n_folds: int = 5,
                     weight_grid: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Learn optimal symptom weights via cross-validation.
        
        Args:
            cases: List of cases with symptoms and correct remedies
            n_folds: Number of CV folds
            weight_grid: Grid of weight values to try
            
        Returns:
            Optimal weights and CV statistics
        """
        if weight_grid is None:
            weight_grid = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        
        # Get all unique symptoms
        all_symptoms = set()
        for case in cases:
            all_symptoms.update(case.get('symptoms', []))
        
        # Create folds
        folds = self.create_folds(cases, n_folds)
        
        # Grid search over weight combinations
        # For simplicity, use same weight for all symptoms
        best_weights = None
        best_score = -1
        all_results = []
        
        for base_weight in weight_grid:
            weights = {s: base_weight for s in all_symptoms}
            
            fold_scores = []
            for train_cases, test_cases in folds:
                result = self.evaluate_weights(train_cases, test_cases, weights)
                fold_scores.append(result['accuracy'])
            
            avg_score = sum(fold_scores) / len(fold_scores)
            
            all_results.append({
                'base_weight': base_weight,
                'mean_accuracy': avg_score,
                'fold_scores': fold_scores,
                'std': (sum((s - avg_score) ** 2 for s in fold_scores) / len(fold_scores)) ** 0.5
            })
            
            if avg_score > best_score:
                best_score = avg_score
                best_weights = weights.copy()
        
        return {
            'optimal_weights': best_weights,
            'optimal_base_weight': best_weights[list(best_weights.keys())[0]] if best_weights else 1.0,
            'best_cv_score': best_score,
            'all_results': all_results,
            'n_symptoms': len(all_symptoms),
            'n_cases': len(cases)
        }
    
    def get_feature_importance(self, cases: List[Dict],
                               n_permutations: int = 100) -> Dict[str, float]:
        """
        Calculate feature importance via permutation.
        
        Args:
            cases: List of cases
            n_permutations: Number of permutation iterations
            
        Returns:
            Importance score per symptom
        """
        # Baseline accuracy
        baseline = self.learn_weights(cases, n_folds=3)
        baseline_score = baseline['best_cv_score']
        
        # Get all symptoms
        all_symptoms = set()
        for case in cases:
            all_symptoms.update(case.get('symptoms', []))
        
        importances = {}
        
        for symptom in all_symptoms:
            # Permute this symptom
            permuted_cases = []
            for case in cases:
                new_case = case.copy()
                symptoms = case.get('symptoms', [])
                if symptom in symptoms:
                    # Remove symptom
                    new_case['symptoms'] = [s for s in symptoms if s != symptom]
                permuted_cases.append(new_case)
            
            # Evaluate without this symptom
            result = self.learn_weights(permuted_cases, n_folds=3)
            score_without = result['best_cv_score']
            
            # Importance = drop in performance
            importances[symptom] = baseline_score - score_without
        
        return importances


def quick_learn_weights(cases: List[Dict], n_folds: int = 5) -> Dict[str, Any]:
    """Quick static function for weight learning."""
    learner = CVSymptomWeightLearner()
    return learner.learn_weights(cases, n_folds=n_folds)
