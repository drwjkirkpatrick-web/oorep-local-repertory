"""
Model Router — Benefit #57

Routes computational tasks to the most appropriate inference backend
based on heuristics, historical performance, and latency requirements.

Supported targets:
  - ``local_jetson``  → On-device inference (Nano / Orin), low latency for
                        simple lookups, no network dependency.
  - ``cloud``         → Remote LLM / NLP API, higher accuracy, suited for
                        complex generation or batch analysis.

Usage:
    from oorep.model_router import ModelRouter
    router = ModelRouter()

    route = router.route_task("repertorize")
    # → {"model": "local_jetson", "rationale": "..."}

    router.track_performance("repertorize", "local_jetson", latency=0.4, quality=0.92)
    best = router.get_optimal_route("repertorize")
    fallback = router.fallback_chain("summarize_case")
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"

# ── Task-type heuristics ──────────────────────────────────────────────────────
_SIMPLE_TASKS = frozenset([
    "repertorize", "search_rubrics", "search_remedies", "get_remedy",
    "get_rubric", "list_patients", "get_prescription", "get_soap",
    "get_history", "verify_chain", "compare_remedies", "query_case",
])

_COMPLEX_NLP_TASKS = frozenset([
    "summarize_case", "generate_letter", "parse_conversation",
    "scrub_phi", "nlp_extraction", "clinical_nlp", "extract_entities",
    "sentiment_analysis", "risk_assessment_nlp",
])

_BATCH_TASKS = frozenset([
    "batch_repertorize", "batch_phi_scrub", "cohort_analytics",
    "export_for_licensure", "batch_export",
])

_DEFAULT_LATENCY_BUDGET_MS: Dict[str, int] = {
    "repertorize": 800,
    "search_rubrics": 300,
    "generate_letter": 3000,
    "summarize_case": 2000,
    "scrub_phi": 500,
    "batch_repertorize": 5000,
}

_FALLBACK_ORDER = ["local_jetson", "cloud"]


class ModelRouter:
    """
    Intelligent task-to-model router with performance tracking.

    Stores historical latency / quality scores in ``model_performance``
    so that ``get_optimal_route()`` can adapt over time.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Args:
            db_path: SQLite database path for the performance table.
        """
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create ``model_performance`` table."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                model TEXT NOT NULL,
                latency REAL,
                quality REAL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_perf_task ON model_performance(task_type)"
        )
        conn.commit()
        conn.close()

    # ── Routing heuristics ────────────────────────────────────────────────────

    def route_task(self, task_type: str, latency_budget_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Pick the best target model for a task using static heuristics.

        Args:
            task_type: Descriptive task string (e.g. "repertorize").
            latency_budget_ms: Optional override for the acceptable latency ceiling.

        Returns:
            Dict with ``model`` ("local_jetson" | "cloud") and ``rationale`` (str).
        """
        task = task_type.lower().strip()
        budget = latency_budget_ms or _DEFAULT_LATENCY_BUDGET_MS.get(task, 2000)

        if task in _SIMPLE_TASKS:
            rationale = (
                f"'{task}' is a simple lookup / deterministic operation. "
                f"Local Jetson satisfies latency budget of {budget} ms without "
                "network overhead or privacy risk."
            )
            return {"model": "local_jetson", "rationale": rationale}

        if task in _COMPLEX_NLP_TASKS:
            rationale = (
                f"'{task}' requires complex NLP or generation. "
                f"Cloud model provides higher accuracy within latency budget {budget} ms."
            )
            return {"model": "cloud", "rationale": rationale}

        if task in _BATCH_TASKS:
            rationale = (
                f"'{task}' is a batch operation; cloud parallelism "
                f"scales better than local Jetson for throughput within budget {budget} ms."
            )
            return {"model": "cloud", "rationale": rationale}

        # Unknown task → default to local for privacy, but note uncertainty
        rationale = (
            f"Unknown task type '{task}'. Defaulting to local Jetson for "
            "privacy and low-latency safety; cloud can be forced if needed."
        )
        return {"model": "local_jetson", "rationale": rationale}

    # ── Performance tracking ──────────────────────────────────────────────────

    def track_performance(
        self,
        task_type: str,
        model: str,
        latency: float,
        quality: Optional[float] = None,
    ) -> None:
        """
        Log a performance observation for adaptive routing.

        Args:
            task_type: Task identifier.
            model: Which model served the task ("local_jetson" or "cloud").
            latency: Measured latency in seconds.
            quality: Optional quality score 0.0–1.0.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO model_performance (task_type, model, latency, quality, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                task_type.lower().strip(),
                model,
                latency,
                quality,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    # ── Historical optimal route ────────────────────────────────────────────

    def get_optimal_route(self, task_type: str) -> Dict[str, Any]:
        """
        Return the historically best-performing model for ``task_type``
        based on average latency and quality.

        Returns:
            Dict with ``model`` and ``rationale``.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT model, AVG(latency) AS avg_latency, AVG(IFNULL(quality, 0.5)) AS avg_quality
            FROM model_performance
            WHERE task_type = ?
            GROUP BY model
            ORDER BY avg_quality DESC, avg_latency ASC
            """,
            (task_type.lower().strip(),),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            # No history yet → fall back to heuristic
            return self.route_task(task_type)

        # Score = quality / latency (higher is better); penalise missing quality
        best = None
        best_score = -1.0
        for model, avg_lat, avg_qual in rows:
            avg_lat = avg_lat or 1.0
            avg_qual = avg_qual or 0.5
            score = avg_qual / avg_lat
            if score > best_score:
                best_score = score
                best = model

        return {
            "model": best,
            "rationale": (
                f"Historical data shows '{best}' as optimal for '{task_type}' "
                f"(quality/latency score = {best_score:.3f})."
            ),
        }

    # ── Fallback chain ──────────────────────────────────────────────────────

    def fallback_chain(self, task_type: str) -> List[Dict[str, Any]]:
        """
        Produce an ordered list of models to attempt, with brief rationale.

        Args:
            task_type: Task identifier.

        Returns:
            List of dicts with ``model`` and ``rationale``.
        """
        heuristic = self.route_task(task_type)
        primary = heuristic["model"]
        secondary = "cloud" if primary == "local_jetson" else "local_jetson"
        return [
            {
                "model": primary,
                "rationale": heuristic["rationale"],
            },
            {
                "model": secondary,
                "rationale": (
                    f"Fallback to '{secondary}' if '{primary}' fails, "
                    f"exceeds latency budget, or returns low quality."
                ),
            },
        ]

    # ── Raw performance query ─────────────────────────────────────────────────

    def get_performance_summary(self, task_type: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Return raw performance rows, optionally filtered by task type.
        Ordered newest-first.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        if task_type:
            cursor.execute(
                "SELECT task_type, model, latency, quality, recorded_at "
                "FROM model_performance WHERE task_type = ? ORDER BY recorded_at DESC LIMIT ?",
                (task_type.lower().strip(), limit),
            )
        else:
            cursor.execute(
                "SELECT task_type, model, latency, quality, recorded_at "
                "FROM model_performance ORDER BY recorded_at DESC LIMIT ?",
                (limit,),
            )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "task_type": r[0],
                "model": r[1],
                "latency": r[2],
                "quality": r[3],
                "recorded_at": r[4],
            }
            for r in rows
        ]
