"""
Comprehensive tests for bibliographic_engine.py (Feature #26)

Covers:
  - Database initialization and classical source seeding
  - Source CRUD (register, get, list, delete)
  - Citation link management (rubric↔source, remedy↔source)
  - Retrieval: get_rubric_citations, get_remedy_citations, get_source_citations
  - Formatting: Vancouver, BibTeX, plain
  - Bibliography generation for rubric/remedy sets
  - Footnote generation
  - Coverage statistics
  - Edge cases: missing sources, empty citations, duplicate links
"""

import sqlite3
import pytest
from pathlib import Path
from oorep.bibliographic_engine import BibliographicEngine, Source


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_engine(tmp_path: Path):
    """Engine with isolated temp database."""
    db = tmp_path / "biblio_test.db"
    return BibliographicEngine(db_path=db)


# ── DB Initialization ──────────────────────────────────────────────────────────

class TestInit:

    def test_db_created(self, tmp_path: Path):
        db = tmp_path / "new_biblio.db"
        engine = BibliographicEngine(db_path=db)
        assert db.exists()

    def test_classical_sources_seeded(self, fresh_engine):
        sources = fresh_engine.list_sources()
        assert len(sources) >= 12  # All classical sources pre-loaded
        ids = {s.source_id for s in sources}
        assert "hahnemann_1810" in ids
        assert "kent_1900" in ids
        assert "oorep_2024" in ids

    def test_sources_by_type(self, fresh_engine):
        treatises = fresh_engine.list_sources(type_filter="treatise")
        mms = fresh_engine.list_sources(type_filter="materia_medica")
        reps = fresh_engine.list_sources(type_filter="repertory")
        assert len(treatises) >= 2
        assert len(mms) >= 4
        assert len(reps) >= 2


# ── Source CRUD ────────────────────────────────────────────────────────────────

class TestSourceCRUD:

    def test_register_and_get(self, fresh_engine):
        ok = fresh_engine.register_source(
            source_id="test_2024",
            title="Test Materia Medica",
            author="Dr. Test",
            year=2024,
            edition="1st",
            publisher="Test Press",
            type="materia_medica",
        )
        assert ok is True

        src = fresh_engine.get_source("test_2024")
        assert src is not None
        assert src.title == "Test Materia Medica"
        assert src.author == "Dr. Test"
        assert src.year == 2024
        assert src.type == "materia_medica"

    def test_list_all(self, fresh_engine):
        all_src = fresh_engine.list_sources()
        assert len(all_src) >= 12

    def test_delete_source(self, fresh_engine):
        fresh_engine.register_source("del_me", "Del", "D", 2000)
        assert fresh_engine.get_source("del_me") is not None
        ok = fresh_engine.delete_source("del_me")
        assert ok is True
        assert fresh_engine.get_source("del_me") is None

    def test_get_missing_source(self, fresh_engine):
        assert fresh_engine.get_source("nonexistent") is None


# ── Citation Links ───────────────────────────────────────────────────────────

class TestCitationLinks:

    def test_link_rubric_to_source(self, fresh_engine):
        fresh_engine.link_rubric_to_source(rubric_id=12345, source_id="kent_1900", page="247")
        cites = fresh_engine.get_rubric_citations(12345)
        assert len(cites) == 1
        assert cites[0]["source_id"] == "kent_1900"
        assert cites[0]["page"] == "247"
        assert "Kent" in cites[0]["author"]

    def test_link_remedy_to_source(self, fresh_engine):
        fresh_engine.link_remedy_to_source(remedy_abbrev="ARS", source_id="allen_1874", page="120")
        cites = fresh_engine.get_remedy_citations("ARS")
        assert len(cites) == 1
        assert cites[0]["source_id"] == "allen_1874"
        assert cites[0]["page"] == "120"

    def test_multiple_links_per_rubric(self, fresh_engine):
        fresh_engine.link_rubric_to_source(999, "hahnemann_1810", page="1")
        fresh_engine.link_rubric_to_source(999, "kent_1900", page="100")
        fresh_engine.link_rubric_to_source(999, "oorep_2024")
        cites = fresh_engine.get_rubric_citations(999)
        assert len(cites) == 3
        ids = {c["source_id"] for c in cites}
        assert ids == {"hahnemann_1810", "kent_1900", "oorep_2024"}

    def test_empty_citations(self, fresh_engine):
        assert fresh_engine.get_rubric_citations(77777) == []
        assert fresh_engine.get_remedy_citations("XYZ") == []


# ── Source ↔ Citation reverse lookup ──────────────────────────────────────────

class TestSourceCitations:

    def test_get_source_citations(self, fresh_engine):
        fresh_engine.link_rubric_to_source(100, "herscu_1996", page="45")
        fresh_engine.link_remedy_to_source("STRAM", "herscu_1996", page="50")
        result = fresh_engine.get_source_citations("herscu_1996")
        assert len(result["rubrics"]) == 1
        assert len(result["remedies"]) == 1
        assert result["rubrics"][0]["rubric_id"] == 100
        assert result["remedies"][0]["remedy_abbrev"] == "STRAM"


