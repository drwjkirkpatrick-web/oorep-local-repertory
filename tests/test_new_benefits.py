"""
Tests for new OOREP modules (Phase 1+2 benefits).

Run with pytest from repo root:
    pytest tests/test_new_benefits.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# 1. REMEDY COMPARATOR (Benefit #3)
# ═══════════════════════════════════════════════════════════════════
from oorep.remedy_comparator import RemedyComparator


class FakeRepertory:
    """Minimal fake for comparator tests."""
    rubric_to_remedies = {
        1: [{"abbrev": "Puls.", "weight": 3}, {"abbrev": "Nux-v.", "weight": 2}],
        2: [{"abbrev": "Puls.", "weight": 1}, {"abbrev": "Ars.", "weight": 3}],
        3: [{"abbrev": "Nux-v.", "weight": 2}],
    }
    rubrics = {
        1: {"fullpath": "Mind; Anxiety", "source": "kent-de"},
        2: {"fullpath": "Head; Pain", "source": "kent-de"},
        3: {"fullpath": "Stomach; Nausea", "source": "kent-de"},
    }

    def get_remedy_by_abbrev(self, abbrev):
        # Simple exact match
        for links in self.rubric_to_remedies.values():
            for l in links:
                if l["abbrev"] == abbrev:
                    return {"abbrev": abbrev, "name": abbrev}
        # Also accept dotless forms by adding dot
        if not abbrev.endswith("."):
            return self.get_remedy_by_abbrev(abbrev + ".")
        return None

    def search_remedies(self, query, limit=1):
        # Fuzzy fallback: just return the query if matched
        r = self.get_remedy_by_abbrev(query)
        if r:
            return [r]
        return []

    def get_rubric_by_id(self, rid):
        return self.rubrics.get(rid)

    def get_remedies_for_rubric(self, rid):
        return self.rubric_to_remedies.get(rid, [])


def test_comparator_init():
    comp = RemedyComparator(repertory=FakeRepertory())
    assert "Puls." in comp._remedy_rubric_index
    assert comp._remedy_rubric_index["Puls."][1] == 3


def test_comparator_overlap():
    comp = RemedyComparator(repertory=FakeRepertory())
    result = comp.compare_remedies(["Puls.", "Nux-v."])
    assert result.remedies == ["Puls.", "Nux-v."]
    assert len(result.overlap_rubrics) == 1  # rubric 1 shared
    assert result.overlap_rubrics[0]["rubric_id"] == 1


def test_comparator_exclusive():
    comp = RemedyComparator(repertory=FakeRepertory())
    result = comp.compare_remedies(["Puls.", "Nux-v."])
    # Puls. exclusive: rubric 2
    assert "Puls." in result.exclusive_rubrics
    assert any(r["rubric_id"] == 2 for r in result.exclusive_rubrics["Puls."])
    # Nux-v. exclusive: rubric 3
    assert any(r["rubric_id"] == 3 for r in result.exclusive_rubrics["Nux-v."])


def test_comparator_jaccard():
    comp = RemedyComparator(repertory=FakeRepertory())
    result = comp.compare_remedies(["Puls.", "Nux-v."])
    # Shared = {1}, union = {1,2,3} -> jaccard = 1/3
    assert result.similarity_matrix["Puls."]["Nux-v."] == round(1 / 3, 3)


def test_comparator_pairwise():
    comp = RemedyComparator(repertory=FakeRepertory())
    result = comp.compare_remedies(["Puls.", "Ars."])
    # Shared: rubric 2 (both present, Puls weight 1, Ars weight 3)
    pw = result.pairwise_divergence[0]
    assert pw["remedy_a"] == "Puls."
    assert pw["remedy_b"] == "Ars."
    assert pw["b_advantage_count"] == 1
    assert pw["a_advantage_count"] == 0


# ═══════════════════════════════════════════════════════════════════
# 2. SRP DETECTOR (Benefit #13)
# ═══════════════════════════════════════════════════════════════════
from oorep.srp_detector import SRPDetector, SRPResult


def test_srp_paradoxical():
    detector = SRPDetector()
    r = detector.analyze_symptom("worse from consolation")
    assert r.is_srp is True
    assert r.srp_type == "modality"
    assert r.boost >= 2.0


def test_srp_strange_sensation():
    detector = SRPDetector()
    r = detector.analyze_symptom("sensation as if body is floating")
    assert r.is_srp is True
    assert "as if" in r.matched_keywords


def test_srp_no_markers():
    detector = SRPDetector()
    r = detector.analyze_symptom("slight cough in the morning")
    assert r.is_srp is False
    assert r.boost == 1.0


def test_srp_boost_case_rubrics():
    detector = SRPDetector()
    items = [
        {"symptom": "worse from consolation", "rubric_id": 1, "rubric": "Mind; Anxiety", "weight": 2},
        {"symptom": "slight cough", "rubric_id": 2, "rubric": "Cough; Dry", "weight": 2},
    ]
    boosted = detector.boost_case_rubrics(items)
    assert boosted[0]["_boosted_score"] == 5.0  # 2 * 2.5
    assert boosted[1]["_srp_boost"] == 1.0  # No SRP


def test_srp_batch():
    detector = SRPDetector()
    results = detector.analyze_symptoms([
        "worse from consolation",
        "slight cough",
    ])
    assert results[0].is_srp is True
    assert results[1].is_srp is False


# ═══════════════════════════════════════════════════════════════════
# 3. PHANTOM RUBRIC ANALYZER (Benefit #27)
# ═══════════════════════════════════════════════════════════════════
from oorep.phantom_rubric_analyzer import PhantomRubricAnalyzer


class FakeRepPhantom:
    rubric_to_remedies = {
        1: [
            {"abbrev": "Puls.", "weight": 3, "remedy_id": 1},
            {"abbrev": "Nux-v.", "weight": 3, "remedy_id": 2},
            {"abbrev": "Ars.", "weight": 3, "remedy_id": 3},
        ],
        2: [
            {"abbrev": "Puls.", "weight": 3, "remedy_id": 1},
        ],
        3: [
            {"abbrev": "Puls.", "weight": 3, "remedy_id": 1},
            {"abbrev": "Nux-v.", "weight": 2, "remedy_id": 2},
        ],
    }
    rubrics = {
        1: {"fullpath": "Mind; Anxiety", "source": "kent-de"},
        2: {"fullpath": "Mind; Delusions", "source": "kent-de"},
        3: {"fullpath": "Head; Pain", "source": "kent-de"},
    }

    def get_rubric_by_id(self, rid):
        return self.rubrics.get(rid)

    def get_remedies_for_rubric(self, rid):
        return self.rubric_to_remedies.get(rid, [])


def test_phantom_analyze():
    analyzer = PhantomRubricAnalyzer(repertory=FakeRepPhantom())
    report = analyzer.analyze_rubric(1)
    assert report is not None
    assert report.gini_coefficient == 0.0  # Equal weights
    # 3-remedy rubric where all 3 are the top 3 → concentration = 1.0 ≥ 0.50, flagged
    assert report.is_flagged is True


def test_phantom_flag_concentrated():
    analyzer = PhantomRubricAnalyzer(repertory=FakeRepPhantom())
    report = analyzer.analyze_rubric(2)
    assert report is not None
    # Single remedy: Gini formula returns 0.0 for n=1
    assert report.gini_coefficient == 0.0
    assert report.is_flagged is True  # Entropy=0 + HHI=1.0 triggers flag


def test_phantom_find_phantoms():
    analyzer = PhantomRubricAnalyzer(repertory=FakeRepPhantom())
    phantoms = analyzer.find_phantom_rubrics(top_n=10)
    assert any(p.rubric_id == 2 for p in phantoms)


def test_phantom_summary():
    analyzer = PhantomRubricAnalyzer(repertory=FakeRepPhantom())
    summary = analyzer.differentiation_summary()
    assert summary["total_rubrics_analyzed"] == 3
    assert summary["flagged_phantom_rubrics"] >= 1


# ═══════════════════════════════════════════════════════════════════
# 4. RUBRIC CO-OCCURRENCE ENGINE (Benefit #24)
# ═══════════════════════════════════════════════════════════════════
from oorep.rubric_cooccurrence import RubricCooccurrenceEngine


class FakeRepCooc:
    rubric_to_remedies = {
        1: [{"abbrev": "Puls.", "weight": 3}, {"abbrev": "Nux-v.", "weight": 2}],
        2: [{"abbrev": "Puls.", "weight": 1}, {"abbrev": "Ars.", "weight": 3}],
        3: [{"abbrev": "Nux-v.", "weight": 2}, {"abbrev": "Ars.", "weight": 1}],
        4: [{"abbrev": "Puls.", "weight": 2}],
    }
    rubrics = {
        1: {"fullpath": "A", "source": "x"},
        2: {"fullpath": "B", "source": "x"},
        3: {"fullpath": "C", "source": "x"},
        4: {"fullpath": "D", "source": "x"},
    }

    def get_rubric_by_id(self, rid):
        return self.rubrics.get(rid)

    def get_remedies_for_rubric(self, rid):
        return self.rubric_to_remedies.get(rid, [])


def test_cooc_init():
    engine = RubricCooccurrenceEngine(repertory=FakeRepCooc())
    assert engine._remedy_counts["Puls."] == 3
    assert engine._remedy_counts["Nux-v."] == 2


def test_cooc_common_rubrics():
    engine = RubricCooccurrenceEngine(repertory=FakeRepCooc())
    common = engine.get_common_rubrics("Puls.", "Nux-v.")
    assert any(r["rubric_id"] == 1 for r in common)


def test_cooc_pair():
    engine = RubricCooccurrenceEngine(repertory=FakeRepCooc())
    pair = engine.compute_pair("Puls.", "Nux-v.")
    assert pair is not None
    assert pair.joint_count == 1
    assert pair.jaccard == round(1 / 4, 4)


def test_cooc_top_pairs():
    engine = RubricCooccurrenceEngine(repertory=FakeRepCooc())
    pairs = engine.top_pairs(min_cooccurrence=1, limit=10)
    assert len(pairs) > 0
    # Puls-Nux shared: 1 rubric; Puls-Ars: 1; Nux-Ars: 1


def test_cooc_cluster():
    engine = RubricCooccurrenceEngine(repertory=FakeRepCooc())
    cluster = engine.cluster_for_remedy("Puls.", min_cooccurrence=1)
    assert cluster["target_remedy"] == "Puls."
    assert cluster["cluster_size"] > 0


# ═══════════════════════════════════════════════════════════════════
# 5. PRIVATE RUBRICS (Benefit #41)
# ═══════════════════════════════════════════════════════════════════
import tempfile
from pathlib import Path
from oorep.private_rubrics import PrivateRubricManager


def test_private_create_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "priv.db"
        mgr = PrivateRubricManager(db_path=db)
        rid = mgr.create_private_rubric(
            fullpath="Mind; Anxiety; Custom",
            remedy_abbrevs={"Ars.": 3, "Acon.": 2},
            practitioner_id="dr.test",
            note="Test rubric",
        )
        assert rid.startswith("priv_")
        rubric = mgr.get_private_rubric(rid)
        assert rubric["fullpath"] == "Mind; Anxiety; Custom"
        assert rubric["remedy_abbrevs"]["Ars."] == 3


def test_private_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "priv.db"
        mgr = PrivateRubricManager(db_path=db)
        mgr.create_private_rubric("A", {"Ars.": 1}, "dr.a", note="")
        mgr.create_private_rubric("B", {"Puls.": 2}, "dr.b", note="")
        all_r = mgr.list_private_rubrics(limit=10)
        assert len(all_r) == 2
        a_only = mgr.list_private_rubrics(practitioner_id="dr.a", limit=10)
        assert len(a_only) == 1


def test_private_deactivate():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "priv.db"
        mgr = PrivateRubricManager(db_path=db)
        rid = mgr.create_private_rubric("A", {"Ars.": 1}, "dr.a", note="")
        assert mgr.deactivate_private_rubric(rid) is True
        rubric = mgr.get_private_rubric(rid)
        assert rubric["is_active"] is False


def test_private_merge_repertorization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "priv.db"
        mgr = PrivateRubricManager(db_path=db)
        rid = mgr.create_private_rubric("A", {"Ars.": 3}, "dr.a", note="")
        scores = defaultdict(lambda: {"score": 0, "matches": [], "_rubric_ids": set()})
        mgr.merge_into_repertorization(scores, [rid])
        assert scores["Ars."]["score"] == 3
        assert any(m["source"] == "private" for m in scores["Ars."]["matches"])


# ═══════════════════════════════════════════════════════════════════
# 6. PRACTITIONER APPROVAL GATE (Benefit #50)
# ═══════════════════════════════════════════════════════════════════
import tempfile
from oorep.practitioner_approval_gate import PractitionerApprovalGate, ApprovalRequired


def test_gate_approved():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "audit.db"
        gate = PractitionerApprovalGate(mode="strict", log_db_path=db)
        assert gate.require_approval("prescription", True, remedy_abbrev="Ars.", patient_id="PT-1") is True


def test_gate_denied():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "audit.db"
        gate = PractitionerApprovalGate(mode="strict", log_db_path=db)
        with pytest.raises(ApprovalRequired):
            gate.require_approval("prescription", False, remedy_abbrev="Ars.", patient_id="PT-1")


def test_gate_audit_only():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "audit.db"
        gate = PractitionerApprovalGate(mode="audit_only", log_db_path=db)
        assert gate.require_approval("prescription", False) is True
        log = gate.get_audit_log()
        assert len(log) == 1
        assert log[0]["decision"] == "denied"


def test_gate_test_mode():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "audit.db"
        gate = PractitionerApprovalGate(mode="test_mode", log_db_path=db)
        assert gate.require_approval("prescription", False) is True
        log = gate.get_audit_log()
        assert log[0]["decision"] == "test_pass"


# ═══════════════════════════════════════════════════════════════════
# 7. PATIENT CASE MANAGER (Benefits #7, #8, #9, #11)  — smoke only
# ═══════════════════════════════════════════════════════════════════
from oorep.patient_case_manager import PatientCaseManager


def test_case_manager_smoke():
    # Without feedback store, should gracefully degrade
    pcm = PatientCaseManager()
    result = pcm.query_case("PT-001")
    # If feedback store unavailable → error dict
    assert "error" in result or "timeline" in result


def test_case_manager_ask_hermes_no_store():
    pcm = PatientCaseManager()
    result = pcm.ask_hermes("What did I prescribe PT-001?")
    assert isinstance(result, str)
    assert "Feedback store not available" in result or "Please specify" in result or "Case" in result
