"""
Comprehensive pytest tests for OOREP batch-C modules.

Run from repo root:
    pytest tests/test_batch_c.py -v
"""

import pytest
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_db_path(tmp_path):
    """Provide an isolated SQLite DB path."""
    return tmp_path / "test_feedback.db"


@pytest.fixture
def fake_repertory():
    """Minimal fake HomeopathicRepertory for kent_vs_boenninghausen tests."""
    class FakeRepertory:
        rubric_to_remedies = {
            1: [
                {"abbrev": "Puls.", "weight": 3, "remedy_id": 1},
                {"abbrev": "Nux-v.", "weight": 2, "remedy_id": 2},
                {"abbrev": "Ars.", "weight": 3, "remedy_id": 3},
            ],
            2: [
                {"abbrev": "Puls.", "weight": 1, "remedy_id": 1},
                {"abbrev": "Ars.", "weight": 3, "remedy_id": 3},
                {"abbrev": "Bry.", "weight": 2, "remedy_id": 4},
            ],
            3: [
                {"abbrev": "Nux-v.", "weight": 2, "remedy_id": 2},
                {"abbrev": "Ars.", "weight": 1, "remedy_id": 3},
                {"abbrev": "Puls.", "weight": 2, "remedy_id": 1},
            ],
            4: [
                {"abbrev": "Puls.", "weight": 2, "remedy_id": 1},
                {"abbrev": "Nux-v.", "weight": 1, "remedy_id": 2},
            ],
            5: [
                {"abbrev": "Ars.", "weight": 3, "remedy_id": 3},
            ],
        }
        rubrics = {
            1: {"fullpath": "Mind; Anxiety", "source": "kent-de"},
            2: {"fullpath": "Head; Pain, headache, chronic", "source": "kent-de"},
            3: {"fullpath": "Stomach; Nausea", "source": "kent-de"},
            4: {"fullpath": "Generalities; Fever", "source": "kent-de"},
            5: {"fullpath": "Skin; Burning", "source": "kent-de"},
        }

        def get_rubric_by_id(self, rid):
            return self.rubrics.get(rid)

        def get_remedies_for_rubric(self, rid):
            return self.rubric_to_remedies.get(rid, [])

    return FakeRepertory()


# ═══════════════════════════════════════════════════════════════════
# 1. LetterGenerator
# ═══════════════════════════════════════════════════════════════════
from oorep.letter_generator import LetterGenerator


