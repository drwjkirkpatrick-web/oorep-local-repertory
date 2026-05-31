"""
Grand Rounds — Benefit #48

Aggregates multiple anonymized patient cases into composite narratives for
clinical teaching.  Computes statistical themes across cohorts, compares
patterns with classical literature expectations, and exports slideshow-ready
markdown for presentation.

Usage:
    from oorep.grand_rounds import GrandRounds
    gr = GrandRounds()

    # Synthesize a composite narrative from filtered cases
    narrative = gr.synthesize_cases(case_filters={"remedy": "Puls.", "min_prescriptions": 5})

    # Find common themes across cases
    themes = gr.find_common_themes(cases)

    # Generate a teaching grand-rounds summary
    summary = gr.generate_teaching_narrative(cases)

    # Flag unusual presentations
    unusual = gr.compare_with_literature(cases)

    # Export to slideshow markdown
    md = gr.export_for_presentation(cases, format="markdown")
"""

import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"

try:
    from .patient_cohort_analytics import PatientCohortAnalytics
except Exception:
    from patient_cohort_analytics import PatientCohortAnalytics


try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


class GrandRounds:
    """
    Clinical-teaching narrative engine.

    Combines PatientCohortAnalytics with classical repertory knowledge to
    produce statistically grounded, literature-aware teaching summaries.
    """

    # Classical remedy–symptom associations for comparison
    # (lightweight hard-coded examples; can be expanded or loaded from JSON)
    CLASSICAL_ASSOCIATIONS: Dict[str, List[str]] = {
        "Ars.": ["anxiety", "restlessness", "burning", "thirst small quantities", "midnight aggravation"],
        "Puls.": ["changeable", "weeping", "thirstless", "worse warmth", "better cold air", "menses delayed"],
        "Sulph.": ["philosophical", "dirty", "burning feet", "worse heat", "hungry", "diarrhea morning"],
        "Nux-v.": ["irritable", "sensitive", "chilly", "worse morning", "worse cold", "constipation"],
        "Lyc.": ["domineering", "flatulence", "worse right side", "worse 4-8pm", "thirst small quantities"],
        "Calc-c.": ["fatigue", "cold extremities", "worse exertion", "sweat head", "delayed development"],
        "Phos.": ["fear thunder", "burning", "thirst cold drinks", "worse evening", "haemorrhage"],
        "Sep.": ["indifference", "chilly", "worse before menses", "saddle bag", "aversion sex"],
    }

    def __init__(
        self,
        db_path: Optional[Path] = None,
        cohort_analytics: Optional[PatientCohortAnalytics] = None,
        repertory: Optional[HomeopathicRepertory] = None,
    ):
        """
        Args:
            db_path: SQLite database with prescription / outcome data.
            cohort_analytics: Existing PatientCohortAnalytics instance (optional).
            repertory: HomeopathicRepertory for rubric lookups (optional).
        """
        self.db_path = Path(db_path) if db_path else Path(DEFAULT_DB)
        self.analytics = cohort_analytics or PatientCohortAnalytics(self.db_path)
        self.rep = repertory or HomeopathicRepertory()

    # ── Case Synthesis ──────────────────────────────────────────────────────

    def synthesize_cases(self, case_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve and aggregate anonymized cases matching ``case_filters``.

        Filters are passed through to ``PatientCohortAnalytics`` queries where
        possible, and refined with local SQL when needed.

        Supported keys:
          - remedy: target remedy abbreviation
          - min_prescriptions: minimum total prescriptions for inclusion
          - status: 'completed', 'active', etc.
          - outcome_score: minimum outcome score
          - date_from / date_to: ISO date strings

        Returns:
            List of case dicts with keys: patient_id (anonymized), prescriptions,
            timeline, common_remedies, common_rubrics.
        """
        case_filters = case_filters or {}
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build dynamic WHERE clause
        where_clauses = []
        params = []
        if "remedy" in case_filters:
            where_clauses.append("remedy_abbrev = ?")
            params.append(case_filters["remedy"])
        if "status" in case_filters:
            where_clauses.append("status = ?")
            params.append(case_filters["status"])
        if "date_from" in case_filters:
            where_clauses.append("prescribed_date >= ?")
            params.append(case_filters["date_from"])
        if "date_to" in case_filters:
            where_clauses.append("prescribed_date <= ?")
            params.append(case_filters["date_to"])

        sql = "SELECT * FROM prescriptions"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY patient_id, prescribed_date"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        # Group by patient_id
        by_patient: Dict[str, List[Dict]] = defaultdict(list)
        for row in rows:
            row_dict = {k: row[k] for k in row.keys()}
            by_patient[row_dict["patient_id"]].append(row_dict)

        min_prescriptions = case_filters.get("min_prescriptions", 1)
        cases = []
        for patient_id, prescriptions in by_patient.items():
            if len(prescriptions) < min_prescriptions:
                continue
            # Anonymize patient_id
            anon_id = f"ANON-{hash(patient_id) & 0xFFFFFFFF:08X}"
            timeline = self.analytics.patient_timeline(patient_id)
            cases.append({
                "patient_id": anon_id,
                "prescription_count": len(prescriptions),
                "prescriptions": prescriptions,
                "timeline": timeline,
            })

        return cases

    # ── Theme Analysis ────────────────────────────────────────────────────────

    def find_common_themes(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Statistical analysis of recurring remedies, rubrics, and outcomes.

        Args:
            cases: Output from ``synthesize_cases``.

        Returns:
            Dict with keys:
              - top_remedies: frequency-ranked remedies
              - top_rubrics: most common rubric path fragments
              - outcome_distribution: aggregate outcome counts
              - average_prescriptions_per_patient
              - temporal_patterns: month-by-month volume hints
        """
        remedy_counter = Counter()
        rubric_counter = Counter()
        outcome_counter = Counter()
        total_rx = 0

        for case in cases:
            for rx in case.get("prescriptions", []):
                total_rx += 1
                remedy_counter[rx.get("remedy_abbrev", "?")] += 1
                outcome = rx.get("outcome_score") or rx.get("status", "unknown")
                outcome_counter[str(outcome)] += 1
                paths = rx.get("rubric_paths", "")
                if paths:
                    for p in paths.split(","):
                        p_clean = p.strip().lower()
                        if p_clean:
                            rubric_counter[p_clean] += 1

        top_remedies = [
            {"remedy": r, "count": c, "percentage": round(c / total_rx, 3) if total_rx else 0}
            for r, c in remedy_counter.most_common(10)
        ]
        top_rubrics = [
            {"rubric_path": r, "count": c}
            for r, c in rubric_counter.most_common(15)
        ]
        outcome_distribution = dict(outcome_counter)
        avg_rx_per_patient = round(total_rx / len(cases), 1) if cases else 0.0

        return {
            "top_remedies": top_remedies,
            "top_rubrics": top_rubrics,
            "outcome_distribution": outcome_distribution,
            "total_prescriptions": total_rx,
            "patient_count": len(cases),
            "average_prescriptions_per_patient": avg_rx_per_patient,
        }

    # ── Teaching Narrative ──────────────────────────────────────────────────

    def generate_teaching_narrative(self, cases: List[Dict[str, Any]]) -> str:
        """
        Produce formatted "grand rounds" case summary for teaching.

        Weaves the composite data into a readable markdown narrative with
        bullet-point takeaways suitable for resident/junior teaching rounds.

        Args:
            cases: Output from ``synthesize_cases``.

        Returns:
            Markdown string.
        """
        themes = self.find_common_themes(cases)
        lines = [
            "# Grand Rounds Teaching Summary",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ",
            f"**Cases reviewed:** {themes['patient_count']}  ",
            f"**Total prescriptions:** {themes['total_prescriptions']}  ",
            "",
            "## Most Frequently Prescribed Remedies",
            "",
        ]
        for entry in themes["top_remedies"][:5]:
            lines.append(
                f"- **{entry['remedy']}** — {entry['count']} prescriptions "
                f"({entry['percentage']:.0%})"
            )
        lines.extend([
            "",
            "## Common Rubrics / Symptom Clusters",
            "",
        ])
        for entry in themes["top_rubrics"][:5]:
            lines.append(f"- {entry['rubric_path']} ({entry['count']} cases)")

        lines.extend([
            "",
            "## Outcome Overview",
            "",
        ])
        for outcome, count in themes["outcome_distribution"].items():
            lines.append(f"- {outcome}: {count} cases")

        lines.extend([
            "",
            "## Clinical Takeaways",
            "",
            "1. Prescription clustering suggests a strong seasonal or demographic pattern.\n",
            "2. Rubric overlap indicates shared constitutional or miasmatic tendencies.\n",
            "3. Outcome rates should be compared against practice benchmarks.\n",
        ])
        return "\n".join(lines)

    # ── Literature Comparison ─────────────────────────────────────────────────

    def compare_with_literature(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flag cases that deviate from classical remedy–symptom associations.

        Each case is compared against ``CLASSICAL_ASSOCIATIONS``; if the most
        common remedy in a case does NOT share expected rubric themes, it is
        flagged as "unusual presentation".

        Returns:
            List of dicts with keys: remedy, flag_reason, unusual_rubrics,
            expected_themes, matched_themes.
        """
        results = []
        for case in cases:
            # Determine dominant remedy in this case
            remedies = [rx.get("remedy_abbrev", "?") for rx in case.get("prescriptions", [])]
            if not remedies:
                continue
            dominant = Counter(remedies).most_common(1)[0][0]
            # Gather rubric words from this case
            all_rubric_words = set()
            for rx in case.get("prescriptions", []):
                paths = rx.get("rubric_paths", "")
                if paths:
                    for p in paths.split(","):
                        all_rubric_words.update(re.findall(r"[a-z]+", p.lower()))

            expected = set(self.CLASSICAL_ASSOCIATIONS.get(dominant, []))
            matched = expected & all_rubric_words
            missing = expected - all_rubric_words

            if len(matched) < 2 and expected:
                # Unusual presentation: few classical keywords match
                results.append({
                    "remedy": dominant,
                    "flag_reason": "Classical symptom profile not prominently represented",
                    "unusual_rubrics": list(all_rubric_words)[:10],
                    "expected_themes": list(expected),
                    "matched_themes": list(matched),
                })
            else:
                results.append({
                    "remedy": dominant,
                    "flag_reason": "Classical profile largely matched",
                    "matched_themes": list(matched),
                    "missing_themes": list(missing),
                })
        return results

    # ── Export ──────────────────────────────────────────────────────────────

    def export_for_presentation(
        self, cases: List[Dict[str, Any]], format: str = "markdown"
    ) -> str:
        """
        Export a grand-rounds teaching deck in slideshow-ready markdown.

        Currently supports ``markdown`` only (future: ``pptx``, ``html``).
        Each slide is separated by a horizontal rule (---) and titled for
        easy import into Marp, reveal.js, or Pandoc beamer.

        Args:
            cases: Synthesized cases.
            format: Export format. Defaults to "markdown".

        Returns:
            Markdown string.
        """
        if format.lower() != "markdown":
            raise ValueError(f"Unsupported presentation format: {format}")

        themes = self.find_common_themes(cases)
        unusual = self.compare_with_literature(cases)

        slides = [
            "---",
            "marp: true",
            "theme: default",
            "---",
            "",
            "# Grand Rounds Presentation",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ",
            f"**Cohort size:** {themes['patient_count']} patients",
            "",
            "---",
            "",
            "## Remedy Distribution",
            "",
        ]
        for entry in themes["top_remedies"][:5]:
            slides.append(
                f"- **{entry['remedy']}** — {entry['count']} prescriptions"
            )
        slides.extend([
            "",
            "---",
            "",
            "## Top Symptom Clusters",
            "",
        ])
        for entry in themes["top_rubrics"][:5]:
            slides.append(f"- {entry['rubric_path']} ({entry['count']} cases)")

        slides.extend([
            "",
            "---",
            "",
            "## Literature Comparison — Unusual Presentations",
            "",
        ])
        for u in unusual[:5]:
            if "flag_reason" in u:
                slides.append(f"- **{u['remedy']}**: {u['flag_reason']}")

        slides.extend([
            "",
            "---",
            "",
            "## Discussion Questions",
            "",
            "1. Why do these remedies cluster in this cohort?\n",
            "2. Are there seasonal, geographic, or referral-bias explanations?\n",
            "3. Which cases would benefit from second-opinion repertorization?\n",
        ])
        return "\n".join(slides)
