"""Tests for cycles_and_segments.py — Benefit: Cycles & Segments analysis.

Validates the Herscu method implementation: data model, Stramonium cycle,
case-to-cycle matching, generalization, and hierarchy lookup.
"""

import json
from pathlib import Path

import pytest

from oorep.cycles_and_segments import (
    CycleSegment,
    RemedyCycle,
    CyclesAndSegmentsEngine,
)


# ── Data-model unit tests ────────────────────────────────────────────────────

class TestCycleSegment:
    def test_segment_defaults(self):
        seg = CycleSegment(name="Fear")
        assert seg.name == "Fear"
        assert seg.description == ""
        assert seg.symptoms == []
        assert seg.generalizations == []
        assert seg.next_segment is None

    def test_segment_full(self):
        seg = CycleSegment(
            name="Rage",
            description="Explosive anger",
            symptoms=["striking", "biting"],
            generalizations=["violence"],
            next_segment="Withdrawal",
        )
        assert seg.next_segment == "Withdrawal"
        assert seg.symptoms == ["striking", "biting"]


class TestRemedyCycle:
    def test_stramonium_cycle_structure(self):
        rc = RemedyCycle(
            remedy_name="Stramonium",
            remedy_abbrev="Stram.",
            sentence="Test sentence.",
            segments=[
                CycleSegment(name="A", next_segment="B"),
                CycleSegment(name="B", next_segment="A"),
            ],
            cycle_loop=True,
        )
        assert rc.remedy_name == "Stramonium"
        assert len(rc.segments) == 2
        assert rc.cycle_loop is True

    def test_transition_pairs_loop(self):
        rc = RemedyCycle(
            remedy_name="X",
            remedy_abbrev="X.",
            sentence="s",
            segments=[
                CycleSegment(name="A", next_segment="B"),
                CycleSegment(name="B", next_segment="C"),
                CycleSegment(name="C"),  # no explicit next; loop closes it
            ],
            cycle_loop=True,
        )
        pairs = rc.transition_pairs()
        assert pairs == [("A", "B"), ("B", "C"), ("C", "A")]

    def test_transition_pairs_no_loop(self):
        rc = RemedyCycle(
            remedy_name="X",
            remedy_abbrev="X.",
            sentence="s",
            segments=[
                CycleSegment(name="A", next_segment="B"),
                CycleSegment(name="B"),
            ],
            cycle_loop=False,
        )
        assert rc.transition_pairs() == [("A", "B")]

    def test_segment_by_name(self):
        rc = RemedyCycle(
            remedy_name="X",
            remedy_abbrev="X.",
            sentence="s",
            segments=[CycleSegment(name="Alpha"), CycleSegment(name="Beta")],
        )
        assert rc.segment_by_name("Alpha") is not None
        assert rc.segment_by_name("alpha") is not None  # case-insensitive
        assert rc.segment_by_name("Gamma") is None

    def test_all_symptoms(self):
        rc = RemedyCycle(
            remedy_name="X",
            remedy_abbrev="X.",
            sentence="s",
            segments=[
                CycleSegment(name="A", symptoms=["x", "y"]),
                CycleSegment(name="B", symptoms=["z"]),
            ],
        )
        assert rc.all_symptoms() == ["x", "y", "z"]

    def test_serialize_roundtrip(self):
        rc = RemedyCycle(
            remedy_name="Stramonium",
            remedy_abbrev="Stram.",
            sentence="Driven by confusion...",
            segments=[
                CycleSegment(
                    name="Fear",
                    symptoms=["fear of death"],
                    next_segment="Rage",
                ),
                CycleSegment(name="Rage", next_segment="Fear"),
            ],
            cycle_loop=True,
            map_of_hierarchy_phase=4,
            references=["Herscu (1996)"],
        )
        d = rc.to_dict()
        rc2 = RemedyCycle.from_dict(d)
        assert rc2.remedy_name == rc.remedy_name
        assert rc2.cycle_loop == rc.cycle_loop
        assert rc2.map_of_hierarchy_phase == 4
        assert len(rc2.segments) == 2
        assert rc2.segments[0].next_segment == "Rage"


# ── Engine tests ─────────────────────────────────────────────────────────────

