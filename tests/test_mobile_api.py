"""
Tests for Mobile-Responsive API Layer — Feature #27

Covers: route descriptors, repertorize, search, health, errors.
"""

import pytest
from oorep.mobile_api import OOREPApp, APIRoute


class MockRep:

    def repertorize(self, symptoms):
        return [{"remedy": "ARS", "score": 28}]

    def search_rubrics(self, q):
        return [{"id": 1, "text": q}]

    def search_remedies(self, q):
        return [{"remedy": q.upper(), "score": 10}]


class TestRoutes:

    def test_get_routes_returns_list(self):
        app = OOREPApp()
        routes = app.get_routes()
        assert isinstance(routes, list)
        assert len(routes) > 0
        assert all(isinstance(r, APIRoute) for r in routes)

    def test_routes_have_paths(self):
        app = OOREPApp()
        paths = [r.path for r in app.get_routes()]
        assert "/api/repertorize" in paths
        assert "/api/health" in paths


class TestRepertorize:

    def test_repertorize_ok(self):
        app = OOREPApp(repertory=MockRep())
        result = app.repertorize(symptoms=[{"id": 1}])
        assert result["status"] == "ok"
        assert result["count"] == 1

    def test_repertorize_no_rep_errors(self):
        app = OOREPApp()
        result = app.repertorize(symptoms=[{"id": 1}])
        assert result["status"] == "error"
        assert result["code"] == 503


class TestSearchRubrics:

    def test_search_rubrics_ok(self):
        app = OOREPApp(repertory=MockRep())
        result = app.search_rubrics(q="anxiety")
        assert result["status"] == "ok"
        assert result["query"] == "anxiety"

    def test_search_rubrics_no_rep(self):
        app = OOREPApp()
        result = app.search_rubrics(q="anxiety")
        assert result["status"] == "error"


class TestSearchRemedies:

    def test_search_remedies_ok(self):
        app = OOREPApp(repertory=MockRep())
        result = app.search_remedies(q="ars")
        assert result["status"] == "ok"

    def test_search_remedies_no_q(self):
        app = OOREPApp(repertory=MockRep())
        result = app.search_remedies(q="")
        assert result["status"] == "error"


class TestCompareRemedies:

    def test_compare_two_remedies(self):
        app = OOREPApp(repertory=MockRep())
        result = app.compare_remedies(a="ars", b="puls")
        assert result["status"] == "ok"
        assert "results_a" in result
        assert "results_b" in result


class TestHealth:

    def test_health_check(self):
        app = OOREPApp()
        result = app.health_check()
        assert result["status"] == "ok"
        assert result["service"] == "OOREP API"


class TestFeatureOverview:

    def test_overview(self):
        app = OOREPApp()
        ov = app.get_feature_overview()
        assert ov["feature_id"] == 27
        assert ov["feature_name"] == "Mobile-Responsive API Layer"
        assert ov["routes"] > 0
