"""tests/test_batch_d.py — Batch D modules (corrected signatures)."""
import datetime
import json
import sqlite3
from pathlib import Path

import pytest

from oorep.model_router import ModelRouter
from oorep.student_training import StudentTraining
from oorep.clinical_vignette_quiz import ClinicalVignetteQuiz
from oorep.grand_rounds import GrandRounds
from oorep.rubric_gap_analyzer import RubricGapAnalyzer
from oorep.remedy_freshness_tracker import RemedyFreshnessTracker
from oorep.subagent_orchestrator import SubagentOrchestrator


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


# ── ModelRouter ────────────────────────────────────────────────────────────────

class TestModelRouter:
    def test_route_task_simple(self, tmp_db_path: Path):
        router = ModelRouter(db_path=tmp_db_path)
        route = router.route_task("repertorize")
        assert route["model"] in ("local_jetson", "cloud")
        assert "rationale" in route

    def test_track_and_optimal(self, tmp_db_path: Path):
        router = ModelRouter(db_path=tmp_db_path)
        router.track_performance("repertorize", "local_jetson", latency=0.3, quality=0.92)
        best = router.get_optimal_route("repertorize")
        assert "model" in best

    def test_fallback_chain(self, tmp_db_path: Path):
        router = ModelRouter(db_path=tmp_db_path)
        chain = router.fallback_chain("summarize_case")
        assert isinstance(chain, list) and len(chain) >= 1


# ── StudentTraining ────────────────────────────────────────────────────────────

class TestStudentTraining:
    def test_generate_simulated_patient(self, tmp_db_path: Path):
        st = StudentTraining(db_path=tmp_db_path)
        case = st.generate_simulated_patient()
        assert case is not None
        assert "case_id" in case
        assert "correct_remedy" in case
        assert isinstance(case.get("rubrics", []), list)
        assert "chief_complaint" in case

    def test_generate_quiz(self, tmp_db_path: Path):
        st = StudentTraining(db_path=tmp_db_path)
        case = st.generate_simulated_patient()
        quiz = st.generate_quiz([case])
        assert isinstance(quiz, dict)
        assert "quiz_id" in quiz
        assert "questions" in quiz
        assert len(quiz["questions"]) > 0
        q = quiz["questions"][0]
        assert "options" in q
        assert len(q["options"]) == 4
        assert "correct_answer" in q

    def test_evaluate_correct_answer(self, tmp_db_path: Path):
        st = StudentTraining(db_path=tmp_db_path)
        case = st.generate_simulated_patient()
        cid = case["case_id"]
        correct = case["correct_remedy"]
        result = st.evaluate_answer(cid, correct)
        assert result.get("correct") is True
        assert "explanation" in result

    def test_evaluate_incorrect_answer(self, tmp_db_path: Path):
        st = StudentTraining(db_path=tmp_db_path)
        case = st.generate_simulated_patient()
        cid = case["case_id"]
        result = st.evaluate_answer(cid, "WRONG")
        assert result.get("correct") is False

    def test_track_progress(self, tmp_db_path: Path):
        st = StudentTraining(db_path=tmp_db_path)
        case = st.generate_simulated_patient()
        st.record_attempt(
            "student_x",
            case["case_id"],
            "Arsenicum",
            False,
            rubrics=[{"rubric_id": "1"}],
            weak_areas=["rubric selection"],
        )
        progress = st.track_progress("student_x")
        assert progress["cases_attempted"] >= 1

    def test_warm_up_questions(self, tmp_db_path: Path):
        st = StudentTraining(db_path=tmp_db_path)
        questions = st.generate_warm_up_questions("sleep", num_questions=3)
        assert isinstance(questions, list)


# ── ClinicalVignetteQuiz ──────────────────────────────────────────────────────

