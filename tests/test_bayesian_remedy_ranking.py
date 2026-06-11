"""
Tests for Bayesian Remedy Ranking with Thompson Sampling (Module #111)
"""

import pytest
import tempfile
import os
from pathlib import Path

from oorep.bayesian_remedy_ranking import BayesianRemedyRanking, quick_rank


class TestBayesianRemedyRanking:
    """Test suite for Thompson Sampling remedy ranking."""
    
    @pytest.fixture
    def engine(self, tmp_path):
        """Create a fresh engine with temp database."""
        db_path = tmp_path / "test_outcomes.db"
        return BayesianRemedyRanking(db_path=str(db_path))
    
    def test_initialization_creates_database(self, engine):
        """Test that initialization creates the database."""
        assert engine.db_path.exists()
    
    def test_record_outcome(self, engine):
        """Test recording outcomes."""
        engine.record_outcome("Puls", "PT-001", 0.9, "anxiety")
        stats = engine.get_learning_stats()
        assert stats['total_observations'] == 1
        assert 'Puls' in stats['remedy_counts']
    
    def test_beta_params_with_no_data(self, engine):
        """Test beta parameters with no observations (Laplace smoothing)."""
        alpha, beta = engine._get_beta_params("UnknownRemedy")
        assert alpha == 1.0  # Laplace prior
        assert beta == 1.0
    
    def test_beta_params_with_success(self, engine):
        """Test beta parameters update with success."""
        engine.record_outcome("Puls", "PT-001", 1.0, "anxiety")
        alpha, beta = engine._get_beta_params("Puls")
        assert alpha == 2.0  # 1 success + 1 prior
        assert beta == 1.0   # 0 failures + 1 prior
    
    def test_beta_params_with_failure(self, engine):
        """Test beta parameters update with failure."""
        engine.record_outcome("Puls", "PT-001", 0.0, "anxiety")
        alpha, beta = engine._get_beta_params("Puls")
        assert alpha == 1.0  # 0 successes + 1 prior
        assert beta == 2.0   # 1 failure + 1 prior
    
    def test_rank_remedies_empty_list(self, engine):
        """Test ranking empty list returns empty."""
        result = engine.rank_remedies([])
        assert result == []
    
    def test_rank_remedies_returns_all_fields(self, engine):
        """Test that ranking returns expected fields."""
        remedies = [
            {"remedy": "Puls", "score": 28.5},
            {"remedy": "Ars", "score": 24.0},
        ]
        
        # Add some outcome data
        engine.record_outcome("Puls", "PT-001", 0.9, "anxiety")
        engine.record_outcome("Puls", "PT-002", 0.8, "insomnia")
        
        result = engine.rank_remedies(remedies, top_n=2)
        
        assert len(result) == 2
        for r in result:
            assert 'thompson_score' in r
            assert 'uncertainty' in r
            assert 'alpha' in r
            assert 'beta' in r
            assert 'observations' in r
            assert 'posterior_mean' in r
    
    def test_rank_remedies_orders_by_thompson_score(self, engine):
        """Test that remedies are ordered by Thompson score."""
        # Puls has better outcomes
        engine.record_outcome("Puls", "PT-001", 1.0, "anxiety")
        engine.record_outcome("Puls", "PT-002", 1.0, "insomnia")
        engine.record_outcome("Ars", "PT-003", 0.5, "anxiety")
        
        remedies = [
            {"remedy": "Ars", "score": 30.0},  # Higher classical score
            {"remedy": "Puls", "score": 20.0},
        ]
        
        result = engine.rank_remedies(remedies, top_n=2, samples=100)
        
        # Puls should rank higher due to better outcomes
        assert result[0]['remedy'] == 'Puls'
        assert result[0]['posterior_mean'] > result[1]['posterior_mean']
    
    def test_uncertainty_decreases_with_observations(self, engine):
        """Test that uncertainty decreases with more observations."""
        # Add many observations for Puls
        for i in range(20):
            engine.record_outcome("Puls", f"PT-{i:03d}", 0.9, "anxiety")
        
        # Add few observations for Ars
        engine.record_outcome("Ars", "PT-100", 0.9, "anxiety")
        
        remedies = [
            {"remedy": "Puls", "score": 25.0},
            {"remedy": "Ars", "score": 25.0},
        ]
        
        result = engine.rank_remedies(remedies, samples=500)
        
        # Puls should have lower uncertainty
        puls = next(r for r in result if r['remedy'] == 'Puls')
        ars = next(r for r in result if r['remedy'] == 'Ars')
        assert puls['observations'] > ars['observations']
    
    def test_cumulative_regret(self, engine):
        """Test regret calculation."""
        engine.record_outcome("Puls", "PT-001", 1.0, "anxiety")
        engine.record_outcome("Puls", "PT-002", 1.0, "anxiety")
        engine.record_outcome("Ars", "PT-003", 0.5, "anxiety")
        
        regret = engine.get_cumulative_regret("Puls", "Ars")
        assert regret > 0  # Regret should be positive
        
        # No regret if optimal is selected
        regret_optimal = engine.get_cumulative_regret("Puls", "Puls")
        assert regret_optimal == 0.0
    
    def test_recommend_with_exploration(self, engine):
        """Test epsilon-greedy recommendation."""
        engine.record_outcome("Puls", "PT-001", 1.0, "anxiety")
        
        remedies = [
            {"remedy": "Puls", "score": 25.0},
            {"remedy": "Ars", "score": 20.0},
        ]
        
        # With exploration_rate=0, should always use Thompson
        result = engine.recommend_with_exploration(remedies, exploration_rate=0.0)
        assert result is not None
        assert result['selection_method'] == 'thompson_sampling'
    
    def test_recommend_with_exploration_empty(self, engine):
        """Test recommendation with empty list."""
        result = engine.recommend_with_exploration([])
        assert result is None
    
    def test_learning_stats(self, engine):
        """Test learning statistics."""
        # Add multiple remedies
        engine.record_outcome("Puls", "PT-001", 0.9, "anxiety")
        engine.record_outcome("Puls", "PT-002", 0.8, "anxiety")
        engine.record_outcome("Ars", "PT-003", 0.7, "anxiety")
        
        stats = engine.get_learning_stats()
        
        assert stats['total_observations'] == 3
        assert stats['remedies_with_data'] == 2
        assert 'Puls' in stats['remedy_counts']
        assert 'Ars' in stats['remedy_counts']
        assert stats['remedy_counts']['Puls']['n'] == 2
    
    def test_quick_rank_function(self, tmp_path):
        """Test the quick_rank convenience function."""
        db_path = tmp_path / "quick_test.db"
        
        remedies = [
            {"remedy": "Puls", "score": 28.5},
            {"remedy": "Ars", "score": 24.0},
        ]
        
        result = quick_rank(remedies, db_path=str(db_path))
        assert len(result) == 2
        assert 'thompson_score' in result[0]
    
    def test_cache_invalidation(self, engine):
        """Test that cache is invalidated after new outcome."""
        engine.record_outcome("Puls", "PT-001", 0.9, "anxiety")
        
        # First call populates cache
        alpha1, beta1 = engine._get_beta_params("Puls")
        
        # Add another outcome
        engine.record_outcome("Puls", "PT-002", 0.8, "anxiety")
        
        # Cache should be cleared, new params returned
        alpha2, beta2 = engine._get_beta_params("Puls")
        assert alpha2 > alpha1  # More successes
    
    def test_multiple_outcomes_same_patient_updates(self, engine):
        """Test that same patient remedy updates rather than duplicates."""
        engine.record_outcome("Puls", "PT-001", 0.5, "anxiety")
        engine.record_outcome("Puls", "PT-001", 0.9, "anxiety")  # Update
        
        stats = engine.get_learning_stats()
        assert stats['total_observations'] == 1
        assert stats['remedy_counts']['Puls']['avg_score'] == 0.9
