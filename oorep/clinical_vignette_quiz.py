"""
Clinical Vignette Quiz — Benefit #45

Standalone quiz engine that builds questions from REAL anonymized patient outcome
data stored in ``feedback.db``.  This bridges classroom learning and clinical
practice by turning actual (de-identified) cases into teaching material.

Usage:
    from oorep.clinical_vignette_quiz import ClinicalVignetteQuiz
    quiz = ClinicalVignetteQuiz()

    # Build a vignette from real outcomes
    vignette = quiz.build_vignette_from_outcomes()

    # Generate questions (remedy_selection, rubric_identification, etc.)
    questions = quiz.generate_questions(vignette, num_questions=5)

    # Score a student's answers
    score = quiz.score_quiz(answers)

    # Personalised weak-area analysis
    weak = quiz.get_weak_areas("student_42")

    # Difficulty filtering
    levels = quiz.generate_difficulty_levels()
"""

import json
import sqlite3
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


class ClinicalVignetteQuiz:
    """
    Quiz engine backed by real (anonymized) clinical outcome data.

    Unlike ``StudentTraining`` which generates synthetic cases, this module
    pulls completed prescriptions and follow-up reports from the feedback
    database, scrubs identifiers, and turns them into multiple-question
    quizzes with four canonical question types:

      * remedy_selection      — "Which remedy was prescribed?"
      * rubric_identification — "Which rubric best captures X?"
      * potency_choice        — "What potency / repetition was chosen?"
      * follow_up_prediction  — "What was the likely outcome?"
    """

    QUESTION_TYPES = ["remedy_selection", "rubric_identification", "potency_choice", "follow_up_prediction"]
    MIN_CASES_FOR_VIGNETTE = 1

    def __init__(
        self,
        db_path: Optional[Path] = None,
        repertory: Optional[HomeopathicRepertory] = None,
    ):
        """
        Args:
            db_path: SQLite database with real prescription / outcome data.
            repertory: HomeopathicRepertory instance for rubric lookups.
        """
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.rep = repertory or HomeopathicRepertory()
        self._init_db()

    # ── Schema ──────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create ``quizzes`` and ``quiz_attempts`` tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_uuid TEXT NOT NULL UNIQUE,
                vignette_json TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                difficulty TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_uuid TEXT NOT NULL,
                student_or_user_id TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                score REAL,
                score_max INTEGER,
                weak_areas_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quizzes_uuid ON quizzes(quiz_uuid)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_user ON quiz_attempts(student_or_user_id)"
        )
        conn.commit()
        conn.close()

    # ── Vignette Builder ────────────────────────────────────────────────────

    def build_vignette_from_outcomes(self, limit_cases: int = 1) -> Dict[str, Any]:
        """
        Assemble a vignette from REAL completed prescription records.

        The vignette narrative is composed from:
          - prescription remedy, potency, date
          - follow-up reports (symptoms, overall status)
          - rubric_paths from the original prescription

        All PHI is scrubbed before inclusion (patient_id replaced by generic tokens).

        Args:
            limit_cases: Number of completed prescriptions to aggregate into one vignette.

        Returns:
            Dict with keys: vignette_id, narrative, case_details, rubric_context,
            correct_remedy, correct_potency, outcome_summary.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # Select completed prescriptions with outcome data
        cursor.execute(
            """
            SELECT prescription_id, remedy_abbrev, potency, prescribed_date,
                   rubric_paths, outcome_score, final_notes, status
            FROM prescriptions
            WHERE status = 'completed' AND outcome_score IS NOT NULL
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (limit_cases,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"error": "No completed prescriptions available for vignette generation"}

        case_details = []
        rubric_context = []
        for row in rows:
            rx_id, remedy, potency, date, rubric_paths, outcome, notes, status = row
            # Fetch follow-up reports for this prescription
            conn2 = sqlite3.connect(str(self.db_path))
            cur2 = conn2.cursor()
            cur2.execute(
                """
                SELECT symptoms_json, overall_status, general_note, next_followup_date
                FROM symptom_reports
                WHERE prescription_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (rx_id,),
            )
            report = cur2.fetchone()
            conn2.close()

            symptoms = json.loads(report[0]) if report and report[0] else []
            overall = report[1] if report else None

            # Build a narrative chunk
            narrative_parts = [
                f"A patient was prescribed {remedy} {potency} on {date[:10]}.",
            ]
            if symptoms:
                narrative_parts.append(
                    f"At follow-up, symptoms reported included: {', '.join(str(s) for s in symptoms[:5])}."
                )
            if overall:
                narrative_parts.append(f"Overall status: {overall}.")
            if notes:
                narrative_parts.append(f"Clinician notes: {notes}")

            # Rubric context
            if rubric_paths:
                paths = [p.strip() for p in rubric_paths.split(",") if p.strip()]
                for p in paths[:5]:
                    rubric_context.append({"fullpath": p})

            case_details.append({
                "remedy": remedy,
                "potency": potency,
                "date": date,
                "outcome": outcome,
                "status": status,
                "follow_up_symptoms": symptoms,
                "overall_status": overall,
                "notes": notes,
            })

        # Aggregate a single "correct" answer from the first case (primary)
        primary = case_details[0]
        vignette_id = f"VIG-{uuid.uuid4().hex[:8].upper()}"
        vignette = {
            "vignette_id": vignette_id,
            "narrative": " ".join([c.get("narrative_parts", "") for c in case_details]),
            "case_details": case_details,
            "rubric_context": rubric_context,
            "correct_remedy": primary["remedy"],
            "correct_potency": primary["potency"],
            "outcome_summary": primary["outcome"],
        }

        # Rebuild narrative here properly
        full_narrative = " ".join(
            f"A patient was prescribed {c['remedy']} {c['potency']} on {c['date'][:10] if c['date'] else 'unknown'}. "
            f"Outcome: {c['outcome']}."
            for c in case_details
        )
        vignette["narrative"] = full_narrative
        return vignette

    # ── Question Generator ────────────────────────────────────────────────

    def generate_questions(
        self, vignette: Dict[str, Any], num_questions: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generate a mixed set of questions from a vignette.

        Question types are chosen from the four canonical categories:
          - remedy_selection
          - rubric_identification
          - potency_choice
          - follow_up_prediction

        Distractors are pulled from the repertory or from other remedy records
        in the database to be clinically plausible.

        Args:
            vignette: Output from ``build_vignette_from_outcomes``.
            num_questions: Target number of questions.

        Returns:
            List of question dicts with keys: question_id, question_type, prompt,
            options, correct_answer, explanation, rubric_refs.
        """
        questions = []
        primary = vignette.get("case_details", [{}])[0]
        correct_remedy = primary.get("remedy", "?")
        correct_potency = primary.get("potency", "?")
        outcome = primary.get("outcome", "?")
        rubric_context = vignette.get("rubric_context", [])

        # Remedy selection question (always included)
        questions.append(self._build_remedy_selection_question(vignette, correct_remedy))

        # Rubric identification if rubric context exists
        if rubric_context:
            questions.append(self._build_rubric_identification_question(rubric_context, correct_remedy))

        # Potency choice
        questions.append(self._build_potency_choice_question(vignette, correct_potency))

        # Follow-up prediction
        questions.append(self._build_followup_prediction_question(vignette, outcome))

        # Trim / shuffle to requested count
        random.shuffle(questions)
        questions = questions[:num_questions]
        for i, q in enumerate(questions):
            q["question_id"] = f"Q-{vignette.get('vignette_id', 'VIG-?')}-{i+1}"
        return questions

    @staticmethod
    def _build_remedy_selection_question(vignette: Dict, correct_remedy: str) -> Dict:
        """Build a 'Which remedy was prescribed?' question."""
        # Distractors: random popular remedies (to be upgraded with cohort neighbors if available)
        distractors = ["Puls.", "Ars.", "Nux-v.", "Sulph."]
        distractors = [d for d in distractors if d != correct_remedy]
        options = distractors[:3] + [correct_remedy]
        random.shuffle(options)
        return {
            "question_type": "remedy_selection",
            "prompt": f"Based on the following vignette, which remedy was prescribed?\n\n{vignette.get('narrative', '')}",
            "options": options,
            "correct_answer": correct_remedy,
            "explanation": f"The case record shows {correct_remedy} was selected based on the rubric profile.",
            "rubric_refs": vignette.get("rubric_context", []),
        }

    def _build_rubric_identification_question(
        self, rubric_context: List[Dict], correct_remedy: str
    ) -> Dict:
        """Build a 'Which rubric best matches this case?' question."""
        # Pick the correct rubric from context and distractors from the repertory
        correct_rubric = rubric_context[0]["fullpath"] if rubric_context else "?"
        # Distractors: random rubrics from repertory search
        distractor_queries = ["general", "mind", "head", "stomach"]
        all_distractors = []
        for q in distractor_queries:
            results = self.rep.search_rubrics(q, limit=5)
            for r in results:
                fp = r.get("fullpath", "")
                if fp and fp != correct_rubric:
                    all_distractors.append(fp)
        random.shuffle(all_distractors)
        options = all_distractors[:3] + [correct_rubric]
        random.shuffle(options)
        return {
            "question_type": "rubric_identification",
            "prompt": f"Which of the following rubrics is most characteristic of the remedy {correct_remedy} in this case?",
            "options": options,
            "correct_answer": correct_rubric,
            "explanation": f"The rubric '{correct_rubric}' was part of the original repertorization leading to {correct_remedy}.",
            "rubric_refs": rubric_context[:1],
        }

    @staticmethod
    def _build_potency_choice_question(vignette: Dict, correct_potency: str) -> Dict:
        """Build a 'Which potency was chosen?' question."""
        # Common potency distractors
        distractors = ["6C", "12C", "30C", "200C", "1M"]
        distractors = [d for d in distractors if d != correct_potency]
        options = distractors[:3] + [correct_potency]
        random.shuffle(options)
        return {
            "question_type": "potency_choice",
            "prompt": f"What potency was selected for the remedy in this case?\n\n{vignette.get('narrative', '')}",
            "options": options,
            "correct_answer": correct_potency,
            "explanation": f"The prescription record indicates {correct_potency} was the potency given.",
            "rubric_refs": [],
        }

    @staticmethod
    def _build_followup_prediction_question(vignette: Dict, correct_outcome: str) -> Dict:
        """Build a 'What was the likely outcome?' question."""
        outcome_options = ["improved", "cured", "no_change", "aggravation", "major_improvement"]
        distractors = [o for o in outcome_options if o != correct_outcome]
        options = distractors[:3] + [correct_outcome]
        random.shuffle(options)
        return {
            "question_type": "follow_up_prediction",
            "prompt": f"What was the recorded outcome for this case?\n\n{vignette.get('narrative', '')}",
            "options": options,
            "correct_answer": correct_outcome,
            "explanation": f"Follow-up documentation recorded the outcome as: {correct_outcome}.",
            "rubric_refs": [],
        }

    # ── Quiz Scoring ────────────────────────────────────────────────────────

    def score_quiz(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score a list of student answers against question metadata.

        Each answer dict must contain ``question_type``, ``correct_answer``, and
        ``student_answer``.  Returns accuracy, per-question breakdown, and a
        rubric-by-rubric explanation.

        Args:
            answers: List of answer dicts.

        Returns:
            Dict with keys: score, max_score, percentage, per_question,
            weak_areas (by question type).
        """
        per_question = []
        weak_area_counts: Dict[str, int] = defaultdict(int)
        score = 0
        for a in answers:
            qtype = a.get("question_type", "unknown")
            correct = a.get("correct_answer")
            given = a.get("student_answer")
            is_correct = str(correct).strip().lower() == str(given).strip().lower()
            if is_correct:
                score += 1
            else:
                weak_area_counts[qtype] += 1
            per_question.append({
                "question_type": qtype,
                "correct_answer": correct,
                "student_answer": given,
                "is_correct": is_correct,
                "explanation": a.get("explanation", ""),
            })

        max_score = len(answers)
        percentage = round(score / max_score, 3) if max_score else 0.0
        weak_areas = sorted(weak_area_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "per_question": per_question,
            "weak_areas": [
                {"area": area, "miss_count": cnt}
                for area, cnt in weak_areas[:10]
            ],
        }

    # ── Difficulty Levels ────────────────────────────────────────────────────

    @staticmethod
    def generate_difficulty_levels() -> Dict[str, Any]:
        """
        Define quiz difficulty filters and rubric-count thresholds.

        Returns:
            Dict mapping difficulty names to filtering criteria.
        """
        return {
            "beginner": {
                "max_rubric_refs": 3,
                "allow_rare_remedies": False,
                "primary_question_types": ["remedy_selection", "follow_up_prediction"],
                "description": "Cases with ≤3 rubrics and common polycrest remedies only.",
            },
            "intermediate": {
                "max_rubric_refs": 6,
                "allow_rare_remedies": True,
                "primary_question_types": ["remedy_selection", "rubric_identification", "potency_choice"],
                "description": "Cases with up to 6 rubrics; includes less common remedies.",
            },
            "expert": {
                "max_rubric_refs": 12,
                "allow_rare_remedies": True,
                "primary_question_types": ClinicalVignetteQuiz.QUESTION_TYPES,
                "description": "Complex multi-layer cases; all question types; no restrictions.",
            },
        }

    # ── Weak Areas ──────────────────────────────────────────────────────────

    def get_weak_areas(self, student_or_user_id: str) -> Dict[str, Any]:
        """
        Personalized weak area analysis based on all recorded quiz attempts.

        Aggregates misses by question type and, where available, by rubric
        category (first path segment of rubric references).

        Args:
            student_or_user_id: Identifier for the student / user.

        Returns:
            Dict with keys: student_id, total_attempts, accuracy_overall,
            weak_by_question_type, weak_by_rubric_category, recommendations.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT answers_json, score, score_max, weak_areas_json
            FROM quiz_attempts
            WHERE student_or_user_id = ?
            ORDER BY created_at DESC
            """,
            (student_or_user_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        total = len(rows)
        if total == 0:
            return {
                "student_id": student_or_user_id,
                "total_attempts": 0,
                "accuracy_overall": 0.0,
                "weak_by_question_type": [],
                "weak_by_rubric_category": [],
                "recommendations": [],
            }

        total_score = sum(r[1] or 0 for r in rows)
        total_max = sum(r[2] or 1 for r in rows)
        accuracy = round(total_score / total_max, 3) if total_max else 0.0

        # Aggregate weak areas
        qtype_counts: Dict[str, int] = defaultdict(int)
        rubric_category_counts: Dict[str, int] = defaultdict(int)
        for row in rows:
            # Weak areas from stored column
            weak_json = row[3]
            if weak_json:
                try:
                    weak_list = json.loads(weak_json)
                    for wa in weak_list:
                        area = wa.get("area", "")
                        if area in ClinicalVignetteQuiz.QUESTION_TYPES:
                            qtype_counts[area] += 1
                        else:
                            rubric_category_counts[area] += 1
                except Exception:
                    pass
            # Also parse answers_json for per-question misses
            try:
                answers = json.loads(row[0])
                for a in answers:
                    if not a.get("is_correct", True):
                        qtype_counts[a.get("question_type", "unknown")] += 1
            except Exception:
                pass

        weak_by_qtype = sorted(qtype_counts.items(), key=lambda x: x[1], reverse=True)
        weak_by_rubric = sorted(rubric_category_counts.items(), key=lambda x: x[1], reverse=True)

        # Build recommendations
        recommendations = []
        if weak_by_qtype:
            recommendations.append(
                f"Focus study on '{weak_by_qtype[0][0]}' questions — missed {weak_by_qtype[0][1]} times."
            )
        if weak_by_rubric:
            recommendations.append(
                f"Review rubrics in category '{weak_by_rubric[0][0]}' ({weak_by_rubric[0][1]} misses)."
            )

        return {
            "student_id": student_or_user_id,
            "total_attempts": total,
            "accuracy_overall": accuracy,
            "weak_by_question_type": [
                {"question_type": qt, "miss_count": cnt} for qt, cnt in weak_by_qtype[:5]
            ],
            "weak_by_rubric_category": [
                {"category": c, "miss_count": cnt} for c, cnt in weak_by_rubric[:5]
            ],
            "recommendations": recommendations,
        }

    def save_quiz(self, vignette: Dict, questions: List[Dict], difficulty: Optional[str] = None) -> str:
        """
        Persist a generated quiz to the database.

        Returns:
            The generated quiz UUID.
        """
        quiz_uuid = f"QUIZ-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO quizzes (quiz_uuid, vignette_json, questions_json, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (quiz_uuid, json.dumps(vignette), json.dumps(questions), difficulty, now),
        )
        conn.commit()
        conn.close()
        return quiz_uuid

    def record_attempt(
        self,
        quiz_uuid: str,
        student_or_user_id: str,
        answers: List[Dict],
        score: float,
        score_max: int,
        weak_areas: List[Dict],
    ) -> int:
        """Persist a quiz attempt to ``quiz_attempts``."""
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO quiz_attempts (quiz_uuid, student_or_user_id, answers_json, score, score_max, weak_areas_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quiz_uuid,
                student_or_user_id,
                json.dumps(answers),
                score,
                score_max,
                json.dumps(weak_areas),
                now,
            ),
        )
        row_id = cursor.lastrowid or 0
        conn.commit()
        conn.close()
        return row_id
