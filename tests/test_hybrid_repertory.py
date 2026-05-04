import json
from pathlib import Path

from oorep.homeopathic_repertory import HomeopathicRepertory


class FakeVector:
    def __init__(self, by_query):
        self.by_query = by_query

    def search(self, query, top_k=20):
        return self.by_query.get(query, [])[:top_k]


def _write_dataset(tmp_path: Path):
    (tmp_path / "remedies.json").write_text(
        json.dumps(
            [
                {"id": 1, "abbrev": "Rem-A", "name": "Remedy A"},
                {"id": 2, "abbrev": "Rem-B", "name": "Remedy B"},
            ]
        ),
        encoding="utf-8",
    )

    (tmp_path / "remedies_by_abbrev.json").write_text(
        json.dumps(
            {
                "Rem-A": {"id": 1, "abbrev": "Rem-A", "name": "Remedy A"},
                "Rem-B": {"id": 2, "abbrev": "Rem-B", "name": "Remedy B"},
            }
        ),
        encoding="utf-8",
    )

    rubrics = [
        {"id": 101, "source": "publicum", "fullpath": "Head, pain, morning", "path_parts": ["Head", "pain", "morning"]},
        {"id": 102, "source": "publicum", "fullpath": "Stomach, thirst, evening", "path_parts": ["Stomach", "thirst", "evening"]},
    ]
    (tmp_path / "rubrics.json").write_text(json.dumps(rubrics), encoding="utf-8")

    search_index = {
        "head": [101],
        "pain": [101],
        "morning": [101],
        "stomach": [102],
        "thirst": [102],
        "evening": [102],
    }
    (tmp_path / "rubric_search_index.json").write_text(json.dumps(search_index), encoding="utf-8")

    rubric_to_remedies = {
        "101": [
            {"rubric_id": 101, "remedy_id": 1, "weight": 3},
            {"rubric_id": 101, "remedy_id": 2, "weight": 1},
        ],
        "102": [
            {"rubric_id": 102, "remedy_id": 1, "weight": 1},
            {"rubric_id": 102, "remedy_id": 2, "weight": 4},
        ],
    }
    (tmp_path / "rubric_to_remedies.json").write_text(json.dumps(rubric_to_remedies), encoding="utf-8")


def test_hybrid_search_merges_lexical_and_vector(tmp_path):
    _write_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))
    rep._vector = FakeVector(
        {
            "head pain": [
                {"rubric_id": 102, "fullpath": "Stomach, thirst, evening", "source": "publicum", "score": 0.9}
            ]
        }
    )

    results = rep.search_rubrics_hybrid("head pain", limit=5)

    ids = [r["id"] for r in results]
    assert 101 in ids
    assert 102 in ids


def test_repertorize_hybrid_preserves_classical_grade_scoring(tmp_path):
    _write_dataset(tmp_path)
    rep = HomeopathicRepertory(data_dir=str(tmp_path))
    rep._vector = FakeVector(
        {
            "head": [{"rubric_id": 101, "fullpath": "Head, pain, morning", "source": "publicum", "score": 0.99}],
            "thirst": [{"rubric_id": 102, "fullpath": "Stomach, thirst, evening", "source": "publicum", "score": 0.99}],
        }
    )

    results = rep.repertorize(["head", "thirst"], top_n=2, retrieval="hybrid", rubrics_per_symptom=1)

    # Classical scoring should be sum of remedy grades from selected rubrics, not retrieval confidence.
    assert results[0]["abbrev"] == "Rem-B"
    assert results[0]["score"] == 5
    assert results[1]["abbrev"] == "Rem-A"
    assert results[1]["score"] == 4