def _seed_quiz_db(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, pseudonym TEXT)")
    c.execute("INSERT INTO patients (pseudonym) VALUES (?)", ("pt_test",))
    pid = c.lastrowid
    c.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY, patient_id INTEGER, remedy TEXT,
            rubric_ids TEXT, potency TEXT, prescriber_ack TEXT,
            next_followup TEXT, created_at TEXT
        )
    """)
    c.execute("INSERT INTO prescriptions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
              (pid, "Pulsatilla", "[1,2,3]", "30C", "ack", "2025-06-01", "2025-01-01"))
    c.execute("""
        CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY, patient_id INTEGER,
            symptom_changes TEXT, overall_outcome TEXT, created_at TEXT
        )
    """)
    c.execute("INSERT INTO follow_ups VALUES (NULL, ?, ?, ?, ?)",
              (pid, "improved sleep", "good", "2025-01-15"))
    conn.commit()
    conn.close()


class TestClinicalVignetteQuiz:
    def test_score_quiz(self, tmp_db_path: Path):
        quiz = ClinicalVignetteQuiz(db_path=tmp_db_path)
        answers = [
            {"question_type": "remedy", "correct_answer": "Ars", "student_answer": "Ars"},
            {"question_type": "potency", "correct_answer": "30C", "student_answer": "Wrong"},
            {"question_type": "rubric", "correct_answer": "Mind; anxiety", "student_answer": "Mind; anxiety"},
        ]
        score = quiz.score_quiz(answers)
        assert "percentage" in score
        assert "per_question" in score
        assert score["percentage"] == pytest.approx(2 / 3, rel=1e-3)

    def test_generate_difficulty_levels(self, tmp_db_path: Path):
        levels = ClinicalVignetteQuiz.generate_difficulty_levels()
        assert isinstance(levels, dict)
        assert "beginner" in levels
        assert "intermediate" in levels
        assert "expert" in levels


# ── GrandRounds ───────────────────────────────────────────────────────────────

CASES = [
    {"pseudonym": "A", "remedy": "Pulsatilla", "rubrics": ["weepy"], "outcome": "good"},
    {"pseudonym": "B", "remedy": "Pulsatilla", "rubrics": ["weepy", "chilly"], "outcome": "good"},
    {"pseudonym": "C", "remedy": "Arsenicum", "rubrics": ["anxious"], "outcome": "good"},
]


class TestGrandRounds:
    def test_synthesize_cases(self):
        gr = GrandRounds()
        result = gr.synthesize_cases()
        assert isinstance(result, list)

    def test_find_common_themes(self):
        gr = GrandRounds()
        themes = gr.find_common_themes(CASES)
        assert isinstance(themes, dict)

    def test_generate_teaching_narrative(self):
        gr = GrandRounds()
        narrative = gr.generate_teaching_narrative(CASES)
        assert isinstance(narrative, str)
        assert "Grand Rounds" in narrative

    def test_compare_with_literature(self):
        gr = GrandRounds()
        lit = gr.compare_with_literature(CASES)
        assert isinstance(lit, list)

    def test_export_for_presentation(self):
        gr = GrandRounds()
        md = gr.export_for_presentation(CASES, format="markdown")
        assert isinstance(md, str)
        assert "#" in md


# ── RubricGapAnalyzer ───────────────────────────────────────────────────────────

class TestRubricGapAnalyzer:
    def test_init(self):
        rga = RubricGapAnalyzer()
        assert rga is not None

    def test_analyze_mapping(self):
        rga = RubricGapAnalyzer()
        result = rga.analyze_mapping(
            "chronic anxiety worse at night",
            [{"rubric_id": "123", "fullpath": "Mind; anxiety, chronic", "confidence": 0.6}],
        )
        assert isinstance(result, dict)
        assert "token_coverage" in result
        assert "rubric_confidences" in result

    def test_find_uncovered_symptoms(self):
        rga = RubricGapAnalyzer()
        uncovered = rga.find_uncovered_symptoms(
            [
                "strange tingling in fingertips",
                "burning pain in soles",
            ]
        )
        assert isinstance(uncovered, list)

    def test_suggest_new_rubric_text(self):
        rga = RubricGapAnalyzer()
        suggestions = rga.suggest_new_rubric_text(
            [
                {"symptom_text": "tingling in fingertips"},
                {"symptom_text": "burning pain in soles"},
            ]
        )
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_score_rubric_quality(self):
        rga = RubricGapAnalyzer()
        score = rga.score_rubric_quality(1, include_phantom=False)
        assert score is None or isinstance(score, dict)

    def test_generate_gap_report(self):
        rga = RubricGapAnalyzer()
        report = rga.generate_gap_report(
            symptom_samples=["chronic anxiety"],
            sample_size=5,
        )
        assert isinstance(report, dict)
        assert "uncovered_symptoms" in report


# ── RemedyFreshnessTracker ────────────────────────────────────────────────────

class TestRemedyFreshnessTracker:
    def test_init(self, tmp_db_path: Path):
        rft = RemedyFreshnessTracker(db_path=tmp_db_path)
        assert rft is not None

    def test_record_and_check_not_stale(self, tmp_db_path: Path):
        rft = RemedyFreshnessTracker(db_path=tmp_db_path)
        rft.record_proving_update("Pulsatilla", "Kent", "2025-01-01", "new proving")
        stale = rft.check_staleness(threshold_days=9999)
        assert isinstance(stale, list)

    def test_check_staleness_uses_last_update(self, tmp_db_path: Path):
        rft = RemedyFreshnessTracker(db_path=tmp_db_path)
        conn = sqlite3.connect(str(tmp_db_path))
        c = conn.cursor()
        old_date = "2000-01-01T00:00:00"
        c.execute(
            "INSERT INTO remedy_freshness (remedy_abbrev, last_update_date, freshness_score, updated_at) VALUES (?, ?, ?, ?)",
            ("Arsenicum", old_date, 0.1, old_date),
        )
        conn.commit()
        conn.close()
        stale = rft.check_staleness(threshold_days=30)
        assert len(stale) >= 1
        assert any(r["remedy_abbrev"] == "Arsenicum" for r in stale)

    def test_flag_for_review(self, tmp_db_path: Path):
        rft = RemedyFreshnessTracker(db_path=tmp_db_path)
        ids = rft.flag_for_review(["Arsenicum"], "needs modern proving")
        assert isinstance(ids, list)

    def test_get_freshness_report(self, tmp_db_path: Path):
        rft = RemedyFreshnessTracker(db_path=tmp_db_path)
        rft.record_proving_update("Lycopodium", "Allen", "2024-12-01", "update")
        report = rft.get_freshness_report()
        assert isinstance(report, dict)
        assert "tracked_remedies" in report or "average_score" in report

    def test_schedule_review(self, tmp_db_path: Path):
        rft = RemedyFreshnessTracker(db_path=tmp_db_path)
        idx = rft.schedule_review("Silica", "2026-01-01")
        assert isinstance(idx, int) or idx is None


# ── SubagentOrchestrator ─────────────────────────────────────────────────────────

class TestSubagentOrchestrator:
    def test_plan_case_analysis(self):
        orch = SubagentOrchestrator()
        case = {"symptoms": [{"text": "insomnia"}, {"text": "anxiety"}], "patient_age": 30}
        plan = orch.plan_case_analysis(case)
        assert hasattr(plan, "plan_id") or isinstance(plan, dict)

    def test_distribute_literature_review(self):
        orch = SubagentOrchestrator()
        plan = orch.distribute_literature_review(["anxiety", "insomnia"])
        assert hasattr(plan, "plan_id") or isinstance(plan, dict)

    def test_request_second_opinion(self):
        orch = SubagentOrchestrator()
        case = {"symptoms": [{"text": "anxiety"}], "current_remedy": "Arsenicum"}
        plan = orch.request_second_opinion(case)
        assert hasattr(plan, "plan_id") or isinstance(plan, dict)

    def test_summarize_findings(self):
        results = [
            {"step_id": "s1", "task_type": "rubric_research", "status": "completed",
             "outputs": {"recommendation": {"remedy": "Ars", "rationale": "r"}}},
            {"step_id": "s2", "task_type": "strategy_synthesis", "status": "completed",
             "outputs": {"recommendation": {"remedy": "Ars", "rationale": "r"}}},
        ]
        summary = SubagentOrchestrator.summarize_findings(results)
        assert isinstance(summary, dict)
        assert "summary_text" in summary
        assert "confidence_level" in summary

    def test_review_queue(self):
        orch = SubagentOrchestrator()
        queue = orch.review_queue()
        assert isinstance(queue, list)

    def test_escalation_path(self):
        orch = SubagentOrchestrator()
        path = orch.escalation_path("critical")
        assert isinstance(path, dict)
        assert "next_steps" in path
        assert "contacts" in path