class TestLetterGenerator:
    def test_generate_referral_structure_and_red_flags(self, tmp_db_path):
        gen = LetterGenerator(db_path=tmp_db_path)
        letter = gen.generate_referral(
            patient_info={"pseudonym": "PT-001", "age": "45", "gender": "F"},
            red_flags=["Chest pain on exertion", "Dyspnoea at rest"],
            rationale="Ruled out cardiac etiology; recommend ECG",
            provider_info={"name": "Dr. Smith", "specialty": "Cardiology", "contact": "555-1234"},
        )
        assert "REFERRAL LETTER" in letter
        assert "Dr. Smith" in letter
        assert "Cardiology" in letter
        assert "PT-001" in letter
        assert "Chest pain on exertion" in letter
        assert "Dyspnoea at rest" in letter
        assert "Ruled out cardiac etiology" in letter
        assert "CONFIDENTIAL" in letter

    def test_generate_patient_summary_with_timeline(self, tmp_db_path):
        gen = LetterGenerator(db_path=tmp_db_path)
        letter = gen.generate_patient_summary(
            patient_info={"pseudonym": "PT-002", "age": "30", "gender": "M", "salutation": "Mr. Doe"},
            remedies=[
                {"name": "Pulsatilla", "potency": "30C", "date": "2025-01-10", "status": "active"},
            ],
            timeline=[
                {"date": "2025-01-10", "description": "Initial consultation"},
                {"date": "2025-02-14", "description": "Follow-up: improved"},
            ],
        )
        assert "PATIENT SUMMARY" in letter
        assert "PATIENT COPY" in letter
        assert "Mr. Doe" in letter
        assert "Pulsatilla 30C" in letter
        assert "Initial consultation" in letter
        assert "Follow-up: improved" in letter
        assert "2025-01-10" in letter
        assert "2025-02-14" in letter

    def test_generate_prescription_rationale_with_potency(self, tmp_db_path):
        gen = LetterGenerator(db_path=tmp_db_path)
        letter = gen.generate_prescription_rationale(
            patient_info={"pseudonym": "PT-003"},
            remedy="Arsenicum album",
            rubrics=[
                {"fullpath": "Mind; Anxiety", "source": "kent-de", "weight": 3},
                {"fullpath": "Generalities; Burning pain", "source": "kent-de", "grade": 2},
            ],
            potency="200C",
        )
        assert "PRESCRIPTION RATIONALE" in letter
        assert "Arsenicum album 200C" in letter
        assert "Mind; Anxiety" in letter
        assert "Generalities; Burning pain" in letter
        assert "grade: 3" in letter
        assert "grade: 2" in letter
        assert "OOREP" in letter

    def test_get_and_list_letters_persistence(self, tmp_db_path):
        gen = LetterGenerator(db_path=tmp_db_path)
        letter = gen.generate_referral(
            patient_info={"pseudonym": "PT-004"},
            red_flags=["Fever"],
            rationale="Rationale text",
            provider_info={"name": "Dr. X"},
        )
        # list_letters should return the persisted letter
        all_letters = gen.list_letters()
        assert len(all_letters) >= 1
        persisted = all_letters[0]
        assert persisted["type"] == "referral"
        assert persisted["patient"] == "PT-004"
        assert "Fever" in persisted["content"]

        # get_letter by id
        fetched = gen.get_letter(persisted["id"])
        assert fetched is not None
        assert fetched["id"] == persisted["id"]
        assert fetched["content"] == persisted["content"]

    def test_list_letters_filter_by_type_and_patient(self, tmp_db_path):
        gen = LetterGenerator(db_path=tmp_db_path)
        gen.generate_referral(
            patient_info={"pseudonym": "PT-A"},
            red_flags=["R"],
            rationale="R1",
            provider_info={"name": "Dr. A"},
        )
        gen.generate_patient_summary(
            patient_info={"pseudonym": "PT-A"},
            remedies=[],
            timeline=[],
        )
        gen.generate_referral(
            patient_info={"pseudonym": "PT-B"},
            red_flags=["R"],
            rationale="R2",
            provider_info={"name": "Dr. B"},
        )
        by_type = gen.list_letters(letter_type="referral")
        assert all(l["type"] == "referral" for l in by_type)
        # At least 2 referrals
        assert len(by_type) >= 2

        by_patient = gen.list_letters(patient="PT-A")
        assert all(l["patient"] == "PT-A" for l in by_patient)
        assert len(by_patient) >= 2

    def test_empty_input_handling(self, tmp_db_path):
        gen = LetterGenerator(db_path=tmp_db_path)
        # Empty red flags list should still produce a letter without crashing
        letter = gen.generate_referral(
            patient_info={},
            red_flags=[],
            rationale="",
            provider_info={},
        )
        assert "REFERRAL LETTER" in letter
        assert "Unknown" in letter

        # Empty summary
        letter2 = gen.generate_patient_summary(
            patient_info={},
            remedies=[],
            timeline=[],
        )
        assert "PATIENT SUMMARY" in letter2

    def test_sqlite_roundtrip(self, tmp_db_path):
        gen1 = LetterGenerator(db_path=tmp_db_path)
        letter = gen1.generate_prescription_rationale(
            patient_info={"pseudonym": "PT-RT"},
            remedy="Sulphur",
            rubrics=[],
            potency="30C",
        )
        all1 = gen1.list_letters()
        ids1 = {l["id"] for l in all1}

        gen2 = LetterGenerator(db_path=tmp_db_path)
        all2 = gen2.list_letters()
        ids2 = {l["id"] for l in all2}
        assert ids1 == ids2
        for l in all2:
            if l["patient"] == "PT-RT":
                assert "Sulphur" in l["content"]


# ═══════════════════════════════════════════════════════════════════
# 2. PHIScrubber
# ═══════════════════════════════════════════════════════════════════
from oorep.phi_scrubber import PHIScrubber


