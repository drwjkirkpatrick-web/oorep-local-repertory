"""
Comprehensive pytest tests for OOREP batch-A modules.

Run from repo root:
    pytest tests/test_batch_a.py -v
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
    """Minimal fake HomeopathicRepertory for elimination/tagger tests."""
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
            ],
            3: [
                {"abbrev": "Nux-v.", "weight": 2, "remedy_id": 2},
                {"abbrev": "Ars.", "weight": 1, "remedy_id": 3},
            ],
            4: [
                {"abbrev": "Puls.", "weight": 2, "remedy_id": 1},
            ],
            5: [],  # empty rubric
        }
        rubrics = {
            1: {"fullpath": "Mind; Anxiety", "source": "kent-de"},
            2: {"fullpath": "Head; Pain, headache, chronic", "source": "kent-de"},
            3: {"fullpath": "Stomach; Nausea", "source": "kent-de"},
            4: {"fullpath": "Generalities; Fever", "source": "kent-de"},
            5: {"fullpath": "Skin; Eruptions", "source": "kent-de"},
        }

        def get_rubric_by_id(self, rid):
            return self.rubrics.get(rid)

        def get_remedies_for_rubric(self, rid):
            return self.rubric_to_remedies.get(rid, [])

    return FakeRepertory()


# ═══════════════════════════════════════════════════════════════════
# 1. RemedyRelationships
# ═══════════════════════════════════════════════════════════════════
from oorep.remedy_relationships import RemedyRelationships


class TestRemedyRelationships:
    def test_init_seeds_data(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        all_rels = rel.list_all()
        assert len(all_rels) > 0  # classical seed data present

    def test_get_relationships_no_filter(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        rows = rel.get_relationships("Puls.")
        assert isinstance(rows, list)
        assert any("Puls." in {r["remedy_a"], r["remedy_b"]} for r in rows)

    def test_get_comparatives(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        comp = rel.get_comparatives("Lach.")
        assert all(c["rel_type"] == "comparative" for c in comp)

    def test_get_antidotes(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        # Ars. has an antidotal relationship with Nux-v.
        antidotes = rel.get_antidotes("Ars.")
        assert isinstance(antidotes, list)
        if antidotes:
            assert antidotes[0]["rel_type"] in ("antidotal", "antidote")
            assert "remedy" in antidotes[0]

    def test_check_conflict_known(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        # Puls. vs Nux-v. is inimical in seed data
        result = rel.check_conflict("Puls.", "Nux-v.")
        assert result["has_conflict"] is True
        assert result["severity"] == "critical"
        assert len(result["conflicts"]) > 0

    def test_check_conflict_non_conflict(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        # Ars. and Rhus-t. are complementary (not a conflict)
        result = rel.check_conflict("Ars.", "Rhus-t.")
        assert result["has_conflict"] is False
        assert result["severity"] == "none"
        assert result["conflicts"] == []

    def test_add_relationship_and_persistence(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        row_id = rel.add_relationship("Test-a.", "Test-b.", "complementary", "TestSource")
        assert row_id > 0
        rows = rel.get_relationships("Test-a.", rel_type="complementary")
        assert any(r["source"] == "TestSource" for r in rows)

    def test_sqlite_roundtrip(self, tmp_db_path):
        # First instance seeds
        rel1 = RemedyRelationships(db_path=str(tmp_db_path))
        rel1.add_relationship("Zinc.", "Calc.", "follows-well", "Kent")
        # Second instance reads same DB
        rel2 = RemedyRelationships(db_path=str(tmp_db_path))
        rows = rel2.get_relationships("Zinc.", rel_type="follows-well")
        assert any(r["source"] == "Kent" for r in rows)

    def test_invalid_rel_type_raises(self, tmp_db_path):
        rel = RemedyRelationships(db_path=str(tmp_db_path))
        with pytest.raises(ValueError):
            rel.add_relationship("A", "B", "invalid_type")


# ═══════════════════════════════════════════════════════════════════
# 2. RedFlagDetector
# ═══════════════════════════════════════════════════════════════════
from oorep.red_flag_detector import RedFlagDetector


class TestRedFlagDetector:
    def test_scan_critical(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        result = det.scan("patient shows signs of anaphylaxis after bee sting")
        assert result["has_red_flags"] is True
        assert result["max_severity"] == "critical"
        assert any(h["severity"] == "critical" for h in result["hits"])
        assert "emergency" in result["recommendation"].lower()

    def test_scan_urgent(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        result = det.scan("chest pain and shortness of breath")
        assert result["has_red_flags"] is True
        assert result["max_severity"] == "urgent"
        assert any(h["severity"] == "urgent" for h in result["hits"])

    def test_scan_advisory(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        result = det.scan("persistent cough and night sweats for two weeks")
        assert result["has_red_flags"] is True
        assert result["max_severity"] == "advisory"
        assert any(h["severity"] == "advisory" for h in result["hits"])

    def test_scan_empty_text(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        result = det.scan("")
        assert result["has_red_flags"] is False
        assert result["max_severity"] is None
        assert result["hits"] == []
        assert "proceed" in result["recommendation"].lower()

    def test_gate_repertorization_without_flags(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        rubric_results = [
            {
                "matches": [
                    {"rubric": "Mind; Anxiety", "query_symptom": "anxious about exams"}
                ]
            }
        ]
        gate = det.gate_repertorization(rubric_results)
        assert gate["proceed"] is True
        assert gate["warnings"] == []

    def test_gate_repertorization_with_critical(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        rubric_results = [
            {
                "matches": [
                    {"rubric": "Generalities; Fever", "query_symptom": "anaphylaxis after food"}
                ]
            }
        ]
        gate = det.gate_repertorization(rubric_results)
        assert gate["proceed"] is False
        assert any("CRITICAL" in w for w in gate["warnings"])

    def test_add_custom_red_flag_and_persistence(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        assert det.add_custom_red_flag("test-keyword-xyz", "urgent") is True
        result = det.scan("the patient has test-keyword-xyz symptoms")
        assert result["has_red_flags"] is True
        assert any(h["keyword"] == "test-keyword-xyz" for h in result["hits"])
        # Persistence across new instance
        det2 = RedFlagDetector(db_path=str(tmp_db_path))
        result2 = det2.scan("test-keyword-xyz again")
        assert result2["has_red_flags"] is True

    def test_add_custom_red_flag_invalid_severity(self, tmp_db_path):
        det = RedFlagDetector(db_path=str(tmp_db_path))
        with pytest.raises(ValueError):
            det.add_custom_red_flag("kw", "invalid")


# ═══════════════════════════════════════════════════════════════════
# 3. EliminationAnalyzer
# ═══════════════════════════════════════════════════════════════════
from oorep.elimination_analysis import EliminationAnalyzer


class TestEliminationAnalyzer:
    def test_find_eliminators(self, fake_repertory):
        ea = EliminationAnalyzer(repertory=fake_repertory)
        rubric_results = [
            {
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind; Anxiety", "query_symptom": "anxious"},
                    {"rubric_id": 2, "rubric": "Head; Pain, headache, chronic", "query_symptom": "headache"},
                ]
            },
            {
                "matches": [
                    {"rubric_id": 3, "rubric": "Stomach; Nausea", "query_symptom": "nausea"},
                ]
            },
        ]
        # Nux-v. is not in rubric 2 (head pain chronic)
        eliminators = ea.find_eliminators(rubric_results, "Nux-v.")
        assert any(e["rubric_id"] == 2 for e in eliminators)
        # Nux-v. IS in rubric 1 and 3
        assert not any(e["rubric_id"] == 1 for e in eliminators)
        assert not any(e["rubric_id"] == 3 for e in eliminators)

    def test_find_excluders_grade_one(self, fake_repertory):
        ea = EliminationAnalyzer(repertory=fake_repertory)
        # Puls. has weight 1 in rubric 2 while Ars. has weight 3 there.
        rubric_results = [
            {
                "matches": [
                    {"rubric_id": 2, "rubric": "Head; Pain, headache, chronic", "query_symptom": "headache"},
                ]
            }
        ]
        excluders = ea.find_excluders(rubric_results, "Puls.")
        assert len(excluders) == 1
        assert excluders[0]["rubric_id"] == 2
        assert excluders[0]["target_weight"] == 1
        assert excluders[0]["top_grade_in_rubric"] == 3
        assert "weak coverage" in excluders[0]["rationale"].lower()

    def test_generate_elimination_report_structure(self, fake_repertory):
        ea = EliminationAnalyzer(repertory=fake_repertory)
        rubric_results = [
            {
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind; Anxiety", "query_symptom": "anxious"},
                    {"rubric_id": 2, "rubric": "Head; Pain, headache, chronic", "query_symptom": "headache"},
                    {"rubric_id": 3, "rubric": "Stomach; Nausea", "query_symptom": "nausea"},
                ]
            }
        ]
        report = ea.generate_elimination_report(rubric_results, "Puls.")
        assert report["remedy"] == "Puls."
        assert report["total_case_rubrics"] == 3
        assert isinstance(report["present_rubrics"], int)
        assert isinstance(report["missing_rubrics"], int)
        assert isinstance(report["weak_coverage_rubrics"], int)
        assert isinstance(report["eliminators"], list)
        assert isinstance(report["excluders"], list)
        assert isinstance(report["summary"], str)

    def test_rank_remedies_by_coverage(self, fake_repertory):
        ea = EliminationAnalyzer(repertory=fake_repertory)
        rubric_results = [
            {
                "matches": [
                    {"rubric_id": 1, "rubric": "Mind; Anxiety", "query_symptom": "anxious"},
                    {"rubric_id": 2, "rubric": "Head; Pain, headache, chronic", "query_symptom": "headache"},
                    {"rubric_id": 3, "rubric": "Stomach; Nausea", "query_symptom": "nausea"},
                ]
            }
        ]
        ranked = ea.rank_remedies_by_coverage(rubric_results, ["Puls.", "Ars.", "Nux-v."])
        assert len(ranked) == 3
        assert all("score" in r for r in ranked)
        # Should be sorted descending by score
        scores = [r["score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)


# ═══════════════════════════════════════════════════════════════════
# 4. PotencyGuidance
# ═══════════════════════════════════════════════════════════════════
from oorep.potency_guidance import PotencyGuidance


class TestPotencyGuidance:
    def test_suggest_potency_acute_physical(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        result = pg.suggest_potency("Lyc.", symptom_layer="physical", chronicity="acute")
        assert result["layer"] == "low"
        assert result["suggested_potency"] in result["remedy_profile"]["layer"]["low"]
        assert isinstance(result["alternatives"], list)
        assert isinstance(result["rationale"], str)

    def test_suggest_potency_chronic_mental(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        result = pg.suggest_potency("Lyc.", symptom_layer="mental", chronicity="chronic")
        assert result["layer"] == "high"
        assert result["suggested_potency"] in result["remedy_profile"]["layer"]["high"]

    def test_suggest_potency_acute_layer(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        result = pg.suggest_potency("Bry.", symptom_layer="acute", chronicity="acute")
        assert result["layer"] == "medium"
        assert result["suggested_potency"] in result["remedy_profile"]["layer"]["medium"]

    def test_get_potency_ladder_known(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        ladder = pg.get_potency_ladder("Sulph.")
        assert ladder["remedy"] == "Sulph."
        assert isinstance(ladder["low"], list)
        assert isinstance(ladder["medium"], list)
        assert isinstance(ladder["high"], list)
        assert "notes" in ladder

    def test_add_custom_profile_and_persistence(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        custom = {"layer": {"low": ["3C"], "medium": ["12C"], "high": ["200C"]}, "notes": "Custom test profile"}
        assert pg.add_custom_profile("Testrem.", custom) is True
        # Should override / merge with generic fallback
        result = pg.suggest_potency("Testrem.", symptom_layer="mental", chronicity="chronic")
        assert result["remedy_profile"] is not None
        ladder = pg.get_potency_ladder("Testrem.")
        assert ladder["high"] == ["200C"]

    def test_fallback_unknown_remedy(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        result = pg.suggest_potency("Unknownremedy123", symptom_layer="physical", chronicity="acute")
        assert result["layer"] == "low"
        assert result["remedy_profile"] is None
        assert "no specific classical profile" in result["rationale"].lower()

    def test_get_potency_ladder_fallback(self, tmp_db_path):
        pg = PotencyGuidance(db_path=str(tmp_db_path))
        ladder = pg.get_potency_ladder("Nonexistentremedy")
        assert ladder["low"] == ["3C", "6C"]
        assert ladder["medium"] == ["12C", "30C"]
        assert ladder["high"] == ["200C", "1M"]
        assert "generic" in ladder["notes"].lower()


# ═══════════════════════════════════════════════════════════════════
# 5. AcuteChronicTagger
# ═══════════════════════════════════════════════════════════════════
from oorep.acute_chronic_layer import AcuteChronicTagger


class TestAcuteChronicTagger:
    def test_tag_rubric_texts_acute(self):
        tagger = AcuteChronicTagger()
        texts = ["sudden fever with chill", "acute inflammation of throat"]
        tags = tagger.tag_rubric_texts(texts)
        assert tags[texts[0]] == "acute"
        assert tags[texts[1]] == "acute"

    def test_tag_rubric_texts_chronic(self):
        tagger = AcuteChronicTagger()
        texts = ["chronic fatigue with wasting", "old people with cachexia"]
        tags = tagger.tag_rubric_texts(texts)
        assert tags[texts[0]] == "chronic"
        assert tags[texts[1]] == "chronic"

    def test_tag_rubric_texts_both(self):
        tagger = AcuteChronicTagger()
        texts = ["chronic fever with acute exacerbation"]
        tags = tagger.tag_rubric_texts(texts)
        assert tags[texts[0]] == "both"

    def test_tag_rubric_texts_unknown(self):
        tagger = AcuteChronicTagger()
        texts = ["some totally neutral description"]
        tags = tagger.tag_rubric_texts(texts)
        # Default is conservative "both"
        assert tags[texts[0]] == "both"

    def test_separate_layers_mixed(self, fake_repertory):
        tagger = AcuteChronicTagger()
        # ids 1 (Mind; Anxiety -> chronic via prefix map), 2 (Head; Pain, headache, chronic -> chronic),
        # 3 (Stomach; Nausea -> heuristic both), 4 (Generalities; Fever -> acute)
        layers = tagger.separate_layers([1, 2, 3, 4, 5], repertory=fake_repertory)
        assert isinstance(layers["acute"], list)
        assert isinstance(layers["chronic"], list)
        assert isinstance(layers["both"], list)
        # id 4 (Fever) is acute
        assert 4 in layers["acute"] or 4 in layers["both"]
        # id 5 (Skin; Eruptions) maps to both in hardcoded map
        assert 5 in layers["both"]

    def test_layer_priority_balanced(self, fake_repertory):
        tagger = AcuteChronicTagger()
        rubric_results = [
            {"abbrev": "Puls.", "score": 100, "matches": [{"rubric": "Generalities; Fever"}]},
            {"abbrev": "Nux-v.", "score": 80, "matches": [{"rubric": "Mind; Anxiety"}]},
        ]
        out = tagger.layer_priority(rubric_results, mode="balanced")
        assert len(out) == 2
        for entry in out:
            assert entry["_layer_adjusted_score"] == entry.get("score", 0)
            assert entry["_layer_boost_applied"] == 1.0

    def test_layer_priority_acute_boost(self, fake_repertory):
        tagger = AcuteChronicTagger()
        rubric_results = [
            {"abbrev": "Puls.", "score": 100, "matches": [{"rubric": "Generalities; Fever"}]},
            {"abbrev": "Nux-v.", "score": 80, "matches": [{"rubric": "Mind; Anxiety"}]},
        ]
        out = tagger.layer_priority(rubric_results, mode="acute")
        # At least one entry should have a boost > 1.0 (if acute matches exist)
        boosted = [e for e in out if e.get("_layer_boost_applied", 1.0) > 1.0]
        # Generalities; Fever is acute, so Puls. should receive boost
        puls_entry = next(e for e in out if e["abbrev"] == "Puls.")
        assert puls_entry["_layer_boost_applied"] > 1.0
        assert puls_entry["_layer_adjusted_score"] >= puls_entry["score"]
        # Should be sorted descending by adjusted score
        adj_scores = [e["_layer_adjusted_score"] for e in out]
        assert adj_scores == sorted(adj_scores, reverse=True)

    def test_layer_priority_chronic_boost(self, fake_repertory):
        tagger = AcuteChronicTagger()
        rubric_results = [
            {"abbrev": "Puls.", "score": 100, "matches": [{"rubric": "Generalities; Fever"}]},
            {"abbrev": "Nux-v.", "score": 80, "matches": [{"rubric": "Mind; Anxiety"}]},
        ]
        out = tagger.layer_priority(rubric_results, mode="chronic")
        nux_entry = next(e for e in out if e["abbrev"] == "Nux-v.")
        assert nux_entry["_layer_boost_applied"] > 1.0
