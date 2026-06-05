"""
Tests for clipboard_manager.py — Multi-Clipboard Symptom Collection
"""

import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Ensure imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "oorep"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clipboard_manager import ClipboardManager, ClipboardType, Clipboard


def test_create_and_list_clipboards():
    """Test creating and listing clipboards."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test_clipboards.db"
        cm = ClipboardManager(db_path=db)

        cb1 = cm.create_clipboard("morning_headache", ClipboardType.INCLUSION, "Mrs J case")
        cb2 = cm.create_clipboard("eliminate_mercury", ClipboardType.ELIMINATION)
        cb3 = cm.create_clipboard("optional_thirst", ClipboardType.OPTIONAL)

        all_cbs = cm.list_clipboards()
        assert len(all_cbs) == 3
        assert all_cbs[0].name == "optional_thirst"  # Most recent first

        # Check retrieval by ID
        got = cm.get_clipboard(cb1.id)
        assert got is not None
        assert got.name == "morning_headache"
        assert got.type == "inclusion"
        assert got.description == "Mrs J case"
        assert got.rubric_count == 0

        print("✓ create and list clipboards")


def test_add_remove_rubrics():
    """Test adding and removing rubrics from a clipboard."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)
        cb = cm.create_clipboard("test_cb")

        # Add rubrics
        r1 = cm.add_rubric(cb.id, rubric_id=12345, rubric_fullpath="Mind; anxiety", source="kent", remedy_weight=3, user_weight=1.5, notes="strong keynote")
        r2 = cm.add_rubric(cb.id, rubric_id=67890, rubric_fullpath="Head; pain; morning", source="kent", remedy_weight=2)

        rubrics = cm.get_rubrics(cb.id)
        assert len(rubrics) == 2
        assert rubrics[0].rubric_id == 12345
        assert rubrics[0].user_weight == 1.5

        # Check rubric_count updated
        cb_refreshed = cm.get_clipboard(cb.id)
        assert cb_refreshed.rubric_count == 2

        # Remove one
        removed = cm.remove_rubric(cb.id, rubric_id=12345)
        assert removed is True
        assert len(cm.get_rubrics(cb.id)) == 1
        assert cm.get_clipboard(cb.id).rubric_count == 1

        print("✓ add and remove rubrics")


def test_user_weight_adjustment():
    """Test adjusting user weights on rubric entries."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)
        cb = cm.create_clipboard("weighted")
        entry = cm.add_rubric(cb.id, rubric_id=111, remedy_weight=3, user_weight=1.0)

        # Boost the weight
        ok = cm.set_user_weight(entry.id, 2.0)
        assert ok is True

        rubrics = cm.get_rubrics(cb.id)
        assert rubrics[0].user_weight == 2.0

        print("✓ user weight adjustment")


def test_duplicate_clipboard():
    """Test duplicating a clipboard with all rubrics."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)
        cb = cm.create_clipboard("original")
        cm.add_rubric(cb.id, rubric_id=1001, rubric_fullpath="A", remedy_weight=3)
        cm.add_rubric(cb.id, rubric_id=1002, rubric_fullpath="B", remedy_weight=2)

        clone = cm.duplicate_clipboard(cb.id, "original_clone")
        assert clone is not None
        assert clone.name == "original_clone"
        assert clone.type == "inclusion"

        clone_rubrics = cm.get_rubrics(clone.id)
        assert len(clone_rubrics) == 2
        assert clone_rubrics[0].rubric_fullpath == "A"

        print("✓ duplicate clipboard")


