"""
Strange-Rare-Peculiar (SRP) Detector

Detects symptoms that are striking, singular, and individualizing — the hallmark
of the genuine homeopathic case. SRP symptoms receive boosted weighting in
repertorization because they more accurately point to the simillimum.

Usage:
    from oorep.srp_detector import SRPDetector
    detector = SRPDetector()
    result = detector.analyze_symptom("worse from consolation")
    # result.is_srp=True, result.srp_type="modality", result.boost=2.0
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class SRPResult:
    symptom: str
    is_srp: bool
    srp_type: Optional[str]   # modality, concomitant, strange_sensation, peculiar_time, etc.
    confidence: float         # 0.0–1.0
    matched_keywords: List[str]
    boost: float              # Repertory weight multiplier (e.g. 1.5–3.0)
    rationale: str


class SRPDetector:
    """
    Detects Strange-Rare-Peculiar symptoms using keyword markers and pattern rules.

    SRP symptoms (as defined in classical homeopathy):
        - Symptoms opposite to the expected natural reaction
        - Peculiar localizations or sensations
        - Striking concomitants
        - Modalities that are unusual or paradoxical
        - Isolated symptoms that stand out from the general case
    """

    # ── Classical SRP keyword markers ──────────────────────────────────────
    SRP_KEYWORDS: Dict[str, Dict[str, Any]] = {
        # Paradoxical modalities (symptom behaves opposite to common sense)
        "paradoxical": {
            "keywords": [
                "worse from consolation", "better from contradiction",
                "worse from warmth", "better from cold air",
                "worse from lying down", "better from motion",
                "worse after sleep", "worse during perspiration",
                "better from pressure", "worse from pressure",
                "worse from heat of bed", "better from cold bathing",
                "worse when fasting", "worse after eating",
                "worse from looking at moving objects",
                "worse from smell of food",
                "worse from touch", "better from touch",
                "worse from noise", "better from noise",
                "worse from light", "better from light",
                "worse from company", "better from company",
                "worse from solitude", "better from solitude",
                "worse during storm", "worse before storm",
                "worse from music", "worse from talking",
            ],
            "boost": 2.5,
            "type": "modality",
        },
        # Strange or queer sensations (language the patient uses that is odd)
        "strange_sensation": {
            "keywords": [
                "as if", "as though", "feels like", "sensation of",
                "as if a", "as though a", "like a", "imagines",
                "delusion", "sensation as if", " thinks he is",
                " believes he is", "fancies", "hallucination",
                "visual illusion", "auditory illusion",
                "feels tall", "feels short", "feels detached",
                "spaced out", "floating", "disconnected",
                "body feels separated", "two wills",
                "double personality", "not himself",
                "everything seems unreal", "dream-like",
                "time passes too", "time stands still",
            ],
            "boost": 2.0,
            "type": "sensation",
        },
        # Peculiar times (odd periodicities or clock-hour symptoms)
        "peculiar_time": {
            "keywords": [
                "at 3 a.m.", "at 3 am", "3am", "3 am",
                "at 11 p.m.", "11pm", "11 pm",
                "midnight", "after midnight", "just before midnight",
                "same hour every", "at same time", "periodically",
                "every 14 days", "every seven days", "every 7 days",
                "every 28 days", "every third day", "alternate days",
                "same day every", "annual", "seasonal",
                "worse at full moon", "worse at new moon",
                "worse at menses", "better at menses",
                "worse at menopause", "better after menopause",
            ],
            "boost": 2.2,
            "type": "time",
        },
        # Concomitants that are striking or unusual
        "striking_concomitant": {
            "keywords": [
                "with anxiety", "with fear of death", "with weeping",
                "with chilliness", "with burning",
                "with confusion", "with vertigo",
                "with palpitations", "with nausea",
                "without thirst", "without appetite",
                "desires air", "must have fresh air",
                "must move", "cannot keep still",
                "weeping without cause", "laughing at serious matters",
                "religious mania", "singing with pain",
                "cursing during", "praying during",
                "desires to be alone", "company aggravates",
                "amorous with headache", "suicidal with headache",
            ],
            "boost": 2.0,
            "type": "concomitant",
        },
        # Isolated / pathognomonic symptoms
        "singular": {
            "keywords": [
                "only symptom", "sole complaint",
                "nothing else", "no other",
                "never had this before", "first time",
                "unprecedented", "unusual for",
                "not like me", "out of character",
                "characteristic", "individualizing",
                "peculiar", "unique to",
                "never experienced", "strange for",
            ],
            "boost": 2.5,
            "type": "singular",
        },
    }

    # Compiled regex cache
    def __init__(self):
        self._pattern_cache: Dict[str, List[Tuple[str, re.Pattern]]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        for category, data in self.SRP_KEYWORDS.items():
            patterns = []
            for kw in data["keywords"]:
                # Escape for regex, allow word boundaries
                escaped = re.escape(kw.lower())
                pat = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
                patterns.append((kw, pat))
            self._pattern_cache[category] = patterns

    def analyze_symptom(self, symptom: str) -> SRPResult:
        """
        Analyze a single symptom text for SRP markers.

        Returns SRPResult with is_srp, confidence score, boost multiplier, and rationale.
        """
        text = (symptom or "").lower().strip()
        if not text:
            return SRPResult(
                symptom=symptom,
                is_srp=False,
                srp_type=None,
                confidence=0.0,
                matched_keywords=[],
                boost=1.0,
                rationale="Empty symptom text",
            )

        matched_categories = []
        all_matched_keywords = []
        total_boost = 1.0
        max_confidence = 0.0

        for category, patterns in self._pattern_cache.items():
            cat_matched = []
            for kw, pat in patterns:
                if pat.search(text):
                    cat_matched.append(kw)
                    all_matched_keywords.append(kw)
            if cat_matched:
                info = self.SRP_KEYWORDS[category]
                matched_categories.append({
                    "category": category,
                    "type": info["type"],
                    "boost": info["boost"],
                    "matched": cat_matched,
                })
                total_boost = max(total_boost, info["boost"])
                # Confidence: more keywords matched in a category → higher confidence
                cat_conf = min(0.3 + 0.2 * len(cat_matched), 0.95)
                max_confidence = max(max_confidence, cat_conf)

        if matched_categories:
            # Build rationale string
            parts = []
            for m in matched_categories:
                parts.append(f"{m['category'].replace('_', ' ')}: {', '.join(m['matched'][:3])}")
            rationale = "SRP detected — " + "; ".join(parts)
            primary_type = matched_categories[0]["type"]
            return SRPResult(
                symptom=symptom,
                is_srp=True,
                srp_type=primary_type,
                confidence=round(max_confidence, 2),
                matched_keywords=all_matched_keywords,
                boost=round(total_boost, 1),
                rationale=rationale,
            )

        return SRPResult(
            symptom=symptom,
            is_srp=False,
            srp_type=None,
            confidence=0.0,
            matched_keywords=[],
            boost=1.0,
            rationale="No SRP markers detected",
        )

    def analyze_symptoms(self, symptoms: List[str]) -> List[SRPResult]:
        """Batch analyze multiple symptoms."""
        return [self.analyze_symptom(s) for s in symptoms]

    def boost_case_rubrics(self, symptom_rubrics: List[Dict]) -> List[Dict]:
        """
        Apply SRP boost to a list of symptom-rubric mappings.

        Each item should have:
            - 'symptom': the original symptom text
            - 'rubric_id': int
            - 'rubric': fullpath
            - 'weight': base weight

        Returns copies with '_srp_boost' and '_boosted_score' added.
        """
        out = []
        for item in symptom_rubrics:
            srp = self.analyze_symptom(item.get("symptom", ""))
            boosted = item.copy()
            boosted["_srp"] = asdict(srp)
            boosted["_srp_boost"] = srp.boost
            base_weight = item.get("weight", 1)
            boosted["_boosted_score"] = round(base_weight * srp.boost, 2)
            out.append(boosted)
        return out

    def get_srp_weights_for_repertorization(self, symptoms: List[str]) -> Dict[str, float]:
        """
        Return a mapping symptom_text -> boost_multiplier for repertorization.
        """
        return {s: self.analyze_symptom(s).boost for s in symptoms}


def quick_analyze(symptom: str) -> Dict:
    """Convenience one-liner."""
    detector = SRPDetector()
    return asdict(detector.analyze_symptom(symptom))


# ── Pre-built SRP keyword expansion for ClinicalRubricMapper ───────────────
SRP_SYNONYMS = {
    # These extend the ClinicalRubricMapper synonym table
    "as if": ["sensation", "imagines", "feels like"],
    "peculiar": ["strange", "odd", "singular", "individualizing", "unique"],
    "worse from consolation": ["worse consolation", "worse sympathy", "worse comforted"],
    "worse from warmth": ["worse heat", "worse warm room", "worse hot"],
    "better from cold air": ["better cold", "better open air", "better fresh air"],
    "3am": ["after midnight", "3 a.m.", "waking 3"],
    "pathognomonic": ["characteristic", "individualizing", "keynote"],
}
