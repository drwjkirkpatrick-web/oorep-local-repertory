"""
Test Family Grouping Engine

Tests kingdom filtering, family scoring, family comparison, and taxonomy
enrichment. Uses bounded rubric counts for Jetson memory safety.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oorep.family_grouping import FamilyGroupingEngine, group_by_family
from oorep.homeopathic_repertory import HomeopathicRepertory


@pytest.fixture(scope="module")
def engine():
    return FamilyGroupingEngine()


@pytest.fixture(scope="module")
def sample_rubric_ids():
    rep = HomeopathicRepertory()
    rubrics = rep.search_rubrics("anxiety restlessness", limit=3)
    rubrics += rep.search_rubrics("thirst small quantities", limit=3)
    rubrics += rep.search_rubrics("burning pains", limit=3)
    seen = set()
    out = []
    for r in rubrics:
        rid = int(r["id"])
        if rid not in seen:
            seen.add(rid)
            out.append(rid)
    return out[:5]


# ── Construction ────────────────────────────────────────────────────────────

def test_engine_construction(engine):
    assert engine is not None
    assert engine.rep is not None
    assert engine.taxonomy is not None


# ── Kingdom filtering ─────────────────────────────────────────────────────

def test_filter_by_kingdom(engine):
    # Create dummy results with known remedies
    dummy = [
        {"abbrev": "Bell."},   # plant / Solanaceae
        {"abbrev": "Ars."},    # mineral
        {"abbrev": "Puls."},   # plant / Ranunculaceae
        {"abbrev": "Lach."},   # animal
    ]
    plants = engine.filter_by_kingdom(dummy, kingdom="plant")
    abbrevs = [r["abbrev"] for r in plants]
    assert "Bell." in abbrevs
    assert "Puls." in abbrevs
    assert "Ars." not in abbrevs
    assert "Lach." not in abbrevs


def test_filter_by_family(engine):
    dummy = [
        {"abbrev": "Bell."},   # Solanaceae
        {"abbrev": "Hyos."},  # Solanaceae
        {"abbrev": "Puls."},  # Ranunculaceae
        {"abbrev": "Ars."},   # Arsenic-series
    ]
    solanaceae = engine.filter_by_family(dummy, family="Solanaceae")
    abbrevs = [r["abbrev"] for r in solanaceae]
    assert "Bell." in abbrevs
    assert "Hyos." in abbrevs
    assert "Puls." not in abbrevs


# ── Family queries ─────────────────────────────────────────────────────────

def test_get_family_remedies(engine):
    sol = engine.get_family_remedies("Solanaceae")
    assert isinstance(sol, list)
    assert len(sol) >= 2  # Bell., Hyos. at minimum
    abbrevs = [r["abbrev"] for r in sol]
    assert "Bell." in abbrevs


def test_get_kingdom_remedies(engine):
    minerals = engine.get_kingdom_remedies("mineral")
    assert isinstance(minerals, list)
    assert len(minerals) >= 5
    assert all(r.get("kingdom") == "mineral" for r in minerals)


def test_list_all_families(engine):
    families = engine.list_all_families()
    assert isinstance(families, list)
    assert "Solanaceae" in families
    assert "Ranunculaceae" in families


def test_list_all_kingdoms(engine):
    kingdoms = engine.list_all_kingdoms()
    assert isinstance(kingdoms, list)
    assert "plant" in kingdoms
    assert "mineral" in kingdoms
    assert "animal" in kingdoms


# ── Family-level scoring ───────────────────────────────────────────────────

def test_group_by_family(engine, sample_rubric_ids):
    if len(sample_rubric_ids) < 3:
        pytest.skip("Not enough rubrics for family scoring")
    results = engine.group_by_family(rubric_ids=sample_rubric_ids, top_n=10)
    assert isinstance(results, list)
    assert len(results) > 0
    # Each result should be a FamilyScoreResult
    top = results[0]
    assert hasattr(top, "family")
    assert hasattr(top, "total_score")
    assert hasattr(top, "remedy_count")
    assert hasattr(top, "coverage_ratio")
    assert top.total_score >= 0
    assert 0.0 <= top.coverage_ratio <= 1.0


def test_group_by_family_returns_kingdom(engine, sample_rubric_ids):
    if len(sample_rubric_ids) < 3:
        pytest.skip("Not enough rubrics")
    results = engine.group_by_family(rubric_ids=sample_rubric_ids, top_n=10)
    if results:
        assert results[0].kingdom in ("plant", "mineral", "animal", "nosode", "sarcode", "imponderable")


# ── Kingdom-level scoring ─────────────────────────────────────────────────

def test_group_by_kingdom(engine, sample_rubric_ids):
    if len(sample_rubric_ids) < 3:
        pytest.skip("Not enough rubrics")
    results = engine.group_by_kingdom(rubric_ids=sample_rubric_ids, top_n=10)
    assert isinstance(results, list)
    assert len(results) > 0
    top = results[0]
    assert hasattr(top, "kingdom")
    assert hasattr(top, "total_score")
    assert hasattr(top, "families")
    assert top.total_score >= 0


# ── Family comparison ─────────────────────────────────────────────────────

def test_compare_families(engine, sample_rubric_ids):
    if len(sample_rubric_ids) < 3:
        pytest.skip("Not enough rubrics")
    comp = engine.compare_families("Solanaceae", "Ranunculaceae", rubric_ids=sample_rubric_ids)
    assert "family_a" in comp
    assert "family_b" in comp
    assert comp["family_a"] == "Solanaceae"
    assert comp["family_b"] == "Ranunculaceae"
    assert "a_total_score" in comp
    assert "b_total_score" in comp
    assert "winner" in comp
    assert comp["winner"] in ("Solanaceae", "Ranunculaceae", "tie")


# ── Kingdom comparison ────────────────────────────────────────────────────

def test_compare_kingdoms(engine, sample_rubric_ids):
    if len(sample_rubric_ids) < 3:
        pytest.skip("Not enough rubrics")
    comp = engine.compare_kingdoms("plant", "mineral", rubric_ids=sample_rubric_ids)
    assert "kingdom_a" in comp
    assert "kingdom_b" in comp
    assert comp["kingdom_a"] == "plant"
    assert comp["kingdom_b"] == "mineral"
    assert "winner" in comp
    assert comp["winner"] in ("plant", "mineral", "tie")


# ── Taxonomy enrichment ─────────────────────────────────────────────────────

def test_enrich_results_with_taxonomy(engine):
    dummy = [
        {"abbrev": "Bell.", "score": 15},
        {"abbrev": "Ars.", "score": 12},
    ]
    enriched = engine.enrich_results_with_taxonomy(dummy)
    assert len(enriched) == 2
    assert "_taxonomy" in enriched[0]
    assert enriched[0]["_taxonomy"]["kingdom"] == "plant"
    assert enriched[0]["_taxonomy"]["family"] == "Solanaceae"
    assert enriched[1]["_taxonomy"]["kingdom"] == "mineral"


def test_enrich_unknown_remedy(engine):
    dummy = [{"abbrev": "UnknownRemedy123", "score": 5}]
    enriched = engine.enrich_results_with_taxonomy(dummy)
    assert enriched[0]["_taxonomy"] is None


# ── Family summary ──────────────────────────────────────────────────────────

def test_get_family_summary(engine):
    summary = engine.get_family_summary("Solanaceae")
    assert summary["family"] == "Solanaceae"
    assert "kingdom" in summary
    assert summary["kingdom"] == "plant"
    assert summary["remedy_count"] >= 2
    assert "Bell." in [r["abbrev"] for r in summary["remedies"]]


def test_get_family_summary_not_found(engine):
    summary = engine.get_family_summary("NonexistentFamilyXYZ")
    assert "error" in summary


# ── Convenience function ────────────────────────────────────────────────────

def test_group_by_family_convenience(sample_rubric_ids):
    if len(sample_rubric_ids) < 3:
        pytest.skip("Not enough rubrics")
    results = group_by_family(rubric_ids=sample_rubric_ids, top_n=5)
    assert isinstance(results, list)
    if results:
        assert "family" in results[0]
        assert "total_score" in results[0]
        assert "remedies" in results[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
