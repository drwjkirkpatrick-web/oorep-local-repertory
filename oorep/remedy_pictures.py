"""
Remedy Pictures — Visual Remedy Reference Database

Visual reference for remedies: source images, constitutional types.
Scaffold — requires image sourcing.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class RemedyPictures:
    """
    Manage remedy image references.
    Stores metadata; actual images are external files.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.catalog_path = self.data_dir / "remedy_pictures.json"
        self.catalog: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.catalog_path.exists():
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(self.catalog, f, indent=2)

    def add_picture(self, remedy: str, image_path: str,
                    image_type: str = "source",  # source, constitution, proving, keynote
                    caption: str = "",
                    source_credit: str = "") -> Dict[str, Any]:
        if remedy not in self.catalog:
            self.catalog[remedy] = []
        pic = {
            "path": image_path,
            "type": image_type,
            "caption": caption,
            "source_credit": source_credit,
        }
        self.catalog[remedy].append(pic)
        self._save()
        return {"remedy": remedy, "picture": pic}

    def get_pictures(self, remedy: str) -> List[Dict[str, Any]]:
        return self.catalog.get(remedy, [])

    def list_remedies_with_pictures(self) -> List[str]:
        return sorted(self.catalog.keys())

    def get_picture_types(self) -> List[str]:
        return ["source", "constitution", "proving", "keynote"]

    def seed_sample_catalog(self) -> int:
        """Seed with sample entries for demonstration."""
        if not self.catalog:
            self.catalog = {
                "PULS": [
                    {"path": "images/pulsatilla_plant.jpg", "type": "source", "caption": "Pulsatilla pratensis — Pasque flower", "source_credit": "Wikipedia Commons"},
                    {"path": "images/puls_constitution.jpg", "type": "constitution", "caption": "Typical Pulsatilla constitution", "source_credit": "Classical Materia Medica"},
                ],
                "SULPH": [
                    {"path": "images/sulphur_crystal.jpg", "type": "source", "caption": "Sulphur crystal", "source_credit": "Wikipedia Commons"},
                ],
            }
            self._save()
            return 2
        return 0

    def get_stats(self) -> Dict[str, Any]:
        total = sum(len(v) for v in self.catalog.values())
        by_type = {}
        for pics in self.catalog.values():
            for p in pics:
                t = p.get("type", "unknown")
                by_type[t] = by_type.get(t, 0) + 1
        return {
            "remedies_with_pictures": len(self.catalog),
            "total_pictures": total,
            "by_type": by_type,
            "note": "Actual image files must be sourced separately. This catalog manages metadata only.",
        }
