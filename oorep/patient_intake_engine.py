"""
Patient Intake Engine (Module #131)

The central orchestrator for a homeopathic patient interview. Combines:
  - Chief complaint triage (Module #133)
  - The question bank (Module #132)
  - Adaptive sequencing (Module #123)
  - Active learning tracker (Module #129)
  - Case workup analyzer (Module #122)
  - Symptom capture and validation

Maintains the interview state (current phase, asked questions, captured
symptoms, modality grid), produces the next question to ask, and emits
a structured case snapshot when the interview is complete.

Usage:
    from oorep.patient_intake_engine import PatientIntakeEngine
    engine = PatientIntakeEngine()
    engine.start(chief_complaint="I've had migraines for 3 days")
    question = engine.next_question()
    engine.record_answer("the pain is throbbing, on the right side")
    snapshot = engine.complete()
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from .interview_question_bank import (
        InterviewQuestionBank, InterviewQuestion, QuestionPhase, QuestionDepth
    )
    from .chief_complaint_triager import ChiefComplaintTriager, TriageResult
    from .active_learning_intake_tracker import ActiveLearningIntakeTracker
    from .information_theoretic_case_workup import CaseWorkupAnalyzer
    from .discriminant_rubric_selector import DiscriminantRubricSelector
except Exception:
    from interview_question_bank import (
        InterviewQuestionBank, InterviewQuestion, QuestionPhase, QuestionDepth
    )
    from chief_complaint_triager import ChiefComplaintTriager, TriageResult
    from active_learning_intake_tracker import ActiveLearningIntakeTracker
    from information_theoretic_case_workup import CaseWorkupAnalyzer
    from discriminant_rubric_selector import DiscriminantRubricSelector


class IntakeStatus(Enum):
    """Status of the interview."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_FOLLOWUP = "awaiting_followup"  # Asked a question, waiting for deep probe
    READY_TO_COMPLETE = "ready_to_complete"
    COMPLETE = "complete"
    ABANDONED = "abandoned"


@dataclass
class CapturedSymptom:
    """A symptom captured during the interview."""
    symptom_id: str
    text: str                           # The patient's words
    chapter: str                        # Mind, Head, Sleep, etc.
    question_id: str                    # Which question elicited it
    phase: QuestionPhase
    grade: int = 0                      # 0=absent, 1-4=presence
    modality_axes: List[str] = field(default_factory=list)
    srp_score: float = 0.0              # How SRP-like is this symptom?
    keywords: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class Modality:
    """A modality captured for a symptom (amelioration/aggravation)."""
    symptom_id: str
    axis: str                           # time, temperature, motion, position, etc.
    direction: str                      # "amelioration" or "aggravation"
    value: str                          # "evening", "warmth", "lying down", etc.
    confidence: float = 0.5


@dataclass
class IntakeSession:
    """A complete patient interview session."""
    session_id: str
    started_at: str
    completed_at: Optional[str] = None
    chief_complaint: str = ""
    triage: Optional[TriageResult] = None
    symptoms: List[CapturedSymptom] = field(default_factory=list)
    modalities: List[Modality] = field(default_factory=list)
    asked_questions: List[str] = field(default_factory=list)
    skipped_questions: List[str] = field(default_factory=list)
    phase_progress: Dict[QuestionPhase, int] = field(default_factory=dict)
    case_completeness: float = 0.0
    sufficiency: float = 0.0
    candidate_remedies: List[str] = field(default_factory=list)
    notes: str = ""


