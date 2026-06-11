"""
Tests for Multi-Armed Bandit Rubric Selection (Module #112)
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from oorep.rubric_bandit_selector import RubricBanditSelector, quick_select


class TestRubricBanditSelector:
    """Test suite for UCB1 rubric selection."""
    
    @pytest.fixture
    def selector(self, tmp_path):
        """Create a fresh selector with temp database."""
        db_path = tmp_path / "test_bandit.db"
        return RubricBanditSelector(db_path=str(db_path))
    
    def test_initialization_creates_database(self, selector):
        """Test that initialization creates the database."""
        assert selector.db_path.exists()
    
    def test_record_rubric_performance(self, selector):
        """Test recording rubric performance."""
        selector.record_rubric_performance(
            "Mind; Anxiety", "Puls", was_correct=True
        )
        
        indices = selector.get_discrimination_indices()
        assert "Mind; Anxiety" in indices
        assert indices["Mind; Anxiety"]["successes"] == 1
        assert indices["Mind; Anxiety"]["trials"] == 1
    
    def test_record_multiple_performances(self, selector):
        """Test recording multiple performances for same rubric."""
        # Record 3 correct identifications
        for i in range(3):
            selector.record_rubric_performance(
                "Mind; Anxiety", f"PT-{i}", was_correct=True
            )
        
        indices = selector.get_discrimination_indices()
        assert indices["Mind; Anxiety"]["successes"] == 3
        assert indices["Mind; Anxiety"]["trials"] == 3
        assert indices["Mind; Anxiety"]["discrimination_rate"] == 1.0
    
    def test_ucb_score_calculation(self, selector):
        """Test UCB score calculation."""
        # Record some outcomes
        selector.record_rubric_performance("Rubric1", "Puls", True)
        selector.record_rubric_performance("Rubric1", "Ars", True)
        selector.record_rubric_performance("Rubric2", "Puls", False)
        
        ucb1 = selector.calculate_ucb_score("Rubric1", total_trials=3)
        ucb2 = selector.calculate_ucb_score("Rubric2", total_trials=3)
        
        assert ucb1 > ucb2  # Rubric1 should have higher score
    
    def test_ucb_score_new_rubric(self, selector):
        """Test UCB score for untried rubric."""
        ucb = selector.calculate_ucb_score("NewRubric", total_trials=1)
        assert ucb == float('inf')  # Infinite exploration bonus
    
    def test_select_rubrics_empty_list(self, selector):
        """Test selecting from empty list."""
        result = selector.select_rubrics([])
        assert result == []
    
    def test_select_rubrics_fewer_than_k(self, selector):
        """Test selecting when candidates < k."""
        rubrics = [{"fullpath": "Mind; Anxiety"}]
        result = selector.select_rubrics(rubrics, k=5)
        assert len(result) == 1
    
    def test_select_rubrics_returns_fields(self, selector):
        """Test that selection returns expected fields."""
        rubrics = [{"fullpath": "Mind; Anxiety", "id": 1}]
        
        selector.record_rubric_performance("Mind; Anxiety", "Puls", True)
        
        result = selector.select_rubrics(rubrics, k=1)
        
        assert len(result) == 1
        assert result[0]["fullpath"] == "Mind; Anxiety"
        assert "ucb_score" in result[0]
        assert "trials" in result[0]
        assert "successes" in result[0]
    
    def test_select_rubrics_orders_by_ucb(self, selector):
        """Test that rubrics are ordered by UCB score."""
        rubrics = [
            {"fullpath": "Rubric1"},
            {"fullpath": "Rubric2"},
            {"fullpath": "Rubric3"}
        ]
        
        # Record different performances
        selector.record_rubric_performance("Rubric1", "Puls", True)
        selector.record_rubric_performance("Rubric1", "Ars", True)
        selector.record_rubric_performance("Rubric2", "Puls", False)
        selector.record_rubric_performance("Rubric2", "Ars", False)
        
        result = selector.select_rubrics(rubrics, k=3)
        
        # Rubric1 should have highest UCB score
        assert result[0]["fullpath"] == "Rubric1"
        assert result[0]["ucb_score"] > result[1]["ucb_score"]
    
    def test_discrimination_indices(self, selector):
        """Test discrimination index calculation."""
        selector.record_rubric_performance("TestRubric", "Puls", True)
        selector.record_rubric_performance("TestRubric", "Puls", True)
        selector.record_rubric_performance("TestRubric", "Ars", False)
        
        indices = selector.get_discrimination_indices()
        
        assert "TestRubric" in indices
        assert indices["TestRubric"]["discrimination_rate"] == 2/3
        assert 0 < indices["TestRubric"]["standard_error"] < 1
        assert len(indices["TestRubric"]["confidence_interval_95"]) == 2
    
    def test_discrimination_indices_empty(self, selector):
        """Test discrimination indices with no data."""
        indices = selector.get_discrimination_indices()
        assert indices == {}
    
    def test_rubric_remedy_effectiveness(self, selector):
        """Test per-remedy effectiveness tracking."""
        selector.record_rubric_performance("Mind; Anxiety", "Puls", True)
        selector.record_rubric_performance("Mind; Anxiety", "Puls", True)
        selector.record_rubric_performance("Mind; Anxiety", "Ars", False)
        
        effectiveness = selector.get_rubric_remedy_effectiveness("Mind; Anxiety")
        
        assert "Puls" in effectiveness
        assert "Ars" in effectiveness
        assert effectiveness["Puls"]["accuracy"] == 1.0
        assert effectiveness["Ars"]["accuracy"] == 0.0
    
    def test_precision_at_k(self, selector):
        """Test precision@k calculation."""
        # Setup rubric remedy associations
        selector.record_rubric_performance("Rubric1", "Puls", True)
        selector.record_rubric_performance("Rubric2", "Puls", True)
        selector.record_rubric_performance("Rubric3", "Ars", True)
        
        selected_rubrics = [
            {"fullpath": "Rubric1"},
            {"fullpath": "Rubric2"}
        ]
        
        precision = selector.calculate_precision_at_k(
            selected_rubrics, "Puls"
        )
        assert precision == 1.0  # Both selected rubrics contain Puls
    
    def test_precision_at_k_empty_selection(self, selector):
        """Test precision@k with empty selection."""
        precision = selector.calculate_precision_at_k([], "Puls")
        assert precision == 0.0
    
    def test_bandit_stats(self, selector):
        """Test bandit statistics."""
        # Add some data
        selector.record_rubric_performance("Rubric1", "Puls", True)
        selector.record_rubric_performance("Rubric2", "Puls", False)
        
        stats = selector.get_bandit_stats()
        
        assert stats['total_rubrics_tracked'] == 2
        assert stats['total_trials'] == 2
        assert stats['total_successes'] == 1
        assert stats['overall_success_rate'] == 0.5
        assert len(stats['top_performing_rubrics']) == 2
    
    def test_quick_select_function(self, tmp_path):
        """Test the quick_select convenience function."""
        db_path = tmp_path / "quick_test.db"
        
        rubrics = [
            {"fullpath": "Mind; Anxiety"},
            {"fullpath": "Head; Pain; Morning"}
        ]
        
        result = quick_select(rubrics, k=2, db_path=str(db_path))
        assert len(result) == 2
    
    def test_exploration_constant_parameter(self, selector):
        """Test exploration constant parameter."""
        rubrics = [
            {"fullpath": "Rubric1"},
            {"fullpath": "Rubric2"}
        ]
        
        selector.record_rubric_performance("Rubric1", "Puls", True)
        
        # Different exploration constants should yield different results
        result_high = selector.select_rubrics(rubrics, k=2, exploration_constant=4.0)
        result_low = selector.select_rubrics(rubrics, k=2, exploration_constant=0.5)
        
        # Both should return both rubrics since we have few candidates
        assert len(result_high) == 2
        assert len(result_low) == 2
    
    def test_cache_behavior(self, selector):
        """Test cache behavior."""
        # First call should populate cache
        selector._get_rubric_stats("TestRubric")
        
        # Record new data
        selector.record_rubric_performance("TestRubric", "Puls", True)
        
        # Cache should be cleared, new data reflected
        trials, successes = selector._get_rubric_stats("TestRubric")
        assert trials == 1
        assert successes == 1