class TestEngineBasics:
    def test_stramonium_builtin(self):
        engine = CyclesAndSegmentsEngine()
        assert "Stramonium" in engine.list_cycles()

    def test_get_cycle_by_name(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        assert rc is not None
        assert rc.remedy_name == "Stramonium"

    def test_get_cycle_by_abbrev(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stram.")
        assert rc is not None
        assert rc.remedy_name == "Stramonium"

    def test_get_cycle_case_insensitive(self):
        engine = CyclesAndSegmentsEngine()
        assert engine.get_cycle("stramonium") is not None
        assert engine.get_cycle("STRAM") is not None

    def test_get_cycle_unknown_returns_none(self):
        engine = CyclesAndSegmentsEngine()
        assert engine.get_cycle("UnknownRemedy") is None

    def test_stramonium_segment_count(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        assert len(rc.segments) == 6

    def test_stramonium_cycle_is_loop(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        assert rc.cycle_loop is True
        pairs = rc.transition_pairs()
        assert len(pairs) == 6
        # Verify it loops back to start
        assert pairs[-1][1] == rc.segments[0].name

    def test_stramonium_one_sentence(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        assert "confusion" in rc.sentence.lower()
        assert "battle" in rc.sentence.lower()

    def test_stramonium_references_present(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        assert any("Herscu" in ref for ref in rc.references)
        assert any("Stramonium" in ref for ref in rc.references)

    def test_map_of_hierarchy(self):
        engine = CyclesAndSegmentsEngine()
        h = engine.get_map_of_hierarchy()
        assert 4 in h
        assert "Stramonium" in h[4]


class TestCaseMatching:
    def test_empty_case(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        match = engine.match_case_to_cycle([], rc)
        assert match["coverage"] == 0.0
        assert match["matched_segments"] == []
        assert len(match["missing_segments"]) == len(rc.segments)

    def test_exact_symptom_match(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        case = ["fear of death"]
        match = engine.match_case_to_cycle(case, rc)
        assert "Fear of death or injury" in match["matched_segments"]
        assert match["coverage"] > 0.0

    def test_multi_symptom_match(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        case = ["fear of death", "violent outbursts", "wants to be alone"]
        match = engine.match_case_to_cycle(case, rc)
        assert "Fear of death or injury" in match["matched_segments"]
        assert "Violent overreaction" in match["matched_segments"]
        assert "Desire to close off / shut down" in match["matched_segments"]

    def test_generalization_match(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        # 'terror' is a generalization of the Fear segment
        case = ["terror"]
        match = engine.match_case_to_cycle(case, rc, generalize=True)
        assert "Fear of death or injury" in match["matched_segments"]
        assert "terror" in match["generalized_hits"]

    def test_suggest_cycles(self):
        engine = CyclesAndSegmentsEngine()
        case = ["fear of death", "violent outbursts"]
        suggestions = engine.suggest_cycles_for_case(case)
        assert len(suggestions) > 0
        name, coverage, _ = suggestions[0]
        assert name == "Stramonium"
        assert coverage > 0.0


class TestGeneralization:
    def test_generalize_known_symptom(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        seg = rc.segment_by_name("Fear of death or injury")
        gen = engine.generalize_symptom("fear of death", seg)
        assert gen == "fear"

    def test_generalize_unknown_symptom(self):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle("Stramonium")
        seg = rc.segment_by_name("Fear of death or injury")
        gen = engine.generalize_symptom("some random symptom", seg)
        assert gen is None


# ── Persistence / I/O tests ─────────────────────────────────────────────────

class TestIO:
    def test_export_import_json(self, tmp_path: Path):
        engine = CyclesAndSegmentsEngine()
        out_path = tmp_path / "cycles.json"
        engine.export_cycles_json(str(out_path))

        assert out_path.exists()
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert any(item["remedy_name"] == "Stramonium" for item in data)

    def test_load_from_json_file(self, tmp_path: Path):
        payload = [
            {
                "remedy_name": "TestRemedy",
                "remedy_abbrev": "Test.",
                "sentence": "A test remedy.",
                "segments": [
                    {
                        "name": "SegmentA",
                        "symptoms": ["symptom one"],
                        "next_segment": "SegmentB",
                    },
                    {
                        "name": "SegmentB",
                        "symptoms": ["symptom two"],
                    },
                ],
                "cycle_loop": True,
            }
        ]
        path = tmp_path / "extra.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        engine = CyclesAndSegmentsEngine(str(path))
        assert "TestRemedy" in engine.list_cycles()
        rc = engine.get_cycle("TestRemedy")
        assert rc.sentence == "A test remedy."
        assert len(rc.segments) == 2

    def test_load_from_json_dir(self, tmp_path: Path):
        payload = [
            {
                "remedy_name": "DirRemedy",
                "remedy_abbrev": "Dir.",
                "sentence": "From a directory.",
                "segments": [{"name": "Only", "symptoms": ["s"]}],
                "cycle_loop": False,
            }
        ]
        path = tmp_path / "dir_cycles.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        engine = CyclesAndSegmentsEngine(str(tmp_path))
        assert "DirRemedy" in engine.list_cycles()


# ── Regression: __init__ integration ─────────────────────────────────────────

class TestPackageIntegration:
    def test_import_from_package(self):
        from oorep import CyclesAndSegmentsEngine, RemedyCycle, CycleSegment
        assert CyclesAndSegmentsEngine is not None
        assert RemedyCycle is not None
        assert CycleSegment is not None
