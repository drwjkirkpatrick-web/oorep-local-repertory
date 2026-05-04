import json
from pathlib import Path

from oorep import ClinicalRubricMapper, HomeopathicRepertory


def _write_dataset(tmp_path: Path, duplicate_links: bool = False, no_remedy_best_match: bool = False):
    (tmp_path / "remedies.json").write_text(
        json.dumps([
            {"id": 1, "abbrev": "Ars.", "name": "Arsenicum Album"},
            {"id": 2, "abbrev": "Sulph.", "name": "Sulphur"},
        ]),
        encoding="utf-8",
    )
    (tmp_path / "remedies_by_abbrev.json").write_text(
        json.dumps({
            "Ars.": {"id": 1, "abbrev": "Ars.", "name": "Arsenicum Album"},
            "Sulph.": {"id": 2, "abbrev": "Sulph.", "name": "Sulphur"},
        }),
        encoding="utf-8",
    )
    rubrics = [
        {"id": 101, "source": "publicum", "fullpath": "Sleep, sleeplessness, waking after midnight", "path_parts": []},
        {"id": 102, "source": "publicum", "fullpath": "Stomach, thirst, small quantities", "path_parts": []},
        {"id": 103, "source": "publicum", "fullpath": "Mind, anxiety, health, about", "path_parts": []},
    ]
    if no_remedy_best_match:
        rubrics.insert(0, {"id": 104, "source": "publicum", "fullpath": "Mind, anxiety, health, about, exact but no remedies", "path_parts": []})
    (tmp_path / "rubrics.json").write_text(json.dumps(rubrics), encoding="utf-8")
    search_index = {
        "sleep": [101], "sleeplessness": [101], "waking": [101], "midnight": [101],
        "stomach": [102], "thirst": [102], "small": [102], "quantities": [102],
        "mind": [103], "anxiety": [103], "health": [103], "about": [103],
    }
    if no_remedy_best_match:
        for word in ["mind", "anxiety", "health", "about", "exact", "remedies"]:
            search_index.setdefault(word, []).insert(0, 104)
    (tmp_path / "rubric_search_index.json").write_text(
        json.dumps(search_index),
        encoding="utf-8",
    )
    thirst_links = [{"rubric_id": 102, "remedy_id": 1, "weight": 3}, {"rubric_id": 102, "remedy_id": 2, "weight": 1}]
    if duplicate_links:
        thirst_links.append({"rubric_id": 102, "remedy_id": 1, "weight": 3})
    rubric_to_remedies = {
        "101": [{"rubric_id": 101, "remedy_id": 2, "weight": 3}],
        "102": thirst_links,
        "103": [{"rubric_id": 103, "remedy_id": 1, "weight": 2}],
    }
    if no_remedy_best_match:
        rubric_to_remedies["104"] = []
    (tmp_path / "rubric_to_remedies.json").write_text(
        json.dumps(rubric_to_remedies),
        encoding="utf-8",
    )


def test_normalize_expands_patient_sleep_language():
    mapper = ClinicalRubricMapper(repertory=None)

    normalized = mapper.normalize_symptom("can't sleep after 3am")

    assert "sleeplessness" in normalized.expanded_query
    assert "waking" in normalized.expanded_query
    assert "midnight" in normalized.expanded_query


def test_suggest_candidates_returns_reviewable_rubrics(tmp_path):
    _write_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))
    mapper = ClinicalRubricMapper(rep)

    candidates = mapper.suggest_candidates("thirst for little sips", limit=3, retrieval="hybrid")

    assert candidates[0]["rubric_id"] == 102
    assert candidates[0]["review_status"] == "pending"
    assert candidates[0]["query_original"] == "thirst for little sips"
    assert "small quantities" in candidates[0]["rubric"].lower()


def test_suggest_candidates_excludes_rubrics_without_remedy_links(tmp_path):
    _write_dataset(tmp_path, no_remedy_best_match=True)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))
    mapper = ClinicalRubricMapper(rep)

    candidates = mapper.suggest_candidates("anxiety about health exact", limit=3, retrieval="lexical")

    assert candidates
    assert all(c["rubric_id"] != 104 for c in candidates)
    assert candidates[0]["remedy_count"] > 0


def test_repertorize_accepted_rubrics_uses_only_classical_grades(tmp_path):
    _write_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))
    mapper = ClinicalRubricMapper(rep)

    result = mapper.repertorize_accepted_rubrics([
        {"rubric_id": 102, "query_original": "thirst small sips"},
        {"rubric_id": 103, "query_original": "anxiety about health"},
    ], top_n=2)

    assert result[0]["abbrev"] == "Ars."
    assert result[0]["score"] == 5
    assert result[0]["match_count"] == 2
    assert result[1]["abbrev"] == "Sulph."
    assert result[1]["score"] == 1


def test_repertorize_accepted_rubrics_deduplicates_repeated_remedy_links(tmp_path):
    _write_dataset(tmp_path, duplicate_links=True)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))
    mapper = ClinicalRubricMapper(rep)

    result = mapper.repertorize_accepted_rubrics([
        {"rubric_id": 102, "query_original": "thirst small sips"},
    ], top_n=2)

    assert result[0]["abbrev"] == "Ars."
    assert result[0]["score"] == 3
    assert len(result[0]["matches"]) == 1


def test_default_repertorize_routes_case_symptoms_through_clinical_mapper(tmp_path):
    _write_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))

    result = rep.repertorize(["little sips"], top_n=2, retrieval="lexical", rubrics_per_symptom=3)

    assert result[0]["abbrev"] == "Ars."
    assert result[0]["score"] == 3
    assert result[0]["matches"][0]["query_expanded"]
    assert "small quantities" in result[0]["matches"][0]["query_expanded"]
