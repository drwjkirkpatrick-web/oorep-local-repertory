"""
Botanical Repertory Bridge — Benefit #28

Cross-maps OOREP remedy IDs to WHO Monograph (and other botanical reference)
IDs.  Provides the pivot that lets you switch between homeopathic remedy
selection and botanical-medicine reference material.

Usage:
    from oorep.botanical_bridge import BotanicalBridge
    bb = BotanicalBridge()
    bb.get_monograph("Puls.")
    bb.get_remedies_by_plant("Achillea millefolium")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


# ── Seed cross-mapping (OOREP remedy abbrev -> botanical reference data) ───────
_BOTANICAL_SEED: List[Dict] = [
    {"remedy_abbrev": "Puls.",   "latin_name": "Pulsatilla pratensis",      "common_names": ["pasque-flower", "wind-flower"],                "who_vol": None,         "family": "Ranunculaceae"},
    {"remedy_abbrev": "Lyc.",   "latin_name": "Lycopodium clavatum",       "common_names": ["club-moss", "stag's-horn"],                  "who_vol": None,         "family": "Lycopodiaceae"},
    {"remedy_abbrev": "Bell.",   "latin_name": "Atropa belladonna",          "common_names": ["deadly-nightshade"],                        "who_vol": None,         "family": "Solanaceae"},
    {"remedy_abbrev": "Hyos.",   "latin_name": "Hyoscyamus niger",           "common_names": ["henbane", "black henbane"],                  "who_vol": None,         "family": "Solanaceae"},
    {"remedy_abbrev": "Cham.",   "latin_name": "Chamomilla recutita",        "common_names": ["german-chamomile", "matricaria"],            "who_vol": "Vol1",       "family": "Asteraceae"},
    {"remedy_abbrev": "Arn.",    "latin_name": "Arnica montana",             "common_names": ["arnica", "mountain-daisy", "leopard's-bane"],   "who_vol": "Vol3",       "family": "Asteraceae"},
    {"remedy_abbrev": "All-c.",  "latin_name": "Allium sativum",             "common_names": ["garlic"],                                    "who_vol": "Vol1",       "family": "Amaryllidaceae"},
    {"remedy_abbrev": "Sulph.",  "latin_name": "Sulphur",                    "common_names": ["brimstone", "sulfur"],                         "who_vol": None,         "family": "Mineral"},
    {"remedy_abbrev": "Calc.",   "latin_name": "Calcarea carbonica",         "common_names": ["oyster-shell", "calcium carbonate"],          "who_vol": None,         "family": "Mineral"},
    {"remedy_abbrev": "Sil.",   "latin_name": "Silica",                     "common_names": ["flint", "quartz"],                            "who_vol": None,         "family": "Mineral"},
    {"remedy_abbrev": "Apis.",   "latin_name": "Apis mellifera",             "common_names": ["honey-bee"],                                 "who_vol": None,         "family": "Apidae"},
    {"remedy_abbrev": "Coff.",   "latin_name": "Coffea arabica",             "common_names": ["coffee", "arabica"],                         "who_vol": "Vol1",       "family": "Rubiaceae"},
    {"remedy_abbrev": "Chin.",   "latin_name": "Cinchona pubescens",         "common_names": ["cinchona", "Peruvian-bark"],                 "who_vol": "Vol1",       "family": "Rubiaceae"},
    {"remedy_abbrev": "Lach.",   "latin_name": "Lachesis muta",              "common_names": ["bushmaster"],                                "who_vol": None,         "family": "Viperidae"},
    {"remedy_abbrev": "Sep.",    "latin_name": "Sepia officinalis",          "common_names": ["cuttlefish", "cuttlefish-ink"],              "who_vol": None,         "family": "Sepiidae"},
    {"remedy_abbrev": "Thuja.",  "latin_name": "Thuja occidentalis",         "common_names": ["arbor-vitae", "white-cedar"],                "who_vol": None,         "family": "Cupressaceae"},
    {"remedy_abbrev": "Colch.",  "latin_name": "Colchicum autumnale",        "common_names": ["meadow-saffron", "autumn-crocus"],           "who_vol": None,         "family": "Colchicaceae"},
    {"remedy_abbrev": "Phos.",   "latin_name": "Phosphorus",                 "common_names": ["phosphorus"],                                "who_vol": None,         "family": "Mineral"},
    {"remedy_abbrev": "Merc.",   "latin_name": "Mercurius vivus",            "common_names": ["mercury", "quicksilver"],                     "who_vol": None,         "family": "Mineral"},
]


class BotanicalBridge:
    """Cross-map between homeopathic remedies and botanical references."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS botanical_crossmap (
                remedy_abbrev TEXT PRIMARY KEY,
                latin_name TEXT,
                common_names_json TEXT,
                who_monograph_vol TEXT,
                family TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_bbot_family ON botanical_crossmap(family)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_bbot_latin ON botanical_crossmap(latin_name)")
        conn.commit()
        c.execute("SELECT COUNT(*) FROM botanical_crossmap")
        if c.fetchone()[0] == 0 and _BOTANICAL_SEED:
            for entry in _BOTANICAL_SEED:
                c.execute(
                    """INSERT OR IGNORE INTO botanical_crossmap
                    (remedy_abbrev, latin_name, common_names_json, who_monograph_vol, family, notes)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (entry["remedy_abbrev"], entry["latin_name"], json.dumps(entry.get("common_names")),
                     entry.get("who_vol"), entry.get("family"), "seed_entry")
                )
            conn.commit()
        conn.close()

    def get_monograph(self, remedy_abbrev: str) -> Optional[Dict]:
        """Return botanical reference data for a remedy."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT remedy_abbrev, latin_name, common_names_json, who_monograph_vol, family, notes FROM botanical_crossmap WHERE remedy_abbrev = ?", (remedy_abbrev,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "remedy_abbrev": row[0], "latin_name": row[1],
            "common_names": json.loads(row[2]) if row[2] else [],
            "who_monograph_vol": row[3], "family": row[4], "notes": row[5]
        }

    def get_remedies_by_plant(self, latin_name: str) -> List[str]:
        """Find remedies derived from a given plant species."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT remedy_abbrev FROM botanical_crossmap WHERE latin_name = ?", (latin_name,))
        rows = [r[0] for r in c.fetchall()]
        conn.close()
        return rows

    def get_remedies_by_family(self, family: str) -> List[str]:
        """Find all remedies in a botanical family."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT remedy_abbrev FROM botanical_crossmap WHERE family = ?", (family,))
        rows = [r[0] for r in c.fetchall()]
        conn.close()
        return rows

    def who_covered_remedies(self) -> List[Dict]:
        """Return remedies with WHO Monograph coverage."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT remedy_abbrev, latin_name, who_monograph_vol FROM botanical_crossmap WHERE who_monograph_vol IS NOT NULL")
        rows = c.fetchall()
        conn.close()
        return [{"remedy": r[0], "latin_name": r[1], "who_vol": r[2]} for r in rows]

    def add_crossmap(self, remedy_abbrev: str, latin_name: str, common_names=None, who_vol=None, family=None, notes=None):
        """Add or update a cross-map entry."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute(
            """INSERT OR REPLACE INTO botanical_crossmap
            (remedy_abbrev, latin_name, common_names_json, who_monograph_vol, family, notes)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (remedy_abbrev, latin_name, json.dumps(common_names or []), who_vol, family, notes)
        )
        conn.commit()
        conn.close()
        return remedy_abbrev

    def search_common_name(self, name_query: str) -> List[Dict]:
        """Search by common name substring."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT remedy_abbrev, latin_name, common_names_json FROM botanical_crossmap")
        results = []
        for row in c.fetchall():
            names = json.loads(row[2]) if row[2] else []
            if any(name_query.lower() in n.lower() for n in names):
                results.append({"remedy": row[0], "latin_name": row[1], "matching_names": [n for n in names if name_query.lower() in n.lower()]})
        conn.close()
        return results
