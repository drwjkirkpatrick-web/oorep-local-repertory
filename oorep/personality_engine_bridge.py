"""
Personality Engine Bridge — Benefits #47, #56

Connects OOREP remedy abbreviations ↔ the remedy personality narrative
system stored at ``~/.hermes/remedy-personalities/personalities/``.

Functions:
  - ``get_personality(remedy_name)`` → narrative
  - ``suggest_by_personality(patient_description)`` → ranked matches
  - ``compare_personalities(remedy_a, remedy_b)`` → side-by-side narrative
  - ``personality_to_rubrics(personality_narrative)`` → likely rubrics

If the local personality files are absent, falls back to a hardcoded
core set of ~20 polychrest narratives so the module is always usable.

Usage:
    from oorep.personality_engine_bridge import PersonalityEngineBridge
    bridge = PersonalityEngineBridge()

    narrative = bridge.get_personality("arsenicum album")
    matches = bridge.suggest_by_personality("anxious, restless, tidy")
    comparison = bridge.compare_personalities("Ars.", "Nux-v.")
    rubrics = bridge.personality_to_rubrics(narrative)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Default personality directory ────────────────────────────────────────────
_PERSONALITY_DIR = Path.home() / ".hermes" / "remedy-personalities" / "personalities"

# ── Hardcoded fallback narratives (~20 polychrests) ───────────────────────────
# These are short paragraph summaries suitable for keyword matching and rubric extraction.
_FALLBACK_PERSONALITIES: Dict[str, str] = {
    "arsenicum album": (
        "Restless, anxious, meticulously tidy. Fear of death and disease. "
        "Burning pains relieved by warmth. Fastidious, critical, chilly. "
        "Worse after midnight, especially 1–3 a.m. Thirsty for small sips."
    ),
    "nux vomica": (
        "Irritable, impatient, hypersensitive. Overworked, sedentary lifestyle. "
        "Chilly, worse from cold air and drafts. Digestive complaints from rich food, alcohol, stimulants. "
        "Wants to be left alone but is easily offended. Early morning waking, 3–4 a.m."
    ),
    "pulsatilla": (
        "Mild, gentle, changeable, weepy. Desire for company and consolation. "
        "Thirstless, warm-blooded, worse in heat and closed rooms. "
        "Suppressed menses, wandering pains, shifting symptoms. Emotional and clingy."
    ),
    "sulphur": (
        "Philosophical, lazy, theoretical genius but impractical. Untidy, averse to bathing. "
        "Burning heat with hot feet shoved out of bed. Intense itching worse from heat of bed. "
        "Hunger at 11 a.m., tendency to skin eruptions."
    ),
    "lycopodium": (
        "Intellectually capable yet lacks self-confidence. Anticipatory anxiety, stage fright. "
        "Domineering to subordinates, timid with superiors. Digestive bloating, gas, 4–8 p.m. aggravation. "
        "Right-sided complaints, desire for sweets, craving warmth."
    ),
    "calcarea carbonica": (
        "Responsible, methodical, overworked, anxious about health and robbers. "
        "Chilly, sweating on exertion (especially head and palms). Craving eggs and indigestible things. "
        "Swollen glands, slow dentition, fear of insanity."
    ),
    "natrum muriaticum": (
        "Grief-stricken, holds grudges, wants to be alone. Consolation aggravates. "
        "Thirsty for cold water, sun headaches, averse to heat. Craving salty and starchy foods. "
        "Dry mucous membranes, cracked lips, emotional walls."
    ),
    "sepia": (
        "Indifferent, exhausted, aversion to family and occupation. "
        "Bearing-down sensation, prolapse, hormonal irregularities. "
        "Chilly, worse before menses, desire for sour and vinegar. Better from vigorous exercise."
    ),
    "phosphorus": (
        "Sympathetic, anxious, vivid imagination, fear of the dark, storms, and being alone. "
        "Hemorrhagic diathesis, burning thirst for cold water. Easily startled, warm-blooded. "
        "Desire for company but exhausted by it. Nosebleeds, bleeding gums."
    ),
    "china officinalis": (
        "Debilitated from loss of vital fluids (blood, sweat, diarrhoea). "
        "Periodic complaints: fevers alternate with chills. Tinnitus, bloating after small meals. "
        "Sensitive to touch, worse from drafts, despondent but not hopeless."
    ),
    "silicea": (
        "Yielding but stubborn deep down. Lack of vital heat, cold extremities. "
        "Suppurative tendency: abscesses, fistulas, slow-healing wounds. Splinter sensation. "
        "Offensive foot sweat, desire for warm drinks, worse from cold air."
    ),
    "lyssinum (hydrophobinum)": (
        "Furious, sexual mania, fear of water, biting, spitting. "
        "Acute sensitivity to drafts and bright light. Inflamed throat with inability to swallow."
    ),
    "aconitum napellus": (
        "Sudden violent onset, intense fear of death. Restlessness and palpitations. "
        "Dry burning heat, unquenchable thirst. Worse from cold wind, exposure. "
        "Acute anxiety, shock, fever with fear."
    ),
    "belladonna": (
        "Violent, hot, red, throbbing. Sudden onset with high fever. "
        "Dilated pupils, photophobia, delirium. Right-sided headaches, worse from jar and light. "
        "Desire to escape, vivid hallucinations."
    ),
    "bryonia": (
        "Dry, thirsty, irritable. Wants to be left alone. "
        "Worse from slightest motion, better from pressure and rest. Stitching pains. "
        "Constipation with dry hard stools, morning headache, business worries."
    ),
    "rhus toxicodendron": (
        "Restless, needs to move to relieve stiffness. Anxious, weepy at night. "
        "Sprains, strains, herpetic eruptions. Left-sided complaints, worse from cold wet weather. "
        "Better from warmth and continued motion."
    ),
    "mercurius solubilis": (
        "Offensive everything: breath, sweat, urine. Destroyed bones and glands. "
        "Thirsty despite salivation. Worse at night, from extremes of temperature. "
        "Hurried, impulsive, suspicious. Trembling weakness."
    ),
    "hepar sulphur": (
        "Hypersensitive to touch and pain, irritable, chilly. "
        "Splinter-like pains, abscesses that are sensitive to cold air. "
        "Hasty speech, desire for sour and strong flavours. Offensive exudates."
    ),
    "causticum": (
        "Sympathetic to others' suffering, politically engaged, idealistic. "
        "Paralytic weakness, raw burning sensations, involuntary urination on coughing. "
        "Worse from cold dry wind, better from warm moist air. Chronic hoarseness."
    ),
    "ignatia amara": (
        "Contradictory, paradoxical, silent grief. Emotional shock, sighing, trembling. "
        "Hysterical laughter alternating with tears. Lump in throat, empty feeling in stomach. "
        "Worse from coffee, tobacco, consolation."
    ),
}

# Expand abbreviations to same key space
_ABBREV_MAP: Dict[str, str] = {
    "ars.": "arsenicum album",
    "nux-v.": "nux vomica",
    "puls.": "pulsatilla",
    "sulph.": "sulphur",
    "lyc.": "lycopodium",
    "calc.": "calcarea carbonica",
    "nat-m.": "natrum muriaticum",
    "sep.": "sepia",
    "phos.": "phosphorus",
    "chin.": "china officinalis",
    "sil.": "silicea",
    "lyss.": "lyssinum (hydrophobinum)",
    "acon.": "aconitum napellus",
    "bell.": "belladonna",
    "bry.": "bryonia",
    "rhus-t.": "rhus toxicodendron",
    "merc.": "mercurius solubilis",
    "hep.": "hepar sulphur",
    "caust.": "causticum",
    "ign.": "ignatia amara",
}

# ── Reverse abbreviation map ─────────────────────────────────────────────────
_NAME_TO_ABBREV: Dict[str, str] = {v: k for k, v in _ABBREV_MAP.items()}


class PersonalityEngineBridge:
    """
    Bridge between OOREP remedy identifiers and the local remedy
    personality narrative system.
    """

    def __init__(self, personality_dir: Optional[Path] = None):
        """
        Args:
            personality_dir: Path to markdown personality files.
                             Defaults to ``~/.hermes/remedy-personalities/personalities/``.
        """
        self.personality_dir = Path(personality_dir) if personality_dir else _PERSONALITY_DIR
        self._cache: Dict[str, str] = {}

    # ── Personality retrieval ──────────────────────────────────────────────────

    def get_personality(self, remedy_name: str) -> Optional[str]:
        """
        Return the personality narrative for a remedy.

        Args:
            remedy_name: Remedy abbreviation ("Ars.") or full name
                         ("Arsenicum album" or "arsenicum-album").

        Returns:
            Narrative string or ``None`` if no personality found.
        """
        canonical = self._canonical_key(remedy_name)
        base = self._base_key(remedy_name)
        for key in (canonical, base):
            if key in self._cache:
                return self._cache[key]

        # 1. Try local markdown files
        narrative = self._load_from_file(canonical) or self._load_from_file(base)
        if narrative:
            self._cache[canonical] = narrative
            self._cache[base] = narrative
            return narrative

        # 2. Try abbreviation map directly (exact or base)
        for lookup in (canonical, base):
            full_name = _ABBREV_MAP.get(lookup)
            if full_name:
                break
        else:
            full_name = None

        # 3. Try hardcoded fallback by full_name or direct match
        for lookup in (canonical, base, full_name):
            if not lookup:
                continue
            for key, text in _FALLBACK_PERSONALITIES.items():
                if key == lookup or key.replace(" ", "-") == lookup:
                    self._cache[canonical] = text
                    self._cache[base] = text
                    return text

        # 4. Try abbreviation map fallback again via file
        if full_name:
            narrative = self._load_from_file(full_name)
            if narrative:
                self._cache[canonical] = narrative
                self._cache[base] = narrative
                return narrative
            narrative = _FALLBACK_PERSONALITIES.get(full_name)
            if narrative:
                self._cache[canonical] = narrative
                self._cache[base] = narrative
                return narrative

        return None

    def _load_from_file(self, canonical: str) -> Optional[str]:
        """Attempt to read a ``{canonical}.md`` personality file."""
        if not self.personality_dir.exists():
            return None
        candidates = [
            self.personality_dir / f"{canonical}.md",
            self.personality_dir / f"{canonical.replace(' ', '-')}.md",
            self.personality_dir / f"{canonical.replace('_', '-')}.md",
            self.personality_dir / f"{canonical.replace(' ', '')}.md",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8")
                except Exception:
                    continue
        return None

    @staticmethod
    def _canonical_key(remedy_name: str) -> str:
        """Normalise a remedy string to lowercase; keep dot and spaces for flexibility."""
        return remedy_name.strip().lower()

    @staticmethod
    def _base_key(remedy_name: str) -> str:
        """Stripped of trailing dot and spaces, hyphens replaced with spaces."""
        return remedy_name.strip().lower().rstrip(".").replace("-", " ")

    # ── Matching patient descriptions to personalities ───────────────────────

    def suggest_by_personality(self, patient_description: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Rank remedies whose personality narratives best match the patient description.

        Uses simple keyword overlap scoring (no external LLM), so it is fast
        and runs entirely offline.

        Args:
            patient_description: Free-text description of the patient's
                                 temperament, sensations, and modalities.
            top_n: Number of top matches to return.

        Returns:
            List of dicts with ``remedy_abbrev``, ``remedy_name``, ``score``,
            ``matched_keywords``.
        """
        desc_tokens = set(self._tokenize(patient_description))
        if not desc_tokens:
            return []

        scores: List[Dict[str, Any]] = []
        for full_name, narrative in _FALLBACK_PERSONALITIES.items():
            abbrev = _NAME_TO_ABBREV.get(full_name, "?")
            narrative_tokens = set(self._tokenize(narrative))
            intersection = desc_tokens & narrative_tokens
            if intersection:
                scores.append({
                    "remedy_name": full_name,
                    "remedy_abbrev": abbrev,
                    "score": len(intersection),
                    "matched_keywords": sorted(intersection),
                })

        # Also scan local personality files if they exist
        if self.personality_dir.exists():
            for path in self.personality_dir.iterdir():
                if not path.suffix == ".md":
                    continue
                full_name = path.stem.replace("-", " ")
                if full_name in _FALLBACK_PERSONALITIES:
                    continue  # already scored
                try:
                    narrative = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                narrative_tokens = set(self._tokenize(narrative))
                intersection = desc_tokens & narrative_tokens
                if intersection:
                    scores.append({
                        "remedy_name": full_name,
                        "remedy_abbrev": "?",  # unknown abbrev unless mapped
                        "score": len(intersection),
                        "matched_keywords": sorted(intersection),
                    })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_n]

    # ── Personality comparison ──────────────────────────────────────────────

    def compare_personalities(self, remedy_a: str, remedy_b: str) -> Dict[str, Any]:
        """
        Side-by-side narrative comparison of two remedy personalities.

        Returns:
            Dict with ``remedy_a``, ``remedy_b``, ``personality_a``,
            ``personality_b``, ``shared_keywords``, ``a_unique_keywords``,
            ``b_unique_keywords``.
        """
        pa = self.get_personality(remedy_a) or ""
        pb = self.get_personality(remedy_b) or ""

        tokens_a = set(self._tokenize(pa))
        tokens_b = set(self._tokenize(pb))

        shared = sorted(tokens_a & tokens_b)
        unique_a = sorted(tokens_a - tokens_b)
        unique_b = sorted(tokens_b - tokens_a)

        return {
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "personality_a": pa[:500] if len(pa) > 500 else pa,
            "personality_b": pb[:500] if len(pb) > 500 else pb,
            "shared_keywords": shared,
            "a_unique_keywords": unique_a,
            "b_unique_keywords": unique_b,
        }

    # ── Personality → rubrics extraction ──────────────────────────────────────

    def personality_to_rubrics(self, personality_narrative: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extract likely OOREP-style rubric snippets from a personality narrative.

        Uses keyword-to-rubric heuristic mapping. This is a lightweight
        generator for exploration, not a substitute for proper repertorization.

        Args:
            personality_narrative: Text describing a remedy personality.
            top_n: Maximum number of suggested rubric strings to return.

        Returns:
            List of dicts with ``rubric_path`` and ``confidence`` (1–3).
        """
        text_lower = personality_narrative.lower()
        suggestions: List[Dict[str, Any]] = []

        # Keyword → rubric heuristics
        _RUBRIC_KEYWORDS = [
            ("mind; anxiety", ["anxious", "fear", "worried", "apprehension", "panic"]),
            ("mind; restlessness", ["restless", "cannot sit still", "fidgety"]),
            ("mind; irritability", ["irritable", "impatient", "angry easily", "cross"]),
            ("mind; weeping", ["weepy", "cries easily", "tearful", "sobbing"]),
            ("mind; indifference", ["indifferent", "aversion to family", "careless"]),
            ("head; pain", ["headache", "head pain", "migraine", "aching head"]),
            ("stomach; thirst", ["thirsty", "thirstless", "desire water", "aversion water"]),
            ("stomach; appetite", ["hunger", "loss of appetite", "craving", "aversion"]),
            ("extremities; coldness", ["cold feet", "cold hands", "chilly"]),
            ("skin; itching", ["itching", "pruritus", "burning skin"]),
            ("sleep; sleeplessness", ["insomnia", "sleepless", "waking early"]),
            ("fever; heat", ["burning heat", "hot flashes", "fever"]),
            ("female; menses", ["menses", "suppressed menses", "menstrual"]),
            ("chest; palpitation", ["palpitation", "racing heart"]),
            ("generals; weakness", ["weakness", "exhaustion", "debility", "prostration"]),
        ]

        for rubric, keywords in _RUBRIC_KEYWORDS:
            confidence = sum(1 for kw in keywords if kw in text_lower)
            if confidence:
                suggestions.append({
                    "rubric_path": rubric,
                    "confidence": min(confidence, 3),
                    "matched_keywords": [kw for kw in keywords if kw in text_lower],
                })

        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:top_n]

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple alphanumeric tokenisation for overlap scoring."""
        return re.findall(r"[a-z]{3,}", text.lower())
