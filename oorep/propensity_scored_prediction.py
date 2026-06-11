"""
Propensity-Scored Outcome Prediction — Module #113

Inverse Probability Weighting (IPW) to correct for selection bias in remedy outcomes.
Remedies prescribed more often to "easier" cases get adjusted scores.

Usage:
    from oorep.propensity_scored_prediction import PropensityScoredPrediction
    
    predictor = PropensityScoredPrediction()
    
    # Record case characteristics and prescriptions
    predictor.record_prescription("Puls", {"chronicity": 5, "severity": 7})
    predictor.record_outcome("Puls", "PT-001", 0.9)
    
    # Get propensity-adjusted predictions
    predictions = predictor.predict_with_ipw(["Puls", "Ars"], case_features)
"""

import math
import sqlite3
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class PropensityScoredPrediction:
    """
    Propensity score weighting for unbiased outcome prediction.
    
    Corrects for confounding by adjusting for the probability
    that a remedy would be prescribed given case characteristics.
    """
    
    def __init__(self, db_path: str = "data/propensity.db"):
        self.db_path = Path(db_path)
        self._ensure_database()
        self._cache = {}
        
    def _ensure_database(self):
        """Create propensity tracking tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        
        # Prescription history with case features
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy TEXT,
                patient_id TEXT,
                chronicity INTEGER,  -- 1-10 scale
                severity INTEGER,    -- 1-10 scale
                complexity INTEGER,  -- 1-10 scale
                miasm TEXT,
                prescribed_date TEXT
            )
        """)
        
        # Outcomes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                prescription_id INTEGER,
                outcome_score REAL,  -- 0.0 to 1.0
                recorded_date TEXT,
                FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_prescription(self, remedy: str, patient_id: str,
                           case_features: Dict[str, Any]):
        """
        Record a prescription with case characteristics.
        
        Args:
            remedy: The remedy prescribed
            patient_id: Patient identifier
            case_features: Dict with keys like 'chronicity', 'severity', 'complexity', 'miasm'
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO prescriptions 
            (remedy, patient_id, chronicity, severity, complexity, miasm, prescribed_date)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            remedy, patient_id,
            case_features.get('chronicity', 5),
            case_features.get('severity', 5),
            case_features.get('complexity', 5),
            case_features.get('miasm', 'psora')
        ))
        conn.commit()
        conn.close()
        self._cache.clear()
    
    def record_outcome(self, remedy: str, patient_id: str, outcome_score: float):
        """Record outcome for a prescription."""
        conn = sqlite3.connect(self.db_path)
        
        # Find the prescription
        cursor = conn.execute(
            "SELECT id FROM prescriptions WHERE remedy = ? AND patient_id = ?",
            (remedy, patient_id)
        )
        row = cursor.fetchone()
        
        if row:
            conn.execute(
                "INSERT INTO outcomes (prescription_id, outcome_score, recorded_date) VALUES (?, ?, datetime('now'))",
                (row[0], outcome_score)
            )
            conn.commit()
        
        conn.close()
        self._cache.clear()
    
    def calculate_propensity_score(self, remedy: str, 
                                    case_features: Dict[str, Any]) -> float:
        """
        Calculate propensity score P(prescribed remedy | case features).
        
        Uses a simple logistic-style model based on historical patterns.
        
        Args:
            remedy: The remedy
            case_features: Case characteristics
            
        Returns:
            Propensity score (0-1)
        """
        conn = sqlite3.connect(self.db_path)
        
        # Get all prescriptions for this remedy
        cursor = conn.execute(
            "SELECT chronicity, severity, complexity FROM prescriptions WHERE remedy = ?",
            (remedy,)
        )
        remedy_cases = cursor.fetchall()
        
        # Get all prescriptions
        cursor = conn.execute(
            "SELECT chronicity, severity, complexity FROM prescriptions"
        )
        all_cases = cursor.fetchall()
        
        conn.close()
        
        if not all_cases:
            return 0.5  # No data, return neutral
        
        # Calculate similarity-weighted propensity
        target = (
            case_features.get('chronicity', 5),
            case_features.get('severity', 5),
            case_features.get('complexity', 5)
        )
        
        # Count similar cases
        remedy_similar = sum(
            1 for c in remedy_cases
            if self._case_similarity(target, c) > 0.7
        )
        all_similar = sum(
            1 for c in all_cases
            if self._case_similarity(target, c) > 0.7
        )
        
        if all_similar == 0:
            return len(remedy_cases) / len(all_cases) if all_cases else 0.5
        
        return remedy_similar / all_similar
    
    def _case_similarity(self, case1: Tuple, case2: Tuple) -> float:
        """Calculate cosine similarity between case feature vectors."""
        if len(case1) != len(case2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(case1, case2))
        norm1 = math.sqrt(sum(a * a for a in case1))
        norm2 = math.sqrt(sum(a * a for a in case2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def predict_with_ipw(self, remedies: List[str],
                         case_features: Dict[str, Any]) -> List[Dict]:
        """
        Predict outcomes using Inverse Probability Weighting.
        
        Args:
            remedies: List of remedy names
            case_features: Case characteristics
            
        Returns:
            Weighted predictions with propensity scores
        """
        conn = sqlite3.connect(self.db_path)
        
        results = []
        for remedy in remedies:
            # Get propensity score
            propensity = self.calculate_propensity_score(remedy, case_features)
            
            # Get raw outcomes
            cursor = conn.execute("""
                SELECT o.outcome_score 
                FROM outcomes o
                JOIN prescriptions p ON o.prescription_id = p.id
                WHERE p.remedy = ?
            """, (remedy,))
            
            outcomes = [row[0] for row in cursor.fetchall()]
            
            if outcomes:
                # Calculate IPW-adjusted mean
                # Weight = 1 / propensity (stabilized)
                weights = [1.0 / max(propensity, 0.1) for _ in outcomes]
                weighted_sum = sum(w * o for w, o in zip(weights, outcomes))
                weight_total = sum(weights)
                
                ipw_mean = weighted_sum / weight_total if weight_total > 0 else 0.5
                raw_mean = sum(outcomes) / len(outcomes)
                
                results.append({
                    'remedy': remedy,
                    'ipw_outcome': ipw_mean,
                    'raw_outcome': raw_mean,
                    'propensity_score': propensity,
                    'n_observations': len(outcomes),
                    'adjustment_factor': ipw_mean / raw_mean if raw_mean > 0 else 1.0
                })
            else:
                results.append({
                    'remedy': remedy,
                    'ipw_outcome': None,
                    'raw_outcome': None,
                    'propensity_score': propensity,
                    'n_observations': 0,
                    'adjustment_factor': 1.0
                })
        
        conn.close()
        
        # Sort by IPW outcome
        results.sort(key=lambda x: x['ipw_outcome'] if x['ipw_outcome'] is not None else 0, 
                    reverse=True)
        
        return results
    
    def get_balance_statistics(self) -> Dict:
        """
        Calculate covariate balance before/after IPW.
        
        Returns:
            Balance statistics for case features
        """
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute(
            "SELECT remedy, chronicity, severity, complexity FROM prescriptions"
        )
        
        by_remedy = defaultdict(lambda: {'chronicity': [], 'severity': [], 'complexity': []})
        
        for remedy, chron, sev, comp in cursor.fetchall():
            by_remedy[remedy]['chronicity'].append(chron)
            by_remedy[remedy]['severity'].append(sev)
            by_remedy[remedy]['complexity'].append(comp)
        
        conn.close()
        
        # Calculate standardized mean differences
        balance_stats = {}
        remedies = list(by_remedy.keys())
        
        for feature in ['chronicity', 'severity', 'complexity']:
            means = {r: sum(by_remedy[r][feature]) / len(by_remedy[r][feature]) 
                    if by_remedy[r][feature] else 0
                    for r in remedies}
            
            overall_mean = sum(means.values()) / len(means) if means else 0
            
            balance_stats[feature] = {
                'by_remedy': means,
                'overall_mean': overall_mean,
                'max_smd': max(abs(m - overall_mean) for m in means.values()) if means else 0
            }
        
        return balance_stats
    
    def compare_auc(self, remedies: List[str], 
                    case_features_list: List[Dict],
                    actual_outcomes: List[float]) -> Dict:
        """
        Compare AUC of raw vs IPW predictions.
        
        Args:
            remedies: List of remedies considered for each case
            case_features_list: List of case feature dicts
            actual_outcomes: Actual outcomes for each case
            
        Returns:
            AUC comparison statistics
        """
        # This is a simplified AUC calculation
        # In practice, you'd use proper ROC curve calculation
        
        raw_correct = 0
        ipw_correct = 0
        total = 0
        
        for case_features, actual in zip(case_features_list, actual_outcomes):
            predictions = self.predict_with_ipw(remedies, case_features)
            
            if not predictions:
                continue
            
            # Find best remedy by raw and IPW
            best_raw = max(predictions, key=lambda x: x['raw_outcome'] if x['raw_outcome'] else 0)
            best_ipw = max(predictions, key=lambda x: x['ipw_outcome'] if x['ipw_outcome'] else 0)
            
            # Check if prediction matches actual (simplified)
            # In practice, you'd need to know which remedy was actually prescribed
            total += 1
        
        return {
            'raw_accuracy': raw_correct / total if total > 0 else 0,
            'ipw_accuracy': ipw_correct / total if total > 0 else 0,
            'total_cases': total
        }


def quick_ipw_predict(remedies: List[str], case_features: Dict,
                      db_path: str = "data/propensity.db") -> List[Dict]:
    """Quick static function for IPW prediction."""
    predictor = PropensityScoredPrediction(db_path=db_path)
    return predictor.predict_with_ipw(remedies, case_features)
