"""
Potency Guidance

Classical potency selection support:
- Layer-based defaults (physical, acute, chronic/mental)
- Remedy-specific classical ladders from the major texts
- Practitioner custom overrides (stored in SQLite)

Usage:
    from oorep.potency_guidance import PotencyGuidance
    pg = PotencyGuidance()
    suggestion = pg.suggest_potency("Lyc.", symptom_layer="acute", chronicity="acute")
    ladder = pg.get_potency_ladder("Sulph.")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


# ── Classical remedy potency profiles (~40 entries) ─────────────────────────
# Each entry maps remedy abbreviation -> {"layer": [potencies], "notes": str}
_POTENCY_PROFILES: Dict[str, Dict] = {
    "Ars.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C", "1M"]},
        "notes": "Sensitive patients; 30C for acute anxiety, 200C for deep chronic/restlessness.",
    },
    "Lyc.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C", "1M", "10M"]},
        "notes": "Classical ladder: 30C, 200C, 1M. Low potencies for GI/physical; high for ego/suppressed anger.",
    },
    "Sulph.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C", "1M"]},
        "notes": "Skin/constitutional. Hering: start low if psoric background; 200C+ for deep chronic suppression.",
    },
    "Calc.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C", "1M"]},
        "notes": "Children, growth issues, slow onset. Often starts 30C; 200C for long-standing glandular/structural.",
    },
    "Sil.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C", "1M"]},
        "notes": "Slow deep-acting; low for suppuration/skin, 200C for deep constitutional/silica type.",
    },
    "Nat-m.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C", "1M"]},
        "notes": "Grief-based chronicity. 30C for acute grief headaches; 200C+ for deep melancholia.",
    },
    "Sep.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Hormonal/chronic. 30C for acute hormonal flares; 200C+ for deep sepia-state exhaustion.",
    },
    "Puls.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C", "1M"]},
        "notes": "Acute/teething/ears: 30C. Chronic changeable moods: 200C. Very sensitive to high potencies.",
    },
    "Nux-v.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Acute drug/poisoning: low. Irritable dyspepsia: 30C. Chronic high-strung: 200C. Use high cautiously.",
    },
    "Phos.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Haemorrhagic/burning. 30C for acute bleeding/diarrhoea; 200C+ for deep mental/constitutional.",
    },
    "Bry.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Acute inflammatory: 30C. Dry mucous membranes. Deep constitutional less common.",
    },
    "Rhus-t.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Acute sprains/rheumatism: 30C. Chronic restlessness/herpes: 200C.",
    },
    "Bell.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Acute inflammation with heat/redness/dryness: 30C. 200C rarely needed unless deep abscess history.",
    },
    "Cham.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Teething/irritable infants: 30C. Intolerable pain: low repeated. Mental rage: 200C.",
    },
    "Ign.": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Grief/shock: 30C acute; 200C+ for long-standing suppressed grief. Sensitive to low repeats.",
    },
    "Acon.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Sudden violent onset/fear: 30C acute. 200C for post-traumatic fright tendencies.",
    },
    "Apis": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Oedema/stinging: 30C. Chronic infiltration/kidney: 200C.",
    },
    "Thuja": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Sycotic/foreign-body sensations. Classical: 200C then 1M after interval. Low for warts.",
    },
    "Merc.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Suppuration/night sweats: 30C. Toxic/deep syphilitic taint: 200C. Mercury remedies need caution.",
    },
    "Hep.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Abscess/ulceration: 30C. Oversensitive to touch: low repeated. Chronic suppuration: 200C.",
    },
    "Kali-c.": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Catarrh/dropsy/structural. Slow deep-acting. 30C for acute; 200C+ for chronic dropsy/asthma.",
    },
    "Graph.": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Eczema/rough skin: 30C. Obesity/constipation: 200C chronic.",
    },
    "Lach.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Septic conditions/left-sided. 30C acute septic throat; 200C+ for deep constitutional syphilitic taint.",
    },
    "Caust.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Paralysis/cough. Chronic effects of burns. 30C acute; 200C deep sclerotic/paralytic.",
    },
    "Staph.": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Suppressions/anger. 30C acute UTI/styes; 200C deep suppressed anger/grief.",
    },
    "Calc-p.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Rickets/bone/teething. Generally lower-medium chronic potency.",
    },
    "Mag-m.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Cramping/nerve pain. 30C acute cramps; 200C chronic neuralgia.",
    },
    "Aur.": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Deep depression/bone necrosis. Gold is powerful; rarely start below 200C in chronic.",
    },
    "Plat.": {
        "layer": {"low": ["6C"], "medium": ["30C"], "high": ["200C", "1M"]},
        "notes": "Hysterical/egotistical states. Platinum is deep and high-potency in classics.",
    },
    "Tarent.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Restlessness/compulsion. 30C acute; 200C deep chorea/OCD tendencies.",
    },
    "Coff.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Acute sleeplessness/excitability: 30C. 200C for deep post-shock hyperaesthesia.",
    },
    "Zinc.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Brain fatigue/weakness. 30C acute exam stress; 200C deep nervous breakdown.",
    },
    "Lycps.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Urinary/prostate. 30C acute retention; 200C chronic prostatic.",
    },
    "Op.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Constipation/narcotic effects. 30C acute ileus; 200C deep constitutional apathy.",
    },
    "Nit-ac.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Cracks/fissures/haemorrhage. 30C acute; 200C deep syphilitic ulceration.",
    },
    "Dros.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Dry spasmodic cough. 30C acute whooping; 200C chronic cough diathesis.",
    },
    "Cina": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Worms/irritability in children. Usually 30C; 200C for deep worm-related temper.",
    },
    "Iod.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Cachexia/thyroid. 30C acute goitre flare; 200C deep wasting states.",
    },
    "Bor.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Borax children: dread downward motion. 30C acute aphthae; 200C deep fear state.",
    },
    "Ferr.": {
        "layer": {"low": ["3C", "6C"], "medium": ["12C", "30C"], "high": ["200C"]},
        "notes": "Anaemia/flushing. 30C acute chlorosis; 200C deep constitutional blood deficiency.",
    },
    "Samb.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Croup/acute suffocative cough. 30C acute croup; 200C recurrent croup diathesis.",
    },
    "Verat.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Collapse/cold sweat/vomiting. 30C acute choleraic collapse; 200C deep mental prostration.",
    },
    "Arn.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Trauma/bruising. 30C acute injury; 200C for old traumatic sequelae.",
    },
    "Ruta": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Ligament/bone bruise. 30C acute overuse; 200C deep periosteal chronicity.",
    },
    "Ham.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Passive haemorrhage/varicose veins. 30C acute bleeding; 200C constitutional varicosity.",
    },
    "Crot-h.": {
        "layer": {"low": ["3C", "6C"], "medium": ["30C"], "high": ["200C"]},
        "notes": "Septic/right-sided/oedema. 30C acute cellulitis; 200C deep septic constitutional.",
    },
}

_DEFAULT_LAYER_RATIONALE = {
    "low": "Low potencies (3C–6C) are traditionally used for localized physical pathology and organ-specific complaints.",
    "medium": "Medium potencies (12C–30C) are the classical acute default, balancing depth with gentleness.",
    "high": "High potencies (200C+) address chronic, mental, and deeply suppressed states.",
}


class PotencyGuidance:
    """
    Provide potency suggestions based on classical materia medica
    and practitioner custom profiles stored in SQLite.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_potency_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy TEXT NOT NULL UNIQUE,
                profile_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def _get_profile(self, remedy: str) -> Optional[Dict]:
        """Return merged profile (hardcoded + custom override)."""
        abbrev = remedy.strip()
        # Try exact then without trailing dot
        profile = _POTENCY_PROFILES.get(abbrev)
        alt = abbrev.rstrip(".")
        if profile is None:
            profile = _POTENCY_PROFILES.get(alt)
        # Load custom if any
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT profile_json FROM custom_potency_profiles WHERE remedy = ?",
            (abbrev,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "SELECT profile_json FROM custom_potency_profiles WHERE remedy = ?",
                (alt,),
            )
            row = cursor.fetchone()
        conn.close()
        if row:
            custom = json.loads(row[0])
            if profile:
                # Shallow merge layers
                merged = {**profile}
                if "layer" in custom:
                    merged["layer"] = {**profile.get("layer", {}), **custom["layer"]}
                if "notes" in custom:
                    merged["notes"] = custom["notes"]
                return merged
            return custom
        return profile

    # ── Public API ───────────────────────────────────────────────────────────

    def suggest_potency(
        self,
        remedy: str,
        symptom_layer: str = "physical",
        chronicity: str = "acute",
    ) -> Dict:
        """
        Suggest a potency for a remedy given symptom layer and chronicity.

        Args:
            remedy: Remedy abbreviation (e.g. "Lyc.").
            symptom_layer: One of "physical", "acute_mental", "chronic", "deep_suppressed".
            chronicity: One of "acute" or "chronic".

        Returns:
            Dict with keys:
                suggested_potency: str
                layer: str (low / medium / high)
                rationale: str
                alternatives: list[str]
                remedy_profile: dict or None
        """
        profile = self._get_profile(remedy)
        layer_key: str
        if symptom_layer in ("physical",):
            layer_key = "low"
        elif symptom_layer in ("acute", "acute_mental"):
            layer_key = "medium"
        elif symptom_layer in ("chronic", "deep_suppressed", "mental"):
            layer_key = "high"
        else:
            # Default by chronicity
            layer_key = "medium" if chronicity == "acute" else "high"

        if profile and "layer" in profile:
            potencies = profile["layer"].get(layer_key, [])
            if not potencies:
                # Fall back within profile to nearest layer
                for fallback in ("medium", "low", "high"):
                    potencies = profile["layer"].get(fallback, [])
                    if potencies:
                        break
            suggestion = potencies[0] if potencies else "30C"
            alternatives = potencies[1:3] if len(potencies) > 1 else []
            rationale = (
                profile.get("notes", "")
                + " "
                + _DEFAULT_LAYER_RATIONALE.get(layer_key, "")
            ).strip()
        else:
            # Generic fallback
            defaults = {"low": ["6C", "3C"], "medium": ["30C", "12C"], "high": ["200C", "1M"]}
            potencies = defaults.get(layer_key, ["30C"])
            suggestion = potencies[0]
            alternatives = potencies[1:]
            rationale = (
                f"No specific classical profile found for {remedy}. "
                f"Using default {layer_key} potency guidelines. "
                + _DEFAULT_LAYER_RATIONALE.get(layer_key, "")
            )

        return {
            "suggested_potency": suggestion,
            "layer": layer_key,
            "rationale": rationale,
            "alternatives": alternatives,
            "remedy_profile": profile,
        }

    def get_potency_ladder(self, remedy: str) -> Dict:
        """
        Return the full potency ladder for a remedy (low → medium → high).

        Returns:
            Dict with keys: remedy, low, medium, high, notes.
        """
        profile = self._get_profile(remedy)
        if profile and "layer" in profile:
            return {
                "remedy": remedy,
                "low": profile["layer"].get("low", []),
                "medium": profile["layer"].get("medium", []),
                "high": profile["layer"].get("high", []),
                "notes": profile.get("notes", ""),
            }
        return {
            "remedy": remedy,
            "low": ["3C", "6C"],
            "medium": ["12C", "30C"],
            "high": ["200C", "1M"],
            "notes": "Generic classical ladder — no specific remedy profile found.",
        }

    def add_custom_profile(self, remedy: str, profile: Dict) -> bool:
        """
        Add or override a remedy potency profile.

        Args:
            remedy: Remedy abbreviation.
            profile: Dict with optional keys 'layer' (dict) and 'notes' (str).

        Returns:
            True on success.
        """
        abbrev = remedy.strip()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            (
                "INSERT INTO custom_potency_profiles (remedy, profile_json, created_at) "
                "VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(remedy) DO UPDATE SET profile_json=excluded.profile_json, created_at=datetime('now')"
            ),
            (abbrev, json.dumps(profile)),
        )
        conn.commit()
        conn.close()
        return True
