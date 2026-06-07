"""Tests for repertory_pca.py (Module #67)"""

import pytest
from oorep.repertory_pca import RepertoryPCA


@pytest.fixture
def pca():
    return RepertoryPCA()


class TestFit:

    def test_fit_basic(self, pca):
        result = pca.fit(n_components=3)
        assert "n_components" in result
        assert result["n_remedies"] == 8
        assert result["n_rubrics"] == 6
        assert len(result["explained_variance"]) == 3

    def test_variance_sums(self, pca):
        result = pca.fit(n_components=5)
        assert sum(result["explained_variance"]) <= 1.0
        assert result["cumulative_variance"][-1] <= 1.0

    def test_singular_values_positive(self, pca):
        result = pca.fit(n_components=4)
        for s in result["singular_values"]:
            assert s >= 0


class TestProjection:

    def test_project_2d(self, pca):
        pca.fit(n_components=2)
        proj = pca.project_2d()
        assert len(proj) == 8
        assert "x" in proj[0]
        assert "y" in proj[0]
        assert proj[0]["remedy"] == "PULS"

    def test_project_3d(self, pca):
        pca.fit(n_components=3)
        proj = pca.project_3d()
        assert len(proj) == 8
        assert "z" in proj[0]


class TestLoadings:

    def test_loadings(self, pca):
        pca.fit(n_components=3)
        loadings = pca.get_loadings(component=0, top_n=5)
        assert len(loadings) <= 5
        assert "loading" in loadings[0]


class TestFeatureOverview:

    def test_overview(self, pca):
        ov = pca.get_feature_overview()
        assert ov["feature_id"] == 67
        assert "pca" in ov["supports"]
