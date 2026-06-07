"""
Author / Provenance Filter — Filter Repertory by Source Authority

Filter repertory view to show only rubrics from specific provings
or authors, or exclude additions by specific authors.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class AuthorFilter:
    """
    Filter rubric visibility by source author/proving.
    Leverages the BibliographicEngine source registry.
    """

    AUTHOR_RANGES: Dict[str, Dict[str, Any]] = {
        "Hahnemann": {"era": "1796-1843"},
        "Hering": {"era": "1830-1880"},
        "Allen": {"era": "1870-1900"},
        "Clarke": {"era": "1880-1920"},
        "Kent": {"era": "1890-1910"},
        "Boenninghausen": {"era": "1830-1860"},
        "Nash": {"era": "1880-1910"},
        "Boger": {"era": "1900-1930"},
        "Herscu": {"era": "1980-present"},
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.active_filters: Dict[str, Any] = {}
        self.config_path = self.data_dir / "author_filter_config.json"
        self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.active_filters = json.load(f)

    def _save_config(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.active_filters, f, indent=2)

    def include_only(self, authors: List[str]) -> Dict[str, Any]:
        """Show rubrics from these authors only."""
        self.active_filters = {"mode": "include", "authors": authors}
        self._save_config()
        return {"mode": "include", "authors": authors, "n_authors": len(authors)}

    def exclude(self, authors: List[str]) -> Dict[str, Any]:
        """Hide rubrics from these authors."""
        self.active_filters = {"mode": "exclude", "authors": authors}
        self._save_config()
        return {"mode": "exclude", "authors": authors, "n_authors": len(authors)}

    def filter_rubric(self, rubric_sources: List[str]) -> bool:
        """
        Returns True if rubric should be VISIBLE given active filters.
        """
        if not self.active_filters:
            return True
        mode = self.active_filters.get("mode", "include")
        authors = set(self.active_filters.get("authors", []))
        rubric_set = set(rubric_sources)
        if mode == "include":
            return bool(rubric_set & authors)
        else:
            return not bool(rubric_set & authors)

    def get_active_filter(self) -> Optional[Dict[str, Any]]:
        return self.active_filters if self.active_filters else None

    def clear_filter(self) -> Dict[str, Any]:
        self.active_filters = {}
        self._save_config()
        return {"status": "cleared"}

    def list_available_authors(self) -> List[Dict[str, Any]]:
        return [
            {"name": name, "era": info["era"], "status": "available"}
            for name, info in self.AUTHOR_RANGES.items()
        ]
