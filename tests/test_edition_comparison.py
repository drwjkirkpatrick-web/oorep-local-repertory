"""
Tests for Comparative Repertory Edition Analysis (Feature #29)

Covers:
  - Construction and edition loading
  - Full diff: added, removed, grade_changed, unchanged rubrics
  - Remedy-level grade changes
  - Coverage report per edition
  - Drift metrics (Jaccard, weighted, consistency)
  - Remedy filtering in comparisons
  - Symmetry in drift
  - Edge cases: missing edition, empty data, self-comparison
"""

import json
import pytest
from pathlib import Path
from oorep.edition_comparison import EditionComparisonEngine


@pytest.fixture
def tmp_rubrics(tmp_path: Path):
    """Create two minimal edition JSON files with real data diffs."""
    edition = tmp_path / "edition_a.json"
    edition_b = tmp_path / "edition_b.json"

    with open(edition, "w") as f:
        json.dump([
            {
                "id": 1,
                "fullpath": "Mind; Anxiety",
                "remedies": [
                    {"remedy": "ARS", "grade": 3},
                    {"remedy": "AUR", "grade": 2},
                    {"remedy": "PULS", "grade": 1},
                ],
            },
            {
                "id": 2,
                "fullpath": "Mind; Fear; death",
                "remedies": [
                    {"remedy": "ARS", "grade": 3},
                    {"remedy": "AUR", "grade": 1},
                ],
            },
        ], f)

    with open(edition_b, "w") as f:
        json.dump([
            {
                "id": 1,
                "fullpath": "Mind; Anxiety",
                "remedies": [
                    {"remedy": "ARS", "grade": 3},
                    {"remedy": "AUR", "grade": 3},  # upgraded
                    {"remedy": "PULS", "grade": 1},
                    {"remedy": "LACH", "grade": 2},  # new
                ],
            },
            {
                "id": 2,
                "fullpath": "Mind; Fear; death",
                "remedies": [
                    {"remedy": "ARS", "grade": 2},  # downgraded
                ],
            },
            {
                "id": 3,
                "fullpath": "Head; Pain",
                "remedies": [
                    {"remedy": "BELL", "grade": 3},
                ],  # new rubric
            },
        ], f)

    return {"a": str(edition), "b": str(edition_b)}


@pytest.fixture
def shared_engine(tmp_rubrics):
    return EditionComparisonEngine({"a": tmp_rubrics["a"], "b": tmp_rubrics["b"]})


# ──────────────────────────────────────────────────────────────────────────────
# Construction & loading
# ──────────────────────────────────────────────────────────────────────────────

class TestConstruction:

    def test_load_edition(self, tmp_rubrics):
        engine = EditionComparisonEngine({"a": tmp_rubrics["a"]})
        idx = engine.load_edition("a")
        assert len(idx) == 2
        assert "1" in idx
        assert idx["1"]["path"] == "Mind; Anxiety"
        assert len(idx["1"]["remedies"]) == 3

    def test_get_rubric(self, tmp_rubrics):
        engine = EditionComparisonEngine({"a": tmp_rubrics["a"]})
        r = engine.get_rubric("a", "1")
        assert r is not None
        assert r["path"] == "Mind; Anxiety"
        assert engine.get_rubric("a", "99") is None

    def test_missing_edition_raises(self):
        engine = EditionComparisonEngine({"a": "dummy.json"})
        with pytest.raises(ValueError, match="not registered"):
            engine.load_edition("b")

    def test_caching(self, tmp_rubrics):
        engine = EditionComparisonEngine({"a": tmp_rubrics["a"]})
        idx1 = engine.load_edition("a")
        idx2 = engine.load_edition("a")
        assert idx1 is idx2  # same cached object


# ──────────────────────────────────────────────────────────────────────────────
# Compare
# ──────────────────────────────────────────────────────────────────────────────

class TestCompare:

    def test_full_diff(self, shared_engine):
        result = shared_engine.compare("a", "b")
        assert result["baseline"] == "a"
        assert result["target"] == "b"
        assert result["summary"]["added_count"] == 1      # rubric 3
        assert result["summary"]["removed_count"] == 0     # nothing lost
        assert result["summary"]["grade_changed_count"] == 2  # rubric 1 & 2
        # rubric 1 is not unchanged because AUR changed grade + LACH added
        assert result["summary"]["unchanged_count"] == 0

    def test_added_rubric_list(self, shared_engine):
        result = shared_engine.compare("a", "b")
        added = result["added"]
        assert len(added) == 1
        assert added[0]["rubric_id"] == "3"
        assert added[0]["path"] == "Head; Pain"
        assert added[0]["change_type"] == "added"

    def test_grade_changed_list(self, shared_engine):
        result = shared_engine.compare("a", "b")
        changed = result["grade_changed"]
        assert len(changed) == 2
        ids = {c["rubric_id"] for c in changed}
        assert ids == {"1", "2"}

    def test_remedy_diffs_in_rubric1(self, shared_engine):
        result = shared_engine.compare("a", "b")
        rubric1 = next((c for c in result["grade_changed"] if c["rubric_id"] == "1"), None)
        assert rubric1 is not None
        diffs = rubric1["remedy_diffs"]
        assert len(diffs) == 2  # AUR 2→3, LACH added

        aur = next((d for d in diffs if d["remedy"] == "AUR"), None)
        assert aur is not None
        assert aur["baseline_grade"] == 2
        assert aur["target_grade"] == 3
        assert aur["change"] == "grade_changed"

        lach = next((d for d in diffs if d["remedy"] == "LACH"), None)
        assert lach is not None
        assert lach["change"] == "added"

    def test_filter_remedies(self, shared_engine):
        """When filtering to ARS only, rubric 1 (ARS grade 3 in both) is UNCHANGED."""
        result = shared_engine.compare("a", "b", remedies_of_interest=["ARS"])
        # With ARS only, rubric 1 ARS=3 in both (unchanged for ARS); rubric 2 ARS=3→2 (changed)
        # So: 1 unchanged, 1 grade_changed, 1 added (rubric with no ARS is still added?)
        # Actually rubric 3 doesn't have ARS, and it's not in baseline, so it counts as added
        assert result["summary"]["added_count"] == 1
        assert result["summary"]["grade_changed_count"] == 1
        assert result["summary"]["unchanged_count"] == 1


