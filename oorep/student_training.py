"""
Student Training — Benefit #38

Generates simulated patient vignettes and interactive quizzes for homeopathic
students.  Cases are built from real rubric co-occurrence patterns so they feel
clinically coherent rather than random noise.  Progress is tracked in SQLite.

Usage:
    from oorep.student_training import StudentTraining
    trainer = StudentTraining()

    # Generate a realistic simulated case
    case = trainer.generate_simulated_patient()

    # Build a quiz from one or more cases
    quiz = trainer.generate_quiz([case])

    # Evaluate a student's answer
    result = trainer.evaluate_answer(case["case_id"], remedy_guess="Puls.")

    # Track progress across sessions
    progress = trainer.track_progress("student_42")

    # Warm-up questions on a specific topic
    warmups = trainer.generate_warm_up_questions(topic="anxiety")
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
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory

try:
    from .rubric_cooccurrence import RubricCooccurrenceEngine
except Exception:
    from rubric_cooccurrence import RubricCooccurrenceEngine

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class StudentTraining:
    """
    Training engine for homeopathic students.

    Simulates realistic patient vignettes by clustering rubrics that
    co-occur in the repertory, then generates multiple-choice quizzes
    and tracks learning progress over time.
    """

    # Configurable quiz parameters
    QUIZ_OPTIONS_COUNT = 4
    MIN_RUBRICS_PER_CASE = 3
    MAX_RUBRICS_PER_CASE = 8
    SIMULATED_CHIEF_COMPLAINTS = [
        "anxiety with restlessness",
        "headache aggravated by motion",
        "skin eruption with burning pain",
        "digestive disturbance after eating",
        "recurrent urinary complaints",
        "respiratory constriction on exertion",
        "menstrual irregularity with mood changes",
        "insomnia with early waking",
        "joint stiffness worse in morning",
        "fever with chilliness",
    ]

    def __init__(
        self,
        db_path: Optional[Path] = None,
        repertory: Optional[HomeopathicRepertory] = None,
        cooccurrence: Optional[RubricCooccurrenceEngine] = None,
    ):
        """
        Args:
            db_path: SQLite path for progress tracking. Defaults to feedback.db.
            repertory: Existing HomeopathicRepertory instance (optional).
            cooccurrence: Existing RubricCooccurrenceEngine instance (optional).
        """
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.rep = repertory or HomeopathicRepertory()
        self.cooc = cooccurrence or RubricCooccurrenceEngine(self.rep)

        self._cases_cache: Dict[str, Dict] = {}
        self._init_db()

    # ── Schema ──────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create ``student_progress`` and ``simulated_cases`` tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                case_id TEXT,
                remedy_guess TEXT,
                correct INTEGER,
                rubrics_json TEXT,
                weak_areas_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_progress_student ON student_progress(student_id)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS simulated_cases (
                case_id TEXT PRIMARY KEY,
                vignette TEXT,
                rubrics_json TEXT,
                correct_remedy TEXT,
                explanation TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    # ── Simulated Patient Generation ─────────────────────────────────────────

    def generate_simulated_patient(self) -> Dict[str, Any]:
        """
        Generate a randomized but clinically coherent simulated patient vignette.

        Uses rubric co-occurrence patterns to pick rubrics that are likely to
        appear together in real repertory data, producing case clusters that
        feel organic rather than random noise.

        Returns:
            Dict with keys: case_id, chief_complaint, history, rubrics,
            modalities, sensations, demographics, correct_remedy, explanation.
        """
        # Pick a random "seed remedy" to anchor realistic clustering
        all_abbrevs = list(self.cooc._remedy_rubrics.keys())
        if not all_abbrevs:
            return {"error": "No remedy data available for simulation"}

        seed_remedy = random.choice(all_abbrevs)
        cluster_info = self.cooc.cluster_for_remedy(seed_remedy, min_cooccurrence=5)
        neighbor_abbrevs = [n["remedy_a"] if n["remedy_b"] == seed_remedy else n["remedy_b"]
                            for n in cluster_info.get("neighbors", [])]

        # Decide on the correct remedy — either seed or a close neighbor
        if neighbor_abbrevs and random.random() < 0.5:
            correct_remedy = random.choice(neighbor_abbrevs)
        else:
            correct_remedy = seed_remedy

        # Gather rubrics connected to the correct remedy
        connected_rubric_ids = list(self.cooc._remedy_rubrics.get(correct_remedy, set()))
        if not connected_rubric_ids:
            connected_rubric_ids = list(self.rep.rubric_to_remedies.keys())

        num_rubrics = random.randint(self.MIN_RUBRICS_PER_CASE, self.MAX_RUBRICS_PER_CASE)
        chosen_rubric_ids = random.sample(
            connected_rubric_ids, min(num_rubrics, len(connected_rubric_ids))
        )

        # Build rubric details for the case
        rubrics = []
        for rid in chosen_rubric_ids:
            rubric = self.rep.get_rubric_by_id(rid)
            if rubric:
                rubrics.append({
                    "rubric_id": rid,
                    "fullpath": rubric.get("fullpath", "?"),
                    "source": rubric.get("source", "?"),
                })

        # Pick a chief complaint that matches at least one rubric keyword
        chief_complaint = random.choice(self.SIMULATED_CHIEF_COMPLAINTS)
        for r in rubrics:
            fp = r["fullpath"].lower()
            if any(k in fp for k in chief_complaint.split()[:2]):
                chief_complaint = f"{chief_complaint} — notably {r['fullpath']}"
                break

        # Build modalities / sensations from rubric text heuristics
        modalities = self._extract_modalities(rubrics)
        sensations = self._extract_sensations(rubrics)

        # Compose vignette text
        vignette = self._compose_vignette(chief_complaint, rubrics, modalities, sensations)

        # Explanation references rubrics
        explanation = (
            f"This case points strongly toward {correct_remedy} because the following "
            f"rubrics all include {correct_remedy} with significant weight: "
            + ", ".join(f"{r['fullpath']} ({r['source']})" for r in rubrics[:3])
            + "."
        )

        case_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        case = {
            "case_id": case_id,
            "chief_complaint": chief_complaint,
            "history": vignette,
            "rubrics": rubrics,
            "modalities": modalities,
            "sensations": sensations,
            "demographics": {
                "age": random.randint(18, 75),
                "gender": random.choice(["M", "F", "NB"]),
            },
            "correct_remedy": correct_remedy,
            "explanation": explanation,
        }

        # Cache and persist the case so quizzes can reference it later
        self._cases_cache[case_id] = case
        self._persist_case(case)
        return case

    def _compose_vignette(
        self, chief_complaint: str, rubrics: List[Dict], modalities: List[str], sensations: List[str]
    ) -> str:
        """Assemble a readable patient narrative from rubric-derived clues."""
        lines = [f"Patient presents with {chief_complaint}."]
        if modalities:
            lines.append(f"Modalities: {'; '.join(modalities)}.")
        if sensations:
            lines.append(f"Sensations: {'; '.join(sensations)}.")
        lines.append("Key rubrics identified in repertorization:")
        for r in rubrics:
            lines.append(f"  • {r['fullpath']} ({r['source']})")
        return " ".join(lines)

    def _extract_modalities(self, rubrics: List[Dict]) -> List[str]:
        """Heuristic extraction of modality phrases from rubric paths."""
        modality_keywords = ["worse", "better", "amel", "agg", "night", "morning", "motion", "cold", "heat"]
        found = set()
        for r in rubrics:
            fp = r["fullpath"].lower()
            for kw in modality_keywords:
                if kw in fp:
                    found.add(kw)
        return list(found)

    def _extract_sensations(self, rubrics: List[Dict]) -> List[str]:
        """Heuristic extraction of sensation words from rubric paths."""
        sensation_keywords = ["burning", "stinging", "tearing", "throbbing", "numbness", "tingling", "cramping"]
        found = set()
        for r in rubrics:
            fp = r["fullpath"].lower()
            for kw in sensation_keywords:
                if kw in fp:
                    found.add(kw)
        return list(found)

    def _persist_case(self, case: Dict) -> None:
        """Write a simulated case into the SQLite cache table."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO simulated_cases
            (case_id, vignette, rubrics_json, correct_remedy, explanation, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                case["case_id"],
                case["history"],
                json.dumps(case["rubrics"]),
                case["correct_remedy"],
                case["explanation"],
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    # ── Quiz Generation ────────────────────────────────────────────────────

    def generate_quiz(self, cases: List[Dict]) -> Dict[str, Any]:
        """
        Build a multiple-choice quiz: "Which remedy?" with 4 options per case.

        Distractors are chosen from remedies that share rubrics with the correct
        remedy (common differential-diagnosis neighbors), making the quiz
        educationally valuable.

        Args:
            cases: List of case dicts (output from ``generate_simulated_patient``).

        Returns:
            Dict with keys: quiz_id, questions (list of dicts with case_id,
            prompt, options, correct_answer, rubric_context).
        """
        questions = []
        for case in cases:
            correct = case.get("correct_remedy", "?")
            # Gather plausible distractors from co-occurrence neighbors
            cluster_info = self.cooc.cluster_for_remedy(correct, min_cooccurrence=3)
            neighbors = [n["remedy_a"] if n["remedy_b"] == correct else n["remedy_b"]
                         for n in cluster_info.get("neighbors", [])]
            # Ensure unique, not-correct distractors
            distractors = [d for d in neighbors if d != correct]
            if len(distractors) < self.QUIZ_OPTIONS_COUNT - 1:
                # Fill with random remedies
                pool = list(self.cooc._remedy_rubrics.keys())
                random.shuffle(pool)
                for p in pool:
                    if p != correct and p not in distractors:
                        distractors.append(p)
                    if len(distractors) >= self.QUIZ_OPTIONS_COUNT - 1:
                        break

            options = distractors[: self.QUIZ_OPTIONS_COUNT - 1] + [correct]
            random.shuffle(options)

            prompt = (
                f"Case {case['case_id']}: {case['chief_complaint']}\n"
                f"{case['history']}"
            )
            questions.append({
                "case_id": case["case_id"],
                "prompt": prompt,
                "options": options,
                "correct_answer": correct,
                "rubric_context": case.get("rubrics", []),
            })

        return {
            "quiz_id": f"QUIZ-{uuid.uuid4().hex[:8].upper()}",
            "created_at": datetime.now().isoformat(),
            "question_count": len(questions),
            "questions": questions,
        }

    # ── Evaluation ─────────────────────────────────────────────────────────

    def evaluate_answer(self, case_id: str, remedy_guess: str) -> Dict[str, Any]:
        """
        Check a student's remedy guess against the stored correct answer.

        Args:
            case_id: Simulated case ID.
            remedy_guess: Abbreviation of the remedy selected by the student.

        Returns:
            Dict with keys: correct, correct_remedy, remedy_guess, explanation,
            confidence_hint, rubric_breakdown.
        """
        case = self._load_case(case_id)
        if not case:
            return {"error": f"Case {case_id} not found."}

        correct_remedy = case["correct_remedy"]
        is_correct = self._abbrev_match(remedy_guess, correct_remedy)

        # Build per-rubric breakdown of the guessed remedy presence
        rubric_breakdown = []
        for r in case.get("rubrics", []):
            rid = r.get("rubric_id")
            if rid is None:
                continue
            remedies = self.rep.get_remedies_for_rubric(int(rid))
            guess_weight = None
            correct_weight = None
            for rem in remedies:
                if self._abbrev_match(rem.get("abbrev", ""), remedy_guess):
                    guess_weight = rem.get("weight", 1)
                if self._abbrev_match(rem.get("abbrev", ""), correct_remedy):
                    correct_weight = rem.get("weight", 1)
            rubric_breakdown.append({
                "rubric_id": rid,
                "fullpath": r.get("fullpath", "?"),
                "guess_weight": guess_weight,
                "correct_weight": correct_weight,
            })

        confidence_hint = "Strong" if is_correct else "Weak (consider differential)"
        return {
            "correct": is_correct,
            "correct_remedy": correct_remedy,
            "remedy_guess": remedy_guess,
            "explanation": case.get("explanation", ""),
            "confidence_hint": confidence_hint,
            "rubric_breakdown": rubric_breakdown,
        }

    def _load_case(self, case_id: str) -> Optional[Dict]:
        """Retrieve a simulated case from cache or SQLite."""
        if case_id in self._cases_cache:
            return self._cases_cache[case_id]
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT vignette, rubrics_json, correct_remedy, explanation FROM simulated_cases WHERE case_id = ?",
            (case_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        case = {
            "case_id": case_id,
            "history": row[0],
            "rubrics": json.loads(row[1]) if row[1] else [],
            "correct_remedy": row[2],
            "explanation": row[3],
        }
        self._cases_cache[case_id] = case
        return case

    @staticmethod
    def _abbrev_match(a: str, b: str) -> bool:
        """Case-insensitive abbreviation comparison (ignores trailing dots)."""
        return a.strip().lower().rstrip(".") == b.strip().lower().rstrip(".")

    # ── Progress Tracking ────────────────────────────────────────────────────

    def track_progress(self, student_id: str) -> Dict[str, Any]:
        """
        Return aggregated student progress from SQLite ``student_progress``.

        Computes cases attempted, accuracy rate, and weak areas based on
        remedy families or rubric categories the student struggles with.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT case_id, remedy_guess, correct, rubrics_json, weak_areas_json
            FROM student_progress
            WHERE student_id = ?
            ORDER BY created_at DESC
            """,
            (student_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        total = len(rows)
        correct_count = sum(1 for r in rows if r[2])
        accuracy = round(correct_count / total, 3) if total else 0.0

        # Derive weak areas from incorrect guesses
        weak_area_counts: Dict[str, int] = defaultdict(int)
        for r in rows:
            if not r[2]:  # incorrect
                # Parse rubrics and increment path category counts
                rubrics = json.loads(r[3]) if r[3] else []
                for rub in rubrics:
                    fp = rub.get("fullpath", "")
                    # Use first path segment as category
                    category = fp.split(">")[0].strip().lower() if ">" in fp else fp.split(" ")[0].lower()
                    weak_area_counts[category] += 1
                # Also parse explicit weak_areas if present
                explicit = json.loads(r[4]) if r[4] else []
                for wa in explicit:
                    weak_area_counts[str(wa).lower()] += 1

        weak_areas = sorted(weak_area_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "student_id": student_id,
            "cases_attempted": total,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "weak_areas": [
                {"area": area, "miss_count": cnt}
                for area, cnt in weak_areas[:10]
            ],
        }

    def record_attempt(
        self,
        student_id: str,
        case_id: str,
        remedy_guess: str,
        correct: bool,
        rubrics: List[Dict],
        weak_areas: Optional[List[str]] = None,
    ) -> int:
        """
        Persist a single quiz attempt to ``student_progress``.

        Returns:
            Row id of the inserted record.
        """
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO student_progress
            (student_id, case_id, remedy_guess, correct, rubrics_json, weak_areas_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                case_id,
                remedy_guess,
                int(correct),
                json.dumps(rubrics),
                json.dumps(weak_areas or []),
                now,
            ),
        )
        row_id = cursor.lastrowid or 0
        conn.commit()
        conn.close()
        return row_id

    # ── Warm-up Questions ────────────────────────────────────────────────────

    def generate_warm_up_questions(self, topic: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Generate targeted warm-up questions on a specific topic (e.g., "anxiety").

        Queries rubrics matching the topic, selects a relevant remedy, and
        builds mini-quizzes focused on that area to reinforce weak spots.

        Args:
            topic: Keyword topic for targeted practice.
            num_questions: How many warm-up questions to generate.

        Returns:
            List of question dicts (prompt, options, correct_answer, rubric_context).
        """
        matching_rubrics = self.rep.search_rubrics(topic, limit=20)
        if not matching_rubrics:
            return []

        # Pick random matching rubrics and build a question for each
        random.shuffle(matching_rubrics)
        selected = matching_rubrics[:num_questions]
        questions = []
        for rubric_match in selected:
            rid = rubric_match.get("rubric_id")
            remedies = self.rep.get_remedies_for_rubric(rid)
            if not remedies:
                continue
            # Correct answer = top-weighted remedy in that rubric
            remedies_sorted = sorted(remedies, key=lambda r: r.get("weight", 1), reverse=True)
            correct = remedies_sorted[0]["abbrev"]
            # Distractors = next top remedies or random neighbors
            distractors = [r["abbrev"] for r in remedies_sorted[1:4]]
            if len(distractors) < 3:
                pool = list(self.cooc._remedy_rubrics.keys())
                random.shuffle(pool)
                for p in pool:
                    if p != correct and p not in distractors:
                        distractors.append(p)
                    if len(distractors) >= 3:
                        break
            options = distractors[:3] + [correct]
            random.shuffle(options)
            rubric = self.rep.get_rubric_by_id(rid)
            questions.append({
                "prompt": f"Which remedy is most strongly associated with the rubric: {rubric.get('fullpath', '?')}?",
                "options": options,
                "correct_answer": correct,
                "rubric_context": [{"rubric_id": rid, "fullpath": rubric.get("fullpath", "?")}],
            })
        return questions