class TestPHIScrubber:
    def test_scrub_names(self):
        scrubber = PHIScrubber(reversible=False)
        text = "Alice visited the clinic."
        result = scrubber.scrub(text)
        assert "[PATIENT]" in result
        assert "Alice" not in result

    def test_scrub_dates(self):
        scrubber = PHIScrubber(reversible=False)
        text = "Appointment scheduled for 05/30/2026."
        result = scrubber.scrub(text)
        assert "[DATE]" in result
        assert "05/30/2026" not in result

    def test_scrub_phones(self):
        scrubber = PHIScrubber(reversible=False)
        text = "Call 555-123-4567 for follow-up."
        result = scrubber.scrub(text)
        assert "[PHONE]" in result
        assert "555-123-4567" not in result

    def test_scrub_ssn(self):
        scrubber = PHIScrubber(reversible=False)
        text = "National ID AB1234567 on file."
        result = scrubber.scrub(text)
        assert "[ID]" in result
        assert "AB1234567" not in result

    def test_scrub_addresses(self):
        scrubber = PHIScrubber(reversible=False)
        text = "Patient lives at 123 Main St."
        result = scrubber.scrub(text)
        # Heuristic address replacement; ensure it does not crash
        assert "[ADDRESS]" in result or "Main St" not in result

    def test_scrub_combined(self):
        scrubber = PHIScrubber(reversible=False)
        text = "Alice lives at 456 Oak Ave and her phone is 555-987-6543. Born 01/15/1990."
        result = scrubber.scrub(text)
        assert "[PATIENT]" in result or "Alice" not in result
        assert "[PHONE]" in result or "555-987-6543" not in result
        assert "[DATE]" in result or "01/15/1990" not in result

    def test_scrub_case_notes_recursive(self):
        scrubber = PHIScrubber(reversible=False)
        notes = {
            "patient": "Alice",
            "contact": {"phone": "555-000-1111", "address": "789 Pine Road"},
            "dates": ["2024-03-01", "2024-04-15"],
            "ssn": "987-65-4321",
        }
        result = scrubber.scrub_case_notes(notes)
        assert isinstance(result, dict)
        assert result["ssn"] != "987-65-4321"
        assert "[PHONE]" in result["contact"]["phone"] or "555-000-1111" not in result["contact"]["phone"]
        assert result["contact"]["address"] != "789 Pine Road"
        # dates inside list should be scrubbed
        assert all("2024" not in d for d in result["dates"])

    def test_get_pseudonym_and_reveal_round_trip(self, tmp_db_path):
        scrubber = PHIScrubber(reversible=True, db_path=tmp_db_path)
        text = "Robert called from 111-222-3333."
        scrubbed = scrubber.scrub(text)
        # Should produce pseudonyms like [PT001]
        import re
        pseudos = re.findall(r"\[PT\d+\]", scrubbed)
        assert len(pseudos) > 0
        for pseudo in pseudos:
            real = scrubber.reveal(pseudo)
            assert real is not None and real != pseudo

    def test_restore_text(self, tmp_db_path):
        scrubber = PHIScrubber(reversible=True, db_path=tmp_db_path)
        original = "Sarah lives at 99 Birch Lane."
        scrubbed = scrubber.scrub(original)
        assert scrubbed != original
        restored = scrubber.restore_text(scrubbed)
        assert restored == original

    def test_unrecognized_text_passes_unchanged(self):
        scrubber = PHIScrubber(reversible=False)
        text = "The quick brown fox jumps over the lazy dog."
        result = scrubber.scrub(text)
        assert result == text

    def test_empty_input(self):
        scrubber = PHIScrubber(reversible=False)
        assert scrubber.scrub("") == ""
        assert scrubber.scrub_case_notes({}) == {}
        assert scrubber.scrub_case_notes([]) == []
        assert scrubber.scrub_case_notes(None) is None


# ═══════════════════════════════════════════════════════════════════
# 3. AuditTrail
# ═══════════════════════════════════════════════════════════════════
from oorep.audit_trail import AuditTrail