# ──────────────────────────────────────────────────────────────────────────────
# Grade changes
# ──────────────────────────────────────────────────────────────────────────────

class TestGradeChanges:

    def test_ars_changes(self, shared_engine):
        changes = shared_engine.grade_changes("ARS", "a", "b")
        ids = {c["rubric_id"] for c in changes}
        # ARS in rubric 1: 3→3 (no change)
        # ARS in rubric 2: 3→2 (changed)
        assert ids == {"2"}
        row = next(c for c in changes if c["rubric_id"] == "2")
        assert row["baseline_grade"] == 3
        assert row["target_grade"] == 2

    def test_aur_changes(self, shared_engine):
        changes = shared_engine.grade_changes("AUR", "a", "b")
        ids = {c["rubric_id"] for c in changes}
        # AUR in rubric 1: 2→3 (changed)
        # AUR in rubric 2: 1→None (removed)
        assert "1" in ids
        row1 = next(c for c in changes if c["rubric_id"] == "1")
        assert row1["baseline_grade"] == 2
        assert row1["target_grade"] == 3

    def test_no_changes_for_unchanged_remedy(self, shared_engine):
        changes = shared_engine.grade_changes("PULS", "a", "b")
        # PULS only in rubric 1, grade 1 in both
        assert len(changes) == 0


# ──────────────────────────────────────────────────────────────────────────────
# Coverage report
# ──────────────────────────────────────────────────────────────────────────────

class TestCoverageReport:

    def test_coverage_a(self, shared_engine):
        cov = shared_engine.coverage_report("a")
        assert cov["edition"] == "a"
        assert cov["total_rubrics"] == 2
        assert cov["total_remedy_entries"] == 5  # 3 + 2
        assert cov["avg_remedies_per_rubric"] == 2.5
        assert cov["unique_remedies"] == 3  # ARS, AUR, PULS

    def test_coverage_b(self, shared_engine):
        cov = shared_engine.coverage_report("b")
        assert cov["total_rubrics"] == 3
        assert cov["total_remedy_entries"] == 6  # 4 + 1 + 1
        assert cov["avg_remedies_per_rubric"] == 2.0
        assert cov["unique_remedies"] == 5  # ARS, AUR, PULS, LACH, BELL

    def test_missing_edition(self):
        engine = EditionComparisonEngine({})
        cov = engine.coverage_report("missing")
        assert "error" in cov

    def test_grade_counts(self, shared_engine):
        cov = shared_engine.coverage_report("a")
        assert cov["max_grade3_count"] == 2  # ARS rubric 1, ARS rubric 2
        assert cov["max_grade2_count"] == 1  # AUR rubric 1
        assert cov["max_grade1_count"] == 2  # PULS rubric 1, AUR rubric 2


# ──────────────────────────────────────────────────────────────────────────────
# Drift metrics
# ──────────────────────────────────────────────────────────────────────────────

class TestDriftMetrics:

    def test_drift_actual(self, shared_engine):
        drift = shared_engine.edition_drift("a", "b")
        assert drift["baseline_edition"] == "a"
        assert drift["target_edition"] == "b"
        assert 0.0 <= drift["jaccard_similarity"] <= 1.0
        assert 0.0 <= drift["total_drift_score"] <= 1.0
        assert drift["added_rubrics"] == 1
        assert drift["removed_rubrics"] == 0

    def test_self_comparison(self, shared_engine):
        """Comparing an edition with itself should yield 0 drift."""
        drift = shared_engine.edition_drift("a", "a")
        assert drift["jaccard_similarity"] == 1.0
        assert drift["grade_consistency"] == 1.0
        assert drift["total_drift_score"] == 0.0
        assert drift["added_rubrics"] == 0
        assert drift["removed_rubrics"] == 0

    def test_symmetric_jaccard(self, shared_engine):
        forward = shared_engine.edition_drift("a", "b")
        reverse = shared_engine.edition_drift("b", "a")
        assert forward["jaccard_similarity"] == reverse["jaccard_similarity"]
        assert forward["grade_consistency"] == reverse["grade_consistency"]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

class TestRemedyGradeHelper:

    def test_remedy_grade_found(self, shared_engine):
        r = {"remedies": [{"remedy": "ARS", "grade": 3}]}
        assert EditionComparisonEngine._remedy_grade(r, "ARS") == 3

    def test_remedy_grade_none(self, shared_engine):
        r = {"remedies": [{"remedy": "ARS", "grade": 3}]}
        assert EditionComparisonEngine._remedy_grade(r, "PULS") is None


# ──────────────────────────────────────────────────────────────────────────────
# Feature overview
# ──────────────────────────────────────────────────────────────────────────────

class TestFeatureOverview:

    def test_overview(self):
        engine = EditionComparisonEngine({})
        overview = engine.get_feature_overview()
        assert overview["feature_id"] == 29
        assert "Comparative" in overview["feature_name"]
        assert overview["cold_start_capable"] is True
