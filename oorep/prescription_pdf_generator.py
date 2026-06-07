"""
Prescription PDF Generator — Professional Prescription Document Creation

Generate professional PDF prescriptions with remedy, potency,
dosage, and practitioner information.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class PrescriptionPDFGenerator:
    """
    Generate structured prescription data for PDF rendering.
    Does not require external PDF libraries — outputs structured
    dict that any frontend or report engine can render.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.templates_dir = self.data_dir / "prescription_templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, case_id: str, patient_name: str,
                 remedy: str, potency: str,
                 dosage: str = "As directed",
                 instructions: str = "",
                 practitioner: str = "",
                 clinic: str = "",
                 date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a prescription document structure.
        """
        dt = date or datetime.utcnow().strftime("%Y-%m-%d")
        return {
            "document_type": "prescription",
            "date": dt,
            "clinic": clinic,
            "practitioner": practitioner,
            "patient": patient_name,
            "case_id": case_id,
            "prescription": {
                "remedy": remedy,
                "potency": potency,
                "dosage": dosage,
                "instructions": instructions or "Take as directed. Stop on improvement.",
            },
            "footer": "This prescription is for homeopathic use only. Consult your practitioner if symptoms persist.",
            "raw_text": self._format_text(patient_name, remedy, potency, dosage, instructions, practitioner, clinic, dt),
        }

    @staticmethod
    def _format_text(patient: str, remedy: str, potency: str,
                     dosage: str, instructions: str,
                     practitioner: str, clinic: str, date: str) -> str:
        lines = [
            "=" * 40,
            "  HOMŒOPATHIC PRESCRIPTION",
            "=" * 40,
            f"",
            f"Date: {date}",
            f"Clinic: {clinic}",
            f"Practitioner: {practitioner}",
            f"",
            f"Patient: {patient}",
            f"",
            f"Prescribed Remedy: {remedy} {potency}",
            f"Dosage: {dosage}",
            f"Instructions: {instructions or 'Take as directed. Stop on improvement.'}",
            f"",
            f"Signature: _________________________",
            f"",
            f"Note: This prescription is for homeopathic use only.",
            f"Consult your practitioner if symptoms persist.",
            f"{'=' * 40}",
        ]
        return "\n".join(lines)

    def batch_generate(self, prescriptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate multiple prescriptions at once."""
        return [self.generate(**p) for p in prescriptions]

    def template_list(self) -> List[str]:
        """List available prescription templates."""
        return ["standard", "acute", "chronic", "lm_potency"]

    def get_template(self, template_name: str) -> Dict[str, Any]:
        templates = {
            "acute": {
                "dosage": "30C every 2-4 hours until improvement",
                "instructions": "Acute dosing. Stop when symptoms improve. Restart if relapse.",
            },
            "chronic": {
                "dosage": "200C once weekly",
                "instructions": "Chronic constitutional dosing. Monitor over 4-6 weeks.",
            },
            "lm_potency": {
                "dosage": "LM1 once daily in water",
                "instructions": "Dissolve in 4oz water. Sip slowly. Increase potency every 2-4 weeks if needed.",
            },
        }
        return templates.get(template_name, {})
