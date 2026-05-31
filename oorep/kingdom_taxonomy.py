"""
Kingdom / Taxonomy Classification — Benefit #22

Tags each remedy with its kingdom (Mineral, Plant, Animal) and family,
chemical group, or botanical/ zoological classification. Provides:
  - Kingdom-level queries ("show all Animal remedies")
  - Family group analysis ("compare Solanaceae remedies")
  - Chemical column for Mineral remedies
  - Class/Order/Family hierarchy for Plants and Animals
Initial seed data covers 75 classical remedies; user can extend.
Usage:
    from oorep.kingdom_taxonomy import KingdomTaxonomy, KingdomLevel
    kt = KingdomTaxonomy()
    kt.get_tags("Bell.")
    kt.query(kingdom="Plant", family="Solanaceae")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class KingdomLevel(Enum):
    MINERAL = "mineral"
    PLANT = "plant"
    ANIMAL = "animal"
    NOSODE = "nosode"
    SARCODE = "sarcode"
    IMONDERABLE = "imponderable"


# ── Classical seed taxonomy (~75 remedies) ──────────────────────────────────────
_KINGDOM_SEED: Dict[str, Dict] = {
    # PLANTS
    "Puls.":   {"kingdom": "plant",  "family": "Ranunculaceae",   "group": "Wind-plant",     "sub_group": "pasque-flower"},
    "Lyc.":   {"kingdom": "plant",  "family": "Lycopodiaceae",   "group": "Club-moss",        "sub_group": "pollen-bearing"},
    "Bell.":   {"kingdom": "plant",  "family": "Solanaceae",      "group": "Nightshade",       "sub_group": "deadly-nightshade"},
    "Hyos.":   {"kingdom": "plant",  "family": "Solanaceae",      "group": "Nightshade",       "sub_group": "henbane"},
    "Stram.":  {"kingdom": "plant",  "family": "Solanaceae",      "group": "Nightshade",       "sub_group": "thorn-apple"},
    "Tab.":    {"kingdom": "plant",  "family": "Solanaceae",      "group": "Nightshade",       "sub_group": "tobacco"},
    "Dulc.":   {"kingdom": "plant",  "family": "Solanaceae",      "group": "Nightshade",       "sub_group": "bittersweet"},
    "Coff.":   {"kingdom": "plant",  "family": "Rubiaceae",       "group": "Coffee",           "sub_group": "arabica"},
    "Chin.":   {"kingdom": "plant",  "family": "Rubiaceae",       "group": "Cinchona",         "sub_group": "bark"},
    "Ign.":    {"kingdom": "plant",  "family": "Loganiaceae",     "group": "St-Ignatius-bean", "sub_group": "strychnine-related"},
    "Nux-v.":  {"kingdom": "plant",  "family": "Loganiaceae",     "group": "Nux vomica",       "sub_group": "strychnine"},
    "Gels.":   {"kingdom": "plant",  "family": "Loganiaceae",     "group": "Yellow-jessamine", "sub_group": "gelsemium"},
    "Arn.":    {"kingdom": "plant",  "family": "Asteraceae",      "group": "Arnica",           "sub_group": "mountain-daisy"},
    "Cham.":   {"kingdom": "plant",  "family": "Asteraceae",      "group": "Chamomile",        "sub_group": "german-chamomile"},
    "All-c.":  {"kingdom": "plant",  "family": "Amaryllidaceae",  "group": "Allium",           "sub_group": "garlic"},
    "Aloe.":   {"kingdom": "plant",  "family": "Asphodelaceae",   "group": "Aloe",             "sub_group": "socotrina"},
    "Colch.":  {"kingdom": "plant",  "family": "Colchicaceae",    "group": "Meadow-saffron",   "sub_group": "autumn-crocus"},
    "Croc.":   {"kingdom": "plant",  "family": "Iridaceae",       "group": "Saffron",          "sub_group": "crocus-sativus"},
    "Thuja.":  {"kingdom": "plant",  "family": "Cupressaceae",    "group": "Arbor-vitae",      "sub_group": "occidentalis"},
    "Sabin.":  {"kingdom": "plant",  "family": "Cupressaceae",    "group": "Savin",            "sub_group": "juniper"},
    "Rhus-t.": {"kingdom": "plant",  "family": "Anacardiaceae",   "group": "Poison-ivy",       "sub_group": "toxicodendron"},
    "Rhus-g.": {"kingdom": "plant",  "family": "Anacardiaceae",   "group": "Poison-ivy",       "sub_group": "glabra"},
    "Anac.":   {"kingdom": "plant",  "family": "Anacardiaceae",   "group": "Marking-nut",      "sub_group": "semecarpus"},
    "Apis.":   {"kingdom": "plant",  "family": "Apiaceae",        "group": "Honey-bee",        "sub_group": None},  # Animal but classical confusion
    # MINERALS
    "Ars.":    {"kingdom": "mineral", "family": "Arsenic-series",  "group": "Period-4",        "sub_group": "arsenic-trioxide", "column": "Group 15"},
    "Ant-t.":  {"kingdom": "mineral", "family": "Antimony-series", "group": "Period-5",        "sub_group": "tartarated-antimony", "column": "Group 15"},
    "Bism.":   {"kingdom": "mineral", "family": "Bismuth-series",  "group": "Period-6",        "sub_group": "bismuth-subnitrate", "column": "Group 15"},
    "Calc.":   {"kingdom": "mineral", "family": "Calcium-series",  "group": "Period-4",        "sub_group": "carbonate", "column": "Group 2"},
    "Calc-f.": {"kingdom": "mineral", "family": "Calcium-series",  "group": "Period-4",        "sub_group": "fluoride", "column": "Group 2 / Halogen"},
    "Mag-c.":  {"kingdom": "mineral", "family": "Magnesium-series","group": "Period-3",        "sub_group": "carbonate", "column": "Group 2"},
    "Nat-m.":  {"kingdom": "mineral", "family": "Sodium-series",   "group": "Period-3",        "sub_group": "chloride", "column": "Group 1 / Halogen"},
    "Kali-c.": {"kingdom": "mineral", "family": "Potassium-series","group": "Period-4",        "sub_group": "carbonate", "column": "Group 1"},
    "Kali-bi.":{"kingdom": "mineral", "family": "Potassium-series","group": "Period-4",        "sub_group": "bichromate", "column": "Group 1 / Cr"},
    "Ferr.":   {"kingdom": "mineral", "family": "Iron-series",     "group": "Period-4",        "sub_group": "metallic-iron", "column": "Group 8"},
    "Ferr-p.": {"kingdom": "mineral", "family": "Iron-series",     "group": "Period-4",        "sub_group": "phosphate", "column": "Group 8 / P"},
    "Zinc.":   {"kingdom": "mineral", "family": "Zinc-series",     "group": "Period-4",        "sub_group": "metallic-zinc", "column": "Group 12"},
    "Cupr.":   {"kingdom": "mineral", "family": "Copper-series",   "group": "Period-4",        "sub_group": "metallic-copper", "column": "Group 11"},
    "Merc.":   {"kingdom": "mineral", "family": "Mercury-series",  "group": "Period-6",        "sub_group": "vivus", "column": "Group 12"},
    "Aur.":    {"kingdom": "mineral", "family": "Gold-series",     "group": "Period-6",        "sub_group": "metallic-gold", "column": "Group 11"},
    "Plat.":   {"kingdom": "mineral", "family": "Platinum-series", "group": "Period-6",        "sub_group": "metallic-platinum", "column": "Group 10"},
    "Sil.":   {"kingdom": "mineral", "family": "Silica-series",   "group": "Period-3",        "sub_group": "silica", "column": "Group 14"},
    "Sulph.":  {"kingdom": "mineral", "family": "Sulphur-series",  "group": "Period-3",        "sub_group": "sublimated-sulphur", "column": "Group 16"},
    "Phos.":   {"kingdom": "mineral", "family": "Phosphorus-series","group": "Period-3",       "sub_group": "phosphorus", "column": "Group 15"},
    "Bor.":    {"kingdom": "mineral", "family": "Boron-series",    "group": "Period-2",        "sub_group": "borax", "column": "Group 13"},
    "Alum.":   {"kingdom": "mineral", "family": "Aluminum-series", "group": "Period-3",        "sub_group": "alumina", "column": "Group 13"},
    "Bar-c.":  {"kingdom": "mineral", "family": "Barium-series",   "group": "Period-6",        "sub_group": "carbonate", "column": "Group 2"},
    "Stront-c.":{"kingdom": "mineral","family": "Strontium-series","group": "Period-5",       "sub_group": "carbonate", "column": "Group 2"},
    # ANIMALS
    "Lach.":   {"kingdom": "animal", "family": "Viperidae",        "group": "Bushmaster",       "sub_group": "trigonocephalus"},
    "Crot-h.": {"kingdom": "animal", "family": "Viperidae",        "group": "Rattlesnake",      "sub_group": "horridus"},
    "Vip.":    {"kingdom": "animal", "family": "Viperidae",        "group": "Viper",            "sub_group": "berus"},
    "Sep.":    {"kingdom": "animal", "family": "Sepiidae",         "group": "Cuttlefish-ink",   "sub_group": "officinalis"},
    "Apis.":   {"kingdom": "animal", "family": "Apidae",             "group": "Honey-bee",        "sub_group": "mellifica"},
    "Vesp.":   {"kingdom": "animal", "family": "Vespidae",           "group": "Wasp",             "sub_group": "crabro"},
    "Canth.":  {"kingdom": "animal", "family": "Meloidae",           "group": "Spanish-fly",      "sub_group": "vesicatoria"},
    "Tarent.": {"kingdom": "animal", "family": "Lycosidae",          "group": "Wolf-spider",      "sub_group": "hispanica"},
    "Lat-m.":  {"kingdom": "animal", "family": "Theridiidae",        "group": "Black-widow",      "sub_group": "mactans"},
    "Ambra.":  {"kingdom": "animal", "family": "Physeteridae",       "group": "Ambergris",        "sub_group": "ambra-grisea"},
    "Blatta.": {"kingdom": "animal", "family": "Blattidae",          "group": "Cockroach",        "sub_group": "orientalis"},
    "Form.":   {"kingdom": "animal", "family": "Formicidae",         "group": "Ant",              "sub_group": "rufa"},
    # NOSODES / SARCODES
    "Psor.":   {"kingdom": "nosode",   "family": "Human-source",      "group": "Scabies",          "sub_group": "itch-mite-discharge"},
    "Med.":    {"kingdom": "nosode",   "family": "Human-source",      "group": "Gonorrheal",       "sub_group": "medorrhinum"},
    "Syph.":   {"kingdom": "nosode",   "family": "Human-source",      "group": "Syphilitic",       "sub_group": "lueticum"},
    "Tub.":    {"kingdom": "nosode",   "family": "Bovine-source",     "group": "Tuberculin",       "sub_group": "bovinum-koch"},
    "Carc.":   {"kingdom": "sarcode",  "family": "Human-source",      "group": "Cancer-tissue",    "sub_group": "carcinosinum"},
    "Thyr.":   {"kingdom": "sarcode",  "family": "Endocrine",         "group": "Thyroid",          "sub_group": "thyroidinum"},
    # IMONDERABLES
    "Luna.":   {"kingdom": "imponderable", "family": "Lunar",            "group": "Moonlight",        "sub_group": None},
    "Sol.":    {"kingdom": "imponderable", "family": "Solar",            "group": "Sunlight",         "sub_group": None},
    "X-ray.":  {"kingdom": "imponderable", "family": "Radiation",        "group": "X-radiation",      "sub_group": None},
    "Mag-p.":  {"kingdom": "imponderable", "family": "Magnetic",         "group": "Magnetic-pole",    "sub_group": None},
}


class KingdomTaxonomy:
    """Remedy kingdom/family/group classification with SQLite persistence."""
    _CACHE: Dict[str, Dict] = {}

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB
        self._init_db()
        self._load_cache()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS remedy_taxonomy (
                remedy_abbrev TEXT PRIMARY KEY,
                kingdom TEXT NOT NULL,
                family TEXT,
                group_name TEXT,
                sub_group TEXT,
                column_name TEXT,
                metadata_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_tax_kingdom ON remedy_taxonomy(kingdom)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tax_family ON remedy_taxonomy(family)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tax_group ON remedy_taxonomy(group_name)")
        conn.commit()
        # Seed if empty
        c.execute("SELECT COUNT(*) FROM remedy_taxonomy")
        if c.fetchone()[0] == 0:
            for abbrev, tags in _KINGDOM_SEED.items():
                c.execute(
                    """INSERT INTO remedy_taxonomy (remedy_abbrev, kingdom, family, group_name, sub_group, column_name, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (abbrev, tags["kingdom"], tags.get("family"), tags.get("group"), tags.get("sub_group"), tags.get("column"), json.dumps(tags))
                )
            conn.commit()
        conn.close()

    def _load_cache(self):
        if KingdomTaxonomy._CACHE:
            return
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT remedy_abbrev, kingdom, family, group_name, sub_group, column_name FROM remedy_taxonomy")
        for row in c.fetchall():
            KingdomTaxonomy._CACHE[row[0]] = {
                "kingdom": row[1], "family": row[2], "group": row[3], "sub_group": row[4], "column": row[5]
            }
        conn.close()

    def get_tags(self, remedy_abbrev: str) -> Optional[Dict]:
        """Return full taxonomic tags for a remedy."""
        self._load_cache()
        return KingdomTaxonomy._CACHE.get(remedy_abbrev)

    def query(self, kingdom: Optional[str] = None, family: Optional[str] = None,
              group: Optional[str] = None, column: Optional[str] = None) -> List[str]:
        """Return remedies matching all provided filters."""
        self._load_cache()
        results = []
        for abbrev, tags in KingdomTaxonomy._CACHE.items():
            if kingdom and tags["kingdom"] != kingdom.lower():
                continue
            if family and tags.get("family") != family:
                continue
            if group and tags.get("group") != group:
                continue
            if column and tags.get("column") != column:
                continue
            results.append(abbrev)
        return sorted(results)

    def get_families(self, kingdom: Optional[str] = None) -> List[str]:
        """Return all unique family names."""
        self._load_cache()
        families = set()
        for tags in KingdomTaxonomy._CACHE.values():
            if kingdom is None or tags["kingdom"] == kingdom.lower():
                if tags.get("family"):
                    families.add(tags["family"])
        return sorted(families)

    def get_groups(self, family: Optional[str] = None) -> List[str]:
        """Return all unique group names."""
        self._load_cache()
        groups = set()
        for tags in KingdomTaxonomy._CACHE.values():
            if family is None or tags.get("family") == family:
                if tags.get("group"):
                    groups.add(tags["group"])
        return sorted(groups)

    def get_kingdom_counts(self) -> Dict[str, int]:
        """Return counts per kingdom."""
        self._load_cache()
        counts = {}
        for tags in KingdomTaxonomy._CACHE.values():
            k = tags["kingdom"]
            counts[k] = counts.get(k, 0) + 1
        return counts

    def add_tag(self, remedy_abbrev: str, kingdom: str, family=None, group=None, sub_group=None, column=None):
        """Add or update taxonomy for a remedy."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute(
            """INSERT OR REPLACE INTO remedy_taxonomy
            (remedy_abbrev, kingdom, family, group_name, sub_group, column_name, metadata_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (remedy_abbrev, kingdom.lower(), family, group, sub_group, column,
             json.dumps({"kingdom": kingdom, "family": family, "group": group, "sub_group": sub_group, "column": column}))
        )
        conn.commit()
        conn.close()
        KingdomTaxonomy._CACHE[remedy_abbrev] = {
            "kingdom": kingdom.lower(), "family": family, "group": group, "sub_group": sub_group, "column": column
        }

    def compare_by_taxonomy(self, abbrev_a: str, abbrev_b: str) -> Dict:
        """Compare two remedies' taxonomic similarity."""
        a = self.get_tags(abbrev_a) or {}
        b = self.get_tags(abbrev_b) or {}
        matches = []
        for key in ["kingdom", "family", "group", "sub_group", "column"]:
            if a.get(key) and a.get(key) == b.get(key):
                matches.append(key)
        return {
            "remedy_a": abbrev_a, "remedy_b": abbrev_b,
            "same_kingdom": a.get("kingdom") == b.get("kingdom"),
            "same_family": a.get("family") == b.get("family"),
            "same_group": a.get("group") == b.get("group"),
            "matching_keys": matches,
            "overlap_score": len(matches) / 5.0,
        }
