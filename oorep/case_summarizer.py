"""
Case Summarizer — Narrative Case Summary Generation

Auto-generate readable case summaries from structured data:
"Mrs. J, 45, presented with anxiety worse at 3am, thirst for small quantities..."
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class CaseSummarizer:
    """
    Generate human-readable case summaries from structured data.
    Can produce short (one-paragraph) or long (full narrative) formats.
    """

    def __init__(self):
        pass

    def summarize(self, patient_pseudonym: str, age: Optional[int] = None,
                  gender: str = "", chief_complaint: str = "",
                  symptoms: Optional[List[Dict[str, Any]]] = None,
                  modalities: Optional[List[str]] = None,
                  remedies_considered: Optional[List[str]] = None,
                  prescribed_remedy: str = "",
                  potency: str = "",
                  format_type: str = "short") -> Dict[str, Any]:
        """
        Generate a case summary.
        symptoms: [{"rubric": "Mind; anxiety", "severity": 8, "notes": "worse 3am"}, ...]
        """
        symptoms = symptoms or []
        modalities = modalities or []
        remedies = remedies_considered or []

        if format_type == "short":
            text = self._short_summary(patient_pseudonym, age, gender, chief_complaint, symptoms, modalities, prescribed_remedy, potency)
        else:
            text = self._long_summary(patient_pseudonym, age, gender, chief_complaint, symptoms, modalities, remedies, prescribed_remedy, potency)

        return {
            "patient": patient_pseudonym,
            "format": format_type,
            "generated_at": datetime.utcnow().isoformat(),
            "summary_text": text,
            "n_symptoms": len(symptoms),
            "prescribed": f"{prescribed_remedy} {potency}" if prescribed_remedy else None,
        }

    def _short_summary(self, patient: str, age: Optional[int], gender: str,
                       complaint: str, symptoms: List[Dict[str, Any]],
                       modalities: List[str], remedy: str, potency: str) -> str:
        parts = [f"{patient}"]
        if age:
            parts.append(f", {age}y")
        if gender:
            parts.append(f" {gender}")
        parts.append(f". {complaint}. ")

        if symptoms:
            sev_symptoms = [s for s in symptoms if s.get("severity", 0) >= 7]
            if sev_symptoms:
                parts.append("Key symptoms: ")
                parts.append(", ".join([s["rubric"] for s in sev_symptoms[:3]]))
                parts.append(". ")

        if modalities:
            parts.append("Modalities: ")
            parts.append(", ".join(modalities[:3]))
            parts.append(". ")

        if remedy:
            parts.append(f"Prescribed: {remedy} {potency}.")

        return "".join(parts)

    def _long_summary(self, patient: str, age: Optional[int], gender: str,
                      complaint: str, symptoms: List[Dict[str, Any]],
                      modalities: List[str], remedies: List[str],
                      remedy: str, potency: str) -> str:
        lines = [
            f"CASE SUMMARY: {patient}",
            f"{'=' * 40}",
            f"",
            f"Patient: {patient}" + (f", {age} years old" if age else "") + (f", {gender}" if gender else ""),
            f"Chief Complaint: {complaint}",
            f"",
            f"SYMPTOMS:",
        ]
        for s in symptoms:
            sev = s.get("severity", "")
            sev_str = f" (severity: {sev}/10)" if sev else ""
            lines.append(f"  • {s['rubric']}{sev_str}")
            if s.get("notes"):
                lines.append(f"    Note: {s['notes']}")

        if modalities:
            lines += ["", "MODALITIES:"]
            for m in modalities:
                lines.append(f"  • {m}")

        if remedies:
            lines += ["", "REMEDIES CONSIDERED:"]
            for r in remedies:
                lines.append(f"  • {r}")

        if remedy:
            lines += ["", f"PRESCRIPTION: {remedy} {potency}"]

        lines += ["", "=" * 40]
        return "\n".join(lines)

    def compare_summaries(self, old_summary: str, new_summary: str) -> Dict[str, Any]:
        """Compare two case summaries to highlight changes."""
        # Simple line-by-line comparison
        old_lines = set(old_summary.split("\n"))
        new_lines = set(new_summary.split("\n"))
        added = new_lines - old_lines
        removed = old_lines - new_lines
        return {
            "added_lines": list(added),
            "removed_lines": list(removed),
            "n_changes": len(added) + len(removed),
        }
