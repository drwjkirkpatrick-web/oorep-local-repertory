"""tests for case_analysis_bridge.py"""

from oorep.case_analysis_bridge import (
    CaseAnalysisBridge,
    DifferentiatingSyndrome,
    ConfusedPairAnalysis,
    find_differentiating_syndromes,
    build_recommended_questions,
    quick_analysis,
)


def test_generate_mock_cooccurrence_rules():
    """Mock rules should contain realistic lift values."""
    from oorep.case_analysis_bridge import generate_mock_cooccurrence_rules
    rules = generate_mock_cooccurrence_rules()
    assert len(rules) >= 5
    for r in rules:
        assert r["lift"] > 1.0
        assert 0.0 <= r["confidence"] <= 1.0
        assert len(r["remedy_affinity"]) >= 2


def test_generate_mock_confusion_pairs():
    """Mock confusion pairs should have realistic rates."""
    from oorep.case_analysis_bridge import generate_mock_confusion_pairs
    pairs = generate_mock_confusion_pairs()
    assert len(pairs) >= 3
    for p in pairs:
        assert 0.0 < p["rate"] < 1.0
        assert p["total_a"] > 0
        assert p["total_b"] > 0
        assert p["confusion_count"] > 0


def test_find_differentiating_syndromes():
    """Should find syndromes that separate two remedies, excluding shared ones."""
    from oorep.case_analysis_bridge import generate_mock_cooccurrence_rules
    rules = generate_mock_cooccurrence_rules()
    
    # Pulsatilla and Natrum-mur share the weeping rule — should be excluded
    syndromes = find_differentiating_syndromes("Pulsatilla", "Natrum-mur", rules)
    weeping_rule = None
    for s in syndromes:
        if "weep" in s.symptom_a.lower():
            weeping_rule = s
    assert weeping_rule is None, "Shared syndromes should be excluded"
    
    # Pulsatilla and Sepia do not share a rule — should find differentiating syndromes
    syndromes = find_differentiating_syndromes("Pulsatilla", "Sepia", rules)
    # Pulsatilla appears in rules 4 and 8; Sepia appears in none of the mock rules
    # So rules where Pulsatilla appears but Sepia does not should show as differentiating
    assert len(syndromes) > 0


def test_build_recommended_questions():
    """Should generate concrete questions from syndromes."""
    syndrome = DifferentiatingSyndrome(
        symptom_a="worse from motion",
        symptom_b="stitching pain",
        lift=4.2,
        confidence=0.72,
        remedy_a_prevalence=0.65,
        remedy_b_prevalence=0.15,
        discriminative_power=0.5,
    )
    questions = build_recommended_questions([syndrome])
    assert len(questions) > 0
    assert "stitching" in questions[0].lower() or "motion" in questions[0].lower()


def test_case_analysis_bridge_init():
    """Bridge should load mock data."""
    bridge = CaseAnalysisBridge()
    assert len(bridge.cooccurrence_rules) > 0
    assert len(bridge.confusion_pairs) > 0


def test_analyze_confused_pair_found():
    """Should analyze a known confused pair."""
    bridge = CaseAnalysisBridge()
    result = bridge.analyze_confused_pair("Pulsatilla", "Sepia")
    assert result is not None
    assert result.remedy_a == "Pulsatilla"
    assert result.remedy_b == "Sepia"
    assert result.historical_confusion_rate > 0
    assert result.recommended_threshold >= 10.0
    assert len(result.recommended_questions) > 0


def test_analyze_confused_pair_not_found():
    """Should return None for unknown pair."""
    bridge = CaseAnalysisBridge()
    result = bridge.analyze_confused_pair("UnknownA", "UnknownB")
    assert result is None


def test_generate_report():
    """Report should contain all sections."""
    bridge = CaseAnalysisBridge()
    report = bridge.generate_report(top_n=3)
    assert len(report.top_confused_pairs) > 0
    assert len(report.strong_syndromes) > 0
    assert len(report.current_case_recommendations) > 0
    assert 0.0 < report.overall_precision_at_70 < 1.0
    assert 0.0 < report.overall_precision_at_90 < 1.0
    assert report.overall_precision_at_90 > report.overall_precision_at_70


def test_quick_analysis():
    """Quick function should return a report."""
    report = quick_analysis(top_n=3)
    assert len(report.top_confused_pairs) > 0
    assert report.overall_precision_at_70 > 0
    assert len(report.current_case_recommendations) > 0


def test_confusion_rate_affects_threshold():
    """Higher confusion should raise the recommended threshold."""
    bridge = CaseAnalysisBridge()
    
    # Find the most and least confused pairs
    sorted_pairs = sorted(bridge.confusion_pairs, key=lambda p: p["rate"])
    least = sorted_pairs[0]
    most = sorted_pairs[-1]
    
    least_analysis = bridge.analyze_confused_pair(least["remedy_a"], least["remedy_b"])
    most_analysis = bridge.analyze_confused_pair(most["remedy_a"], most["remedy_b"])
    
    assert least_analysis is not None
    assert most_analysis is not None
    assert most_analysis.recommended_threshold >= least_analysis.recommended_threshold
