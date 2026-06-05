"""
Tests for Graphic Analysis (Feature #17)

Covers: heatmap, kingdom_pie, symptom_coverage, timeline, score_distribution,
render_dashboard, edge cases.
"""

import pytest
from oorep.graphic_analysis import GraphicAnalysisEngine


@pytest.fixture
def engine():
    tax = {
        "PULS": {"kingdom": "Plant", "family": "Ranunculaceae"},
        "ARS": {"kingdom": "Mineral", "family": "Metal"},
        "LACH": {"kingdom": "Animal", "family": "Viperidae"},
        "SIL": {"kingdom": "Mineral", "family": "Silica"},
    }
    return GraphicAnalysisEngine(remedy_taxonomy=tax)


@pytest.fixture
def sample_results():
    return [
        {"remedy": "PULS", "score": 28.5, "rubric_ids": [1, 2, 3], "grade": 3},
        {"remedy": "ARS", "score": 24.0, "rubric_ids": [1, 4], "grade": 3},
        {"remedy": "LACH", "score": 22.0, "rubric_ids": [2, 5], "grade": 2},
        {"remedy": "SIL", "score": 18.0, "rubric_ids": [3], "grade": 1},
    ]


class TestHeatmap:

    def test_heatmap_basic(self, engine, sample_results):
        hm = engine.heatmap(sample_results, top_n=3)
        assert hm["type"] == "heatmap"
        assert hm["rows"] == ["PULS", "ARS", "LACH"]
        assert len(hm["values"]) == 3
        assert all(len(row) == len(hm["cols"]) for row in hm["values"])

    def test_heatmap_empty(self, engine):
        hm = engine.heatmap([])
        assert hm["rows"] == []
        assert hm["values"] == []

    def test_heatmap_no_rubric_ids(self, engine):
        r = [{"remedy": "PULS", "score": 10}]
        hm = engine.heatmap(r)
        assert hm["rows"] == ["PULS"]


class TestKingdomPie:

    def test_pie_distribution(self, engine, sample_results):
        pie = engine.kingdom_pie(sample_results)
        assert pie["type"] == "pie"
        assert len(pie["segments"]) > 0
        labels = {s["label"] for s in pie["segments"]}
        assert {"Plant", "Mineral", "Animal"}.issubset(labels) or labels & {"Plant", "Mineral", "Animal"}
        # Check percentages sum to ~100
        total_pct = sum(s["percentage"] for s in pie["segments"])
        assert 99 <= total_pct <= 101

    def test_pie_unknown_taxonomy(self, engine):
        r = [{"remedy": "XYZ", "score": 10}]
        pie = engine.kingdom_pie(r)
        assert any(s["label"] == "Unknown" for s in pie["segments"])

    def test_pie_empty(self, engine):
        pie = engine.kingdom_pie([])
        assert pie["segments"] == []


class TestSymptomCoverage:

    def test_coverage(self, engine, sample_results):
        symptoms = ["anxiety", "fear", "pain"]
        bar = engine.symptom_coverage(sample_results, symptoms)
        assert bar["type"] == "bar"
        assert len(bar["bars"]) == 4
        for b in bar["bars"]:
            assert 0 <= b["value"] <= len(symptoms)


class TestTimeline:

    def test_timeline_sorted(self, engine):
        history = [
            {"date": "2024-06-01", "remedy": "PULS", "potency": "30C", "outcome_score": "improved"},
            {"date": "2024-03-01", "remedy": "ARS", "potency": "6C", "outcome_score": "partial"},
        ]
        tl = engine.timeline(history)
        assert tl["type"] == "timeline"
        assert tl["points"][0]["title"].startswith("ARS")
        assert tl["points"][1]["title"].startswith("PULS")

    def test_timeline_empty(self, engine):
        tl = engine.timeline([])
        assert tl["points"] == []
        assert tl["start_date"] is None


class TestScoreDistribution:

    def test_distribution_bins(self, engine, sample_results):
        hist = engine.score_distribution(sample_results, bins=3)
        assert hist["type"] == "histogram"
        assert len(hist["bins"]) == 3
        assert all("count" in b for b in hist["bins"])
        total = sum(b["count"] for b in hist["bins"])
        assert total == len(sample_results)

    def test_distribution_empty(self, engine):
        hist = engine.score_distribution([])
        assert hist["bins"] == []


class TestDashboard:

    def test_render_dashboard(self, engine, sample_results):
        dash = engine.render_dashboard(
            results=sample_results,
            symptoms=["anxiety", "pain"],
            patient_history=[],
        )
        assert "heatmap" in dash
        assert "kingdom_pie" in dash
        assert "symptom_coverage" in dash
        assert "timeline" in dash
        assert "score_distribution" in dash


class TestFeatureOverview:

    def test_overview(self, engine):
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 17
        assert "charts" in ov
