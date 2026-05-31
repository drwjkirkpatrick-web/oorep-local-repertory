"""
Comprehensive pytest tests for OOREP batch-B modules.

Run from repo root:
    pytest tests/test_batch_b.py -v
"""

import json
import pytest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def tmp_db_path(tmp_path):
    """Provide an isolated SQLite DB path."""
    return tmp_path / "test_feedback.db"


# ═══════════════════════════════════════════════════════════════════
# 1. FamilyConstellation
# ═══════════════════════════════════════════════════════════════════
from oorep.family_constellation import FamilyConstellation


class TestFamilyConstellation:
    def test_init_creates_db(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        assert tmp_db_path.exists()

    def test_add_family_member_and_retrieve(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        row_id = fc.add_family_member("fam-001", "Alice", "mother")
        assert row_id > 0
        members = fc.get_family_members("fam-001")
        assert len(members) == 1
        assert members[0]["pseudonym"] == "Alice"
        assert members[0]["relationship"] == "mother"
        assert members[0]["remedy_history"] == []

    def test_add_with_case_notes(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        fc.add_family_member(
            "fam-002", "Bob", "father",
            case_notes={
                "remedy_history": ["Puls.", "Sep."],
                "suppression_history": [
                    {"suppressed_symptom": "eczema", "suppressing_agent": "steroid", "date": "2023-01-10", "recurrence": "asthma"}
                ]
            }
        )
        members = fc.get_family_members("fam-002")
        assert members[0]["remedy_history"] == ["Puls.", "Sep."]
        assert len(members[0]["suppression_history"]) == 1
        assert members[0]["suppression_history"][0]["suppressed_symptom"] == "eczema"

    def test_get_family_remedy_patterns(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        fc.add_family_member("fam-003", "Anna", "mother", case_notes={"remedy_history": ["Puls.", "Sep."]})
        fc.add_family_member("fam-003", "Ben", "child", case_notes={"remedy_history": ["Puls.", "Sulph."]})
        fc.add_family_member("fam-003", "Clara", "grandmother", case_notes={"remedy_history": ["Nat-m.", "Puls."]})
        patterns = fc.get_family_remedy_patterns("fam-003")
        assert patterns["family_id"] == "fam-003"
        assert patterns["member_count"] == 3
        assert patterns["remedy_counts"]["Puls."] == 3
        assert patterns["remedy_counts"]["Sep."] == 1
        assert patterns["most_common"][0] == "Puls."
        assert set(patterns["most_common"]) == {"Puls.", "Nat-m.", "Sep.", "Sulph."}
        assert "Puls." in patterns["remedy_set"]

    def test_get_suppression_chain(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        fc.add_family_member(
            "fam-004", "Dad", "father",
            case_notes={
                "suppression_history": [
                    {"suppressed_symptom": "rash", "suppressing_agent": "cream", "date": "2022-06-01"},
                    {"suppressed_symptom": "cough", "suppressing_agent": "codeine", "date": "2023-01-15"},
                ]
            }
        )
        fc.add_family_member(
            "fam-004", "Son", "child",
            case_notes={
                "suppression_history": [
                    {"suppressed_symptom": "fever", "suppressing_agent": "paracetamol", "date": "2021-03-10"},
                ]
            }
        )
        chain = fc.get_suppression_chain("fam-004")
        assert len(chain) == 3
        # sorted by date
        dates = [c.get("date", "") for c in chain]
        assert dates == sorted(dates)

    def test_find_constellation(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        fc.add_family_member("fam-005", "Mum", "mother", case_notes={"remedy_history": ["Puls.", "Sep."]})
        fc.add_family_member("fam-005", "Dad", "father", case_notes={"remedy_history": ["Sulph.", "Psor."]})
        constellation = fc.find_constellation("fam-005")
        assert constellation["family_id"] == "fam-005"
        assert constellation["constellation_size"] == 4
        # Emotional cluster from Puls./Sep. and Psoric cluster from Sulph./Psor.
        assert any("Emotional/psychic" in t for t in constellation["shared_themes"])
        assert any("Psoric" in t for t in constellation["shared_themes"])
        assert "miasmatic_hints" in constellation
        assert constellation["narrative"].startswith("Family fam-005")

    def test_empty_family_handling(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        members = fc.get_family_members("nonexistent")
        assert members == []
        patterns = fc.get_family_remedy_patterns("nonexistent")
        assert patterns["member_count"] == 0
        assert patterns["remedy_counts"] == {}
        assert patterns["most_common"] == []
        chain = fc.get_suppression_chain("nonexistent")
        assert chain == []
        constellation = fc.find_constellation("nonexistent")
        assert constellation["constellation_size"] == 0
        assert constellation["narrative"].endswith("Top remedy: N/A. 0 suppression events recorded.")

    def test_update_family_member(self, tmp_db_path):
        fc = FamilyConstellation(db_path=str(tmp_db_path))
        fc.add_family_member("fam-006", "Eve", "mother", case_notes={"remedy_history": ["Puls."]})
        changed = fc.update_family_member("fam-006", "Eve", {"remedy_history": ["Puls.", "Sep."]})
        assert changed is True
        members = fc.get_family_members("fam-006")
        assert members[0]["remedy_history"] == ["Puls.", "Sep."]
        changed2 = fc.update_family_member("fam-006", "Nobody", {"remedy_history": []})
        assert changed2 is False

    def test_sqlite_roundtrip(self, tmp_db_path):
        fc1 = FamilyConstellation(db_path=str(tmp_db_path))
        fc1.add_family_member("fam-rt", "Zoe", "sibling", case_notes={"remedy_history": ["Calc."]})
        fc2 = FamilyConstellation(db_path=str(tmp_db_path))
        members = fc2.get_family_members("fam-rt")
        assert len(members) == 1
        assert members[0]["relationship"] == "sibling"
        assert members[0]["remedy_history"] == ["Calc."]


# ═══════════════════════════════════════════════════════════════════
# 2. SuppressionTracker
# ═══════════════════════════════════════════════════════════════════
from oorep.suppression_tracker import SuppressionTracker


class TestSuppressionTracker:
    def test_init_creates_db(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        assert tmp_db_path.exists()

    def test_record_and_retrieve(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        rid = st.record_suppression("PT-001", "eczema", "topical steroid", "2024-01-15", "asthma flare")
        assert rid > 0
        history = st.get_suppression_history("PT-001")
        assert len(history) == 1
        assert history[0]["suppressed_symptom"] == "eczema"
        assert history[0]["suppressing_agent"] == "topical steroid"
        assert history[0]["recurrence_symptoms"] == "asthma flare"

    def test_multiple_suppressions_per_case(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        st.record_suppression("PT-002", "rash", "cream A", "2023-01-01")
        st.record_suppression("PT-002", "fever", "antipyretic", "2023-02-01", "recurrent fever")
        st.record_suppression("PT-002", "cough", "cough syrup", "2023-03-01")
        history = st.get_suppression_history("PT-002")
        assert len(history) == 3
        symptoms = [h["suppressed_symptom"] for h in history]
        assert symptoms == ["rash", "fever", "cough"]

    def test_check_suppression_warnings_match(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        st.record_suppression("PT-003", "skin rash", "Sulph.", "2022-05-01", "worsening asthma")
        result = st.check_suppression_warnings("Sulph.", "PT-003")
        assert result["has_warning"] is True
        assert len(result["warnings"]) == 1
        assert "Sulph." in result["warnings"][0]
        assert len(result["matched_events"]) == 1

    def test_check_suppression_warnings_no_match(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        st.record_suppression("PT-004", "headache", "Nux-v.", "2022-05-01")
        result = st.check_suppression_warnings("Puls.", "PT-004")
        assert result["has_warning"] is False
        assert result["warnings"] == []
        assert result["matched_events"] == []

    def test_fuzzy_match_strips_period(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        st.record_suppression("PT-005", "cramps", "sulph", "2021-01-01", "joint pain")
        # explorer strips trailing period and lowercases both sides
        result = st.check_suppression_warnings("Sulph.", "PT-005")
        assert result["has_warning"] is True
        assert any("Sulph." in w for w in result["warnings"])

    def test_get_suppression_chronology(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        st.record_suppression("PT-006", "a", "x", "2020-01-01")
        st.record_suppression("PT-006", "b", "y", "2020-02-01")
        chronology = st.get_suppression_chronology("PT-006")
        assert len(chronology) == 2
        assert chronology[0]["stage"] == 1
        assert chronology[1]["stage"] == 2

    def test_empty_case_handling(self, tmp_db_path):
        st = SuppressionTracker(db_path=str(tmp_db_path))
        assert st.get_suppression_history("PT-none") == []
        assert st.get_suppression_chronology("PT-none") == []
        result = st.check_suppression_warnings("Ars.", "PT-none")
        assert result["has_warning"] is False
        assert result["warnings"] == []

    def test_sqlite_persistence(self, tmp_db_path):
        st1 = SuppressionTracker(db_path=str(tmp_db_path))
        st1.record_suppression("PT-007", "sneeze", "allergen", "2024-06-01")
        st2 = SuppressionTracker(db_path=str(tmp_db_path))
        history = st2.get_suppression_history("PT-007")
        assert len(history) == 1
        assert history[0]["suppressing_agent"] == "allergen"


# ═══════════════════════════════════════════════════════════════════
# 3. RubricExplorer (integration tests with real data)
# ═══════════════════════════════════════════════════════════════════
from oorep.rubric_explorer import RubricExplorer


class TestRubricExplorer:
    @pytest.fixture(scope="class")
    def explorer(self):
        data_dir = str(REPO_ROOT / "data")
        return RubricExplorer(data_dir=data_dir)

    def test_get_parent_rubric_real_data(self, explorer):
        # Rubric 10 (Bauch, Angst im) has parent 0 (Bauch)
        parent = explorer.get_parent_rubric(10)
        assert parent is not None
        assert parent["id"] == 0
        assert "Bauch" in parent["fullpath"]

    def test_get_child_rubrics_real_data(self, explorer):
        # Parent 0 (Bauch) should have many children including 10
        children = explorer.get_child_rubrics(0)
        assert len(children) > 0
        child_ids = [c["id"] for c in children]
        assert 10 in child_ids

    def test_get_siblings_real_data(self, explorer):
        # Rubric 10 (Bauch, Angst im) has siblings under Bauch
        siblings = explorer.get_siblings(10)
        assert len(siblings) > 0
        assert all(s["id"] != 10 for s in siblings)

    def test_get_ancestors_real_data(self, explorer):
        # Rubric 135 has ancestors [0] then parent 129
        ancestors = explorer.get_ancestors(135)
        assert len(ancestors) >= 1
        ids = [a["id"] for a in ancestors]
        assert 0 in ids
        # order should be root first
        assert ids[0] == 0

    def test_get_descendants_real_data(self, explorer):
        # Rubric 129 (Bauch, Zusammenziehen) should have descendants including 135
        descendants = explorer.get_descendants(129)
        assert len(descendants) > 0
        ids = [d["id"] for d in descendants]
        assert 135 in ids
        # depth field present
        assert all("depth" in d for d in descendants)

    def test_explore_path_real_data(self, explorer):
        path = explorer.explore_path(135)
        assert path["rubric_id"] == 135
        assert "Bauch" in path["rubric_fullpath"]
        assert path["source"] == "kent-de"
        assert len(path["breadcrumb"]) > 1
        assert path["breadcrumb"][0] == "Bauch"
        assert path["breadcrumb"][-1] == path["rubric_fullpath"]

    def test_nonexistent_rubric_handling(self, explorer):
        assert explorer.get_parent_rubric(999999999) is None
        assert explorer.get_child_rubrics(999999999) == []
        assert explorer.get_siblings(999999999) == []
        assert explorer.get_ancestors(999999999) == []
        assert explorer.get_descendants(999999999) == []
        path = explorer.explore_path(999999999)
        assert path["breadcrumb"] == []
        assert path["rubric_fullpath"] == "?"
        assert path["source"] == "?"

    def test_rubric_stats(self, explorer):
        stats = explorer.get_rubric_stats(129)
        assert stats is not None
        assert stats["rubric_id"] == 129
        assert stats["child_count"] > 0
        assert stats["descendant_count"] > 0
        assert stats["depth"] >= 1


# ═══════════════════════════════════════════════════════════════════
# 4. SOAPAssembler
# ═══════════════════════════════════════════════════════════════════
from oorep.soap_assembler import SOAPAssembler


class TestSOAPAssembler:
    def test_init_creates_db(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        assert tmp_db_path.exists()

    def test_assemble_from_case(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        note = sa.assemble_from_case(
            {
                "subjective": "Patient reports headache worse in morning",
                "objective": "Pulse 72, BP 120/80",
                "assessment": "Acute headache, possible remedy match",
                "plan": "Prescribe Nux-v. 30C",
            },
            patient_pseudonym="PT-SOAP-01",
            rubric_ids=[12345, 67890],
        )
        assert "case_id" in note
        assert note["patient_pseudonym"] == "PT-SOAP-01"
        assert note["sections"]["subjective"] == "Patient reports headache worse in morning"
        assert note["sections"]["plan"] == "Prescribe Nux-v. 30C"
        assert note["rubric_ids"] == [12345, 67890]
        assert "repertorization" in note["repertory_rationale"].lower()

    def test_assemble_from_conversation_raw_text(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        text = (
            "Subjective: Patient says she wakes with a splitting headache.\n"
            "Objective: Pulse elevated at 92. BP 130/85.\n"
            "Assessment: Migraine pattern, possible Nux-v. match.\n"
            "Plan: Prescribe Nux-v. 30C and follow up in one week."
        )
        note = sa.assemble_from_conversation(text, patient_pseudonym="PT-SOAP-02", rubric_ids=[111])
        assert note["patient_pseudonym"] == "PT-SOAP-02"
        sections = note["sections"]
        assert "headache" in sections.get("subjective", "").lower()
        assert "pulse" in sections.get("objective", "").lower()
        assert "migraine" in sections.get("assessment", "").lower()
        assert "nux-v" in sections.get("plan", "").lower()

    def test_get_soap_roundtrip(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        note = sa.assemble_from_case(
            {"subjective": "S", "objective": "O", "assessment": "A", "plan": "P"},
            patient_pseudonym="PT-RT",
            rubric_ids=[1, 2],
        )
        retrieved = sa.get_soap(note["case_id"])
        assert retrieved is not None
        assert retrieved["case_id"] == note["case_id"]
        assert retrieved["patient_pseudonym"] == "PT-RT"
        assert retrieved["sections"]["subjective"] == "S"
        assert retrieved["rubric_ids"] == [1, 2]

    def test_list_soaps(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        sa.assemble_from_case({"subjective": "A", "objective": "B", "assessment": "C", "plan": "D"}, patient_pseudonym="PT-LIST")
        sa.assemble_from_case({"subjective": "E", "objective": "F", "assessment": "G", "plan": "H"}, patient_pseudonym="PT-LIST")
        soaps = sa.list_soaps("PT-LIST")
        assert len(soaps) == 2
        # newest first (order by created_at DESC)
        assert soaps[0]["created_at"] >= soaps[1]["created_at"]

    def test_update_soap(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        note = sa.assemble_from_case(
            {"subjective": "old", "objective": "old", "assessment": "old", "plan": "old"},
            patient_pseudonym="PT-UP",
        )
        updated = sa.update_soap(note["case_id"], {"assessment": "new assessment", "plan": "new plan"})
        assert updated["sections"]["assessment"] == "new assessment"
        assert updated["sections"]["plan"] == "new plan"
        assert updated["sections"]["subjective"] == "old"
        retrieved = sa.get_soap(note["case_id"])
        assert retrieved is not None
        assert retrieved["sections"]["assessment"] == "new assessment"

    def test_update_soap_raises_when_missing(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        with pytest.raises(KeyError):
            sa.update_soap("nonexistent-case-id", {"subjective": "x"})

    def test_empty_input_handling(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        note = sa.assemble_from_case({})
        assert note["sections"]["subjective"] == ""
        assert note["sections"]["objective"] == ""
        assert note["sections"]["assessment"] == ""
        assert note["sections"]["plan"] == ""
        assert note["rubric_ids"] == []
        assert "no rubrics" in note["repertory_rationale"].lower()

    def test_malformed_input_handling(self, tmp_db_path):
        sa = SOAPAssembler(db_path=tmp_db_path)
        note = sa.assemble_from_case(
            {"subjective": "Only subjective", "extra_field": "preserved"},
            patient_pseudonym="PT-MAL",
        )
        assert note["sections"]["subjective"] == "Only subjective"
        assert note["sections"]["extra_field"] == "preserved"
        assert note["sections"]["objective"] == ""
        assert note["patient_pseudonym"] == "PT-MAL"

    def test_persistence_roundtrip(self, tmp_db_path):
        sa1 = SOAPAssembler(db_path=tmp_db_path)
        note = sa1.assemble_from_case(
            {"subjective": "Sx", "objective": "Ox", "assessment": "Ax", "plan": "Px"},
            patient_pseudonym="PT-PERSIST",
            rubric_ids=[99],
        )
        case_id = note["case_id"]
        sa2 = SOAPAssembler(db_path=tmp_db_path)
        retrieved = sa2.get_soap(case_id)
        assert retrieved is not None
        assert retrieved["patient_pseudonym"] == "PT-PERSIST"
        assert retrieved["rubric_ids"] == [99]
        assert retrieved["sections"]["subjective"] == "Sx"
