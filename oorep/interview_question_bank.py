"""
Homeopathic Interview Question Bank (Module #132)

A master database of evidence-based homeopathic case-taking questions
organized by:
  - Phase (chief complaint → modalities → concomitants → mind → generals → constitution)
  - Chapter (Mind, Generals, Sleep, Dreams, Appetite, Stomach, etc.)
  - Question type (open, closed, scale, multiple choice)
  - Depth level (introductory, intermediate, deep probe)
  - SRP potential (does this question tend to elicit Strange-Rare-Peculiar symptoms?)
  - Discriminative power (which remedies does this question help differentiate?)

Each question knows:
  - Why it matters (the homeopathic principle)
  - What SRP symptoms to look for in the answer
  - Which modalities to probe (time, temperature, motion, position, etc.)
  - Follow-up prompts for vague answers

The bank is consumed by:
  - PatientIntakeEngine (orchestrates the interview)
  - AdaptiveSymptomSequencer (chooses next question)
  - ActiveLearningIntakeTracker (tracks coverage)

Usage:
    from oorep.interview_question_bank import InterviewQuestionBank, QuestionPhase
    bank = InterviewQuestionBank()
    chief_complaint_questions = bank.get_questions_for_phase(QuestionPhase.CHIEF_COMPLAINT)
    deep_mind = bank.get_questions_for_chapter("Mind", depth=QuestionDepth.DEEP)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class QuestionPhase(Enum):
    """The six phases of a classical homeopathic interview."""
    OPENING = "opening"               # Welcome, context, chief concern
    CHIEF_COMPLAINT = "chief_complaint"  # The main reason for visit
    HISTORY = "history"                # Etiology, timeline, prior treatments
    MODALITIES = "modalities"         # What makes better/worse
    CONCOMITANTS = "concomitants"     # Symptoms accompanying the chief
    MIND = "mind"                      # Mental/emotional pattern
    GENERALS = "generals"             # Sleep, appetite, thermal, etc.
    CONSTITUTION = "constitution"     # Overall pattern, lifelong tendencies
    REVIEW = "review"                  # Open-ended: anything else?


class QuestionDepth(Enum):
    """How deep to probe with this question."""
    INTRODUCTORY = 1   # First-pass broad question
    INTERMEDIATE = 2  # Mid-depth follow-up
    DEEP = 3          # Probe for SRP / peculiar symptoms


class QuestionType(Enum):
    """The format of the question."""
    OPEN = "open"              # "Tell me about..."
    CLOSED = "closed"          # Yes/no
    SCALE = "scale"            # 0-10 severity
    MULTIPLE_CHOICE = "mc"     # Pick from options
    PROBE = "probe"            # "What else?"


@dataclass
class InterviewQuestion:
    """A single interview question with all its metadata."""
    question_id: str
    phase: QuestionPhase
    chapter: str                      # Mind, Generals, Sleep, etc.
    question_text: str                # The question itself
    question_type: QuestionType
    depth: QuestionDepth
    rationale: str                    # Why this matters (homeopathic principle)
    srp_potential: float              # 0-1: likelihood of eliciting SRP
    modality_axes: List[str] = field(default_factory=list)  # ["time", "temperature", "motion", ...]
    follow_up_prompts: List[str] = field(default_factory=list)  # What to ask if answer is vague
    expected_duration_sec: int = 60   # ~how long the answer takes
    discriminative_remedies: List[str] = field(default_factory=list)  # Helps differentiate these
    keywords_to_capture: List[str] = field(default_factory=list)
    is_required: bool = True


class InterviewQuestionBank:
    """
    Master database of homeopathic case-taking questions.
    """

    def __init__(self):
        self._questions: Dict[str, InterviewQuestion] = {}
        self._by_phase: Dict[QuestionPhase, List[str]] = defaultdict(list)
        self._by_chapter: Dict[str, List[str]] = defaultdict(list)
        self._build_question_bank()

    def _register(self, q: InterviewQuestion) -> None:
        self._questions[q.question_id] = q
        self._by_phase[q.phase].append(q.question_id)
        self._by_chapter[q.chapter].append(q.question_id)

    def _build_question_bank(self) -> None:
        """Populate the bank with the canonical interview questions."""

        # ─── OPENING (Phase 0: rapport & chief concern) ─────────────────
        self._register(InterviewQuestion(
            question_id="O.01",
            phase=QuestionPhase.OPENING,
            chapter="General",
            question_text="What brings you here today? In your own words, what is the main concern?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTRODUCTORY,
            rationale="Hahnemann §84: 'The patient details his sufferings.' Let the patient speak first.",
            srp_potential=0.3,
            modality_axes=[],
            follow_up_prompts=["Take your time.", "What else?", "When did this first start?"],
            expected_duration_sec=120,
            keywords_to_capture=["chief_complaint", "duration", "onset"],
        ))
        self._register(InterviewQuestion(
            question_id="O.02",
            phase=QuestionPhase.OPENING,
            chapter="General",
            question_text="How has this affected your daily life? What's most difficult about it?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTRODUCTORY,
            rationale="Reveals the functional impact and what the patient values most.",
            srp_potential=0.4,
            modality_axes=[],
            follow_up_prompts=["What does that stop you from doing?"],
            expected_duration_sec=90,
        ))

        # ─── CHIEF COMPLAINT (Phase 1: localize & characterize) ────────
        self._register(InterviewQuestion(
            question_id="CC.01",
            phase=QuestionPhase.CHIEF_COMPLAINT,
            chapter="General",
            question_text="Can you describe the exact sensation? What does it feel like?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Kent: 'The character of the symptom is paramount.' Sensation reveals the remedy.",
            srp_potential=0.7,
            modality_axes=["sensation"],
            follow_up_prompts=[
                "Is it sharp, dull, burning, throbbing, pressing?",
                "Does it feel like anything you'd compare it to?",
            ],
            expected_duration_sec=60,
            keywords_to_capture=["sensation", "character", "quality"],
        ))
        self._register(InterviewQuestion(
            question_id="CC.02",
            phase=QuestionPhase.CHIEF_COMPLAINT,
            chapter="General",
            question_text="Where exactly in your body do you feel this? Can you point to it?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Location often narrows the chapter. Peculiar localizations (e.g. 'only left temple') are SRP.",
            srp_potential=0.8,
            modality_axes=["location"],
            follow_up_prompts=[
                "Does it stay in one place or move around?",
                "Side preference — left or right?",
            ],
            expected_duration_sec=45,
            discriminative_remedies=["Lach.", "Lyco.", "Sulph.", "Calc."],
        ))
        self._register(InterviewQuestion(
            question_id="CC.03",
            phase=QuestionPhase.CHIEF_COMPLAINT,
            chapter="General",
            question_text="How would you rate the intensity right now, on a scale of 0 to 10?",
            question_type=QuestionType.SCALE,
            depth=QuestionDepth.INTRODUCTORY,
            rationale="Establishes baseline severity and tracks response to treatment.",
            srp_potential=0.1,
            modality_axes=[],
            follow_up_prompts=["When is it at its worst? When at its best?"],
            expected_duration_sec=20,
            is_required=True,
        ))
        self._register(InterviewQuestion(
            question_id="CC.04",
            phase=QuestionPhase.CHIEF_COMPLAINT,
            chapter="General",
            question_text="When did this first begin? Was there a specific trigger?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Etiology drives many prescriptions (e.g. ailments from grief, from anger, from cold).",
            srp_potential=0.5,
            modality_axes=["time"],
            follow_up_prompts=[
                "Did anything significant happen around that time?",
                "An illness? Loss? Shock? Change of life?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["onset", "etiology", "trigger", "causation"],
        ))

        # ─── HISTORY (Phase 2: timeline & treatments) ───────────────────
        self._register(InterviewQuestion(
            question_id="H.01",
            phase=QuestionPhase.HISTORY,
            chapter="General",
            question_text="What have you tried so far for this? What worked, what didn't?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Hering's Law: track direction of cure. Suppression is critical to identify.",
            srp_potential=0.6,
            modality_axes=["treatment_response"],
            follow_up_prompts=[
                "Any medications? Herbal remedies? Other therapies?",
                "Did any treatment make the original symptom go away but something new appear?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["suppression", "treatments", "response"],
        ))
        self._register(InterviewQuestion(
            question_id="H.02",
            phase=QuestionPhase.HISTORY,
            chapter="General",
            question_text="Walk me through the timeline. When did each new symptom appear, and when did old ones go?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.DEEP,
            rationale="Layer theory: each suppressed layer has its own remedy. Hering's direction of cure.",
            srp_potential=0.7,
            modality_axes=["time"],
            follow_up_prompts=["Has the character of the problem changed over time?"],
            expected_duration_sec=120,
        ))
        self._register(InterviewQuestion(
            question_id="H.03",
            phase=QuestionPhase.HISTORY,
            chapter="Family",
            question_text="What's the health history in your immediate family? Any similar conditions?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Miasmatic inheritance (Tuberculous, Sycotic, etc.) shapes susceptibility.",
            srp_potential=0.4,
            modality_axes=[],
            follow_up_prompts=["Parents, siblings, grandparents?"],
            expected_duration_sec=60,
        ))

        # ─── MODALITIES (Phase 3: what makes better/worse) ──────────────
        self._register(InterviewQuestion(
            question_id="M.01",
            phase=QuestionPhase.MODALITIES,
            chapter="General",
            question_text="What makes it better? Anything at all — even small things.",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Modalities are the highest-weight differentiators in repertorization (4-grade rubrics).",
            srp_potential=0.9,
            modality_axes=["amelioration"],
            follow_up_prompts=[
                "Position? Motion? Temperature? Time of day? Eating? Drinking? Company?",
                "Even the strangest thing — does anything help, even a little?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["amelioration", "better_from"],
            discriminative_remedies=["Ars.", "Puls.", "Nux-v.", "Rhus-t."],
        ))
        self._register(InterviewQuestion(
            question_id="M.02",
            phase=QuestionPhase.MODALITIES,
            chapter="General",
            question_text="What makes it worse? What triggers it or makes it stronger?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Aggravations are equally weighted. Vithoulkas: 'The modalities are the backbone.'",
            srp_potential=0.9,
            modality_axes=["aggravation"],
            follow_up_prompts=[
                "Time of day? Weather? Food? Emotion? Movement? Rest?",
                "Any particular food, drink, or activity?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["aggravation", "worse_from"],
        ))
        self._register(InterviewQuestion(
            question_id="M.03",
            phase=QuestionPhase.MODALITIES,
            chapter="General",
            question_text="Is there a time of day when it's consistently better or worse?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Time modalities (worse at 3am, better evening) are highly characteristic.",
            srp_potential=0.8,
            modality_axes=["time"],
            follow_up_prompts=[
                "Worse in the morning, evening, night?",
                "Around a specific hour?",
            ],
            expected_duration_sec=60,
            discriminative_remedies=["Ars.", "Nux-v.", "Puls.", "Sulph.", "Lyc."],
        ))
        self._register(InterviewQuestion(
            question_id="M.04",
            phase=QuestionPhase.MODALITIES,
            chapter="General",
            question_text="What about temperature — are you more comfortable in warmth or coolness?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Thermal modality separates hot remedies (Puls., Sulph.) from cold (Ars., Calc.).",
            srp_potential=0.7,
            modality_axes=["temperature"],
            follow_up_prompts=["What about fresh air?"],
            expected_duration_sec=45,
            discriminative_remedies=["Puls.", "Sulph.", "Ars.", "Calc.", "Sil."],
        ))
        self._register(InterviewQuestion(
            question_id="M.05",
            phase=QuestionPhase.MODALITIES,
            chapter="General",
            question_text="Does motion or rest help? Lying still vs. walking around?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Rhus-t. (better from motion), Bry. (worse from motion), etc.",
            srp_potential=0.6,
            modality_axes=["motion"],
            follow_up_prompts=["Does gentle movement help, or only vigorous activity?"],
            expected_duration_sec=45,
            discriminative_remedies=["Rhus-t.", "Bry.", "Puls.", "Ars."],
        ))
        self._register(InterviewQuestion(
            question_id="M.06",
            phase=QuestionPhase.MODALITIES,
            chapter="General",
            question_text="Is there a position that helps — sitting, lying, curled up, stretched out?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Position modalities are peculiar when extreme (e.g. 'knees to chest').",
            srp_potential=0.7,
            modality_axes=["position"],
            follow_up_prompts=["Any specific posture that makes a difference?"],
            expected_duration_sec=45,
        ))

        # ─── CONCOMITANTS (Phase 4: accompanying symptoms) ─────────────
        self._register(InterviewQuestion(
            question_id="CN.01",
            phase=QuestionPhase.CONCOMITANTS,
            chapter="General",
            question_text="When this symptom is at its worst, do you notice anything else happening at the same time? Any other symptoms that come with it?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.DEEP,
            rationale="Concomitants are key differentiators. Kent: 'The concomitants decide the case.'",
            srp_potential=0.9,
            modality_axes=["concomitant"],
            follow_up_prompts=[
                "Nausea with the headache? Chills? Sweating? Irritability? Anxiety?",
                "Anything at all that you notice in your body, mind, or emotions when this happens?",
            ],
            expected_duration_sec=120,
            keywords_to_capture=["concomitant"],
            discriminative_remedies=["Acon.", "Ars.", "Bell.", "Puls.", "Nux-v."],
        ))
        self._register(InterviewQuestion(
            question_id="CN.02",
            phase=QuestionPhase.CONCOMITANTS,
            chapter="General",
            question_text="Is there anything strange, unusual, or peculiar that you've noticed with this? Anything that surprises you?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.DEEP,
            rationale="Direct SRP probe. SRP symptoms (Strange-Rare-Peculiar) carry the highest weight in classical prescribing.",
            srp_potential=1.0,
            modality_axes=["peculiar"],
            follow_up_prompts=[
                "Anything you'd think is weird? Anything that doesn't quite fit?",
                "Something you've never heard anyone else describe?",
            ],
            expected_duration_sec=120,
            discriminative_remedies=["Stram.", "Lach.", "Med.", "Phos.", "Nux-m."],
        ))
        self._register(InterviewQuestion(
            question_id="CN.03",
            phase=QuestionPhase.CONCOMITANTS,
            chapter="General",
            question_text="Are there any symptoms that bother you that seem unrelated to the main concern? Anything else going on?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Sometimes the unrelated symptom is the key to the case. 'A symptom is a symptom.'",
            srp_potential=0.5,
            modality_axes=[],
            follow_up_prompts=["Even small things you wouldn't normally mention to a doctor."],
            expected_duration_sec=90,
        ))

        # ─── MIND (Phase 5: mental/emotional pattern) ──────────────────
        self._register(InterviewQuestion(
            question_id="MN.01",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="How would you describe your emotional state lately? Your general mood?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTRODUCTORY,
            rationale="Vithoulkas: 'The mental state is the most important.' Mind symptoms grade 3-4 most often.",
            srp_potential=0.7,
            modality_axes=["emotion"],
            follow_up_prompts=[
                "Anxious? Irritable? Sad? Withdrawn? Restless?",
                "Have others noticed a change in you?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["mood", "emotion"],
        ))
        self._register(InterviewQuestion(
            question_id="MN.02",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="When you're not feeling well, do you prefer to be alone or with company?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Classic differentiator: Puls. (wants company), Stram./Ars. (wants to be alone).",
            srp_potential=0.8,
            modality_axes=["company"],
            follow_up_prompts=[
                "Does being alone make it better or worse?",
                "Specific people, or any company?",
            ],
            expected_duration_sec=45,
            discriminative_remedies=["Puls.", "Ars.", "Stram.", "Bry.", "Nux-v."],
        ))
        self._register(InterviewQuestion(
            question_id="MN.03",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="Does consolation or sympathy make you feel better, or worse?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Puls. (amel. consolation), Nat-m. (agg. consolation), Sep. (agg. consolation).",
            srp_potential=0.9,
            modality_axes=["consolation"],
            follow_up_prompts=["What about being told 'it'll be okay'?"],
            expected_duration_sec=45,
            discriminative_remedies=["Puls.", "Nat-m.", "Sep.", "Sil."],
        ))
        self._register(InterviewQuestion(
            question_id="MN.04",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="Are there any fears or anxieties that stand out? Anything that worries you excessively?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Specific fears are highly characteristic (fear of death, of being alone, of suffocation).",
            srp_potential=0.8,
            modality_axes=["fear"],
            follow_up_prompts=[
                "Fear of death? Of being alone? Of crowds? Of darkness?",
                "Health anxiety? Hypochondriacal fears?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["fear", "anxiety"],
        ))
        self._register(InterviewQuestion(
            question_id="MN.05",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="How is your memory and concentration? Any difficulty focusing?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Mental confusion is a strong SRP (e.g. 'as if in a dream').",
            srp_potential=0.5,
            modality_axes=["cognition"],
            follow_up_prompts=[
                "What about when reading?",
                "Do you lose your train of thought?",
            ],
            expected_duration_sec=60,
        ))
        self._register(InterviewQuestion(
            question_id="MN.06",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="How do you react to criticism or contradiction?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.DEEP,
            rationale="Highly characteristic: Lyc. (ego, domineering), Aur. (oversensitive), Staph. (indignation).",
            srp_potential=0.9,
            modality_axes=["reaction_to_criticism"],
            expected_duration_sec=45,
            discriminative_remedies=["Lyc.", "Aur.", "Staph.", "Nux-v.", "Ars."],
        ))
        self._register(InterviewQuestion(
            question_id="MN.07",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="How is your patience? Are you generally patient, or easily irritated?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Irritability patterns are strong remedy indicators.",
            srp_potential=0.5,
            modality_axes=["irritability"],
            follow_up_prompts=["Triggers for irritation?"],
            expected_duration_sec=45,
        ))
        self._register(InterviewQuestion(
            question_id="MN.08",
            phase=QuestionPhase.MIND,
            chapter="Mind",
            question_text="Are there any recurring thoughts or feelings you can't shake? Anything that preoccupies you?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.DEEP,
            rationale="Fixed ideas, persistent thoughts, anxieties are strong mental SRP symptoms.",
            srp_potential=0.9,
            modality_axes=["recurrent_thoughts"],
            follow_up_prompts=["Anything that goes round and round in your mind?"],
            expected_duration_sec=90,
        ))

        # ─── GENERALS (Phase 6: whole-person characteristics) ───────────
        self._register(InterviewQuestion(
            question_id="G.01",
            phase=QuestionPhase.GENERALS,
            chapter="Sleep",
            question_text="How is your sleep? Any trouble falling asleep, staying asleep, or waking early?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Sleep position (knees to chest, arms above head) and patterns are highly characteristic.",
            srp_potential=0.6,
            modality_axes=["sleep"],
            follow_up_prompts=["What position do you sleep in?", "What wakes you?"],
            expected_duration_sec=90,
            keywords_to_capture=["sleep"],
        ))
        self._register(InterviewQuestion(
            question_id="G.02",
            phase=QuestionPhase.GENERALS,
            chapter="Dreams",
            question_text="Do you remember your dreams? Any recurring themes or vivid ones?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Dreams are graded 3-4 in many remedies (dreams of fire, water, falling, etc.).",
            srp_potential=0.9,
            modality_axes=["dreams"],
            follow_up_prompts=[
                "Dreams of danger? Of water? Of fire? Animals? Falling?",
                "Are they vivid, anxious, peaceful?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["dreams"],
            discriminative_remedies=["Phos.", "Ars.", "Puls.", "Lach."],
        ))
        self._register(InterviewQuestion(
            question_id="G.03",
            phase=QuestionPhase.GENERALS,
            chapter="Appetite",
            question_text="How is your appetite? Thirst? Any cravings or aversions to specific foods?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Food cravings are highly characteristic: salt, sweets, fat, eggs, oysters, etc.",
            srp_potential=0.8,
            modality_axes=["appetite", "thirst", "food_cravings"],
            follow_up_prompts=[
                "Craving salt? Sweet? Sour? Spicy?",
                "Aversion to fat? Meat? Milk?",
                "How is your thirst?",
            ],
            expected_duration_sec=90,
            keywords_to_capture=["appetite", "thirst", "cravings", "aversions"],
            discriminative_remedies=["Phos.", "Calc.", "Lyc.", "Puls.", "Verat."],
        ))
        self._register(InterviewQuestion(
            question_id="G.04",
            phase=QuestionPhase.GENERALS,
            chapter="Generals",
            question_text="How does weather affect you? Hot, cold, damp, dry, storms?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Weather modalities are strong differentiators (Rhus-t. better dry, Med. better damp).",
            srp_potential=0.6,
            modality_axes=["weather"],
            expected_duration_sec=60,
            discriminative_remedies=["Rhus-t.", "Med.", "Dulc.", "Nux-m.", "Ars."],
        ))
        self._register(InterviewQuestion(
            question_id="G.05",
            phase=QuestionPhase.GENERALS,
            chapter="Generals",
            question_text="How is your energy? When in the day are you at your best, worst?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Energy patterns (morning better, evening better) indicate specific remedies.",
            srp_potential=0.4,
            modality_axes=["energy", "time"],
            expected_duration_sec=45,
        ))
        self._register(InterviewQuestion(
            question_id="G.06",
            phase=QuestionPhase.GENERALS,
            chapter="Perspiration",
            question_text="Do you sweat easily? Any specific areas, times, or circumstances?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Perspiration characteristics are graded 3-4 in many polycrest remedies.",
            srp_potential=0.5,
            modality_axes=["perspiration"],
            expected_duration_sec=45,
        ))
        self._register(InterviewQuestion(
            question_id="G.07",
            phase=QuestionPhase.GENERALS,
            chapter="Generals",
            question_text="Any food or drink that particularly agrees or disagrees with you?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Aversions and aggravations from specific foods are highly characteristic.",
            srp_potential=0.7,
            modality_axes=["food"],
            expected_duration_sec=60,
        ))

        # ─── CONSTITUTION (Phase 7: lifelong pattern) ──────────────────
        self._register(InterviewQuestion(
            question_id="CN.10",
            phase=QuestionPhase.CONSTITUTION,
            chapter="Generals",
            question_text="How have you been most of your life? What's your general pattern of health been?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Constitutional type reflects the deepest, most stable pattern of the person.",
            srp_potential=0.4,
            modality_axes=["constitution"],
            follow_up_prompts=["Tendency toward certain kinds of illness?"],
            expected_duration_sec=120,
        ))
        self._register(InterviewQuestion(
            question_id="CN.11",
            phase=QuestionPhase.CONSTITUTION,
            chapter="Generals",
            question_text="Has anyone in your family had a remedy that worked really well for them?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTERMEDIATE,
            rationale="Family constitutional patterns (e.g. Tuberculinum miasm) often run in families.",
            srp_potential=0.4,
            modality_axes=["constitution"],
            expected_duration_sec=60,
        ))

        # ─── REVIEW (Phase 8: open-ended close) ───────────────────────
        self._register(InterviewQuestion(
            question_id="R.01",
            phase=QuestionPhase.REVIEW,
            chapter="General",
            question_text="Is there anything else you'd like me to know? Anything at all that we haven't covered?",
            question_type=QuestionType.OPEN,
            depth=QuestionDepth.INTRODUCTORY,
            rationale="Vithoulkas: 'The most important symptom is often the last one mentioned.'",
            srp_potential=0.6,
            modality_axes=[],
            expected_duration_sec=120,
        ))

    # ── Query methods ────────────────────────────────────────────────

    def get_questions_for_phase(
        self,
        phase: QuestionPhase,
    ) -> List[InterviewQuestion]:
        """Return all questions for a given phase."""
        return [self._questions[qid] for qid in self._by_phase.get(phase, [])]

    def get_questions_for_chapter(
        self,
        chapter: str,
        depth: Optional[QuestionDepth] = None,
    ) -> List[InterviewQuestion]:
        """Return all questions for a given chapter, optionally filtered by depth."""
        qs = [self._questions[qid] for qid in self._by_chapter.get(chapter, [])]
        if depth is not None:
            qs = [q for q in qs if q.depth == depth]
        return qs

    def get_question(self, question_id: str) -> Optional[InterviewQuestion]:
        return self._questions.get(question_id)

    def get_srp_questions(
        self,
        min_potential: float = 0.7,
    ) -> List[InterviewQuestion]:
        """Return questions with high SRP potential (best for finding the simillimum)."""
        return [q for q in self._questions.values() if q.srp_potential >= min_potential]

    def get_all_questions(self) -> List[InterviewQuestion]:
        return list(self._questions.values())

    def get_phase_order(self) -> List[QuestionPhase]:
        """The classical order of phases."""
        return [
            QuestionPhase.OPENING,
            QuestionPhase.CHIEF_COMPLAINT,
            QuestionPhase.HISTORY,
            QuestionPhase.MODALITIES,
            QuestionPhase.CONCOMITANTS,
            QuestionPhase.MIND,
            QuestionPhase.GENERALS,
            QuestionPhase.CONSTITUTION,
            QuestionPhase.REVIEW,
        ]

    def total_count(self) -> int:
        return len(self._questions)

    def total_duration_estimate(self) -> int:
        """Total seconds to ask all questions (rough estimate)."""
        return sum(q.expected_duration_sec for q in self._questions.values())


# ── Quick function ─────────────────────────────────────────────────────────

def quick_bank() -> InterviewQuestionBank:
    """Quick helper: get the canonical question bank."""
    return InterviewQuestionBank()
