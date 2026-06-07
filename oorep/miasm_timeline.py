"""
Miasm Timeline — Visual Miasmatic Layer History

Track miasmatic layers uncovered over treatment timeline.
Psora → Sycosis → Syphilis → Tubercular → Cancer
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class MiasmTimeline:
    """
    Track the miasmatic history of a case over time.
    Shows which layers were addressed and when.
    """

    MIASM_ORDER = ["psora", "sycosis", "syphilis", "tubercular", "cancer"]

    def __init__(self, db_path: str = "data/miasm_timeline.db"):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS miasm_events (
                id INTEGER PRIMARY KEY,
                case_id TEXT NOT NULL,
                miasm TEXT NOT NULL,
                event_type TEXT NOT NULL,  -- identified, treated, cleared, relapsed
                date TEXT NOT NULL,
                remedy TEXT,
                potency TEXT,
                notes TEXT,
                practitioner TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_miasm_case ON miasm_events(case_id)")
        conn.commit()
        conn.close()

    def record(self, case_id: str, miasm: str, event_type: str, date: str,
               remedy: str = "", potency: str = "",
               notes: str = "", practitioner: str = "") -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO miasm_events (case_id, miasm, event_type, date, remedy, potency, notes, practitioner) VALUES (?,?,?,?,?,?,?,?)",
            (case_id, miasm, event_type, date, remedy, potency, notes, practitioner)
        )
        conn.commit()
        conn.close()
        return {"case_id": case_id, "miasm": miasm, "event": event_type, "date": date}

    def get_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute(
            "SELECT miasm, event_type, date, remedy, potency, notes FROM miasm_events WHERE case_id = ? ORDER BY date",
            (case_id,)
        ).fetchall()
        conn.close()
        return [
            {"miasm": r[0], "event": r[1], "date": r[2], "remedy": r[3], "potency": r[4], "notes": r[5]}
            for r in rows
        ]

    def get_current_layers(self, case_id: str) -> List[str]:
        """Identify currently active miasmatic layers."""
        timeline = self.get_timeline(case_id)
        active = set()
        for t in timeline:
            if t["event"] in ("identified", "treated"):
                active.add(t["miasm"])
            elif t["event"] == "cleared":
                active.discard(t["miasm"])
        return sorted(active, key=lambda m: self.MIASM_ORDER.index(m) if m in self.MIASM_ORDER else 99)

    def get_layer_progression(self, case_id: str) -> Dict[str, Any]:
        """Show the full miasmatic progression of a case."""
        timeline = self.get_timeline(case_id)
        layers: Dict[str, List[Dict[str, Any]]] = {}
        for t in timeline:
            m = t["miasm"]
            if m not in layers:
                layers[m] = []
            layers[m].append(t)

        return {
            "case_id": case_id,
            "layers": layers,
            "active_layers": self.get_current_layers(case_id),
            "cleared_layers": [m for m, events in layers.items() if any(e["event"] == "cleared" for e in events)],
            "deepest_layer": self._deepest_layer(layers),
        }

    def _deepest_layer(self, layers: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        found = [m for m in self.MIASM_ORDER if m in layers]
        return found[-1] if found else None

    def suggest_next_remedy(self, case_id: str) -> Dict[str, Any]:
        """Suggest anti-miasmatic remedy based on active layers."""
        active = self.get_current_layers(case_id)
        if not active:
            return {"case_id": case_id, "suggestion": "No active miasmatic layers identified.", "remedy": None}

        # Classical anti-miasmatic remedies
        anti_miasmatic = {
            "psora": ["SULPH", "PSORINUM", "GRAPH", "NAT-MUR"],
            "sycosis": ["MEDORRHINUM", "THUJA", "NAT-SULPH", "SIL"],
            "syphilis": ["MERC", "SYPHILINUM", "AURUM", "ARS"],
            "tubercular": ["TUBERCULINUM", "CALC", "BARYTA-C"],
            "cancer": ["CARCINOSINUM", "CONIUM", "CADMIUM-MET"],
        }

        # Suggest for the deepest active layer
        deepest = active[-1]
        suggestions = anti_miasmatic.get(deepest, [])
        return {
            "case_id": case_id,
            "deepest_active_layer": deepest,
            "suggested_remedies": suggestions,
            "note": f"Address {deepest} layer first. Consider nosode if well-indicated.",
        }
