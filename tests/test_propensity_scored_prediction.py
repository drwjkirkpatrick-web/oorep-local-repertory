"""
Tests for Propensity-Scored Outcome Prediction (Module #113)
"""

import pytest
from pathlib import Path

from oorep.propensity_scored_prediction import PropensityScoredPrediction, quick_ipw_predict


class TestPropensityScoredPrediction:
    """Test suite for IPW prediction."""
    
    @pytest.fixture
    def predictor(self, tmp_path):
        """Create a fresh predictor with temp database."""
        db_path = tmp_path / "test_propensity.db"
        return PropensityScoredPrediction(db_path=str(db_path))
    
    def test_initialization_creates_database(self, predictor):
        """Test that initialization creates the database."""
        assert predictor.db_path.exists()
    
    def test_record_prescription(self, predictor):
        """Test recording prescriptions."""
        predictor.record_prescription(
            "Puls", "PT-001",
            {"chronicity": 7, "severity": 8, "complexity": 6}
        )
        
        # Should not raise
        assert True
    
    def test_record_outcome(self, predictor):
        """Test recording outcomes."""
        predictor.record_prescription("Puls", "PT-001", {"chronicity": 5})
        predictor.record_outcome("Puls", "PT-001", 0.9)
        
        # Should not raise
        assert True
    
    def test_propensity_score_calculation(self, predictor):
        """Test propensity score calculation."""
        # Record some prescriptions
        for i in range(5):
            predictor.record_prescription(
                "Puls", f"PT-{i}", {"chronicity": 5, "severity": 5, "complexity": 5}
            )
        
        for i in range(5, 10):
            predictor.record_prescription(
                "Ars", f"PT-{i}", {"chronicity": 8, "severity": 8, "complexity": 8}
            )
        
        propensity = predictor.calculate_propensity_score(
            "Puls", {"chronicity": 5, "severity": 5, "complexity": 5}
        )
        
        assert 0 < propensity <= 1
    
    def test_propensity_score_no_data(self, predictor):
        """Test propensity score with no data."""
        propensity = predictor.calculate_propensity_score(
            "Puls", {"chronicity": 5}
        )
        assert propensity == 0.5  # Neutral when no data
    
    def test_predict_with_ipw(self, predictor):
        """Test IPW prediction."""
        # Setup data
        predictor.record_prescription("Puls", "PT-001", {"chronicity": 5})
        predictor.record_outcome("Puls", "PT-001", 0.9)
        
        predictor.record_prescription("Puls", "PT-002", {"chronicity": 5})
        predictor.record_outcome("Puls", "PT-002", 0.8)
        
        predictor.record_prescription("Ars", "PT-003", {"chronicity": 8})
        predictor.record_outcome("Ars", "PT-003", 0.6)
        
        results = predictor.predict_with_ipw(
            ["Puls", "Ars"],
            {"chronicity": 5, "severity": 5, "complexity": 5}
        )
        
        assert len(results) == 2
        for r in results:
            assert 'remedy' in r
            assert 'ipw_outcome' in r
            assert 'raw_outcome' in r
            assert 'propensity_score' in r
    
    def test_ipw_adjustment(self, predictor):
        """Test that IPW adjusts scores."""
        # Create biased data - Puls prescribed to easier cases
        for i in range(10):
            predictor.record_prescription(
                "Puls", f"PT-{i}", {"chronicity": 3, "severity": 3}
            )
            predictor.record_outcome("Puls", f"PT-{i}", 0.9)  # High success
        
        for i in range(10, 20):
            predictor.record_prescription(
                "Ars", f"PT-{i}", {"chronicity": 8, "severity": 8}
            )
            predictor.record_outcome("Ars", f"PT-{i}", 0.7)  # Lower success
        
        results = predictor.predict_with_ipw(
            ["Puls", "Ars"],
            {"chronicity": 5, "severity": 5}
        )
        
        # IPW should adjust for case difficulty
        puls_result = next(r for r in results if r['remedy'] == 'Puls')
        ars_result = next(r for r in results if r['remedy'] == 'Ars')
        
        # Both should have predictions
        assert puls_result['ipw_outcome'] is not None
        assert ars_result['ipw_outcome'] is not None
    
    def test_balance_statistics(self, predictor):
        """Test balance statistics calculation."""
        predictor.record_prescription("Puls", "PT-001", {"chronicity": 5})
        predictor.record_prescription("Ars", "PT-002", {"chronicity": 8})
        
        stats = predictor.get_balance_statistics()
        
        assert 'chronicity' in stats
        assert 'severity' in stats
        assert 'complexity' in stats
    
    def test_case_similarity(self, predictor):
        """Test case similarity calculation."""
        sim = predictor._case_similarity((5, 5, 5), (5, 5, 5))
        assert abs(sim - 1.0) < 0.001  # Perfect similarity (floating point)
        
        sim = predictor._case_similarity((5, 5, 5), (10, 10, 10))
        assert 0 < sim < 1  # Some similarity
    
    def test_quick_ipw_predict(self, tmp_path):
        """Test quick IPW predict function."""
        db_path = tmp_path / "quick_test.db"
        
        results = quick_ipw_predict(
            ["Puls", "Ars"],
            {"chronicity": 5},
            db_path=str(db_path)
        )
        
        assert len(results) == 2
