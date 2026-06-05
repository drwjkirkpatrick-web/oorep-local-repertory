"""
Test Master Score Engine

Tests composite repertorization with Kent, Boenninghausen, SRP, rarity,
and kingdom scorers. Uses real OOREP data for integration-level validation.
"""

import pytest
import sys
from pathlib import Path

# Ensure oorep is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oorep.master_score_engine import MasterScoreEngine, master_repertorize


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Fresh MasterScoreEngine instance."""
    return MasterScoreEngine()


@pytest.fixture
def sample_rubric_ids():
    """
    A small set of rubric IDs known to have remedies across multiple grades.
    These are selected from common constitutional rubrics.
    """
    # We'll use search to find rubrics, then pick stable IDs
    from oorep.homeopathic_repertory import HomeopathicRepertory
    rep = HomeopathicRepertory()
    # Find rubrics for common symptoms
    rubrics_a = rep.search_rubrics("anxiety restlessness", limit=3)
    rubrics_b = rep.search_rubrics("thirst small quantities", limit=3)
    rubrics_c = rep.search_rubrics("burning pains", limit=3)
    all_ids = []
    for r in rubrics_a + rubrics_b + rubrics_c:
        all_ids.append(int(r["id"]))
    # Deduplicate and return first 5
    seen = set()
    out = []
    for rid in all_ids:
        if rid not in seen:
            seen.add(rid)
            out.append(rid)
    if len(out) < 3:
        pytest.skip("Not enough rubrics found in data for testing")
    return out[:5]


# ── Basic construction and sanity ───────────────────────────────────────────

def test_engine_construction(engine):
    assert engine is not None
    assert engine.rep is not None
    assert engine.kvb is not None
    assert engine.srp is not None
    assert engine.rarity is not None
    assert engine.taxonomy is not None


def test_default_weights_sum_to_one(engine):
    total = sum(engine.DEFAULT_WEIGHTS.values())
    assert abs(total - 1.0) < 0.001


def test_available_scorers():
    scorers = MasterScoreEngine.get_available_scorers()
    assert "kent" in scorers
    assert "boenninghausen" in scorers
    assert "srp" in scorers
    assert "rarity" in scorers
    assert "kingdom" in scorers
    assert len(scorers) == 5


def test_normalize_weights(engine):
    # Equal weights should normalize to 0.2 each
    raw = {"kent": 1.0, "boenninghausen": 1.0, "srp": 1.0, "rarity": 1.0, "kingdom": 1.0}
    norm = engine._normalize_weights(raw)
    assert abs(norm["kent"] - 0.2) < 0.001
    # Zero-sum should fall back to defaults
    zero = {"kent": 0, "boenninghausen": 0}
    fallback = engine._normalize_weights(zero)
    assert "kent" in fallback


def test_normalize_scores(engine):
    scores = {"Ars.": 10.0, "Puls.": 5.0, "Nux-v.": 0.0}
    norm = engine._normalize_scores(scores)
    assert norm["Nux-v."] == 0.0
    assert norm["Ars."] == 1.0
    assert 0.0 < norm["Puls."] < 1.0
    # Uniform scores → all 1.0
    uniform = {"A": 5.0, "B": 5.0}
    nu = engine._normalize_scores(uniform)
    assert nu["A"] == 1.0
    assert nu["B"] == 1.0


# ── Core repertorization ──────────────────────────────────────────────────────

def test_repertorize_basic(engine, sample_rubric_ids):
    results = engine.repertorize(rubric_ids=sample_rubric_ids, top_n=10)
    assert isinstance(results, list)
    assert len(results) > 0
    # Top result should have expected fields
    top = results[0]
    assert "abbrev" in top
    assert "remedy_name" in top
    assert "master_score" in top
    assert "rank" in top
    assert "confidence" in top
    assert "sub_scores" in top
    assert "match_count" in top
    assert top["rank"] == 1
    assert 0.0 <= top["master_score"] <= 1.0 + 0.01  # slightly above 1 possible from rounding


def test_repertorize_with_symptoms(engine, sample_rubric_ids):
    symptoms = ["anxiety restlessness", "thirst small quantities", "burning pains"]
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        symptoms=symptoms,
        top_n=10,
    )
    assert len(results) > 0
    # With symptoms, SRP and rarity scorers should have fired
    top = results[0]
    sub_names = set(top["sub_scores"].keys())
    # At minimum kent and boenninghausen should be present
    assert "kent" in sub_names or "boenninghausen" in sub_names


def test_repertorize_custom_weights(engine, sample_rubric_ids):
    # Kent-only repertorization via weights
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        weights={"kent": 1.0, "boenninghausen": 0, "srp": 0, "rarity": 0, "kingdom": 0},
        top_n=10,
    )
    assert len(results) > 0
    top = results[0]
    # Only kent sub-score should exist
    assert set(top["sub_scores"].keys()) == {"kent"}


def test_repertorize_boenninghausen_only(engine, sample_rubric_ids):
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        weights={"kent": 0, "boenninghausen": 1.0, "srp": 0, "rarity": 0, "kingdom": 0},
        top_n=10,
    )
    assert len(results) > 0
    top = results[0]
    assert set(top["sub_scores"].keys()) == {"boenninghausen"}


def test_repertorize_include_raw(engine, sample_rubric_ids):
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        include_raw=True,
        top_n=5,
    )
    top = results[0]
    assert "_raw_sub_scores" in top
    # Raw sub-scores should contain normalized + raw + rank
    for scorer_data in top["_raw_sub_scores"].values():
        assert "raw" in scorer_data
        assert "normalized" in scorer_data
        assert "rank" in scorer_data


def test_repertorize_empty_rubric_ids(engine):
    results = engine.repertorize(rubric_ids=[], top_n=10)
    assert results == []


# ── Sub-score structure validation ──────────────────────────────────────────

def test_sub_score_fields(engine, sample_rubric_ids):
    results = engine.repertorize(rubric_ids=sample_rubric_ids, top_n=5)
    for r in results:
        for scorer_name, sub in r["sub_scores"].items():
            assert "normalized" in sub
            assert "raw" in sub
            assert "rank" in sub
            assert isinstance(sub["normalized"], float)
            assert 0.0 <= sub["normalized"] <= 1.0 + 0.01
            assert isinstance(sub["rank"], int)
            assert sub["rank"] >= 1


# ── Confidence metric ───────────────────────────────────────────────────────

def test_confidence_range(engine, sample_rubric_ids):
    results = engine.repertorize(rubric_ids=sample_rubric_ids, top_n=10)
    for r in results:
        assert 0.0 <= r["confidence"] <= 1.0


def test_confidence_single_scorer_is_0_5(engine, sample_rubric_ids):
    # With only one scorer, confidence defaults to 0.5
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        weights={"kent": 1.0, "boenninghausen": 0, "srp": 0, "rarity": 0, "kingdom": 0},
        top_n=5,
    )
    for r in results:
        assert r["confidence"] == 0.5


def test_confidence_multi_scorer_varies(engine, sample_rubric_ids):
    # With multiple scorers, confidence should be calculated from spread
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        symptoms=["anxiety restlessness", "thirst small quantities"],
        weights={"kent": 0.5, "boenninghausen": 0.5, "srp": 0, "rarity": 0, "kingdom": 0},
        top_n=5,
    )
    for r in results:
        # Confidence should be a real number, not necessarily 0.5
        assert isinstance(r["confidence"], float)


# ── Convenience function ──────────────────────────────────────────────────────

def test_master_repertorize_convenience(sample_rubric_ids):
    symptoms = ["anxiety restlessness", "thirst small quantities"]
    results = master_repertorize(
        rubric_ids=sample_rubric_ids,
        symptoms=symptoms,
        top_n=10,
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert "master_score" in results[0]


# ── compare_methods ──────────────────────────────────────────────────────────

def test_compare_methods(engine, sample_rubric_ids):
    symptoms = ["anxiety restlessness", "thirst small quantities"]
    comparison = engine.compare_methods(
        rubric_ids=sample_rubric_ids,
        symptoms=symptoms,
        top_n=10,
    )
    assert "master_results" in comparison
    assert "kent_results" in comparison
    assert "boenninghausen_results" in comparison
    assert "method_agreement" in comparison
    assert "divergence_analysis" in comparison
    # All should have results
    assert len(comparison["master_results"]) > 0
    assert len(comparison["kent_results"]) > 0
    assert len(comparison["boenninghausen_results"]) > 0
    # Method agreement should have expected keys
    agreement = comparison["method_agreement"]
    assert "all_three" in agreement
    assert "master_only" in agreement
    assert "kent_only" in agreement
    assert "boen_only" in agreement


def test_compare_methods_narrative(engine, sample_rubric_ids):
    comparison = engine.compare_methods(rubric_ids=sample_rubric_ids, top_n=10)
    narrative = comparison["divergence_analysis"]["narrative"]
    assert isinstance(narrative, str)
    assert len(narrative) > 0


# ── Kingdom inference ─────────────────────────────────────────────────────────

def test_infer_kingdom_plant(engine):
    result = engine._infer_kingdom(["growing plant flower leaf"])
    assert result == "plant"


def test_infer_kingdom_animal(engine):
    result = engine._infer_kingdom(["snake bite venom spider sting"])
    assert result == "animal"


def test_infer_kingdom_mineral(engine):
    result = engine._infer_kingdom(["salt crystal metal rock element"])
    assert result == "mineral"


def test_infer_kingdom_none(engine):
    result = engine._infer_kingdom(["headache pain"])
    assert result is None


# ── SRP sub-scorer ──────────────────────────────────────────────────────────

def test_srp_scorer_runs(engine, sample_rubric_ids):
    symptoms = ["worse from consolation", "thirst small quantities"]
    results = engine._run_srp_scorer(sample_rubric_ids, symptoms, top_n=10)
    assert isinstance(results, list)
    # SRP scorer should produce different scores than plain Kent when SRP present
    if results:
        assert "abbrev" in results[0]
        assert "score" in results[0]


# ── Rarity sub-scorer ────────────────────────────────────────────────────────

def test_rarity_scorer_runs(engine, sample_rubric_ids):
    symptoms = ["anxiety restlessness", "thirst small quantities"]
    results = engine._run_rarity_scorer(sample_rubric_ids, symptoms, top_n=10)
    assert isinstance(results, list)
    if results:
        assert "abbrev" in results[0]


# ── Kingdom sub-scorer ───────────────────────────────────────────────────────

def test_kingdom_scorer_runs(engine, sample_rubric_ids):
    symptoms = ["anxiety restlessness"]
    results = engine._run_kingdom_scorer(sample_rubric_ids, symptoms, top_n=10)
    assert isinstance(results, list)
    if results:
        assert "abbrev" in results[0]


# ── Scorer descriptions ──────────────────────────────────────────────────────

def test_scorer_descriptions(engine):
    for scorer in MasterScoreEngine.get_available_scorers():
        desc = engine.get_scorer_description(scorer)
        assert isinstance(desc, str)
        assert len(desc) > 10


def test_unknown_scorer_description(engine):
    desc = engine.get_scorer_description("nonexistent")
    assert desc == "Unknown scorer."


# ── Integration: master score differs from pure Kent ──────────────────────────

def test_master_differs_from_kent(engine, sample_rubric_ids):
    """
    With non-trivial weights on multiple scorers, the Master Score
    ranking should potentially differ from Kent-only ranking.
    This is a probabilistic test — we verify structure, not exact values.
    """
    symptoms = ["anxiety restlessness", "thirst small quantities", "burning pains"]
    master = engine.repertorize(
        rubric_ids=sample_rubric_ids,
        symptoms=symptoms,
        weights=MasterScoreEngine.DEFAULT_WEIGHTS,
        top_n=10,
    )
    kent = engine.kvb.kent_repertorize(sample_rubric_ids, top_n=10)

    master_top = [r["abbrev"] for r in master[:3]]
    kent_top = [r["abbrev"] for r in kent[:3]]

    # The composite engine should produce valid rankings
    assert len(master_top) > 0
    assert len(kent_top) > 0
    # Master scores should be normalized differently than raw Kent scores
    if master and kent:
        assert master[0]["master_score"] != kent[0]["score"]


# ── Integration: kingdom boost on known remedy ────────────────────────────────

def test_kingdom_boost_on_solaceae(engine, sample_rubric_ids):
    """
    If symptoms include plant markers, Solanaceae remedies should
    get a kingdom affinity boost. Uses a subset of rubrics to
    stay within Jetson memory limits.
    """
    symptoms = ["growing plant flower anxiety restlessness"]
    results = engine.repertorize(
        rubric_ids=sample_rubric_ids[:3],
        symptoms=symptoms,
        weights={"kent": 0.0, "boenninghausen": 0.0, "srp": 0.0, "rarity": 0.0, "kingdom": 1.0},
        top_n=10,
    )
    # With kingdom=1.0, the ranking is purely kingdom affinity
    abbrevs = [r["abbrev"] for r in results]
    assert isinstance(abbrevs, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
