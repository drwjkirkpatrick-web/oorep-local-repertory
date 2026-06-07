"""
Multi-Language Display — Multilingual Rubric Rendering

Display rubrics in multiple languages simultaneously.
Requires translation data for each rubric.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class MultiLanguageDisplay:
    """
    Show rubrics in multiple languages.
    Current languages: English, German, French, Spanish (placeholder data).
    """

    SUPPORTED_LANGUAGES = ["en", "de", "fr", "es", "it", "nl"]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.translations_path = self.data_dir / "rubric_translations.json"
        self._translations: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.translations_path.exists():
            with open(self.translations_path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)

    def get_rubric_translations(self, rubric_id: int) -> Dict[str, Any]:
        """Get all language versions of a rubric."""
        return self._translations.get(str(rubric_id), {
            "rubric_id": rubric_id,
            "translations": {},
            "note": "No translations available. English is primary.",
        })

    def display_multilingual(self, rubric_id: int,
                             languages: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Display rubric in multiple languages side-by-side.
        """
        langs = languages or ["en", "de"]
        trans = self.get_rubric_translations(rubric_id)
        available = trans.get("translations", {})

        display = {}
        for lang in langs:
            if lang in available:
                display[lang] = available[lang]
            else:
                display[lang] = {
                    "path": available.get("en", {}).get("path", "Not available"),
                    "note": f"Translation to {lang} not yet available.",
                }

        return {
            "rubric_id": rubric_id,
            "display": display,
            "languages_requested": langs,
            "languages_available": list(available.keys()),
        }

    def add_translation(self, rubric_id: int, language: str,
                        path: str, translator: str = "") -> Dict[str, Any]:
        """Add a translation for a rubric."""
        if str(rubric_id) not in self._translations:
            self._translations[str(rubric_id)] = {"translations": {}}
        self._translations[str(rubric_id)]["translations"][language] = {
            "path": path,
            "translator": translator,
        }
        with open(self.translations_path, "w", encoding="utf-8") as f:
            json.dump(self._translations, f, indent=2)
        return {"rubric_id": rubric_id, "language": language, "status": "added"}

    def seed_sample_translations(self) -> int:
        """Seed with sample translations for demonstration."""
        samples = {
            "1": {
                "translations": {
                    "en": {"path": "Mind; anxiety"},
                    "de": {"path": "Geist; Angst"},
                    "fr": {"path": "Esprit; anxiété"},
                    "es": {"path": "Mente; ansiedad"},
                }
            }
        }
        if not self._translations:
            self._translations = samples
            with open(self.translations_path, "w", encoding="utf-8") as f:
                json.dump(self._translations, f, indent=2)
            return 1
        return 0

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._translations)
        by_lang = {}
        for rid, data in self._translations.items():
            for lang in data.get("translations", {}):
                by_lang[lang] = by_lang.get(lang, 0) + 1
        return {
            "total_rubrics_with_translations": total,
            "by_language": by_lang,
            "note": "Full translation requires community contribution or professional translation service.",
        }
