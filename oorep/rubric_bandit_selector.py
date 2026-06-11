"""
Multi-Armed Bandit for Rubric Selection — Module #112

UCB1 (Upper Confidence Bound) algorithm for dynamically selecting
which rubrics to include in repertorization based on their historical
discrimination power.

Key insight: Not all rubrics are equally informative. This module learns
which rubrics best discriminate the correct remedy and prioritizes them.

Usage:
    from oorep.rubric_bandit_selector import RubricBanditSelector
    
    selector = RubricBanditSelector()
    
    # Record rubric performance
    selector.record_rubric_performance("Mind; Anxiety", "Puls", True)  # Correct
    
    # Select top-k discriminative rubrics
    selected = selector.select_rubrics(all_rubrics, k=5)
    
    # Get discrimination indices
    indices = selector.get_discrimination_indices()
"""

import math
import random
import sqlite3
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class RubricBanditSelector:
    """
    UCB1 Multi-Armed Bandit for rubric selection.
    
    Each rubric is an "arm" with unknown reward distribution.
    UCB1 balances exploration (try less-tested rubrics) with
    exploitation (use rubrics with proven discrimination).
    """
    
    def __init__(self, db_path: str = "data/rubric_bandit.db"):
        self.db_path = Path(db_path)
        self._ensure_database()
        self._cache = {}
        
    def _ensure_database(self):
        """Create bandit tracking tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        
        # Rubric performance tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rubric_performance (
                rubric_fullpath TEXT PRIMARY KEY,
                trials INTEGER DEFAULT 0,
                successes INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)
        
        # Per-remedy rubric effectiveness
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rubric_remedy_effectiveness (
                rubric_fullpath TEXT,
                remedy TEXT,
                times_present INTEGER DEFAULT 0,
                times_correct INTEGER DEFAULT 0,
                PRIMARY KEY (rubric_fullpath, remedy)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_rubric_performance(self, rubric_fullpath: str, 
                                   target_remedy: str,
                                   was_correct: bool):
        """
        Record whether a rubric helped identify the correct remedy.
        
        Args:
            rubric_fullpath: Full path of the rubric (e.g., "Mind; Anxiety")
            target_remedy: The remedy that was correct
            was_correct: Whether this rubric was in the correct remedy's profile
        """
        conn = sqlite3.connect(self.db_path)
        
        # Update overall performance
        conn.execute("""
            INSERT INTO rubric_performance (rubric_fullpath, trials, successes, failures, last_updated)
            VALUES (?, 1, ?, ?, datetime('now'))
            ON CONFLICT(rubric_fullpath) DO UPDATE SET
                trials = trials + 1,
                successes = successes + excluded.successes,
                failures = failures + excluded.failures,
                last_updated = datetime('now')
        """, (rubric_fullpath, 1 if was_correct else 0, 0 if was_correct else 1))
        
        # Update per-remedy effectiveness
        conn.execute("""
            INSERT INTO rubric_remedy_effectiveness 
            (rubric_fullpath, remedy, times_present, times_correct)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(rubric_fullpath, remedy) DO UPDATE SET
                times_present = times_present + 1,
                times_correct = times_correct + excluded.times_correct
        """, (rubric_fullpath, target_remedy, 1 if was_correct else 0))
        
        conn.commit()
        conn.close()
        self._cache.clear()
    
    def _get_rubric_stats(self, rubric_fullpath: str) -> Tuple[int, int]:
        """Get (trials, successes) for a rubric."""
        if rubric_fullpath in self._cache:
            return self._cache[rubric_fullpath]
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT trials, successes FROM rubric_performance WHERE rubric_fullpath = ?",
            (rubric_fullpath,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self._cache[rubric_fullpath] = (row[0], row[1])
            return (row[0], row[1])
        else:
            self._cache[rubric_fullpath] = (0, 0)
            return (0, 0)
    
    def calculate_ucb_score(self, rubric_fullpath: str, 
                           total_trials: int,
                           exploration_constant: float = 2.0) -> float:
        """
        Calculate UCB1 score for a rubric.
        
        UCB = empirical_mean + sqrt(2 * ln(total_trials) / rubric_trials)
        
        Args:
            rubric_fullpath: The rubric to score
            total_trials: Total trials across all rubrics
            exploration_constant: C in UCB formula (higher = more exploration)
            
        Returns:
            UCB score (higher = better)
        """
        trials, successes = self._get_rubric_stats(rubric_fullpath)
        
        if trials == 0:
            # Untried rubrics get infinite exploration bonus
            return float('inf')
        
        empirical_mean = successes / trials
        exploration_bonus = math.sqrt(
            exploration_constant * math.log(total_trials) / trials
        )
        
        return empirical_mean + exploration_bonus
    
    def select_rubrics(self, candidate_rubrics: List[Dict], 
                      k: int = 5,
                      exploration_constant: float = 2.0) -> List[Dict]:
        """
        Select top-k rubrics using UCB1 algorithm.
        
        Args:
            candidate_rubrics: List of rubric dicts with 'fullpath' key
            k: Number of rubrics to select
            exploration_constant: UCB exploration parameter
            
        Returns:
            Selected rubrics with UCB scores
        """
        if not candidate_rubrics:
            return []
        
        if len(candidate_rubrics) <= k:
            # Still need to add UCB scores even when returning all
            total_trials = sum(
                self._get_rubric_stats(r.get('fullpath', ''))[0] 
                for r in candidate_rubrics
            )
            total_trials = max(total_trials, 1)
            
            scored_rubrics = []
            for rubric in candidate_rubrics:
                fullpath = rubric.get('fullpath', '')
                ucb_score = self.calculate_ucb_score(
                    fullpath, total_trials, exploration_constant
                )
                trials, successes = self._get_rubric_stats(fullpath)
                scored_rubrics.append({
                    **rubric,
                    'ucb_score': ucb_score,
                    'trials': trials,
                    'successes': successes,
                    'empirical_mean': successes / trials if trials > 0 else 0.0
                })
            return scored_rubrics
        
        # Calculate total trials for UCB formula
        total_trials = sum(
            self._get_rubric_stats(r.get('fullpath', ''))[0] 
            for r in candidate_rubrics
        )
        total_trials = max(total_trials, 1)  # Avoid log(0)
        
        # Score each rubric
        scored_rubrics = []
        for rubric in candidate_rubrics:
            fullpath = rubric.get('fullpath', '')
            ucb_score = self.calculate_ucb_score(
                fullpath, total_trials, exploration_constant
            )
            
            trials, successes = self._get_rubric_stats(fullpath)
            
            scored_rubrics.append({
                **rubric,
                'ucb_score': ucb_score,
                'trials': trials,
                'successes': successes,
                'empirical_mean': successes / trials if trials > 0 else 0.0
            })
        
        # Sort by UCB score descending
        scored_rubrics.sort(key=lambda x: x['ucb_score'], reverse=True)
        
        return scored_rubrics[:k]
    
    def get_discrimination_indices(self) -> Dict[str, Dict]:
        """
        Calculate discrimination indices for all rubrics.
        
        Returns:
            Dict mapping rubric fullpath to discrimination metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT rubric_fullpath, trials, successes FROM rubric_performance"
        )
        
        indices = {}
        for fullpath, trials, successes in cursor.fetchall():
            if trials > 0:
                empirical_rate = successes / trials
                # Standard error of proportion
                se = math.sqrt(empirical_rate * (1 - empirical_rate) / trials)
                
                indices[fullpath] = {
                    'trials': trials,
                    'successes': successes,
                    'discrimination_rate': empirical_rate,
                    'standard_error': se,
                    'confidence_interval_95': (
                        max(0, empirical_rate - 1.96 * se),
                        min(1, empirical_rate + 1.96 * se)
                    )
                }
        
        conn.close()
        return indices
    
    def get_rubric_remedy_effectiveness(self, rubric_fullpath: str) -> Dict[str, Any]:
        """
        Get per-remedy effectiveness for a specific rubric.
        
        Returns:
            Dict with remedy effectiveness breakdown
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT remedy, times_present, times_correct 
            FROM rubric_remedy_effectiveness 
            WHERE rubric_fullpath = ?
            ORDER BY times_correct DESC
        """, (rubric_fullpath,))
        
        effectiveness = {}
        for remedy, present, correct in cursor.fetchall():
            effectiveness[remedy] = {
                'times_present': present,
                'times_correct': correct,
                'accuracy': correct / present if present > 0 else 0.0
            }
        
        conn.close()
        return effectiveness
    
    def calculate_precision_at_k(self, selected_rubrics: List[Dict],
                                  correct_remedy: str) -> float:
        """
        Calculate precision@k for rubric selection.
        
        Args:
            selected_rubrics: The rubrics that were selected
            correct_remedy: The remedy that was correct
            
        Returns:
            Precision at k (fraction of selected rubrics that contain correct remedy)
        """
        if not selected_rubrics:
            return 0.0
        
        conn = sqlite3.connect(self.db_path)
        
        correct_count = 0
        for rubric in selected_rubrics:
            fullpath = rubric.get('fullpath', '')
            cursor = conn.execute(
                """SELECT 1 FROM rubric_remedy_effectiveness 
                   WHERE rubric_fullpath = ? AND remedy = ? AND times_correct > 0""",
                (fullpath, correct_remedy)
            )
            if cursor.fetchone():
                correct_count += 1
        
        conn.close()
        return correct_count / len(selected_rubrics)
    
    def get_bandit_stats(self) -> Dict:
        """Return bandit algorithm statistics."""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute(
            "SELECT COUNT(*), SUM(trials), SUM(successes) FROM rubric_performance"
        )
        count, total_trials, total_successes = cursor.fetchone()
        
        # Get top performing rubrics
        cursor.execute("""
            SELECT rubric_fullpath, trials, successes 
            FROM rubric_performance 
            WHERE trials > 0
            ORDER BY CAST(successes AS REAL) / trials DESC
            LIMIT 10
        """)
        top_rubrics = [
            {
                'rubric': r[0],
                'trials': r[1],
                'successes': r[2],
                'rate': r[2] / r[1] if r[1] > 0 else 0
            }
            for r in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'total_rubrics_tracked': count or 0,
            'total_trials': total_trials or 0,
            'total_successes': total_successes or 0,
            'overall_success_rate': (total_successes / total_trials) if total_trials else 0.0,
            'top_performing_rubrics': top_rubrics
        }


def quick_select(rubrics: List[Dict], k: int = 5,
                 db_path: str = "data/rubric_bandit.db") -> List[Dict]:
    """Quick static function for UCB rubric selection."""
    selector = RubricBanditSelector(db_path=db_path)
    return selector.select_rubrics(rubrics, k=k)