class PatientIntakeEngine:
    """
    Orchestrates a complete homeopathic patient interview.
    """

    def __init__(self):
        self.bank = InterviewQuestionBank()
        self.triager = ChiefComplaintTriager()
        self.workup = CaseWorkupAnalyzer()
        self.session: Optional[IntakeSession] = None
        self._current_question: Optional[InterviewQuestion] = None
        self._pending_followup: List[str] = []  # Follow-up prompts queued
        self._symptom_counter: int = 0

    def start(
        self,
        chief_complaint: str,
        candidate_remedies: Optional[List[str]] = None,
    ) -> IntakeSession:
        """
        Begin a new intake session.

        Parameters
        ----------
        chief_complaint : str
            The patient's initial complaint in their own words.
        candidate_remedies : list of str, optional
            Pre-existing remedy candidates (from a prior repertorization).
        """
        import uuid
        triage = self.triager.triage(chief_complaint)
        self.session = IntakeSession(
            session_id=str(uuid.uuid4())[:8],
            started_at=datetime.now().isoformat(),
            chief_complaint=chief_complaint,
            triage=triage,
            candidate_remedies=candidate_remedies or [],
            phase_progress={phase: 0 for phase in QuestionPhase},
        )
        # Build candidate pool from triage recommendations
        if not self.session.candidate_remedies:
            # Default: top 30 remedies for sufficiency scoring
            from oorep._v39_index import build_remedy_grade_index
            from oorep.homeopathic_repertory import HomeopathicRepertory
            rep = HomeopathicRepertory()
            index = build_remedy_grade_index(rep)
            self.session.candidate_remedies = [
                r for r, _ in sorted(index.items(), key=lambda x: -len(x[1]))[:30]
            ]
        return self.session

    def next_question(self) -> Optional[InterviewQuestion]:
        """
        Return the next question to ask, or None if interview is complete.
        """
        if self.session is None:
            return None

        # If we have a follow-up queued, use it
        if self._pending_followup and self._current_question is not None:
            # Convert the prompt into a "virtual" probe question
            from oorep.interview_question_bank import InterviewQuestion
            probe = InterviewQuestion(
                question_id=f"{self._current_question.question_id}.probe",
                phase=self._current_question.phase,
                chapter=self._current_question.chapter,
                question_text=self._pending_followup.pop(0),
                question_type=self._current_question.question_type,
                depth=QuestionDepth.DEEP,
                rationale="Probe for more detail on previous answer.",
                srp_potential=0.7,
                expected_duration_sec=30,
            )
            return probe

        # Move to the next question in our recommended sequence
        recommended = self.session.triage.recommended_questions if self.session.triage else []
        asked = set(self.session.asked_questions)
        skipped = set(self.session.skipped_questions)
        # Find first unasked unskipped question
        for qid in recommended:
            if qid in asked or qid in skipped:
                continue
            q = self.bank.get_question(qid)
            if q is None:
                continue
            self._current_question = q
            return q

        # If recommended exhausted, find next unasked question in phase order
        for phase in self.bank.get_phase_order():
            phase_questions = self.bank.get_questions_for_phase(phase)
            for q in phase_questions:
                if q.question_id in asked or q.question_id in skipped:
                    continue
                self._current_question = q
                return q

        # Interview complete
        return None

    def record_answer(
        self,
        answer: str,
        grade: int = 3,
        question_id: Optional[str] = None,
    ) -> List[CapturedSymptom]:
        """
        Record the patient's answer to the current question.

        Extracts symptoms, modalities, and keywords from the answer.
        Returns the symptoms captured.
        """
        if self.session is None or self._current_question is None:
            return []

        q = self._current_question
        qid = question_id or q.question_id

        # Mark question as asked
        if qid not in self.session.asked_questions:
            self.session.asked_questions.append(qid)

        # Update phase progress
        self.session.phase_progress[q.phase] = (
            self.session.phase_progress.get(q.phase, 0) + 1
        )

        # Extract symptoms from the answer
        symptoms = self._extract_symptoms(answer, q)

        # Extract modalities
        modalities = self._extract_modalities(answer, q, symptoms)
        self.session.modalities.extend(modalities)

        # Add symptoms
        self.session.symptoms.extend(symptoms)

        # Check if answer is vague and queue follow-up
        if self._is_vague(answer) and q.follow_up_prompts:
            self._pending_followup = list(q.follow_up_prompts)

        return symptoms

    def skip_question(self, question_id: str) -> None:
        """Mark a question as skipped (e.g. not applicable)."""
        if self.session is not None and question_id not in self.session.skipped_questions:
            self.session.skipped_questions.append(question_id)

    def get_status(self) -> IntakeStatus:
        """Get the current status of the interview."""
        if self.session is None:
            return IntakeStatus.NOT_STARTED
        if self.session.completed_at:
            return IntakeStatus.COMPLETE
        next_q = self.next_question()
        if next_q is None:
            return IntakeStatus.READY_TO_COMPLETE
        if self._pending_followup:
            return IntakeStatus.AWAITING_FOLLOWUP
        return IntakeStatus.IN_PROGRESS

    def complete(self) -> IntakeSession:
        """
        Complete the interview and produce a final case snapshot.
        """
        if self.session is None:
            raise ValueError("No active session. Call start() first.")

        self.session.completed_at = datetime.now().isoformat()

        # Compute case completeness
        symptoms = [s.text for s in self.session.symptoms]
        candidates = self.session.candidate_remedies
        if candidates and symptoms:
            try:
                report = self.workup.assess(symptoms=symptoms, candidate_pool=candidates)
                self.session.case_completeness = report.case_completeness
                self.session.sufficiency = report.sufficiency_score
            except Exception:
                self.session.case_completeness = 0.5
                self.session.sufficiency = 0.5

        return self.session

    def to_case_summary(self) -> str:
        """Render a SOAP-style summary of the captured case."""
        if self.session is None:
            return "No session."

        s = self.session
        lines = [
            f"# Case Session {s.session_id}",
            f"Started: {s.started_at}",
            f"Completed: {s.completed_at or 'in progress'}",
            "",
            "## Chief Complaint",
            s.chief_complaint,
            "",
            "## Triage",
            f"- Chapter: {s.triage.chapter if s.triage else 'N/A'}",
            f"- Category: {s.triage.category.value if s.triage else 'N/A'}",
            f"- Urgency: {s.triage.urgency.value if s.triage else 'N/A'}",
            "",
            f"## Symptoms ({len(s.symptoms)})",
        ]
        for sym in s.symptoms:
            lines.append(
                f"- [{sym.grade}] {sym.text}  *(chapter: {sym.chapter}, "
                f"SRP: {sym.srp_score:.1f}, q: {sym.question_id})*"
            )
        if s.modalities:
            lines.append("")
            lines.append(f"## Modalities ({len(s.modalities)})")
            for mod in s.modalities:
                lines.append(
                    f"- {mod.symptom_id}: {mod.axis} = {mod.direction} from {mod.value}"
                )
        lines.append("")
        lines.append("## Quality")
        lines.append(f"- Case completeness: {s.case_completeness:.2f}")
        lines.append(f"- Sufficiency: {s.sufficiency:.2f}")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize the session to JSON."""
        if self.session is None:
            return "{}"
        return json.dumps(self.session, default=lambda o: o.__dict__, indent=2)

    # ── Internal extractors ────────────────────────────────────────

    def _extract_symptoms(
        self,
        answer: str,
        question: InterviewQuestion,
    ) -> List[CapturedSymptom]:
        """Extract symptoms from a free-text answer."""
        if not answer or not answer.strip():
            return []

        # Split into sentences / clauses
        sentences = self._split_sentences(answer)
        symptoms: List[CapturedSymptom] = []
        for sent in sentences:
            if len(sent.strip()) < 3:
                continue
            self._symptom_counter += 1
            symptom = CapturedSymptom(
                symptom_id=f"S{self._symptom_counter:03d}",
                text=sent.strip(),
                chapter=question.chapter,
                question_id=question.question_id,
                phase=question.phase,
                grade=self._infer_grade(sent),
                modality_axes=list(question.modality_axes),
                srp_score=self._score_srp(sent, question),
                keywords=self._extract_keywords(sent),
                timestamp=datetime.now().isoformat(),
            )
            symptoms.append(symptom)
        return symptoms

    def _split_sentences(self, text: str) -> List[str]:
        """Naive sentence splitter."""
        import re
        # Split on . ; ! ? and newlines
        parts = re.split(r"[.!?;\n]+", text)
        return [p.strip() for p in parts if p.strip()]

    def _infer_grade(self, text: str) -> int:
        """Infer the grade (0-4) of a symptom from its text."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["no ", "not ", "never", "denies", "haven't"]):
            return 0
        if any(w in text_lower for w in ["always", "constantly", "severe", "extreme", "terrible"]):
            return 4
        if any(w in text_lower for w in ["often", "frequently", "really", "very"]):
            return 3
        if any(w in text_lower for w in ["sometimes", "occasionally", "mild"]):
            return 2
        if any(w in text_lower for w in ["slight", "barely", "minor"]):
            return 1
        return 2  # default moderate

    def _score_srp(self, text: str, question: InterviewQuestion) -> float:
        """Score how SRP-like (Strange-Rare-Peculiar) the answer is."""
        score = question.srp_potential * 0.5
        text_lower = text.lower()
        # SRP marker words
        srp_markers = [
            "strange", "weird", "peculiar", "unusual", "uncommon", "rare",
            "only", "specifically", "exactly", "as if", "like a",
            "no one", "never had", "since", "every time",
        ]
        for marker in srp_markers:
            if marker in text_lower:
                score += 0.1
        return min(1.0, score)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract notable keywords from a symptom text."""
        import re
        # Words 3+ chars, alpha only
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        # Deduplicate
        return list(dict.fromkeys(words))[:10]

    def _extract_modalities(
        self,
        answer: str,
        question: InterviewQuestion,
        symptoms: List[CapturedSymptom],
    ) -> List[Modality]:
        """Extract modalities (better/worse) from the answer."""
        modalities: List[Modality] = []
        if not symptoms:
            return modalities
        symptom_id = symptoms[0].symptom_id
        text_lower = answer.lower()

        # Amelioration patterns
        amel_patterns = [
            (r"better\s+(from|with|when|after|if|by)\s+([a-z\s]+?)(?:\.|,|;|and|$)", "amelioration"),
            (r"(improves?|helps?|relieves?)\s+(with|when|by|from)\s+([a-z\s]+?)(?:\.|,|;|and|$)", "amelioration"),
            (r"ameliorated?\s+by\s+([a-z\s]+?)(?:\.|,|;|and|$)", "amelioration"),
        ]
        # Aggravation patterns
        agg_patterns = [
            (r"worse\s+(from|with|when|after|if|by)\s+([a-z\s]+?)(?:\.|,|;|and|$)", "aggravation"),
            (r"(worsens?|aggravates?|triggers?)\s+(with|when|by|from)\s+([a-z\s]+?)(?:\.|,|;|and|$)", "aggravation"),
            (r"aggravated?\s+by\s+([a-z\s]+?)(?:\.|,|;|and|$)", "aggravation"),
        ]
        import re
        for pattern, direction in amel_patterns + agg_patterns:
            for m in re.finditer(pattern, text_lower):
                value = (m.group(2) if direction in ("amelioration", "aggravation") and "by" not in m.group(0) else m.group(1)).strip()
                # Determine axis heuristically
                axis = self._infer_axis(value)
                modalities.append(Modality(
                    symptom_id=symptom_id,
                    axis=axis,
                    direction=direction,
                    value=value,
                    confidence=0.7,
                ))

        # Time-of-day patterns
        time_patterns = [
            (r"worse\s+(at|in)\s+the\s+(morning|afternoon|evening|night)", "aggravation"),
            (r"better\s+(at|in)\s+the\s+(morning|afternoon|evening|night)", "amelioration"),
            (r"worse\s+at\s+(\d{1,2}\s*(am|pm|o'clock)?)", "aggravation"),
            (r"better\s+at\s+(\d{1,2}\s*(am|pm|o'clock)?)", "amelioration"),
        ]
        for pattern, direction in time_patterns:
            for m in re.finditer(pattern, text_lower):
                value = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
                modalities.append(Modality(
                    symptom_id=symptom_id,
                    axis="time",
                    direction=direction,
                    value=value,
                    confidence=0.8,
                ))

        return modalities

    def _infer_axis(self, value: str) -> str:
        """Heuristically determine the modality axis from a value phrase."""
        v = value.lower()
        if any(w in v for w in ["morning", "evening", "night", "am", "pm", "3am", "clock"]):
            return "time"
        if any(w in v for w in ["heat", "cold", "warm", "cool", "temperature"]):
            return "temperature"
        if any(w in v for w in ["motion", "moving", "walking", "running", "rest", "lying"]):
            return "motion"
        if any(w in v for w in ["sitting", "standing", "lying", "side", "position"]):
            return "position"
        if any(w in v for w in ["eat", "drink", "food", "water", "coffee", "tea"]):
            return "food"
        return "general"

    def _is_vague(self, answer: str) -> bool:
        """Determine if the answer is too vague to proceed without follow-up."""
        if not answer:
            return True
        words = answer.split()
        if len(words) < 3:
            return True
        vague_phrases = [
            "i don't know", "not sure", "maybe", "kind of", "sort of",
            "normal", "fine", "ok", "i guess",
        ]
        text_lower = answer.lower()
        return any(p in text_lower for p in vague_phrases)


# ── Quick function ─────────────────────────────────────────────────────────

def quick_intake(chief_complaint: str) -> PatientIntakeEngine:
    """Quick helper: start an intake session and return the engine."""
    engine = PatientIntakeEngine()
    engine.start(chief_complaint)
    return engine
