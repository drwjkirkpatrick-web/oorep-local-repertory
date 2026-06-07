"""
Sensation Method Integration — Sankaran-Style Kingdom/Source/Sensation

Integrate Dr. Rajan Sankaran's Sensation Method:
Kingdom → Sub-kingdom → Source → Sensation → Miasm
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class SensationMethodIntegration:
    """
    Map remedies to Sankaran's sensation method taxonomy.
    Kingdom: Animal, Plant, Mineral, Nosode, Imponderable
    """

    KINGDOMS = ["animal", "plant", "mineral", "nosode", "imponderable", "sarcode"]

    # Simplified mappings (would need comprehensive Sankaran data)
    SENSATION_MAPPINGS: Dict[str, Dict[str, Any]] = {
        "LYC": {"kingdom": "plant", "family": "Ranunculaceae", "sensation": "being small, shrinking", "miasm": "psora"},
        "PULS": {"kingdom": "plant", "family": "Ranunculaceae", "sensation": "changeable, yielding", "miasm": "psora"},
        "ARS": {"kingdom": "mineral", "family": "Metal", "sensation": "insecurity, impending doom", "miasm": "syphilis"},
        "MERC": {"kingdom": "mineral", "family": "Metal", "sensation": "instability, shifting", "miasm": "sycosis"},
        "TARENT": {"kingdom": "animal", "family": "Spider", "sensation": "hurry, restless, trapped", "miasm": "tubercular"},
        "LACH": {"kingdom": "animal", "family": "Snake", "sensation": "constriction, suffocation", "miasm": "sycosis"},
        "SIL": {"kingdom": "mineral", "family": "Silica", "sensation": "fragility, need for support", "miasm": "psora"},
        "AURUM": {"kingdom": "mineral", "family": "Metal", "sensation": "burden, heaviness", "miasm": "syphilis"},
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.custom_mappings_path = self.data_dir / "sensation_mappings.json"
        self._custom: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.custom_mappings_path.exists():
            with open(self.custom_mappings_path, "r", encoding="utf-8") as f:
                self._custom = json.load(f)

    def get_sensation_profile(self, remedy: str) -> Dict[str, Any]:
        """Get Sankaran-style profile for a remedy."""
        # Check custom first, then built-in
        profile = self._custom.get(remedy) or self.SENSATION_MAPPINGS.get(remedy)
        if profile:
            return {"remedy": remedy, **profile, "source": "custom" if remedy in self._custom else "built_in"}
        return {
            "remedy": remedy,
            "kingdom": "unknown",
            "note": "No sensation method mapping available. Consider classical repertorization.",
        }

    def suggest_by_sensation(self, sensation: str) -> List[Dict[str, Any]]:
        """Find remedies matching a sensation description."""
        matches = []
        all_mappings = {**self.SENSATION_MAPPINGS, **self._custom}
        for remedy, profile in all_mappings.items():
            if sensation.lower() in profile.get("sensation", "").lower():
                matches.append({"remedy": remedy, **profile})
        return matches

    def add_custom_mapping(self, remedy: str, kingdom: str, family: str,
                         sensation: str, miasm: str) -> Dict[str, Any]:
        self._custom[remedy] = {
            "kingdom": kingdom,
            "family": family,
            "sensation": sensation,
            "miasm": miasm,
        }
        with open(self.custom_mappings_path, "w", encoding="utf-8") as f:
            json.dump(self._custom, f, indent=2)
        return {"remedy": remedy, "status": "custom mapping added"}

    def list_mapped_remedies(self) -> List[str]:
        return sorted(set(list(self.SENSATION_MAPPINGS.keys()) + list(self._custom.keys())))

    def get_kingdom_distribution(self) -> Dict[str, int]:
        all_maps = {**self.SENSATION_MAPPINGS, **self._custom}
        dist = {}
        for p in all_maps.values():
            k = p.get("kingdom", "unknown")
            dist[k] = dist.get(k, 0) + 1
        return dist

    def get_stats(self) -> Dict[str, Any]:
        return {
            "built_in_mappings": len(self.SENSATION_MAPPINGS),
            "custom_mappings": len(self._custom),
            "kingdom_distribution": self.get_kingdom_distribution(),
            "note": "Full Sankaran integration requires comprehensive remedy-sensation database.",
        }