# ── Formatting ───────────────────────────────────────────────────────────────

class TestFormatting:

    def test_vancouver_format(self, fresh_engine):
        src = fresh_engine.get_source("kent_1900")
        fmt = fresh_engine.format_vancouver(src)
        assert "Kent, James Tyler." in fmt
        assert "1900." in fmt
        assert "Lectures on Homeopathic Materia Medica" in fmt

    def test_bibtex_format(self, fresh_engine):
        src = fresh_engine.get_source("hahnemann_1810")
        fmt = fresh_engine.format_bibtex(src)
        assert "@book{hahnemann_1810," in fmt
        assert "Hahnemann, Samuel" in fmt
        assert "1810" in fmt

    def test_plain_format(self, fresh_engine):
        src = fresh_engine.get_source("herscu_1996")
        fmt = fresh_engine.format_plain(src)
        assert "Herscu, Paul." in fmt
        assert "Stramonium" in fmt
        assert "1996" in fmt

    def test_format_source_dispatch(self, fresh_engine):
        vanc = fresh_engine.format_source("kent_1900", style="vancouver")
        bib = fresh_engine.format_source("kent_1900", style="bibtex")
        plain = fresh_engine.format_source("kent_1900", style="plain")
        assert vanc is not None and "Kent" in vanc
        assert bib is not None and "@book" in bib
        assert plain is not None and "'Lectures" in plain

    def test_format_missing_source(self, fresh_engine):
        assert fresh_engine.format_source("missing", style="vancouver") is None


# ── Bibliography Generation ──────────────────────────────────────────────────

class TestBibliography:

    def test_bibliography_for_rubric(self, fresh_engine):
        fresh_engine.link_rubric_to_source(500, "kent_1897", page="10")
        fresh_engine.link_rubric_to_source(500, "allen_1874", page="20")
        bib = fresh_engine.format_bibliography(rubric_ids=[500], style="vancouver")
        assert bib["style"] == "vancouver"
        assert bib["entry_count"] >= 3  # kent + allen + oorep (always included)
        ids = {e["source_id"] for e in bib["entries"]}
        assert "kent_1897" in ids
        assert "allen_1874" in ids
        assert "oorep_2024" in ids

    def test_bibliography_for_remedy(self, fresh_engine):
        fresh_engine.link_remedy_to_source("PULS", "kent_1900", page="300")
        bib = fresh_engine.format_bibliography(remedies=["PULS"], style="vancouver")
        assert bib["entry_count"] >= 2  # kent + oorep
        ids = {e["source_id"] for e in bib["entries"]}
        assert "kent_1900" in ids
        assert "oorep_2024" in ids

    def test_bibliography_empty(self, fresh_engine):
        bib = fresh_engine.format_bibliography(style="vancouver")
        assert bib["entry_count"] == 1  # OOREP citation always included
        assert bib["entries"][0]["source_id"] == "oorep_2024"


# ── Footnotes ─────────────────────────────────────────────────────────────────

class TestFootnotes:

    def test_footnote_for_rubric(self, fresh_engine):
        fresh_engine.link_rubric_to_source(200, "kent_1900", page="247")
        fn = fresh_engine.footnote_for_rubric(200, style="vancouver")
        assert fn is not None
        assert "Kent" in fn
        assert "1900" in fn
        assert "247" in fn

    def test_footnote_missing(self, fresh_engine):
        assert fresh_engine.footnote_for_rubric(99999) is None


# ── Coverage Statistics ───────────────────────────────────────────────────────

class TestCoverageStats:

    def test_stats_structure(self, fresh_engine):
        stats = fresh_engine.get_source_coverage_stats()
        assert stats["total_sources"] >= 12
        assert "by_type" in stats
        assert stats["total_citation_links"] == 0  # Fresh engine, no links yet

    def test_stats_after_links(self, fresh_engine):
        fresh_engine.link_rubric_to_source(1, "kent_1900")
        fresh_engine.link_rubric_to_source(2, "kent_1900")
        fresh_engine.link_remedy_to_source("ARS", "kent_1900")
        stats = fresh_engine.get_source_coverage_stats()
        assert stats["total_citation_links"] == 3
        assert stats["rubrics_with_citations"] == 2
        assert stats["remedies_with_citations"] == 1


# ── Feature Overview ─────────────────────────────────────────────────────────

class TestFeatureOverview:

    def test_overview(self, fresh_engine):
        ov = fresh_engine.get_feature_overview()
        assert ov["feature_id"] == 26
        assert ov["feature_name"] == "Bibliographic Citation Engine"
        assert ov["classical_sources_preloaded"] >= 12
        assert "source_registration" in ov["supports"]
        assert "bibliography_generation" in ov["supports"]
