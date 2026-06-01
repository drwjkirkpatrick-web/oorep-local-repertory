"""Tests for cycle/segment enrichment inside repertorize() – Benefit #59 extension.

Validates that HomeopathicRepertory.repertorize() adds ``cycle_analysis`` keys
to each result when ``with_cycles=True``, and that the Herscu-method thresholds
(min_segments_matched, min_coverage) are respected.
"""

import json
from pathlib import Path

import pytest


def _write_minimal_dataset(tmp_path: Path):
    """Create a tiny two-remedy repertory dataset with cycle-compatible abbreviations."""
    (tmp_path / "remedies.json").write_text(
        json.dumps([
            {"id": 1, "abbrev": "Stram.", "name": "Stramonium"},
            {"id": 2, "abbrev": "Puls.", "name": "Pulsatilla"},
        ]),
        encoding="utf-8",
    )

    (tmp_path / "remedies_by_abbrev.json").write_text(
        json.dumps({
            "Stram.": {"id": 1, "abbrev": "Stram.", "name": "Stramonium"},
            "Puls.": {"id": 2, "abbrev": "Puls.", "name": "Pulsatilla"},
        }),
        encoding="utf-8",
    )

    rubrics = [
        {"id": 101, "source": "publicum", "fullpath": "Mind, fear, death", "path_parts": ["Mind", "fear", "death"]},
        {"id": 102, "source": "publicum", "fullpath": "Mind, violence, rage", "path_parts": ["Mind", "violence", "rage"]},
        {"id": 103, "source": "publicum", "fullpath": "Mind, wants to be alone", "path_parts": ["Mind", "wants", "alone"]},
    ]
    (tmp_path / "rubrics.json").write_text(json.dumps(rubrics), encoding="utf-8")

    search_index = {
        "fear": [101],
        "death": [101],
        "violence": [102],
        "rage": [102],
        "alone": [103],
    }
    (tmp_path / "rubric_search_index.json").write_text(json.dumps(search_index), encoding="utf-8")

    rubric_to_remedies = {
        "101": [
            {"rubric_id": 101, "remedy_id": 1, "weight": 4},
            {"rubric_id": 101, "remedy_id": 2, "weight": 1},
        ],
        "102": [
            {"rubric_id": 102, "remedy_id": 1, "weight": 3},
        ],
        "103": [
            {"rubric_id": 103, "remedy_id": 1, "weight": 2},
        ],
    }
    (tmp_path / "rubric_to_remedies.json").write_text(json.dumps(rubric_to_remedies), encoding="utf-8")


def test_repertorize_adds_cycle_analysis(tmp_path):
    """When with_cycles=True, every remedy result gains a cycle_analysis dict."""
    from oorep.homeopathic_repertory import HomeopathicRepertory

    _write_minimal_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))

    results = rep.repertorize(
        ["fear death", "violence rage", "wants alone"],
        top_n=2,
        retrieval="lexical",
        rubrics_per_symptom=3,
        with_cycles=True,
    )

    assert len(results) == 2
    for r in results:
        assert "cycle_analysis" in r
        ca = r["cycle_analysis"]
        assert "remedy_cycle" in ca
        assert "segment_matches" in ca
        assert "segments_matched_count" in ca
        assert "total_segments" in ca
        assert "coverage" in ca
        assert "meets_threshold" in ca
        assert isinstance(ca["meets_threshold"], bool)


def test_repertorize_stramonium_meets_threshold(tmp_path):
    """Stramonium should match ≥2 segments with these case symptoms and meet threshold."""
    from oorep.homeopathic_repertory import HomeopathicRepertory

    _write_minimal_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))

    results = rep.repertorize(
        ["fear death", "violence rage", "wants alone"],
        top_n=2,
        retrieval="lexical",
        rubrics_per_symptom=3,
        with_cycles=True,
        cycle_min_segments=2,
        cycle_min_coverage=0.25,
    )

    stram = [r for r in results if r["abbrev"] == "Stram."][0]
    assert stram["cycle_analysis"]["remedy_cycle"] == "Stramonium"
    assert stram["cycle_analysis"]["meets_threshold"] is True
    assert stram["cycle_analysis"]["segments_matched_count"] >= 2
    assert stram["cycle_analysis"]["segment_coverage"] >= 0.20
    assert stram["cycle_analysis"]["segment_coverage"] < 1.0


def test_repertorize_pulsatilla_no_verified_cycle_meets_threshold(tmp_path):
    """Pulsatilla has an auto-derived cycle but should not meet threshold on this case."""
    from oorep.homeopathic_repertory import HomeopathicRepertory

    _write_minimal_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))

    results = rep.repertorize(
        ["fear death", "violence rage"],
        top_n=2,
        retrieval="lexical",
        rubrics_per_symptom=3,
        with_cycles=True,
    )

    puls = [r for r in results if r["abbrev"] == "Puls."][0]
    # Pulsatilla Pratensis auto-derived cycle won't match "fear death" / "violence rage"
    assert puls["cycle_analysis"]["meets_threshold"] is False
    assert puls["cycle_analysis"]["segments_matched_count"] == 0


def test_repertorize_with_cycles_false_skips_enrichment(tmp_path):
    """When with_cycles=False, cycle_analysis should be absent."""
    from oorep.homeopathic_repertory import HomeopathicRepertory

    _write_minimal_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))

    results = rep.repertorize(
        ["fear death"],
        top_n=1,
        retrieval="lexical",
        with_cycles=False,
    )

    assert "cycle_analysis" not in results[0]


def test_repertorize_high_threshold_can_fail(tmp_path):
    """With an extremely high threshold, even Stramonium should not meet it."""
    from oorep.homeopathic_repertory import HomeopathicRepertory

    _write_minimal_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))

    results = rep.repertorize(
        ["fear death"],
        top_n=2,
        retrieval="lexical",
        rubrics_per_symptom=3,
        with_cycles=True,
        cycle_min_segments=10,
        cycle_min_coverage=0.99,
    )

    stram = [r for r in results if r["abbrev"] == "Stram."][0]
    assert stram["cycle_analysis"]["meets_threshold"] is False
