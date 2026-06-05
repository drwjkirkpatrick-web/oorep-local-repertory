"""
Toxicology / Drug Interaction Layer — Feature #23

Safety layer tracking remedy incompatibilities, antidotes, and contraindications.
Database of remedy interactions from classical materia medica.
Alert when a proposed prescription conflicts with patient history.

Usage:
    from oorep.toxicology_layer import ToxicologyLayer
    layer = ToxicologyLayer(db_path="data/feedback.db")

    alert = layer.check_safety("ARS", patient_id="MrsJ2024")
    conflicts = layer.find_conflicts(["ARS", "PULS"])
"""

import sqlite3
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class ToxicologyLayer:
    """
    Safety alerting for remedy incompatibilities and contraindications.
    """

    # Classical inimical pairs from materia medica
    INIMICAL_PAIRS: Set[frozenset] = {
        frozenset(["ARS", "IGN"]),
        frozenset(["ARS", "RHUS-T"]),
        frozenset(["PHOS", "CAUST"]),
        frozenset(["APIS", "RHUS-T"]),
        frozenset(["NUX-V", "IGN"]),
        frozenset(["NUX-V", "COFF"]),
        frozenset(["LYC", "COFF"]),
        frozenset(["ACON", "BELL"]),
        frozenset(["SIL", "MERC"]),
        frozenset(["PULS", "CHAM"]),
        frozenset(["BELL", "STRAM"]),
    }

    ANTIDOTES: Dict[str, List[str]] = {
        "ARS": ["NUX-V", "CARB-V", "CHIN"],
        "NUX-V": ["COFF", "IGN", "PULS"],
        "IGN": ["COFF", "NUX-V"],
        "PULS": ["COFF", "NUX-V", "CHAM"],
        "LYC": ["COFF"],
        "CHAM": ["PULS", "NUX-V"],
        "COFF": ["NUX-V", "IGN"],
        "BELL": ["ACON", "PULS"],
        "AUR": ["BELL", "PULS"],
    }

    def __init__(self, db_path: Optional[str] = None, interaction_db: Optional[Dict] = None):
        self.db_path = db_path
        self.interactions = interaction_db or {}

    # ── Safety check ────────────────────────────────────────────────────────

    def check_safety(
        self,
        remedy: str,
        patient_id: str,
        prior_remedies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Full safety check for a proposed prescription.
        Returns: {alerts: [...], safe: bool, severity}.
        """
        alerts = []
        rem = remedy.upper().replace(".", "")

        # Check inimical pairs
        if prior_remedies:
            for p in prior_remedies:
                if self._is_inimical(rem, p.upper().replace(".", "")):
                    alerts.append({
                        "type": "inimical",
                        "severity": "high",
                        "message": f"{remedy} is classically INIMICAL to {p}.",
                        "pair": [remedy, p],
                    })

        # Check antidotes
        if prior_remedies:
            for p in prior_remedies:
                if self._is_antidote(rem, p.upper().replace(".", "")):
                    alerts.append({
                        "type": "antidote",
                        "severity": "medium",
                        "message": f"{remedy} may antidote the previous effect of {p}.",
                        "pair": [remedy, p],
                    })

        # Check suppression history from DB
        if self.db_path:
            db_alerts = self._check_db_suppression(patient_id, rem)
            alerts.extend(db_alerts)

        # Check contraindications
        contraindicated = self.interactions.get("contraindications", {}).get(rem, [])
        for reason in contraindicated:
            alerts.append({
                "type": "contraindication",
                "severity": "medium",
                "message": reason,
                "remedy": remedy,
            })

        safe = not any(a["severity"] == "high" for a in alerts)
        max_sev = max(
            (3 if a["severity"] == "high" else 2 if a["severity"] == "medium" else 1)
            for a in alerts
        ) if alerts else 0
        severity = ["none", "low", "medium", "high"][max_sev]

        return {
            "remedy": remedy,
            "safe": safe,
            "severity": severity,
            "alert_count": len(alerts),
            "alerts": alerts,
        }

    def find_conflicts(self, remedy_list: List[str]) -> List[Dict[str, Any]]:
        """Find pairs of inimical/antidotal conflicts in a remedy list."""
        conflicts = []
        seen_pairs: Set[frozenset] = set()
        for i, a in enumerate(remedy_list):
            for b in remedy_list[i+1:]:
                pair = frozenset([a.upper().replace(".", ""), b.upper().replace(".", "")])
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                if pair in self.INIMICAL_PAIRS:
                    conflicts.append({"type": "inimical", "pair": [a, b], "severity": "high"})
                elif self._is_antidote(a, b):
                    conflicts.append({"type": "antidote", "pair": [a, b], "severity": "medium"})
        return conflicts

    def _is_inimical(self, a: str, b: str) -> bool:
        pair = frozenset([a, b])
        return pair in self.INIMICAL_PAIRS

    def _is_antidote(self, antidote: str, remedy: str) -> bool:
        """Check if antidote is listed as antidote for remedy (bidirectional)."""
        ant_list = self.ANTIDOTES.get(remedy.upper(), [])
        if antidote.upper() in [x.upper().replace(".", "") for x in ant_list]:
            return True
        # Also check reverse
        ant_list2 = self.ANTIDOTES.get(antidote.upper(), [])
        return remedy.upper() in [x.upper().replace(".", "") for x in ant_list2]

    # ── DB queries ──────────────────────────────────────────────────────────

    def _check_db_suppression(self, patient_id: str, remedy: str) -> List[Dict]:
        """Check suppression history for conflicts."""
        if not self.db_path:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()

        # Check suppression history
        c.execute(
            "SELECT suppressing_agent, suppressed_symptom FROM suppression_history WHERE case_id = ?",
            (patient_id,),
        )
        rows = c.fetchall()
        conn.close()

        alerts = []
        for agent, symptom in rows:
            if agent and agent.upper() == remedy.upper():
                alerts.append({
                    "type": "suppression",
                    "severity": "medium",
                    "message": f"Patient previously suppressed {symptom} with {agent}.",
                })
        return alerts

    def add_interaction(
        self,
        remedy_a: str,
        remedy_b: str,
        rel_type: str,  # "inimical", "antidote", "complementary", "follows"
        source: str = "classical",
    ) -> None:
        """Register a new interaction."""
        if rel_type == "inimical":
            self.INIMICAL_PAIRS.add(frozenset([remedy_a.upper(), remedy_b.upper()]))
        elif rel_type == "antidote":
            self.ANTIDOTES.setdefault(remedy_a.upper(), []).append(remedy_b.upper())

    def get_antidotes(self, remedy: str) -> List[str]:
        """Return known antidotes for a remedy."""
        return self.ANTIDOTES.get(remedy.upper().replace(".", ""), [])

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 23,
            "feature_name": "Toxicology / Drug Interaction Layer",
            "inimical_pairs": len(self.INIMICAL_PAIRS),
            "antidotes_registered": len(self.ANTIDOTES),
            "cold_start_capable": True,
            "version": "1.0",
        }
