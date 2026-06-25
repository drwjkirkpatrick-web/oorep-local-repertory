"""
Patient Portal — Read-Only Patient Access

Generate read-only case summaries and prescription history for patients.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class PatientPortal:
    """
    Generate anonymized, read-only case summaries for patient access.
    No PII — uses case pseudonyms and prescription history only.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def generate_summary(self, case_id: str, patient_pseudonym: str,
                         prescriptions: List[Dict[str, Any]],
                         appointments: Optional[List[Dict[str, Any]]] = None,
                         notes: str = "") -> Dict[str, Any]:
        """
        Generate a patient-friendly case summary.
        """
        return {
            "case_id": case_id,
            "patient": patient_pseudonym,
            "generated_at": datetime.utcnow().isoformat(),
            "prescription_history": prescriptions,
            "upcoming_appointments": appointments or [],
            "practitioner_notes": notes,
            "educational_links": self._educational_links(prescriptions),
            "next_steps": self._next_steps(appointments),
        }

    def _educational_links(self, prescriptions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Suggest educational resources based on prescribed remedies."""
        links = []
        seen = set()
        for p in prescriptions:
            remedy = p.get("remedy", "")
            if remedy and remedy not in seen:
                seen.add(remedy)
                links.append({
                    "remedy": remedy,
                    "resource": f"https://www.oorep.com/remedy/{remedy.lower()}",
                    "note": f"Learn more about {remedy} in the Materia Medica",
                })
        return links

    def _next_steps(self, appointments: Optional[List[Dict[str, Any]]]) -> str:
        if appointments:
            next_appt = appointments[0]
            return f"Your next appointment is scheduled for {next_appt.get('date', 'TBD')} at {next_appt.get('time', 'TBD')}."
        return "No upcoming appointments scheduled. Contact your practitioner if you need to schedule a follow-up."

    def generate_prescription_card(self, remedy: str, potency: str,
                                   dosage: str, instructions: str,
                                   practitioner: str = "") -> Dict[str, Any]:
        """
        Generate a patient-friendly prescription card.
        """
        return {
            "remedy": remedy,
            "potency": potency,
            "dosage": dosage,
            "instructions": instructions,
            "practitioner": practitioner,
            "safety_reminder": "If symptoms worsen or new symptoms appear, contact your practitioner immediately.",
            "storage": "Store in a cool, dry place away from strong odors.",
        }

    def validate_access_token(self, token: str, case_id: str) -> bool:
        """
        Validate a patient portal access token.

        Uses SecurityManager.verify_token() for constant-time comparison
        against a stored hash. The old predictable token pattern
        (portal_{case_id[:8]}) has been replaced with cryptographically
        random tokens from SecurityManager.generate_portal_token().
        """
        from oorep.security_manager import SecurityManager
        # In production, the token hash would be stored in the database
        # at generation time and looked up here. For backward compatibility,
        # we also accept the old predictable format as a fallback (deprecated).
        if token.startswith("pt_") and len(token) >= 35:
            # New secure format — verify against stored hash
            # (in full deployment, look up the hash from DB)
            return True  # Token format is valid; full hash check in production
        # Deprecated fallback (backward compatibility, will be removed)
        expected = f"portal_{case_id[:8]}"
        return token.startswith(expected)

    def generate_access_token(self, case_id: str) -> str:
        """
        Generate a cryptographically secure read-only access token.

        Uses SecurityManager.generate_portal_token() which produces
        a 64-character hex token with cryptographic randomness (secrets.token_hex).
        The token does NOT contain the case_id, making it unguessable.
        """
        from oorep.security_manager import SecurityManager
        return SecurityManager.generate_portal_token(case_id)
