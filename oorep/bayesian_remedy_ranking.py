"""
Bayesian Remedy Ranking with Thompson Sampling — Module #111

Thompson Sampling for Bayesian remedy ranking using beta distributions
to model remedy success probabilities, balancing exploration vs exploitation.

Key insight: Remedies with few observations get higher exploration
weight even if their empirical success rate is lower.

Usage:
    from oorep.bayesian_remedy_ranking import BayesianRemedyRanking
    
    engine = BayesianRemedyRanking()
    
    # Record outcomes for learning
    engine.record_outcome("Puls", "PT-001", 0.9, "anxiety,night,worse")
    
    # Rank remedies using Thompson Sampling
    results = engine.rank_remedies([
        {"remedy": "Puls", "score": 28.5},
        {"remedy": "Ars", "score": 24.0},
    ])
"""

import json
import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
import sqlite3
from pathlib import Path


class BayesianRemedyRanking:
    """
    Thompson Sampling for Bayesian remedy ranking.
    
    Uses beta distributions to model remedy success probabilities,
    balancing exploration vs exploitation based on uncertainty.
    """
    
    def __init__(self, db_path: str = "data/outcomes.db"):
        self.db_path = Path(db_path)
        self._ensure_database()
        self._cache = {}
        
    def _ensure_database(self):
        """Create outcomes table if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS remedy_outcomes (
                remedy TEXT,
                patient_id TEXT,
                outcome_score REAL,  -- 0.0 to 1.0
                prescribed_date TEXT,
                symptom_pattern TEXT,
                PRIMARY KEY (remedy, patient_id)
            )
        """)
        conn.commit()
        conn.close()
    
    def record_outcome(self, remedy: str, patient_id: str, 
                      outcome_score: float, symptom_pattern: str = ""):
        """Record remedy outcome for learning."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO remedy_outcomes 
            (remedy, patient_id, outcome_score, prescribed_date, symptom_pattern)
            VALUES (?, ?, ?, datetime('now'), ?)
        """, (remedy, patient_id, outcome_score, symptom_pattern))
        conn.commit()
        conn.close()
        self._cache.clear()  # Invalidate cache
    
    def _get_beta_params(self, remedy: str) -> Tuple[float, float]:
        """Get alpha and beta parameters for remedy's beta distribution."""
        if remedy in self._cache:
            return self._cache[remedy]
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT outcome_score FROM remedy_outcomes WHERE remedy = ?
        """, (remedy,))
        
        outcomes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Laplace smoothing (uniform prior)
        successes = sum(outcomes) + 1  # Add 1 for smoothing
        failures = len(outcomes) - sum(outcomes) + 1
        
        self._cache[remedy] = (successes, failures)
        return (successes, failures)
    
    def rank_remedies(self, remedies: List[Dict], 
                     top_n: int = 10, samples: int = 1000) -> List[Dict]:
        """
        Rank remedies using Thompson Sampling.
        
        Args:
            remedies: List of remedy dicts with 'remedy' key
            top_n: Number of top remedies to return
            samples: Number of Thompson samples per remedy
            
        Returns:
            Ranked list with Thompson scores and uncertainty
        """
        if not remedies:
            return []
            
        # Get beta parameters for each remedy
        remedy_params = {}
        for r in remedies:
            remedy = r.get('remedy') or r.get('abbrev')
            if not remedy:
                continue
            alpha, beta = self._get_beta_params(remedy)
            remedy_params[remedy] = {'alpha': alpha, 'beta': beta, 'original': r}
        
        if not remedy_params:
            return remedies[:top_n]
        
        # Thompson sampling - track sample statistics
        sample_means = defaultdict(float)
        sample_vars = defaultdict(float)
        
        for _ in range(samples):
            for remedy, params in remedy_params.items():
                # Sample from beta distribution
                sample = random.betavariate(params['alpha'], params['beta'])
                delta = sample - sample_means[remedy]
                sample_means[remedy] += delta / (samples if samples > 0 else 1)
                sample_vars[remedy] += delta * (sample - sample_means[remedy])
        
        # Calculate final rankings with uncertainty
        final_scores = []
        for remedy, params in remedy_params.items():
            n_obs = int(params['alpha'] + params['beta'] - 2)
            variance = sample_vars[remedy] / samples if samples > 1 else 0.0
            
            final_scores.append({
                **params['original'],
                'thompson_score': sample_means[remedy],
                'uncertainty': math.sqrt(variance),
                'alpha': params['alpha'],
                'beta': params['beta'],
                'observations': n_obs,
                'posterior_mean': params['alpha'] / (params['alpha'] + params['beta'])
            })
        
        return sorted(final_scores, key=lambda x: x['thompson_score'], reverse=True)[:top_n]
    
    def get_cumulative_regret(self, optimal_remedy: str, 
                            selected_remedy: str) -> float:
        """
        Calculate cumulative regret for learning evaluation.
        
        Args:
            optimal_remedy: Best remedy in hindsight
            selected_remedy: Remedy actually chosen
            
        Returns:
            Regret value (0 if optimal was chosen)
        """
        opt_alpha, opt_beta = self._get_beta_params(optimal_remedy)
        sel_alpha, sel_beta = self._get_beta_params(selected_remedy)
        
        opt_mean = opt_alpha / (opt_alpha + opt_beta)
        sel_mean = sel_alpha / (sel_alpha + sel_beta)
        
        return max(0.0, opt_mean - sel_mean)
    
    def get_learning_stats(self) -> Dict:
        """Return summary statistics for learning progress."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT remedy, COUNT(*) as n, AVG(outcome_score) as avg_score
            FROM remedy_outcomes
            GROUP BY remedy
        """)
        
        stats = {
            'total_observations': 0,
            'remedies_with_data': 0,
            'avg_outcome_global': 0.0,
            'remedy_counts': {}
        }
        
        total_outcomes = 0
        total_score = 0.0
        
        for remedy, n, avg_score in cursor.fetchall():
            stats['remedy_counts'][remedy] = {'n': n, 'avg_score': avg_score}
            stats['total_observations'] += n
            stats['remedies_with_data'] += 1
            total_outcomes += n
            total_score += avg_score * n
        
        if total_outcomes > 0:
            stats['avg_outcome_global'] = total_score / total_outcomes
            
        conn.close()
        return stats
    
    def recommend_with_exploration(self, remedies: List[Dict],
                                    exploration_rate: float = 0.2) -> Optional[Dict]:
        """
        Recommend remedy with epsilon-greedy exploration.
        
        Args:
            remedies: List of candidate remedies
            exploration_rate: Probability of random exploration
            
        Returns:
            Selected remedy with metadata
        """
        if not remedies:
            return None
            
        if random.random() < exploration_rate:
            # Explore: random selection
            selected = random.choice(remedies)
            return {
                **selected,
                'selection_method': 'exploration',
                'thompson_score': None
            }
        else:
            # Exploit: Thompson sampling
            ranked = self.rank_remedies(remedies, top_n=1)
            if ranked:
                return {
                    **ranked[0],
                    'selection_method': 'thompson_sampling'
                }
            return remedies[0]


def quick_rank(remedies: List[Dict], db_path: str = "data/outcomes.db") -> List[Dict]:
    """Quick static function for Thompson ranking."""
    engine = BayesianRemedyRanking(db_path=db_path)
    return engine.rank_remedies(remedies)
