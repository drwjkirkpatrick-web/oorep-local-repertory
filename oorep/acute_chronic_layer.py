"""
Acute/Chronic Layer Tagger

Tags rubrics as acute, chronic, or both based on keyword patterns.
Used to separate case layers and optionally reweight repertorization
results toward acute or chronic remedy profiles.

Usage:
    from oorep.acute_chronic_layer import AcuteChronicTagger
    tagger = AcuteChronicTagger()
    tags = tagger.tag_rubric_texts(["sudden fever", "chronic fatigue", ...])
    layers = tagger.separate_layers(rubric_ids=[1,2,3], repertory=rep)
    reweighted = tagger.layer_priority(rubric_results, mode="balanced")
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


# ── Keyword heuristics ─────────────────────────────────────────────────────
_ACUTE_PATTERNS: List[str] = [
    r"\bsudden\b",
    r"\bacute\b",
    r"\bviolent\b",
    r"\bintense onset\b",
    r"\battack\b",
    r"\bparoxysm\b",
    r"\bexacerbation\b",
    r"\bcongestion\b",
    r"\bfever\b",
    r"\bchill\b",
    r"\bpainful\b",
    r"\bsevere pain\b",
    r"\bstitching\b",
    r"\blancinating\b",
    r"\bthrobbing\b",
    r"\bpulsating\b",
    r"\bhot\b",
    r"\bburning\b",
    r"\binflammation\b",
    r"\bredness\b",
    r"\bswelling\b",
    r"\btumor\b",
    r"\babscess\b",
    r"\bsuppuration\b",
    r"\bsprain\b",
    r"\bbruise\b",
    r"\btrauma\b",
    r"\binjury\b",
    r"\bwound\b",
    r"\b sting\b",
    r"\bbite\b",
    r"\bnoxious\b",
    r"\bpoison\b",
    r"\btoxic\b",
    r"\binfection\b",
    r"\bflu\b",
    r"\binfluenza\b",
    r"\bcold\b",
    r"\bcoryza\b",
    r"\bdiarrhoea\b",
    r"\bvomiting\b",
    r"\bnausea\b",
    r"\bsyncope\b",
    r"\bfaint\b",
    r"\bshock\b",
    r"\bcollapse\b",
    r"\bconvulsion\b",
    r"\b spasms\b",
    r"\btetanic\b",
    r"\bmeningitis\b",
    r"\bperitonitis\b",
    r"\bpleuritis\b",
    r"\bhepatitis\b",
    r"\bnephritis\b",
    r"\btonsillitis\b",
    r"\blaryngitis\b",
    r"\bcystitis\b",
    r"\bgastritis\b",
    r"\bcolitis\b",
    r"\benteritis\b",
    r"\bpharyngitis\b",
    r"\bburning\b",
    r"\bstinging\b",
]

_CHRONIC_PATTERNS: List[str] = [
    r"\bchronic\b",
    r"\blong-standing\b",
    r"\blong standing\b",
    r"\bconstitutional\b",
    r"\binherited\b",
    r"\bhereditary\b",
    r"\btendency\b",
    r"\bdiathesis\b",
    r"\bdyscrasia\b",
    r"\bmiasmatic\b",
    r"\bscrofulous\b",
    r"\brachitic\b",
    r"\bsyphilitic\b",
    r"\bsycotic\b",
    r"\bmercurial\b",
    r"\bhahnemannian\b",
    r"\bsecondary\b",
    r"\btertiary\b",
    r"\blate stage\b",
    r"\bdegenerative\b",
    r"\bsclerosis\b",
    r"\batrophy\b",
    r"\bhardening\b",
    r"\binduration\b",
    r"\bulcer\b",
    r"\bfistula\b",
    r"\bcancer\b",
    r"\bcarcinoma\b",
    r"\btumor\b",
    r"\bpolyps\b",
    r"\bwarts\b",
    r"\bcondylomata\b",
    r"\bkeloid\b",
    r"\bscar\b",
    r"\bcicatrix\b",
    r"\bsequela\b",
    r"\bsuppressed\b",
    r"\bnever been well\b",
    r"\bsince\b",
    r"\bafter effects\b",
    r"\bconsequences of\b",
    r"\bhabitual\b",
    r"\bpersistent\b",
    r"\bconstant\b",
    r"\bcontinuous\b",
    r"\bpermanent\b",
    r"\brecurrent\b",
    r"\brecurring\b",
    r"\bperiodic\b",
    r"\bintermittent\b",
    r"\brelapsing\b",
    r"\bold people\b",
    r"\baged\b",
    r"\bchildren, sickly\b",
    r"\bdebilitated\b",
    r"\bworn out\b",
    r"\bprostrated\b",
    r"\b cachexia\b",
    r"\bemaciation\b",
    r"\bwasting\b",
    r"\bhypochondriasis\b",
    r"\bneurasthenia\b",
    r"\bpsychosis\b",
    r"\binanity\b",
    r"\bmania\b",
    r"\b melancholia\b",
    r"\bparalysis\b",
    r"\bparalytic\b",
    r"\bpalsy\b",
    r"\bsoftening\b",
]

# Pre-compile for speed
_ACUTE_RE = [re.compile(p, re.IGNORECASE) for p in _ACUTE_PATTERNS]
_CHRONIC_RE = [re.compile(p, re.IGNORECASE) for p in _CHRONIC_PATTERNS]

# ── Hardcoded mapping for ~200 common rubrics (by id where known) ─────────
# Since IDs vary per source, we provide a mapping keyed by fullpath substring.
# The tagger will use an exact match first, then heuristics.
_HARDCODED_RUBRIC_TAGS: Dict[str, str] = {
    # Mental rubrics — often chronic/constitutional
    "Mind; Anxiety; Health; About one's own health": "chronic",
    "Mind; Delusions": "chronic",
    "Mind; Fear; Death": "chronic",
    "Mind; Ailments from grief": "chronic",
    "Mind; Ailments from fright": "both",
    "Mind; Ailments from anger": "both",
    "Mind; Ailments from vexation": "both",
    "Mind; Ailments from disappointed love": "chronic",
    "Mind; Irritability": "chronic",
    "Mind; Weeping": "both",
    "Mind; Homesickness": "chronic",
    "Mind; Dwells": "chronic",
    "Mind; Brooding": "chronic",
    "Mind; Suicidal disposition": "chronic",
    "Mind; Mania": "chronic",
    "Mind; Insanity": "chronic",
    "Mind; Paranoia": "chronic",
    "Mind; Suspicious": "chronic",
    # General rubrics
    "Generalities; Cancer": "chronic",
    "Generalities; Tumors": "chronic",
    "Generalities; Warts": "chronic",
    "Generalities; Scars": "chronic",
    "Generalities; Suppressed": "chronic",
    "Generalities; Ailments from suppressed": "chronic",
    "Generalities; Never well since": "chronic",
    "Generalities; Emaciation": "chronic",
    "Generalities; Wasting": "chronic",
    "Generalities; Debility": "chronic",
    "Generalities; Old people": "chronic",
    "Generalities; Children, sickly": "chronic",
    "Generalities; Dropsy": "chronic",
    "Generalities; Convulsions": "acute",
    "Generalities; Fever": "acute",
    "Generalities; Chill": "acute",
    "Generalities; Sweat": "both",
    "Generalities; Fainting": "acute",
    "Generalities; Collapse": "acute",
    "Generalities; Inflammation": "acute",
    "Generalities; Bruises": "acute",
    "Generalities; Sprains": "acute",
    "Generalities; Wounds": "acute",
    # Head
    "Head; Pain, headache": "both",
    "Head; Pain, headache, chronic": "chronic",
    "Head; Pain, headache, acute": "acute",
    "Head; Pain, headache, congestive": "acute",
    "Head; Pain, headache, nervous": "chronic",
    "Head; Meningitis": "acute",
    "Head; Apoplexy": "acute",
    # Face
    "Face; Neuralgia": "chronic",
    "Face; Paralysis": "chronic",
    "Face; Erysipelas": "acute",
    # Throat / respiratory
    "Throat; Angina": "acute",
    "Throat; Tonsillitis": "acute",
    "Throat; Diphtheria": "acute",
    "Throat; Quinsy": "acute",
    "Respiration; Asthma": "chronic",
    "Respiration; Bronchitis, acute": "acute",
    "Respiration; Bronchitis, chronic": "chronic",
    "Respiration; Croup": "acute",
    "Respiration; Whooping cough": "acute",
    "Respiration; Pneumonia": "acute",
    "Respiration; Pleuritis": "acute",
    "Cough; Dry": "acute",
    "Cough; Paroxysmal": "acute",
    "Cough; Night": "both",
    "Cough; Chronic": "chronic",
    # Chest / heart
    "Chest; Angina pectoris": "acute",
    "Chest; Pericarditis": "acute",
    "Chest; Endocarditis": "acute",
    "Chest; Palpitation": "both",
    # Stomach / abdomen
    "Stomach; Gastritis": "acute",
    "Stomach; Ulcer": "chronic",
    "Stomach; Cancer": "chronic",
    "Stomach; Vomiting": "acute",
    "Stomach; Nausea": "both",
    "Abdomen; Appendicitis": "acute",
    "Abdomen; Peritonitis": "acute",
    "Abdomen; Hernia": "chronic",
    "Abdomen; Ascites": "chronic",
    "Abdomen; Typhlitis": "acute",
    "Abdomen; Enteritis": "acute",
    "Abdomen; Colitis": "chronic",
    # Rectum / bladder
    "Rectum; Diarrhoea": "acute",
    "Rectum; Dysentery": "acute",
    "Rectum; Constipation": "chronic",
    "Rectum; Hemorrhoids": "chronic",
    "Rectum; Fistula": "chronic",
    "Bladder; Cystitis": "acute",
    "Bladder; Retention": "acute",
    # Kidney / urinary
    "Kidneys; Nephritis": "acute",
    "Kidneys; Calculi": "chronic",
    "Kidneys; Bright's disease": "chronic",
    "Urine; Albuminuria": "chronic",
    # Male / female
    "Male; Orchitis": "acute",
    "Male; Sycosis": "chronic",
    "Female; Mastitis": "acute",
    "Female; Ovaritis": "acute",
    "Female; Cancer of uterus": "chronic",
    "Female; Prolapsus": "chronic",
    "Female; Leucorrhoea": "chronic",
    "Female; Amenorrhoea": "chronic",
    "Female; Dysmenorrhoea": "both",
    "Female; Menorrhagia": "both",
    # Skin
    "Skin; Eruptions": "both",
    "Skin; Eczema": "chronic",
    "Skin; Psoriasis": "chronic",
    "Skin; Herpes": "chronic",
    "Skin; Impetigo": "acute",
    "Skin; Erysipelas": "acute",
    "Skin; Boils": "acute",
    "Skin; Carbuncle": "acute",
    "Skin; Ulcers": "chronic",
    "Skin; Gangrene": "acute",
    # Extremities
    "Extremities; Rheumatism, acute": "acute",
    "Extremities; Rheumatism, chronic": "chronic",
    "Extremities; Gout": "chronic",
    "Extremities; Paralysis": "chronic",
    "Extremities; Sprained": "acute",
    "Extremities; Fractures": "acute",
    "Extremities; Dislocation": "acute",
    # Sleep / dreams
    "Sleep; Insomnia": "chronic",
    "Sleep; Sleeplessness": "both",
    "Sleep; Night terrors": "both",
    # Perspiration
    "Perspiration; Night sweats": "chronic",
    # Generals — infectious
    "Generalities; Small pox": "acute",
    "Generalities; Measles": "acute",
    "Generalities; Scarlatina": "acute",
    "Generalities; Varicella": "acute",
    "Generalities; Malaria": "both",
    "Generalities; Syphilis": "chronic",
    "Generalities; Tuberculosis": "chronic",
}


class AcuteChronicTagger:
    """
    Tag rubric texts (or rubric IDs via a repertory lookup) as
    acute, chronic, or both, using a hardcoded map plus keyword heuristics.
    """

    def __init__(self, data_dir: Optional[str] = None):
        # Build exact lookup from hardcoded map keys (lowercased)
        self._exact_map: Dict[str, str] = {
            k.lower(): v for k, v in _HARDCODED_RUBRIC_TAGS.items()
        }
        # Also support prefix matching for partial fullpaths
        self._prefix_keys: List[Tuple[str, str]] = sorted(
            [(k.lower(), v) for k, v in _HARDCODED_RUBRIC_TAGS.items()],
            key=lambda x: len(x[0]),
            reverse=True,
        )

    def _match_exact(self, text: str) -> Optional[str]:
        low = text.lower()
        return self._exact_map.get(low)

    def _match_prefix(self, text: str) -> Optional[str]:
        low = text.lower()
        for prefix, tag in self._prefix_keys:
            if low.startswith(prefix):
                return tag
        return None

    def _heuristic_tag(self, text: str) -> str:
        """Keyword-based heuristic returning acute, chronic, or both."""
        acute_hits = sum(1 for p in _ACUTE_RE if p.search(text))
        chronic_hits = sum(1 for p in _CHRONIC_RE if p.search(text))
        if acute_hits > 0 and chronic_hits > 0:
            return "both"
        if acute_hits > 0:
            return "acute"
        if chronic_hits > 0:
            return "chronic"
        # Default ambiguous -> both (conservative)
        return "both"

    def tag_rubric_texts(self, rubric_texts: List[str]) -> Dict[str, str]:
        """
        Tag a list of rubric fullpath strings.

        Args:
            rubric_texts: List of rubric fullpath strings.

        Returns:
            Dict mapping rubric_text -> tag ('acute' | 'chronic' | 'both').
        """
        out: Dict[str, str] = {}
        for text in rubric_texts:
            tag = self._match_exact(text)
            if tag is None:
                tag = self._match_prefix(text)
            if tag is None:
                tag = self._heuristic_tag(text)
            out[text] = tag
        return out

    def tag_rubrics(self, rubric_dicts: List[Dict]) -> Dict[int, str]:
        """
        Tag rubrics given as dicts with at least 'id' and 'fullpath' keys.

        Returns:
            Dict mapping rubric_id -> tag.
        """
        out: Dict[int, str] = {}
        for r in rubric_dicts:
            rid = r.get("id")
            text = r.get("fullpath", "")
            tag = self._match_exact(text)
            if tag is None:
                tag = self._match_prefix(text)
            if tag is None:
                tag = self._heuristic_tag(text)
            if rid is not None:
                out[rid] = tag
        return out

    def separate_layers(
        self,
        rubric_ids: List[int],
        repertory: Optional[HomeopathicRepertory] = None,
    ) -> Dict[str, List[int]]:
        """
        Given a list of rubric IDs, separate into acute and chronic layers.

        Args:
            rubric_ids: List of OOREP rubric ids.
            repertory: Optional HomeopathicRepertory instance.

        Returns:
            Dict with keys 'acute', 'chronic', 'both' containing lists of ids.
        """
        rep = repertory or HomeopathicRepertory()
        tags: Dict[int, str] = {}
        for rid in rubric_ids:
            rubric = rep.get_rubric_by_id(rid)
            if rubric is None:
                tags[rid] = "both"
                continue
            text = rubric.get("fullpath", "")
            tag = self._match_exact(text)
            if tag is None:
                tag = self._match_prefix(text)
            if tag is None:
                tag = self._heuristic_tag(text)
            tags[rid] = tag

        result: Dict[str, List[int]] = {"acute": [], "chronic": [], "both": []}
        for rid, tag in tags.items():
            result[tag].append(rid)
        return result

    def layer_priority(self, rubric_results: List[Dict], mode: str = "balanced") -> List[Dict]:
        """
        Reweight repertorization results by acute/chronic layer bias.

        Args:
            rubric_results: Output from HomeopathicRepertory.repertorize()
                            (list of dicts with 'abbrev', 'score', 'matches').
            mode: 'balanced' (no change), 'acute' (boost acute rubrics),
                  'chronic' (boost chronic rubrics).

        Returns:
            Copy of rubric_results with '_layer_adjusted_score' added.
        """
        if mode == "balanced":
            # Just annotate, no reweighting
            out = []
            for entry in rubric_results:
                new_entry = dict(entry)
                new_entry["_layer_adjusted_score"] = entry.get("score", 0)
                new_entry["_layer_boost_applied"] = 1.0
                out.append(new_entry)
            return out

        boost_map = {"acute": 1.25, "chronic": 1.25, "both": 1.0}
        target_tag = mode  # 'acute' or 'chronic'
        out = []
        for entry in rubric_results:
            new_entry = dict(entry)
            base_score = entry.get("score", 0)
            # Count how many matches are tagged target vs other
            target_count = 0
            other_count = 0
            for match in entry.get("matches", []):
                rubric_text = match.get("rubric", "")
                tag = self._match_exact(rubric_text) or self._match_prefix(rubric_text) or self._heuristic_tag(rubric_text)
                if tag in (target_tag, "both"):
                    target_count += 1
                else:
                    other_count += 1
            total = target_count + other_count
            if total == 0:
                ratio = 0.5
            else:
                ratio = target_count / total
            # Boost = 1 + (ratio * 0.5) up to 1.25
            boost = 1.0 + (ratio * 0.25)
            adjusted = round(base_score * boost, 2)
            new_entry["_layer_adjusted_score"] = adjusted
            new_entry["_layer_boost_applied"] = round(boost, 3)
            new_entry["_acute_chronic_counts"] = {"target": target_count, "other": other_count}
            out.append(new_entry)
        # Sort by adjusted score
        out.sort(key=lambda x: x.get("_layer_adjusted_score", 0), reverse=True)
        return out
