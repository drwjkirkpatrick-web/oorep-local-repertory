"""
Chief Complaint Triager (Module #133)

The first-pass triage for a new case. Given a patient's initial complaint
(free text), classifies it into:
  - A primary body system / chapter (Mind, Head, Stomach, Skin, etc.)
  - A chief complaint category (acute, chronic, recurring, constitutional)
  - An urgency level (routine, urgent, emergency → red flag)
  - The recommended starting phase of the interview
  - Suggested initial questions to focus on

The triager also flags potential red-flag symptoms that require medical
referral regardless of the homeopathic treatment plan.

Uses simple keyword/regex pattern matching against a curated complaint
taxonomy. Pure-Python; no ML dependencies.

Usage:
    from oorep.chief_complaint_triager import ChiefComplaintTriager, Urgency
    triager = ChiefComplaintTriager()
    triage = triager.triage("I've had a migraine for 3 days, worse on the right side")
    print(triage.chapter, triage.urgency, triage.recommended_questions)
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class Urgency(Enum):
    """How urgently this case needs attention."""
    ROUTINE = "routine"           # Standard homeopathic case
    PRIORITY = "priority"         # Time-sensitive but not emergency
    URGENT = "urgent"             # Needs attention soon
    EMERGENCY = "emergency"       # RED FLAG - refer for medical care


class ComplaintCategory(Enum):
    """The nature of the chief complaint."""
    ACUTE = "acute"               # Sudden onset, recent
    CHRONIC = "chronic"           # Long-standing
    RECURRING = "recurring"       # Comes and goes
    EPISODIC = "episodic"         # Discrete episodes
    CONSTITUTIONAL = "constitutional"  # Overall pattern inquiry
    MENTAL_EMOTIONAL = "mental_emotional"  # Primarily psychological
    DEVELOPMENTAL = "developmental"  # Growth/life-stage related
    TRAUMATIC = "traumatic"       # Injury/accident related


@dataclass
class TriageResult:
    """The output of chief complaint triage."""
    original_complaint: str
    normalized_complaint: str
    chapter: str                          # Primary body system
    secondary_chapters: List[str]         # Other systems mentioned
    category: ComplaintCategory
    urgency: Urgency
    confidence: float                     # 0-1: how confident in classification
    red_flags: List[str]                  # Any red-flag symptoms detected
    recommended_questions: List[str]      # Question IDs to focus on first
    keywords_extracted: List[str]         # Key medical terms extracted
    duration_estimate_sec: int
    rationale: str                        # Why this classification


# Body system keyword patterns
BODY_SYSTEM_PATTERNS: Dict[str, List[str]] = {
    "Mind": [
        r"\banxi(ety|ous)\b", r"\bdepress(ed|ion)\b", r"\bgrief\b", r"\bfear\b",
        r"\bpani(c|ck)\b", r"\birritab(le|ility)\b", r"\bsad(ness)?\b",
        r"\bweep(ing)?\b", r"\bcrying\b", r"\banger\b", r"\brage\b",
        r"\bmental\b", r"\bmood\b", r"\bstress\b", r"\bworri(ed|ing)\b",
    ],
    "Head": [
        r"\bheadache\b", r"\bmigraine\b", r"\bhead\s*ache\b", r"\bhead\s*pain\b",
        r"\bcephalgia\b", r"\bvertex\b", r"\bocciput\b", r"\btemple\b",
        r"\bforehead\b", r"\bhead\b", r"\bdizz(y|iness)\b", r"\bvertigo\b",
    ],
    "Eye": [
        r"\beye(s)?\b", r"\bvision\b", r"\bsight\b", r"\bsquint(ing)?\b",
        r"\btear(ing|s)?\b", r"\bconjunctiv\b", r"\bstye\b", r"\bsore\s*eyes\b",
    ],
    "Ear": [
        r"\bear(s)?\b", r"\bearache\b", r"\bhear(ing)?\b", r"\btinnit(us)?\b",
        r"\bdeaf(ness)?\b", r"\bnoises?\s*in\s*(the\s*)?ear\b",
    ],
    "Nose": [
        r"\bnose\b", r"\bnasal\b", r"\bsinus(es)?\b", r"\brhinitis\b",
        r"\bsneez(ing)?\b", r"\brunn(y|ing)\s*nose\b", r"\bcoryza\b",
        r"\bhay\s*fever\b", r"\bcongestion\b",
    ],
    "Face": [
        r"\bface\b", r"\bfacial\b", r"\bcheek(s)?\b", r"\bchin\b",
        r"\blip(s)?\b", r"\bforehead\b", r"\bja(ws|w)\b",
    ],
    "Mouth": [
        r"\bmouth\b", r"\btong(ue|ues)\b", r"\btaste\b", r"\bsaliva(te)?\b",
        r"\baphth(ous|a)\b", r"\bulcer(s)?\s*(in|on)\s*(the\s*)?mouth\b",
    ],
    "Throat": [
        r"\bthroat\b", r"\bpharyn(x|gitis)\b", r"\bsore\s*throat\b",
        r"\bswallow(ing)?\b", r"\bhoars(e|eness)\b", r"\blaryn(x|geal)\b",
    ],
    "Stomach": [
        r"\bstomach\b", r"\bgastric\b", r"\bnause(a|ous)\b", r"\bvomit(ing)?\b",
        r"\bqueas(y|iness)\b", r"\bappetite\b", r"\bhunger\b", r"\bthirst\b",
        r"\bbelch(ing)?\b", r"\bheartburn\b", r"\breflux\b", r"\bindigestion\b",
    ],
    "Abdomen": [
        r"\babdo(men|men)\b", r"\bbelly\b", r"\bstomach\s*ache\b",
        r"\bliver\b", r"\bgall(bladder)?\b", r"\bbilious\b", r"\bcramp(ing|s)?\b",
        r"\bbloating\b", r"\bflatul(ence|ent)\b", r"\bgas\b",
    ],
    "Rectum": [
        r"\brectum\b", r"\brect(al)?\b", r"\banus\b", r"\bhemorrhoid\b",
        r"\bpiles\b", r"\bitching\s*anus\b", r"\bprolaps(e|ed)\b",
    ],
    "Stool": [
        r"\bstool(s)?\b", r"\bbowel\b", r"\bconstipat(ed|ion)\b",
        r"\bdiarrh(o?ea|ea)\b", r"\bloose\s*motion\b", r"\bbloody\s*stool\b",
    ],
    "Urine": [
        r"\burin(e|ation|ary)\b", r"\bbladder\b", r"\bpeeing\b", r"\bpeeing\s*often\b",
        r"\bfrequent\s*urination\b", r"\bburn(ing)?\s*urin\b", r"\bkidney\b",
    ],
    "Sexual": [
        r"\bsex(ual)?\b", r"\blibido\b", r"\berectile\b", r"\bperiod(s)?\b",
        r"\bmenstru(al|ation)\b", r"\bmenses\b", r"\bpregnan(t|cy)\b",
        r"\bleucorrh(o?ea|ea)\b", r"\bvaginal\b",
    ],
    "Respiration": [
        r"\brespir(ation|atory)\b", r"\bbreath(ing|less)?\b", r"\bbreathless(ness)?\b",
        r"\bshort(ness)?\s*of\s*breath\b", r"\bSOB\b", r"\basthma\b",
        r"\bwheez(ing|y)\b",
    ],
    "Cough": [
        r"\bcough(ing)?\b", r"\bchesty\s*cough\b", r"\bdry\s*cough\b",
        r"\bproductive\s*cough\b", r"\bhacking\b",
    ],
    "Chest": [
        r"\bchest\b", r"\bthorax\b", r"\bheart\s*pain\b", r"\bangina\b",
        r"\bpalpitation(s)?\b", r"\bchest\s*tightness\b", r"\bchest\s*pain\b",
    ],
    "Back": [
        r"\bback(ache)?\b", r"\bspine\b", r"\bspinal\b", r"\blumbar\b",
        r"\bcervical\b", r"\bsciati(c|ca)\b", r"\bneck\s*pain\b",
    ],
    "Extremities": [
        r"\barm(s)?\b", r"\bleg(s)?\b", r"\bhand(s)?\b", r"\bfoot(feet)?\b",
        r"\bjoint(s)?\b", r"\bkn(ee|ees)\b", r"\bshoulder(s)?\b",
        r"\bhip(s)?\b", r"\belbow(s)?\b", r"\bwrist(s)?\b", r"\btoe(s)?\b",
        r"\bfinger(s)?\b", r"\barthr(itis|itic|algia)\b", r"\bnumbness\b",
        r"\btingling\b", r"\bcramp(ing|s)?\b",
    ],
    "Skin": [
        r"\bskin\b", r"\brash(es)?\b", r"\bhive(s)?\b", r"\burticaria\b",
        r"\beczema\b", r"\bpsoriasis\b", r"\bacne\b", r"\bpimple(s)?\b",
        r"\bboil(s)?\b", r"\bfuruncle\b", r"\babscess\b", r"\bmole\b",
        r"\bwart(s)?\b", r"\bicthy\b", r"\bdermatitis\b", r"\bitching\b",
        r"\bprurit(us|ic)\b",
    ],
    "Fever": [
        r"\bfever(ish)?\b", r"\btemperature\b", r"\bpyrexia\b", r"\bchill(s|y)?\b",
        r"\brigors?\b", r"\bhot\s*and\s*cold\b", r"\bsweats?\b",
    ],
    "Sleep": [
        r"\bsleep(ing|less)?\b", r"\binsomnia\b", r"\bsleepless(ness)?\b",
        r"\bwake(s|ful|ing)\b", r"\bnightmare(s)?\b", r"\brestless\s*sleep\b",
    ],
    "Generals": [
        r"\bfatigue\b", r"\btired(ness)?\b", r"\bexhaust(ed|ion)\b",
        r"\bweak(ness)?\b", r"\benergy\b", r"\bmala(ise|ise)\b",
        r"\bweight\s*(loss|gain)\b", r"\boverall\b",
    ],
    "Female": [
        r"\bvagina(l)?\b", r"\bovary\b", r"\buter(us|ine)\b", r"\bcervix\b",
        r"\bmenopaus(e|al)\b", r"\bPMS\b", r"\bPMDD\b",
    ],
    "Male": [
        r"\bprostat(e|ic)\b", r"\btesticle(s)?\b", r"\bpenis\b", r"\bscrot(um|al)\b",
    ],
    "Pregnancy": [
        r"\bpregnan(t|cy)\b", r"\bgestation\b", r"\btrimester\b",
    ],
}

# Red-flag patterns that should trigger emergency triage
RED_FLAG_PATTERNS: List[Tuple[str, str]] = [
    (r"\bchest\s*pain\b", "Chest pain - cardiac workup needed"),
    (r"\bsudden\s*severe\s*headache\b", "Thunderclap headache - need imaging"),
    (r"\bsudden\s*weakness\s*on\s*one\s*side\b", "Stroke symptoms - emergency"),
    (r"\bslurred\s*speech\b", "Stroke symptoms - emergency"),
    (r"\bvision\s*loss\b", "Sudden vision loss - emergency"),
    (r"\b(can't|cannot)\s*breathe\b", "Severe dyspnea - emergency"),
    (r"\bsevere\s*bleeding\b", "Severe hemorrhage - emergency"),
    (r"\bsuicid(al|al\s*thoughts?|e)\b", "Suicidal ideation - safety planning needed"),
    (r"\bself[- ]harm\b", "Self-harm - safety planning needed"),
    (r"\bhomicid(al|e)\b", "Homicidal ideation - safety planning needed"),
    (r"\bpregnan(t|cy).{0,30}\b(bleeding|cramping)\b", "Pregnancy bleeding - OB workup"),
    (r"\bnew\s*onset\s*confusion\b", "Altered mental status - workup needed"),
    (r"\bseizure\b", "Seizure - neurological workup"),
    (r"\bblack(ing)?\s*out\b", "Syncope - cardiac/neurological workup"),
    (r"\bblood\s*in\s*stool\b", "GI bleeding - workup needed"),
    (r"\bvomit(ing)?\s*blood\b", "Hematemesis - emergency"),
    (r"\bcough(ing)?\s*up\s*blood\b", "Hemoptysis - workup needed"),
    (r"\bfever(.{0,30})neck\s*stiff", "Meningitis signs - emergency"),
    (r"\bsevere\s*abdominal\s*pain\b", "Acute abdomen - workup needed"),
]

# Acute/chronic/recur pattern detection
DURATION_PATTERNS = {
    "acute": [
        r"\b(sudden(ly)?|acute|just\s*started|today|yesterday)\b",
        r"\b(this|past)\s*(morning|afternoon|evening|night)\b",
        r"\b(few|couple\s*of)\s*hours?\b",
        r"\blast\s*(24|48)\s*hours\b",
    ],
    "chronic": [
        r"\b(years?|long\s*time|forever|always|chronic|ongoing)\b",
        r"\bsince\s*(i\s*was|childhood|teen|adolescence|years?\s*ago)\b",
        r"\bfor\s*(months?|years?)\b",
    ],
    "recurring": [
        r"\b(recurring|comes?\s*and\s*goes?|every\s*so\s*often|intermittent)\b",
        r"\b(every|each)\s*(week|month|spring|winter|summer|fall|monday|...)\b",
    ],
}


class ChiefComplaintTriager:
    """
    Classifies a chief complaint into a body system, category, urgency, and
    recommends initial questions to focus on.
    """

    def __init__(self):
        # Pre-compile patterns
        self._system_patterns: Dict[str, List[re.Pattern]] = {
            chapter: [re.compile(p, re.IGNORECASE) for p in patterns]
            for chapter, patterns in BODY_SYSTEM_PATTERNS.items()
        }
        self._red_flag_patterns: List[Tuple[re.Pattern, str]] = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in RED_FLAG_PATTERNS
        ]
        self._duration_patterns: Dict[str, List[re.Pattern]] = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in DURATION_PATTERNS.items()
        }

    def triage(self, complaint: str) -> TriageResult:
        """
        Triage a free-text chief complaint.

        Returns a TriageResult with chapter, category, urgency, red flags,
        and recommended questions to start with.
        """
        if not complaint or not complaint.strip():
            return TriageResult(
                original_complaint=complaint or "",
                normalized_complaint="",
                chapter="General",
                secondary_chapters=[],
                category=ComplaintCategory.CONSTITUTIONAL,
                urgency=Urgency.ROUTINE,
                confidence=0.0,
                red_flags=[],
                recommended_questions=["O.01", "MN.01", "G.05"],
                keywords_extracted=[],
                duration_estimate_sec=900,
                rationale="Empty complaint - defaulting to constitutional intake.",
            )

        normalized = self._normalize(complaint)
        chapter_scores: Dict[str, float] = self._score_chapters(normalized)
        red_flags = self._detect_red_flags(normalized)
        category = self._detect_category(normalized)
        urgency = self._determine_urgency(red_flags, category, normalized)
        chapter, confidence = self._top_chapter(chapter_scores)
        secondary = self._secondary_chapters(chapter_scores, chapter)
        keywords = self._extract_keywords(normalized)
        questions = self._recommend_questions(chapter, category, urgency, red_flags)
        rationale = self._build_rationale(chapter, category, urgency, red_flags, chapter_scores)

        return TriageResult(
            original_complaint=complaint,
            normalized_complaint=normalized,
            chapter=chapter,
            secondary_chapters=secondary,
            category=category,
            urgency=urgency,
            confidence=confidence,
            red_flags=red_flags,
            recommended_questions=questions,
            keywords_extracted=keywords,
            duration_estimate_sec=self._estimate_duration(category, urgency),
            rationale=rationale,
        )

    def _normalize(self, text: str) -> str:
        """Normalize text: lowercase, strip punctuation extras."""
        return " ".join(text.lower().split())

    def _score_chapters(self, text: str) -> Dict[str, float]:
        """Score each body system by how many keyword patterns match."""
        scores: Dict[str, float] = defaultdict(float)
        for chapter, patterns in self._system_patterns.items():
            for pat in patterns:
                matches = pat.findall(text)
                if matches:
                    scores[chapter] += len(matches)
        return dict(scores)

    def _detect_red_flags(self, text: str) -> List[str]:
        """Detect any red-flag symptoms in the complaint."""
        flags: List[str] = []
        for pat, msg in self._red_flag_patterns:
            if pat.search(text):
                flags.append(msg)
        return flags

    def _detect_category(self, text: str) -> ComplaintCategory:
        """Determine the category of the complaint (acute/chronic/etc.)."""
        # Check mental/emotional first
        mind_score = sum(1 for p in self._system_patterns["Mind"] if p.search(text))
        if mind_score >= 2:
            return ComplaintCategory.MENTAL_EMOTIONAL

        # Check for trauma patterns
        if re.search(r"\b(injur(y|ed)|accident|fell|hit|broke|burn(ed)?|cut|trauma|whiplash)\b", text, re.IGNORECASE):
            return ComplaintCategory.TRAUMATIC

        # Check for developmental
        if re.search(r"\b(pregnan(t|cy)|infant|toddler|child|adolescen(t|ce)|puberty|menopaus(e|al))\b", text, re.IGNORECASE):
            return ComplaintCategory.DEVELOPMENTAL

        # Acute vs chronic vs recurring
        acute = any(p.search(text) for p in self._duration_patterns["acute"])
        chronic = any(p.search(text) for p in self._duration_patterns["chronic"])
        recurring = any(p.search(text) for p in self._duration_patterns["recurring"])

        if recurring and not chronic:
            return ComplaintCategory.RECURRING
        if acute and not chronic:
            return ComplaintCategory.ACUTE
        if chronic:
            return ComplaintCategory.CHRONIC
        return ComplaintCategory.ACUTE  # default

    def _determine_urgency(
        self,
        red_flags: List[str],
        category: ComplaintCategory,
        text: str,
    ) -> Urgency:
        """Determine urgency based on red flags and category."""
        if red_flags:
            # Any red flag → at least urgent
            return Urgency.EMERGENCY
        if category == ComplaintCategory.ACUTE:
            return Urgency.PRIORITY
        if category == ComplaintCategory.TRAUMATIC:
            return Urgency.PRIORITY
        return Urgency.ROUTINE

    def _top_chapter(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """Get the top-scoring chapter and confidence."""
        if not scores:
            return "General", 0.0
        total = sum(scores.values())
        chapter = max(scores, key=lambda k: scores[k])
        confidence = scores[chapter] / total if total > 0 else 0.0
        return chapter, round(confidence, 2)

    def _secondary_chapters(self, scores: Dict[str, float], primary: str) -> List[str]:
        """Get secondary chapters (with at least 1 point, excluding primary)."""
        return [c for c, s in sorted(scores.items(), key=lambda x: -x[1]) if c != primary and s >= 1][:3]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract notable medical/keyword terms."""
        keywords: Set[str] = set()
        for patterns in self._system_patterns.values():
            for pat in patterns:
                for m in pat.findall(text):
                    if isinstance(m, str) and 3 < len(m) < 30:
                        keywords.add(m)
        return sorted(keywords)[:20]

    def _recommend_questions(
        self,
        chapter: str,
        category: ComplaintCategory,
        urgency: Urgency,
        red_flags: List[str],
    ) -> List[str]:
        """Recommend which questions to ask first."""
        recs: List[str] = ["O.01", "O.02"]  # Always start with opening

        if urgency == Urgency.EMERGENCY:
            # Compress to essential intake
            return recs + ["CC.01", "CC.04", "H.01"]

        # If mental/emotional primary, go deep into Mind
        if category == ComplaintCategory.MENTAL_EMOTIONAL or chapter == "Mind":
            recs += ["MN.01", "MN.02", "MN.04", "MN.06", "MN.08"]

        # Always cover modalities
        recs += ["M.01", "M.02", "M.03", "M.04"]

        # Concomitants - the most discriminative
        recs += ["CN.01", "CN.02"]

        # If acute, prioritize history and causation
        if category == ComplaintCategory.ACUTE:
            recs += ["CC.04", "H.01", "H.02"]

        # Chief complaint detail
        recs += ["CC.01", "CC.02"]

        # Generals at the end
        recs += ["G.01", "G.02", "G.03"]

        return recs

    def _estimate_duration(self, category: ComplaintCategory, urgency: Urgency) -> int:
        """Estimate intake duration in seconds."""
        if urgency == Urgency.EMERGENCY:
            return 600  # 10 min focused
        if category == ComplaintCategory.ACUTE:
            return 1800  # 30 min
        if category == ComplaintCategory.CHRONIC:
            return 5400  # 90 min
        return 3600  # 60 min default

    def _build_rationale(
        self,
        chapter: str,
        category: ComplaintCategory,
        urgency: Urgency,
        red_flags: List[str],
        scores: Dict[str, float],
    ) -> str:
        """Build a human-readable rationale for the triage."""
        parts = [
            f"Classified to chapter '{chapter}' based on keyword match (score {scores.get(chapter, 0)}).",
            f"Category: {category.value}.",
        ]
        if red_flags:
            parts.append(f"⚠ {len(red_flags)} red flag(s) detected: {'; '.join(red_flags)}")
        parts.append(f"Urgency: {urgency.value}.")
        return " ".join(parts)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_triage(complaint: str) -> TriageResult:
    """Quick helper to triage a chief complaint."""
    return ChiefComplaintTriager().triage(complaint)
