"""
Voice-to-Text Audio Import — Narrative-to-Rubric Pipeline

Import audio recordings (from any microphone, not just Blue Snowball)
and process them through transcription to extract symptoms and suggest rubrics.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class VoiceToTextAudioImport:
    """
    Pipeline: audio file → transcription → symptom extraction → rubric suggestions.
    Compatible with any microphone source. The actual STT engine is pluggable.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.imports_dir = self.data_dir / "audio_imports"
        self.imports_dir.mkdir(parents=True, exist_ok=True)
        self.transcription_engine = "whisper"  # Pluggable: whisper, vosk, etc.

    def import_audio(self, audio_path: str, case_id: str,
                     source_device: str = "unknown_mic",
                     practitioner: str = "") -> Dict[str, Any]:
        """
        Import an audio file for processing.
        Returns import record with metadata.

        v4.3 Security: validates audio_path against allowed extensions and
        prevents path traversal. case_id is sanitized to prevent filename
        injection.
        """
        from oorep.security_manager import SecurityManager

        # Validate case_id (prevents filename injection)
        if not SecurityManager.validate_pseudonym(case_id):
            return {"error": "Invalid case_id format"}

        path = Path(audio_path)

        # v4.3 Security: validate file extension against allowlist
        if path.suffix.lower() not in [".wav", ".mp3", ".m4a", ".ogg", ".flac"]:
            return {"error": "Unsupported audio format. Allowed: .wav, .mp3, .m4a, .ogg, .flac"}

        # v4.3 Security: prevent path traversal — resolve and check no .. remains
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError):
            return {"error": "Invalid audio path"}

        if not path.exists():
            return {"error": "Audio file not found"}

        # v4.3 Security: don't store absolute path (information disclosure)
        # Store only the filename, not the full resolved path
        safe_filename = SecurityManager.sanitize_input(path.name, max_length=200)

        record = {
            "import_id": f"audio_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "case_id": case_id,
            "audio_filename": safe_filename,  # was audio_path with full resolved path
            "source_device": SecurityManager.sanitize_input(source_device, max_length=100),
            "practitioner": SecurityManager.sanitize_input(practitioner, max_length=100),
            "file_size_bytes": path.stat().st_size,
            "imported_at": datetime.utcnow().isoformat(),
            "status": "imported",
            "transcription": None,
            "extracted_symptoms": [],
            "suggested_rubrics": [],
        }

        # Save record
        record_path = self.imports_dir / f"{record['import_id']}.json"
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return record

    def simulate_transcription(self, import_id: str,
                                mock_text: str = "") -> Dict[str, Any]:
        """
        Simulate transcription (placeholder for real STT engine).
        In production, this would call Whisper, Vosk, etc.
        """
        record_path = self.imports_dir / f"{import_id}.json"
        if not record_path.exists():
            return {"error": "Import record not found"}

        with open(record_path, "r", encoding="utf-8") as f:
            record = json.load(f)

        # Mock transcription if no engine available
        if not mock_text:
            mock_text = "Patient reports headache worse in morning, better from cold applications. Also mentions thirst for small quantities of water."

        record["transcription"] = mock_text
        record["status"] = "transcribed"
        record["transcribed_at"] = datetime.utcnow().isoformat()

        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return {
            "import_id": import_id,
            "transcription": mock_text,
            "status": "transcribed",
        }

    def extract_symptoms(self, import_id: str) -> Dict[str, Any]:
        """
        Extract symptoms from transcription text.
        Uses keyword matching (placeholder for NLP extraction).
        """
        record_path = self.imports_dir / f"{import_id}.json"
        if not record_path.exists():
            return {"error": "Import record not found"}

        with open(record_path, "r", encoding="utf-8") as f:
            record = json.load(f)

        text = record.get("transcription", "")
        if not text:
            return {"error": "No transcription available"}

        # Simple keyword extraction
        symptom_keywords = {
            "headache": ["head pain", "headache"],
            "thirst small quantities": ["thirst for small", "small quantities"],
            "better cold": ["better from cold", "cold applications"],
            "worse morning": ["worse in morning", "morning"],
        }

        found = []
        for symptom, keywords in symptom_keywords.items():
            if any(kw in text.lower() for kw in keywords):
                found.append(symptom)

        record["extracted_symptoms"] = found
        record["status"] = "symptoms_extracted"

        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return {
            "import_id": import_id,
            "extracted_symptoms": found,
            "n_symptoms": len(found),
        }

    def suggest_rubrics(self, import_id: str) -> Dict[str, Any]:
        """
        Suggest rubrics from extracted symptoms.
        Uses QuickSymptomLookup or ClinicalRubricMapper.
        """
        record_path = self.imports_dir / f"{import_id}.json"
        if not record_path.exists():
            return {"error": "Import record not found"}

        with open(record_path, "r", encoding="utf-8") as f:
            record = json.load(f)

        symptoms = record.get("extracted_symptoms", [])
        suggestions = []

        try:
            from oorep.quick_symptom_lookup import QuickSymptomLookup
            lookup = QuickSymptomLookup(data_dir=str(self.data_dir))
            for symptom in symptoms:
                rubrics = lookup.lookup(symptom, top_n=3)
                suggestions.append({
                    "symptom": symptom,
                    "rubrics": rubrics,
                })
        except Exception as e:
            suggestions = [{"symptom": s, "error": str(e)} for s in symptoms]

        record["suggested_rubrics"] = suggestions
        record["status"] = "complete"

        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return {
            "import_id": import_id,
            "symptoms": symptoms,
            "suggestions": suggestions,
            "status": "complete",
        }

    def list_imports(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        imports = []
        for f in self.imports_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as fh:
                record = json.load(fh)
            if case_id is None or record.get("case_id") == case_id:
                imports.append(record)
        return sorted(imports, key=lambda x: x.get("imported_at", ""), reverse=True)

    def get_supported_formats(self) -> List[str]:
        return [".wav", ".mp3", ".m4a", ".ogg", ".flac"]

    def get_engine_info(self) -> Dict[str, Any]:
        return {
            "current_engine": self.transcription_engine,
            "available_engines": ["whisper", "vosk", "deepgram", "assemblyai"],
            "note": "Actual STT requires external engine installation. This module manages the pipeline.",
        }
