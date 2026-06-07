"""
Mobile App Native — Native Mobile Repertory API

API designed for native iOS/Android app consumption.
Lightweight JSON responses, offline-first data structure.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class MobileAppNative:
    """
    API layer optimized for mobile app consumption.
    Returns compact, cacheable responses.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def search_rubrics_compact(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Compact rubric search results for mobile."""
        try:
            from oorep.homeopathic_repertory import HomeopathicRepertory
            repo = HomeopathicRepertory(data_dir=str(self.data_dir))
            results = repo.search_rubrics(query)[:top_n]
            # Compact: only ID, path, top remedy count
            return [
                {
                    "id": r.get("rubric_id"),
                    "path": r.get("path", ""),
                    "n_remedies": len(r.get("remedies", {})),
                    "top_remedy": self._top_remedy(r.get("remedies", {})),
                }
                for r in results
            ]
        except Exception:
            return []

    def get_remedy_summary(self, remedy: str) -> Dict[str, Any]:
        """Compact remedy summary for mobile."""
        return {
            "remedy": remedy,
            "name": remedy,  # Would lookup full name
            "keynotes": ["keynote1", "keynote2", "keynote3"],  # Placeholder
            "modalities": ["worse cold", "better motion"],  # Placeholder
            "kingdom": "unknown",
            "source": "mobile_compact",
        }

    def get_offline_bundle(self) -> Dict[str, Any]:
        """
        Generate data bundle for offline mobile use.
        Top 500 remedies, top 1000 rubrics, etc.
        """
        return {
            "bundle_type": "offline_mobile",
            "remedies": 500,
            "rubrics": 1000,
            "size_estimate_mb": 5,
            "last_updated": "2026-06-07",
            "note": "Offline bundle generation requires data subset selection logic.",
        }

    @staticmethod
    def _top_remedy(remedies: Dict[str, Any]) -> Optional[str]:
        if not remedies:
            return None
        sorted_rems = sorted(remedies.items(), key=lambda x: x[1].get("grade", 1), reverse=True)
        return sorted_rems[0][0] if sorted_rems else None

    def get_api_version(self) -> Dict[str, Any]:
        return {
            "version": "1.0.0-mobile",
            "formats": ["compact", "full"],
            "compression": "gzip",
            "cache_ttl_seconds": 3600,
        }
