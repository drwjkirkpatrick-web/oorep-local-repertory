"""
Batch Prescription Protocol Builder — Standard Protocol Templates

Build standard protocols for common conditions with symptom sets,
remedy sequences, and potency ladders.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class BatchProtocolBuilder:
    """
    Create, store, and apply standard homeopathic protocols for
    common acute and chronic conditions.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.protocols_path = self.data_dir / "batch_protocols.json"
        self.protocols = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.protocols_path.exists():
            with open(self.protocols_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.protocols_path, "w", encoding="utf-8") as f:
            json.dump(self.protocols, f, indent=2)

    def create_protocol(self, protocol_id: str, name: str,
                        condition: str, symptoms: List[str],
                        steps: List[Dict[str, Any]],
                        tags: Optional[List[str]] = None,
                        author: str = "") -> Dict[str, Any]:
        """
        Create a new protocol.
        steps: [{"remedy": "PULS", "potency": "30C", "when": "first sign",
                  "repeat": "every 4h", "stop_on": "improvement"}, ...]
        """
        protocol = {
            "id": protocol_id,
            "name": name,
            "condition": condition,
            "symptoms": symptoms,
            "steps": steps,
            "tags": tags or [],
            "author": author,
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0,
        }
        self.protocols[protocol_id] = protocol
        self._save()
        return protocol

    def get_protocol(self, protocol_id: str) -> Optional[Dict[str, Any]]:
        return self.protocols.get(protocol_id)

    def list_protocols(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        protocols = list(self.protocols.values())
        if tag:
            protocols = [p for p in protocols if tag in p.get("tags", [])]
        return sorted(protocols, key=lambda x: x.get("usage_count", 0), reverse=True)

    def apply_protocol(self, protocol_id: str, case_id: str,
                       practitioner: str = "") -> Dict[str, Any]:
        """
        Apply a protocol to a case. Returns the prescription sequence.
        """
        protocol = self.protocols.get(protocol_id)
        if not protocol:
            return {"error": "Protocol not found"}
        protocol["usage_count"] = protocol.get("usage_count", 0) + 1
        self._save()
        return {
            "protocol_id": protocol_id,
            "case_id": case_id,
            "protocol_name": protocol["name"],
            "steps": protocol["steps"],
            "practitioner": practitioner,
            "applied_at": datetime.utcnow().isoformat(),
        }

    def search_protocols(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for p in self.protocols.values():
            if (q in p.get("name", "").lower() or
                q in p.get("condition", "").lower() or
                any(q in s.lower() for s in p.get("symptoms", [])) or
                any(q in t.lower() for t in p.get("tags", []))):
                results.append(p)
        return results

    def delete_protocol(self, protocol_id: str) -> Dict[str, Any]:
        if protocol_id in self.protocols:
            del self.protocols[protocol_id]
            self._save()
            return {"status": "deleted", "id": protocol_id}
        return {"error": "Not found"}

    def seed_defaults(self) -> int:
        """Seed with common acute protocols."""
        defaults = [
            {
                "id": "acute_otitis",
                "name": "Acute Otitis Media",
                "condition": "Acute ear infection with pain",
                "symptoms": ["ear pain", "fever", "worse at night", "restlessness"],
                "steps": [
                    {"remedy": "PULS", "potency": "30C", "when": "first sign", "repeat": "every 4h", "stop_on": "improvement"},
                    {"remedy": "BELL", "potency": "30C", "when": "intense throbbing pain", "repeat": "every 2h", "stop_on": "improvement"},
                    {"remedy": "CHAM", "potency": "30C", "when": "pain with irritability", "repeat": "every 4h", "stop_on": "improvement"},
                ],
                "tags": ["acute", "children", "ear"],
                "author": "Classical",
            },
            {
                "id": "acute_fever",
                "name": "Acute Fever Protocol",
                "condition": "Sudden onset fever",
                "symptoms": ["fever", "chills", "heat", "thirst"],
                "steps": [
                    {"remedy": "ACON", "potency": "30C", "when": "sudden onset after cold", "repeat": "every 2h", "stop_on": "improvement"},
                    {"remedy": "BELL", "potency": "30C", "when": "burning heat, red face", "repeat": "every 2h", "stop_on": "improvement"},
                    {"remedy": "GELS", "potency": "30C", "when": "prostration with fever", "repeat": "every 4h", "stop_on": "improvement"},
                ],
                "tags": ["acute", "fever", "general"],
                "author": "Classical",
            },
            {
                "id": "acute_cough",
                "name": "Acute Cough Protocol",
                "condition": "Acute cough",
                "symptoms": ["cough", "dry", "wet", "worse night"],
                "steps": [
                    {"remedy": "ACON", "potency": "30C", "when": "dry cough after cold", "repeat": "every 4h", "stop_on": "improvement"},
                    {"remedy": "BRY", "potency": "30C", "when": "dry cough worse motion", "repeat": "every 4h", "stop_on": "improvement"},
                    {"remedy": "RUMX", "potency": "30C", "when": "tickling cough", "repeat": "every 4h", "stop_on": "improvement"},
                ],
                "tags": ["acute", "respiratory"],
                "author": "Classical",
            },
        ]
        count = 0
        for p in defaults:
            if p["id"] not in self.protocols:
                self.protocols[p["id"]] = p
                count += 1
        if count > 0:
            self._save()
        return count