class TestAuditTrail:
    def test_log_entry_creation(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        row_id = audit.log(
            action="prescribe",
            user="dr.smith",
            resource="prescription/abc123",
            old_value=None,
            new_value={"remedy": "Ars.", "potency": "30C"},
        )
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_verify_chain_empty(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        result = audit.verify_chain()
        assert result["intact"] is True
        assert result["total_entries"] == 0

    def test_verify_chain_intact(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        audit.log("create", "user_a", "resource/1", None, {"data": "a"})
        audit.log("update", "user_a", "resource/1", {"data": "a"}, {"data": "b"})
        result = audit.verify_chain()
        assert result["intact"] is True
        assert result["total_entries"] == 2
        assert result["first_broken_id"] is None

    def test_verify_chain_tampered(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        audit.log("create", "user_a", "resource/1", None, {"data": "a"})
        audit.log("update", "user_a", "resource/1", {"data": "a"}, {"data": "b"})
        # Tamper directly via sqlite3
        import sqlite3
        conn = sqlite3.connect(str(tmp_db_path))
        cursor = conn.cursor()
        cursor.execute("UPDATE audit_log SET action = 'hacked' WHERE id = 1")
        conn.commit()
        conn.close()
        result = audit.verify_chain()
        assert result["intact"] is False
        assert result["first_broken_id"] is not None
        assert "tampered" in result["message"].lower() or "mismatch" in result["message"].lower()

    def test_get_history(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        audit.log("create", "user_a", "resource/99", None, {"data": "v1"})
        audit.log("update", "user_b", "resource/99", {"data": "v1"}, {"data": "v2"})
        audit.log("delete", "user_c", "resource/88", {"data": "x"}, None)
        history = audit.get_history("resource/99")
        assert len(history) == 2
        actions = [h["action"] for h in history]
        assert actions == ["create", "update"]
        for h in history:
            assert h["resource"] == "resource/99"

    def test_prescriber_ack(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        row_id = audit.log("prescribe", "dr.jones", "rx/001", None, {"remedy": "Puls."})
        ok = audit.prescriber_ack(row_id, "Dr. Jones")
        assert ok is True
        history = audit.get_history("rx/001")
        assert len(history) == 1
        assert history[0]["prescriber_ack"] == "Dr. Jones"
        assert history[0]["ack_timestamp"] is not None

    def test_prescriber_ack_nonexistent(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        ok = audit.prescriber_ack(9999, "Dr. Nobody")
        assert ok is False

    def test_export_for_licensure_date_filtering(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        audit.log("create", "user", "res/1", None, {"v": "a"})
        report = audit.export_for_licensure("1900-01-01", "2099-12-31")
        assert "OOREP AUDIT REPORT" in report
        assert "Total entries:" in report
        # Filter to a future date where nothing exists
        empty_report = audit.export_for_licensure("2100-01-01", "2100-12-31")
        assert "Total entries: 0" in empty_report

    def test_multiple_logs_form_chain(self, tmp_db_path):
        audit = AuditTrail(db_path=tmp_db_path)
        ids = []
        for i in range(5):
            row_id = audit.log("step", "auto", "proc/1", {"i": i}, {"i": i + 1})
            ids.append(row_id)
        assert ids == sorted(ids)
        result = audit.verify_chain()
        assert result["intact"] is True
        assert result["total_entries"] == 5


# ═══════════════════════════════════════════════════════════════════
# 4. KentVsBoenninghausen
# ═══════════════════════════════════════════════════════════════════
from oorep.kent_vs_boenninghausen import KentVsBoenninghausen


class TestKentVsBoenninghausen:
    def test_compare_methods_returns_both(self, fake_repertory):
        tool = KentVsBoenninghausen(repertory=fake_repertory)
        result = tool.compare_methods(rubric_ids=[1, 2, 3, 4])
        assert "kent_results" in result
        assert "boenninghausen_results" in result
        assert isinstance(result["kent_results"], list)
        assert isinstance(result["boenninghausen_results"], list)
        assert "top_common" in result
        assert "top_kent_only" in result
        assert "top_boenninghausen_only" in result

    def test_convert_to_kent(self):
        raw = [
            {"abbrev": "Ars.", "grade_sum": 5, "match_count": 2, "matches": []},
            {"abbrev": "Puls.", "score": 3, "match_count": 1},
        ]
        out = KentVsBoenninghausen.convert_to_kent(raw)
        assert len(out) == 2
        assert out[0]["score"] >= out[1]["score"]
        for item in out:
            assert "abbrev" in item
            assert "score" in item
            assert "match_count" in item

    def test_convert_to_boenninghausen(self):
        raw = [
            {"abbrev": "Ars.", "rubric_count": 3, "matches": []},
            {"abbrev": "Puls.", "score": 5, "match_count": 2},
        ]
        out = KentVsBoenninghausen.convert_to_boenninghausen(raw)
        assert len(out) == 2
        assert out[0]["score"] >= out[1]["score"]
        for item in out:
            assert item["score"] == item["match_count"]

    def test_analyze_divergence_flags_disagreements(self, fake_repertory):
        tool = KentVsBoenninghausen(repertory=fake_repertory)
        comparison = tool.compare_methods(rubric_ids=[1, 2, 3, 4, 5])
        divergence = tool.analyze_divergence(comparison)
        assert "common_top" in divergence
        assert "kent_only_top" in divergence
        assert "boenninghausen_only_top" in divergence
        assert "divergent_pairs" in divergence
        assert isinstance(divergence["narrative"], str)

    def test_recommend_method_acute(self):
        tool = KentVsBoenninghausen()
        rec = tool.recommend_method(["fever", "sudden onset", "keynote"])
        assert rec["recommended_method"] == "kent"
        assert "symptom_count" in rec
        assert rec["symptom_count"] == 3

    def test_recommend_method_chronic(self):
        tool = KentVsBoenninghausen()
        rec = tool.recommend_method([
            "chronic fatigue", "long-standing anxiety", "family history",
            "mild depression", "occasional headaches", "digestive issues",
        ])
        assert rec["recommended_method"] == "boenninghausen"
        assert rec["chronic_score"] >= 2

    def test_recommend_method_moderate(self):
        tool = KentVsBoenninghausen()
        rec = tool.recommend_method(["a", "b", "c", "d", "e"])
        assert rec["recommended_method"] == "boenninghausen"

    def test_mock_repertorization_data(self, fake_repertory):
        tool = KentVsBoenninghausen(repertory=fake_repertory)
        kent = tool.kent_repertorize([1, 2, 3])
        boen = tool.boenninghausen_repertorize([1, 2, 3])
        assert len(kent) > 0
        assert len(boen) > 0
        # Kent uses grade sums; Ars. has the highest total weight (3+3+1=7)
        assert kent[0]["abbrev"] == "Ars."
        # Boenninghausen counts rubrics; both Puls. and Ars. cover 3 rubrics
        top_abbrevs = {r["abbrev"] for r in boen[:2]}
        assert "Ars." in top_abbrevs
        assert "Puls." in top_abbrevs
        for r in boen:
            assert r["score"] == r["match_count"]
        assert boen[0]["score"] == 3


# ═══════════════════════════════════════════════════════════════════
# 5. PersonalityEngineBridge
# ═══════════════════════════════════════════════════════════════════
from oorep.personality_engine_bridge import PersonalityEngineBridge


class TestPersonalityEngineBridge:
    def test_get_personality_known_remedy(self):
        bridge = PersonalityEngineBridge()
        narrative = bridge.get_personality("Ars.")
        assert narrative is not None
        assert isinstance(narrative, str)
        # Hardcoded fallback contains expected keywords
        assert "restless" in narrative.lower() or "anxious" in narrative.lower()

    def test_get_personality_by_full_name(self):
        bridge = PersonalityEngineBridge()
        narrative = bridge.get_personality("arsenicum album")
        assert narrative is not None
        assert "restless" in narrative.lower() or "anxious" in narrative.lower()

    def test_get_personality_unknown_remedy(self):
        bridge = PersonalityEngineBridge()
        narrative = bridge.get_personality("Unknownium imaginary")
        assert narrative is None

    def test_suggest_by_personality_keyword_matching(self):
        bridge = PersonalityEngineBridge()
        matches = bridge.suggest_by_personality("anxious, restless, tidy")
        assert isinstance(matches, list)
        assert len(matches) > 0
        # Arsenicum album should rank highly
        abbrevs = [m["remedy_abbrev"] for m in matches]
        assert "ars." in abbrevs or "Ars." in abbrevs
        for m in matches:
            assert "score" in m
            assert "matched_keywords" in m

    def test_compare_personalities_side_by_side(self):
        bridge = PersonalityEngineBridge()
        comp = bridge.compare_personalities("Ars.", "Nux-v.")
        assert comp["remedy_a"] == "Ars."
        assert comp["remedy_b"] == "Nux-v."
        assert isinstance(comp["personality_a"], str)
        assert isinstance(comp["personality_b"], str)
        assert isinstance(comp["shared_keywords"], list)
        assert isinstance(comp["a_unique_keywords"], list)
        assert isinstance(comp["b_unique_keywords"], list)

    def test_personality_to_rubrics_extraction(self):
        bridge = PersonalityEngineBridge()
        narrative = bridge.get_personality("Ars.")
        assert narrative is not None
        rubrics = bridge.personality_to_rubrics(narrative)
        assert isinstance(rubrics, list)
        if rubrics:
            assert "rubric_path" in rubrics[0]
            assert "confidence" in rubrics[0]
            # Should extract anxiety-related rubric
            paths = [r["rubric_path"] for r in rubrics]
            assert any("anxiety" in p for p in paths)

    def test_personality_files_integration_graceful_when_missing(self, tmp_path):
        missing_dir = tmp_path / "nonexistent_personalities"
        bridge = PersonalityEngineBridge(personality_dir=missing_dir)
        # Should still return fallback personalities
        narrative = bridge.get_personality("Puls.")
        assert narrative is not None
        # And suggest still works from fallback map
        matches = bridge.suggest_by_personality("weepy, changeable")
        assert len(matches) > 0

    def test_personality_files_local_override(self, tmp_path):
        pdir = tmp_path / "personalities"
        pdir.mkdir()
        (pdir / "ignatia amara.md").write_text("Silent grief, sighing, trembling, worse from consolation.")
        bridge = PersonalityEngineBridge(personality_dir=pdir)
        narrative = bridge.get_personality("ignatia amara")
        assert narrative is not None
        assert "silent grief" in narrative.lower()
