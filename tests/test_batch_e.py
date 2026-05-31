"""tests/test_batch_e.py — Final 8 benefit modules."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from oorep.materia_medica import MateriaMedica
from oorep.kingdom_taxonomy import KingdomTaxonomy
from oorep.botanical_bridge import BotanicalBridge
from oorep.genomic_hypothesis import GenomicHypothesis
from oorep.flashcard_srs import FlashcardSRS
from oorep.cron_tasks import CronTasks


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_e.db"


# ── MateriaMedica ──────────────────────────────────────────────────────────────

class TestMateriaMedica:
    def test_search_returns_results(self, tmp_db_path: Path):
        mm = MateriaMedica(db_path=tmp_db_path)
        hits = mm.search("burning", limit=5)
        assert isinstance(hits, list)
        if hits:
            assert "remedy_abbrev" in hits[0]
            assert "text_snippet" in hits[0]

    def test_get_proving_text(self, tmp_db_path: Path):
        mm = MateriaMedica(db_path=tmp_db_path)
        entries = mm.get_proving_text("Ars.", author="Kent")
        assert isinstance(entries, list)

    def test_compare_remedies(self, tmp_db_path: Path):
        mm = MateriaMedica(db_path=tmp_db_path)
        comp = mm.compare_remedies("Ars.", "Phos.", query="burning")
        assert comp["remedy_a"] == "Ars."
        assert comp["remedy_b"] == "Phos."
        assert "similarity_ratio" in comp

    def test_list_remedies(self, tmp_db_path: Path):
        mm = MateriaMedica(db_path=tmp_db_path)
        remedies = mm.list_remedies()
        assert isinstance(remedies, list)
        assert "Ars." in remedies

    def test_add_proving_text(self, tmp_db_path: Path):
        mm = MateriaMedica(db_path=tmp_db_path)
        rid = mm.add_proving_text("Test.", "Boericke", "mind", "Test proving text.")
        assert isinstance(rid, int)

    def test_get_sources_for_remedy(self, tmp_db_path: Path):
        mm = MateriaMedica(db_path=tmp_db_path)
        src = mm.get_sources_for_remedy("Ars.")
        assert isinstance(src, list)


# ── KingdomTaxonomy ────────────────────────────────────────────────────────────

class TestKingdomTaxonomy:
    def test_get_tags_plant(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        tags = kt.get_tags("Puls.")
        assert tags is not None
        assert tags["kingdom"] == "plant"

    def test_get_tags_mineral(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        tags = kt.get_tags("Ars.")
        assert tags is not None
        assert tags["kingdom"] == "mineral"
        assert "column" in tags

    def test_query_by_kingdom(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        plants = kt.query(kingdom="plant")
        assert "Puls." in plants

    def test_query_by_family(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        solanaceae = kt.query(family="Solanaceae")
        assert "Bell." in solanaceae

    def test_get_families(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        families = kt.get_families()
        assert "Solanaceae" in families

    def test_get_kingdom_counts(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        counts = kt.get_kingdom_counts()
        assert "plant" in counts
        assert "mineral" in counts
        assert counts["plant"] > 0

    def test_add_tag(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        kt.add_tag("NewRem.", "plant", family="Testaceae", group="Test-group", sub_group="test")
        tags = kt.get_tags("NewRem.")
        assert tags["kingdom"] == "plant"
        assert tags["family"] == "Testaceae"

    def test_compare_by_taxonomy(self, tmp_db_path: Path):
        kt = KingdomTaxonomy(db_path=tmp_db_path)
        comp = kt.compare_by_taxonomy("Puls.", "Bell.")
        assert comp["same_kingdom"] is True  # both plant
        assert comp["same_family"] is False  # different families
        assert "overlap_score" in comp


# ── BotanicalBridge ─────────────────────────────────────────────────────────────

class TestBotanicalBridge:
    def test_get_monograph(self, tmp_db_path: Path):
        bb = BotanicalBridge(db_path=tmp_db_path)
        mono = bb.get_monograph("Puls.")
        assert mono is not None
        assert mono.get("latin_name") == "Pulsatilla pratensis"

    def test_get_remedies_by_family(self, tmp_db_path: Path):
        bb = BotanicalBridge(db_path=tmp_db_path)
        sol = bb.get_remedies_by_family("Solanaceae")
        assert "Bell." in sol

    def test_who_covered_remedies(self, tmp_db_path: Path):
        bb = BotanicalBridge(db_path=tmp_db_path)
        covered = bb.who_covered_remedies()
        assert isinstance(covered, list)
        cham = next((c for c in covered if c.get("remedy") == "Cham."), None)
        if cham and cham is not None:
            assert cham.get("who_vol") == "Vol1"

    def test_search_common_name(self, tmp_db_path: Path):
        bb = BotanicalBridge(db_path=tmp_db_path)
        results = bb.search_common_name("coffee")
        assert any("Coff." in (r.get("remedy") or "") for r in results)

    def test_add_crossmap(self, tmp_db_path: Path):
        bb = BotanicalBridge(db_path=tmp_db_path)
        bb.add_crossmap("Test.", "Testus plantus", ["test plant"], who_vol="Vol99", family="Testaceae")
        mono = bb.get_monograph("Test.")
        assert mono is not None
        assert mono.get("latin_name") == "Testus plantus"


# ── GenomicHypothesis ──────────────────────────────────────────────────────────

class TestGenomicHypothesis:
    def test_register_snp(self, tmp_db_path: Path):
        gh = GenomicHypothesis(db_path=tmp_db_path)
        gh.register_snp("rs999999", "TEST", "T999", ["A", "G"], "test significance")
        snps = gh.list_snps()
        assert any(s["rs_id"] == "rs999999" for s in snps)

    def test_record_genotype_and_outcome(self, tmp_db_path: Path):
        gh = GenomicHypothesis(db_path=tmp_db_path)
        gh.record_genotype("pt-01", "rs1801133", "CT", source="23andMe")
        gh.record_outcome("pt-01", "rs1801133", "CT", "Nux-v.", responded=True, improvement_score=0.8)
        gt = gh.list_patient_genotypes("pt-01")
        assert any(g["rs_id"] == "rs1801133" for g in gt)

    def test_hypothesis_report(self, tmp_db_path: Path):
        gh = GenomicHypothesis(db_path=tmp_db_path)
        # Seed with enough data
        for i in range(4):
            gh.record_outcome(f"pt-{i}", "rs1801133", "CT", "Nux-v.", responded=True, improvement_score=0.7)
            gh.record_outcome(f"pt-{i}", "rs1801133", "TT", "Puls.", responded=False, improvement_score=0.2)
        report = gh.hypothesis_report("rs1801133", min_cases=1)
        assert report.get("gene") == "MTHFR"
        assert "hypotheses" in report

    def test_patient_guidance(self, tmp_db_path: Path):
        gh = GenomicHypothesis(db_path=tmp_db_path)
        gh.record_outcome("pt-01", "rs1801133", "CT", "Nux-v.", responded=True, improvement_score=0.8)
        guidance = gh.patient_guidance("pt-01", ["Nux-v.", "Puls."])
        assert isinstance(guidance, dict)
        assert guidance.get("pseudonym") == "pt-01"

    def test_get_genotype_frequency(self, tmp_db_path: Path):
        gh = GenomicHypothesis(db_path=tmp_db_path)
        gh.record_genotype("pt-01", "rs1801133", "CT")
        gh.record_genotype("pt-02", "rs1801133", "CT")
        gh.record_genotype("pt-03", "rs1801133", "CC")
        freq = gh.get_genotype_frequency("rs1801133")
        assert "CT" in freq
        assert freq["CT"]["count"] == 2


# ── FlashcardSRS ───────────────────────────────────────────────────────────────

class TestFlashcardSRS:
    def test_create_deck(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        deck_id = srs.create_deck("Test Deck", "description")
        assert deck_id.startswith("deck_")

    def test_add_card_and_get(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        deck_id = srs.create_deck("Test")
        cid = srs.add_card(deck_id, "Fear of death, burning pains", "Arsenicum Album", tags=["mind"])
        card = srs.get_card(cid)
        assert card["front"] == "Fear of death, burning pains"
        assert card["back"] == "Arsenicum Album"

    def test_due_cards(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        deck_id = srs.create_deck("Test")
        srs.add_card(deck_id, "Q1", "A1")
        dues = srs.get_due_cards(deck_id, include_new=True)
        assert len(dues) == 1

    def test_review_and_interval(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        deck_id = srs.create_deck("Test")
        cid = srs.add_card(deck_id, "Q", "A")
        # First review: quality 5
        result = srs.review(cid, quality=5)
        assert result["repetitions"] == 1
        assert result["interval"] == 1  # SM-2: first rep = 1 day
        # Second review: quality 5
        result = srs.review(cid, quality=5)
        assert result["repetitions"] == 2
        assert result["interval"] == 6  # SM-2: second rep = 6 days

    def test_deck_stats(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        deck_id = srs.create_deck("Test")
        srs.add_card(deck_id, "Q1", "A1")
        stats = srs.deck_stats(deck_id)
        assert stats["total_cards"] == 1
        assert stats["new_cards"] == 1

    def test_list_decks(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        srs.create_deck("Deck A")
        decks = srs.list_decks()
        assert any(d["name"] == "Deck A" for d in decks)

    def test_browse_cards(self, tmp_db_path: Path):
        srs = FlashcardSRS(db_path=tmp_db_path)
        deck_id = srs.create_deck("BrowseTest")
        srs.add_card(deck_id, "Q1", "A1")
        cards = srs.browse_cards(deck_id)
        assert len(cards) == 1
        assert cards[0]["front"] == "Q1"


# ── CronTasks ───────────────────────────────────────────────────────────────────

class TestCronTasks:
    def test_rebuild_vector_returns_dict(self, tmp_db_path: Path):
        ct = CronTasks(db_path=tmp_db_path)
        # Will fail gracefully if no rubrics.json in tmp path
        result = ct.rebuild_vector_if_stale(force=True)
        assert isinstance(result, dict)
        assert "rebuilt" in result

    def test_github_backup_dry_run(self, tmp_db_path: Path):
        ct = CronTasks(db_path=tmp_db_path)
        result = ct.github_backup(dry_run=True)
        assert result["success"] is True
        assert result["git_output"] == "DRY RUN"

    def test_check_followups_empty(self, tmp_db_path: Path):
        ct = CronTasks(db_path=tmp_db_path)
        alerts = ct.check_followups(days_ahead=7)
        # patients table won't exist in tmp db
        assert isinstance(alerts, list)

    def test_check_followups_with_data(self, tmp_db_path: Path):
        ct = CronTasks(db_path=tmp_db_path)
        conn = sqlite3.connect(str(tmp_db_path))
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, pseudonym TEXT)")
        c.execute("INSERT INTO patients (pseudonym) VALUES (?)", ("test_pt",))
        pid = c.lastrowid
        c.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY, patient_id INTEGER, remedy TEXT,
                potency TEXT, prescriber_ack TEXT, next_followup TEXT
            )
        """)
        followup_date = (datetime.now() + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO prescriptions (patient_id, remedy, potency, prescriber_ack, next_followup) VALUES (?,?,?,?,?)",
                  (pid, "Puls.", "30C", "ack", followup_date))
        conn.commit()
        conn.close()
        alerts = ct.check_followups(days_ahead=1)
        assert len(alerts) >= 1
        assert alerts[0]["remedy"] == "Puls."

    def test_mark_followup_sent(self, tmp_db_path: Path):
        ct = CronTasks(db_path=tmp_db_path)
        # Create a prescription
        conn = sqlite3.connect(str(tmp_db_path))
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS prescriptions (id INTEGER PRIMARY KEY, patient_id INTEGER, next_followup TEXT)")
        c.execute("INSERT INTO prescriptions (patient_id, next_followup) VALUES (?,?)", (1, datetime.now().strftime('%Y-%m-%d')))
        pid = c.lastrowid
        conn.commit()
        conn.close()
        ok = ct.mark_followup_sent(pid)
        assert ok is True