def test_delete_clipboard():
    """Test deleting a clipboard cascades rubrics."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)
        cb = cm.create_clipboard("to_delete")
        cm.add_rubric(cb.id, rubric_id=999)

        deleted = cm.delete_clipboard(cb.id)
        assert deleted is True
        assert cm.get_clipboard(cb.id) is None

        # Verify rubrics table is clean
        conn = sqlite3.connect(str(db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clipboard_rubrics WHERE clipboard_id = ?", (cb.id,))
        assert cursor.fetchone()[0] == 0
        conn.close()

        print("✓ delete clipboard cascades rubrics")


def test_analysis_with_mock_repertory():
    """Test analysis logic with a minimal mock repertory."""
    class MockRepertory:
        def get_remedies_for_rubric(self, rubric_id):
            # Return predictable remedies for known rubric IDs
            mapping = {
                1: [{"abbrev": "Ars.", "name": "Arsenicum album", "weight": 3},
                    {"abbrev": "Nux-v.", "name": "Nux vomica", "weight": 2}],
                2: [{"abbrev": "Ars.", "name": "Arsenicum album", "weight": 2},
                    {"abbrev": "Puls.", "name": "Pulsatilla", "weight": 1}],
                3: [{"abbrev": "Merc.", "name": "Mercurius", "weight": 3}],
            }
            return mapping.get(rubric_id, [])

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)

        # Inclusion clipboard
        inc = cm.create_clipboard("symptoms", ClipboardType.INCLUSION)
        cm.add_rubric(inc.id, rubric_id=1, remedy_weight=3)
        cm.add_rubric(inc.id, rubric_id=2, remedy_weight=2)

        # Elimination clipboard
        elim = cm.create_clipboard("exclude", ClipboardType.ELIMINATION)
        cm.add_rubric(elim.id, rubric_id=3, remedy_weight=3)  # Merc. appears in rubric 3

        mock_rep = MockRepertory()
        result = cm.analyze([inc.id, elim.id], top_n=10, repertory=mock_rep)

        assert result["eliminated_count"] == 1
        assert "Merc." in result["eliminated_remedies"]

        # Ars. should score 3+2=5 (both rubrics contribute)
        # Nux-v. should score 2
        # Puls. should score 1
        remedies = result["remedies"]
        assert len(remedies) == 3
        assert remedies[0]["abbrev"] == "Ars."
        assert remedies[0]["score"] == 5.0
        assert remedies[1]["abbrev"] == "Nux-v."
        assert remedies[1]["score"] == 2.0
        assert remedies[2]["abbrev"] == "Puls."
        assert remedies[2]["score"] == 1.0

        print("✓ analysis with inclusion + elimination")


def test_analysis_optional_weighting():
    """Test that optional clipboards apply 0.5 multiplier."""
    class MockRepertory:
        def get_remedies_for_rubric(self, rubric_id):
            if rubric_id == 10:
                return [{"abbrev": "Ars.", "name": "Arsenicum", "weight": 4}]
            if rubric_id == 11:
                return [{"abbrev": "Ars.", "name": "Arsenicum", "weight": 4}]
            return []

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)

        inc = cm.create_clipboard("main", ClipboardType.INCLUSION)
        cm.add_rubric(inc.id, rubric_id=10, remedy_weight=4)

        opt = cm.create_clipboard("maybe", ClipboardType.OPTIONAL)
        cm.add_rubric(opt.id, rubric_id=11, remedy_weight=4)

        mock_rep = MockRepertory()
        result = cm.analyze([inc.id, opt.id], top_n=10, repertory=mock_rep)

        # Ars. should get 4 from inclusion + 2 from optional = 6
        assert result["remedies"][0]["score"] == 6.0

        print("✓ optional clipboard 0.5 multiplier")


def test_quick_add_search_results():
    """Test bulk-adding rubrics from search results."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cm = ClipboardManager(db_path=db)
        cb = cm.create_clipboard("bulk")

        search_results = [
            {"id": 100, "fullpath": "Mind; anxiety", "source": "kent"},
            {"id": 200, "fullpath": "Head; pain", "source": "kent"},
            {"id": 300, "fullpath": "Stomach; nausea"},
        ]
        added = cm.quick_add_search_results(cb.id, search_results)
        assert added == 3
        assert cm.get_clipboard(cb.id).rubric_count == 3

        print("✓ quick add search results")


def run_all():
    test_create_and_list_clipboards()
    test_add_remove_rubrics()
    test_user_weight_adjustment()
    test_duplicate_clipboard()
    test_delete_clipboard()
    test_analysis_with_mock_repertory()
    test_analysis_optional_weighting()
    test_quick_add_search_results()
    print("\n" + "=" * 50)
    print("All clipboard_manager tests passed ✓")
    print("=" * 50)


if __name__ == "__main__":
    run_all()
