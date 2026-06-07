"""
Symptom Narrative Extractor — NLP Symptom Extraction from Free Text

Paste a case narrative → auto-extract symptoms, modalities, and suggested rubrics.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class SymptomNarrativeExtractor:
    """
    Extract structured symptoms from free-text case narratives.
    Uses keyword patterns and NLP-lite approaches.
    """

    # Symptom keyword patterns
    SYMPTOM_PATTERNS = {
        "headache": ["headache", "head pain", "pain in head", "cephalalgia"],
        "anxiety": ["anxiety", "anxious", "worry", "fear", "nervous"],
        "insomnia": ["insomnia", "cannot sleep", "sleepless", "waking"],
        "thirst small quantities": ["thirst for small", "small quantities", "little sips"],
        "thirst large quantities": ["thirst for large", "great thirst", "much water"],
        "chills": ["chill", "chilly", "coldness", "shivering"],
        "fever": ["fever", "febrile", "high temperature", "burning heat"],
        "nausea": ["nausea", "nauseous", "sick to stomach"],
        "diarrhea": ["diarrhea", "loose stool", "watery stool"],
        "constipation": ["constipation", "hard stool", "no stool"],
        "cough": ["cough", "coughing"],
        "dyspnea": ["shortness of breath", "difficulty breathing", "dyspnea"],
        "fatigue": ["fatigue", "tired", "exhaustion", "weakness"],
    }

    MODALITY_PATTERNS = {
        "worse morning": ["worse morning", "morning aggravation", "am worse"],
        "worse evening": ["worse evening", "evening aggravation", "pm worse"],
        "worse night": ["worse night", "night aggravation", "midnight"],
        "better motion": ["better motion", "amel motion", "relieved by walking"],
        "worse motion": ["worse motion", "agg motion", "relieved by rest"],
        "better cold": ["better cold", "amel cold", "relieved by cold"],
        "worse cold": ["worse cold", "agg cold", "relieved by warmth"],
        "better heat": ["better heat", "amel heat", "relieved by warmth"],
        "better open air": ["better open air", "amel open air", "relieved by fresh air"],
    }

    def __init__(self):
        pass

    def extract(self, narrative: str) -> Dict[str, Any]:
        """
        Extract symptoms and modalities from a case narrative.
        """
        narrative_lower = narrative.lower()

        found_symptoms = []
        for symptom, patterns in self.SYMPTOM_PATTERNS.items():
            for pattern in patterns:
                if pattern in narrative_lower:
                    found_symptoms.append({
                        "symptom": symptom,
                        "matched_phrase": pattern,
                        "position": narrative_lower.find(pattern),
                    })
                    break

        found_modalities = []
        for modality, patterns in self.MODALITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in narrative_lower:
                    found_modalities.append({
                        "modality": modality,
                        "matched_phrase": pattern,
                    })
                    break

        # Deduplicate symptoms
        unique_symptoms = list({s["symptom"]: s for s in found_symptoms}.values())
        unique_modalities = list({m["modality"]: m for m in found_modalities}.values())

        return {
            "original_length": len(narrative),
            "symptoms_found": unique_symptoms,
            "modalities_found": unique_modalities,
            "n_symptoms": len(unique_symptoms),
            "n_modalities": len(unique_modalities),
            "structured_summary": self._build_summary(unique_symptoms, unique_modalities),
        }

    def _build_summary(self, symptoms: List[Dict[str, Any]],
                       modalities: List[Dict[str, Any]]) -> str:
        lines = ["Extracted Symptoms:"]
        for s in symptoms:
            lines.append(f"  • {s['symptom']} (matched: '{s['matched_phrase']}')")
        lines.append("")
        lines.append("Extracted Modalities:")
        for m in modalities:
            lines.append(f"  • {m['modality']} (matched: '{m['matched_phrase']}')")
        return "\n".join(lines)

    def suggest_rubrics(self, narrative: str) -> List[Dict[str, Any]]:
        """
        Extract symptoms then suggest rubrics for each.
        """
        extracted = self.extract(narrative)
        suggestions = []
        try:
            from oorep.quick_symptom_lookup import QuickSymptomLookup
            lookup = QuickSymptomLookup()
            for s in extracted["symptoms_found"]:
                rubrics = lookup.lookup(s["symptom"], top_n=3)
                suggestions.append({
                    "symptom": s["symptom"],
                    "rubrics": rubrics,
                })
        except Exception:
            pass
        return suggestions

    def batch_extract(self, narratives: List[str]) -> List[Dict[str, Any]]:
        return [self.extract(n) for n in narratives]
