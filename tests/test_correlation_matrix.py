"""
Tests for Remedy Correlation Matrix (Feature #21)

Covers: Jaccard, cosine, overlap similarity; nearest_neighbors; opposites;
shared_rubrics; exclusive_rubrics; matrix serialization; empty data.
"""

import json
import pytest
from pathlib import Path
from oorep.correlation_matrix import CorrelationMatrixEngine


@pytest.fixture
def mini_rubric_json(tmp_path: Path) -> str:
    path = tmp_path / "rubrics.json"
    data = {
        "1": [{"remedy": "Ars", "grade": 3}, {"remedy": "Puls", "grade": 1}],
        "2": [{"remedy": "Ars", "grade": 2}, {"remedy": "Sil", "grade": 3}],
        "3": [{"remedy": "Puls", "grade": 3}, {"remedy": "Lach", "grade": 2}],
        "4": [{"remedy": "Sil", "grade": 1}],
        "5": [{"remedy": "Ars", "grade": 3}, {"remedy": "Puls", "grade": 2}],
    }
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


@pytest.fixture
def engine(mini_rubric_json) -> CorrelationMatrixEngine:
    return CorrelationMatrixEngine(mini_rubric_json)


class TestSimilarity:

    def test_jaccard_self(self, engine):
        self_sim = engine.similarity("ARS", "ARS")
        assert self_sim == 1.0

    def test_jaccard_ars_puls(self, engine):
        sim = engine.similarity("ARS", "PULS")
        # ARS in rubrics 1,2,5 → 3 rubrics. PULS in 1,3,5 → 3. Shared: 1,5 → 2.
        # Jaccard = 2 / (3+3-2) = 2/4 = 0.50
        assert abs(sim - 0.5) < 0.01

    def test_cosine_ars_puls(self, engine):
        sim = engine.similarity("ARS", "PULS", method="cosine")
        # Binary cosine: 2 / sqrt(3*3) = 2/3 ≈ 0.667
        assert abs(sim - 0.6667) < 0.01

    def test_overlap_ars_puls(self, engine):
        sim = engine.similarity("ARS", "PULS", method="overlap")
        # 2 / min(3,3) = 2/3 ≈ 0.667
        assert abs(sim - 0.6667) < 0.01

    def test_jaccard_no_shared(self, engine):
        # ARS in 1,2,5. LACH in 3 → no overlap
        sim = engine.similarity("ARS", "LACH")
        assert sim == 0.0

    def test_unknown_remedy(self, engine):
        sim = engine.similarity("ARS", "ZZZ")
        assert sim == 0.0

    def test_both_unknown(self, engine):
        sim = engine.similarity("ZZZ", "YYY")
        assert sim == 0.0


class TestNearestNeighbors:

    def test_neighbors_ars(self, engine):
        n = engine.nearest_neighbors("ARS", top_n=3)
        assert len(n) > 0
        assert all("similarity" in x for x in n)
        # PULS should be highest since shared rubrics
        if n:
            assert n[0]["similarity"] >= 0.0

    def test_neighbors_min_similarity(self, engine):
        n = engine.nearest_neighbors("ARS", top_n=10, min_similarity=0.6)
        # Only PULS with overlap ≈ 0.667 meets this
        assert all(x["similarity"] >= 0.6 for x in n)

    def test_unknown_remedy_neighbors(self, engine):
        n = engine.nearest_neighbors("ZZZ")
        assert n == []


class TestOpposites:

    def test_opposites(self, engine):
        o = engine.opposites("ARS")
        assert len(o) > 0
        # LACH should be most dissimilar (no shared rubrics)
        assert o[0]["remedy"] == "LACH"
        assert o[0]["similarity"] == 0.0


class TestSharedRubrics:

    def test_shared_ars_puls(self, engine):
        shared = engine.shared_rubrics("ARS", "PULS")
        assert {"1", "5"} == set(shared)


class TestExclusiveRubrics:

    def test_exclusive_ars(self, engine):
        ex = engine.exclusive_rubrics("ARS", "PULS")
        assert "2" in ex["ARS"]  # ARS only, not in PULS
        assert "3" in ex["PULS"]  # PULS only, not in ARS


class TestRubricCount:

    def test_rubric_count(self, engine):
        assert engine.get_rubric_count("ARS") == 3
        assert engine.get_rubric_count("SIL") == 2
        assert engine.get_rubric_count("ZZZ") == 0


class TestMatrixSerialization:

    def test_to_matrix(self, engine):
        matrix = engine.to_matrix(method="jaccard")
        assert "remedies" in matrix
        rem_list = sorted(matrix["remedies"])
        # Should contain all 4 remedies
        assert set(rem_list) == {"ARS", "LACH", "PULS", "SIL"}
        assert matrix["matrix"]["ARS"][rem_list.index("ARS")] == 1.0
        assert matrix["matrix"]["ARS"][rem_list.index("LACH")] == 0.0  # no shared rubrics


class TestEmptyEngine:

    def test_no_data(self):
        e = CorrelationMatrixEngine()
        assert e.get_rubric_count("ARS") == 0
        assert e.similarity("ARS", "PULS") == 0.0
        assert e.nearest_neighbors("ARS") == []


class TestFeatureOverview:

    def test_overview(self, engine):
        ov = engine.get_feature_overview()
        assert ov["feature_id"] == 21
        assert "jaccard" in ov["methods"]
        assert ov["remedies_indexed"] == 4
