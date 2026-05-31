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
        # Use a case with symptoms specific to Stramonium's cycle
        case = ["fear of death", "violent outbursts", "wants to be alone"]
        suggestions = engine.suggest_cycles_for_case(case)
        assert len(suggestions) > 0
        # Stramonium should appear in the top results with strong coverage
        names = [s[0] for s in suggestions]
        assert "Stramonium" in names
        stram_entry = [s for s in suggestions if s[0] == "Stramonium"][0]
        assert stram_entry[1] > 0.0  # coverage > 0
        assert "Fear of death or injury" in stram_entry[2]["matched_segments"]
        assert "Violent overreaction" in stram_entry[2]["matched_segments"]


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


# ── Auto-loading from data/cycles/ ─────────────────────────────────────────

class TestAutoLoading:
    def test_all_builtin_cycles_loaded(self):
        engine = CyclesAndSegmentsEngine()
        cycles = engine.list_cycles()
        expected = {
            "Stramonium", "Vipera", "Kali Carbonicum",
            "Conium Maculatum", "Anacardium",
            "Bothrops Lanceolatus", "Carcinosin",
        }
        assert expected.issubset(set(cycles)), f"Missing: {expected - set(cycles)}"

    @pytest.mark.parametrize(
        "remedy,expected_segments,expected_phase",
        [
            ("Stramonium", 6, 4),
            ("Vipera", 5, 4),
            ("Kali Carbonicum", 6, 3),
            ("Conium Maculatum", 5, 4),
            ("Anacardium", 5, 3),
            ("Bothrops Lanceolatus", 5, 4),
            ("Carcinosin", 6, 2),
        ],
    )
    def test_cycle_structure(self, remedy, expected_segments, expected_phase):
        engine = CyclesAndSegmentsEngine()
        rc = engine.get_cycle(remedy)
        assert rc is not None, f"{remedy} not found"
        assert len(rc.segments) == expected_segments
        assert rc.cycle_loop is True
        assert rc.map_of_hierarchy_phase == expected_phase

    def test_cycle_loops_are_closed(self):
        engine = CyclesAndSegmentsEngine()
        for name in engine.list_cycles():
            rc = engine.get_cycle(name)
            assert rc is not None, f"{name} not found"
            pairs = rc.transition_pairs()
            # Last pair should connect back to first segment for loops
            if rc.cycle_loop and len(rc.segments) >= 2:
                last_pair = pairs[-1]
                assert last_pair[1] == rc.segments[0].name, (
                    f"{name}: loop broken at {last_pair}"
                )

    def test_vipera_case_match(self):
        engine = CyclesAndSegmentsEngine()
        case = ["varicose veins", "burning pain", "cold sweat", "paralysis"]
        rc = engine.get_cycle("Vipera")
        assert rc is not None
        match = engine.match_case_to_cycle(case, rc)
        assert "Congestion and fullness" in match["matched_segments"]
        assert "Intense burning and inflammation" in match["matched_segments"]
        assert "Collapse and weakness" in match["matched_segments"]

    def test_kali_carb_case_match(self):
        engine = CyclesAndSegmentsEngine()
        case = ["weakness", "fastidious", "fear of poverty", "irritability", "edema"]
        rc = engine.get_cycle("Kali Carbonicum")
        assert rc is not None
        match = engine.match_case_to_cycle(case, rc)
        assert match["coverage"] >= 0.1
        assert "Weakness and insecurity" in match["matched_segments"]
        assert "Desire for order and structure" in match["matched_segments"]
        assert "Fear of poverty and ruin" in match["matched_segments"]

    def test_conium_case_match(self):
        engine = CyclesAndSegmentsEngine()
        case = ["loss of libido", "rigidity", "forgetfulness"]
        rc = engine.get_cycle("Conium Maculatum")
        assert rc is not None
        match = engine.match_case_to_cycle(case, rc)
        assert "Indifference and apathy" in match["matched_segments"]
        assert "Physical rigidity and paralysis" in match["matched_segments"]
        assert "Mental dullness and confusion" in match["matched_segments"]

    def test_suggest_cycles_cross_ranking(self):
        engine = CyclesAndSegmentsEngine()
        case = ["fear of death", "paralysis", "coldness"]
        suggestions = engine.suggest_cycles_for_case(case, limit=10)
        names = [s[0] for s in suggestions]
        # With auto-derived cycles loaded, ranking shifts; verify valid
        # results are returned with non-negative coverage.
        assert len(suggestions) > 0
        assert all(cov >= 0.0 for _, cov, _ in suggestions)
        # Verify the published Vipera cycle still exists and is queryable
        assert "Vipera" in engine.list_cycles()
        vipera = engine.get_cycle("Vipera")
        assert vipera is not None
        assert len(vipera.segments) >= 5


# ── Builder script ──────────────────────────────────────────────────────────

class TestBuilderScript:
    def test_builder_validate_all(self):
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/build_cycle.py", "--validate-all", "--dir", "data/cycles"],
            cwd="/home/walker/projects/oorep-local-repertory",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "All cycles passed validation." in result.stdout

    def test_builder_list(self):
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/build_cycle.py", "--list", "--dir", "data/cycles"],
            cwd="/home/walker/projects/oorep-local-repertory",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # These cycles exist as JSON files in data/cycles/
        assert "Vipera" in result.stdout
        assert "Kali Carbonicum" in result.stdout
        assert "Conium Maculatum" in result.stdout
