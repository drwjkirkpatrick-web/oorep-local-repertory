"""
Patient Cohort Analytics

SQL-powered analytics over the RemedyFeedbackStore for practice-wide insights:
  - Most common follow-up remedies
  - Remedy → outcome correlations
  - Symptom → remedy success patterns
  - Prescription timelines and timelines
  - Practitioner-level statistics

Usage:
    from oorep.patient_cohort_analytics import PatientCohortAnalytics
    analytics = PatientCohortAnalytics()
    print(analytics.top_followup_remedies("Puls.", top_n=5))
    print(analytics.remedy_outcome_rates())
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime


# Reuse feedback DB path from remedy_feedback if possible
try:
    from scripts.remedy_feedback import RemedyFeedbackStore, DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


class PatientCohortAnalytics:
    """Analytics for patient cohorts and prescription outcomes."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB

    def _execute(self, sql: str, params: tuple = ()) -> List[tuple]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def top_followup_remedies(self, remedy_abbrev: str, top_n: int = 10) -> List[Dict]:
        """
        Given remedy X was prescribed, what remedies were prescribed next
        (for any patient with a follow-up prescription)?
        """
        sql = '''
            SELECT p2.remedy_abbrev, COUNT(*) as cnt
            FROM prescriptions p1
            JOIN prescriptions p2 ON p1.patient_id = p2.patient_id
            WHERE p1.remedy_abbrev = ?
              AND p2.prescribed_date > p1.prescribed_date
            GROUP BY p2.remedy_abbrev
            ORDER BY cnt DESC
            LIMIT ?
        '''
        rows = self._execute(sql, (remedy_abbrev, top_n))
        return [
            {"remedy_abbrev": r[0], "followup_count": r[1]}
            for r in rows
        ]

    def remedy_outcome_rates(self, min_prescriptions: int = 3) -> List[Dict]:
        """
        Calculate outcome rates per remedy.
        Only includes remedies with >= min_prescriptions completed cases.
        """
        sql = '''
            SELECT remedy_abbrev, outcome_score, COUNT(*) as cnt
            FROM prescriptions
            WHERE status = 'completed' AND outcome_score IS NOT NULL
            GROUP BY remedy_abbrev, outcome_score
        '''
        rows = self._execute(sql)
        # Aggregate by remedy
        agg: Dict[str, Dict] = {}
        for remedy, outcome, cnt in rows:
            if remedy not in agg:
                agg[remedy] = {"total": 0, "outcomes": {}}
            agg[remedy]["total"] += cnt
            agg[remedy]["outcomes"][outcome] = agg[remedy]["outcomes"].get(outcome, 0) + cnt

        results = []
        for remedy, data in agg.items():
            if data["total"] < min_prescriptions:
                continue
            outcomes = dict(data["outcomes"])
            success = outcomes.get("cured", 0) + outcomes.get("major_improvement", 0) + outcomes.get("improved", 0)
            success_rate = round(success / data["total"], 3)
            results.append({
                "remedy_abbrev": remedy,
                "total_cases": data["total"],
                "success_rate": success_rate,
                "outcomes": outcomes,
            })
        results.sort(key=lambda x: x["success_rate"], reverse=True)
        return results

    def patient_timeline(self, patient_id: str) -> List[Dict]:
        """
        Return chronological prescription + follow-up timeline for a patient.
        """
        # Prescriptions for patient
        sql_rx = '''
            SELECT prescription_id, remedy_abbrev, potency, prescribed_date,
                   status, outcome_score, final_notes
            FROM prescriptions
            WHERE patient_id = ?
            ORDER BY prescribed_date
        '''
        rx_rows = self._execute(sql_rx, (patient_id,))
        # Reports for any rx by this patient
        sql_rpt = '''
            SELECT r.*
            FROM symptom_reports r
            JOIN prescriptions p ON r.prescription_id = p.prescription_id
            WHERE p.patient_id = ?
            ORDER BY r.timestamp
        '''
        rpt_rows = self._execute(sql_rpt, (patient_id,))

        # Build unified timeline
        timeline = []
        for row in rx_rows:
            rx_id, remedy, potency, date, status, outcome, notes = row
            timeline.append({
                "event_type": "prescription",
                "timestamp": date,
                "prescription_id": rx_id,
                "remedy_abbrev": remedy,
                "potency": potency,
                "status": status,
                "outcome": outcome,
                "notes": notes,
            })
        for row in rpt_rows:
            report_id, rx_id, ts, symptoms, overall, note, next_fu = row
            timeline.append({
                "event_type": "followup_report",
                "timestamp": ts,
                "report_id": report_id,
                "prescription_id": rx_id,
                "overall_status": overall,
                "general_note": note,
                "symptom_count": len(json.loads(symptoms)) if symptoms else 0,
            })
        timeline.sort(key=lambda x: x["timestamp"] or "")
        return timeline

    def symptom_to_remedy_success(self, rubric_path_fragment: str, min_cases: int = 2) -> List[Dict]:
        """
        Which remedies have the best outcomes for cases that included a given
        rubric path fragment (e.g. "anxiety health") in their prescription?
        """
        sql = '''
            SELECT remedy_abbrev, outcome_score, COUNT(*) as cnt
            FROM prescriptions
            WHERE rubric_paths LIKE ? AND status = 'completed'
            GROUP BY remedy_abbrev, outcome_score
        '''
        rows = self._execute(sql, (f"%{rubric_path_fragment}%",))
        agg: Dict[str, Dict] = {}
        for remedy, outcome, cnt in rows:
            if remedy not in agg:
                agg[remedy] = {"total": 0, "outcomes": {}}
            agg[remedy]["total"] += cnt
            agg[remedy]["outcomes"][outcome] = agg[remedy]["outcomes"].get(outcome, 0) + cnt

        results = []
        for remedy, data in agg.items():
            if data["total"] < min_cases:
                continue
            outcomes = dict(data["outcomes"])
            success = outcomes.get("cured", 0) + outcomes.get("major_improvement", 0)
            success_rate = round(success / data["total"], 3)
            results.append({
                "remedy_abbrev": remedy,
                "total_cases": data["total"],
                "success_rate": success_rate,
                "outcomes": outcomes,
            })
        results.sort(key=lambda x: (x["success_rate"], x["total_cases"]), reverse=True)
        return results

    def active_cases_summary(self) -> Dict:
        """Overview of currently active prescriptions."""
        sql = '''
            SELECT COUNT(*), COUNT(DISTINCT patient_id)
            FROM prescriptions
            WHERE status = 'active'
        '''
        row = self._execute(sql)[0]
        return {
            "active_prescriptions": row[0],
            "active_patients": row[1],
        }

    def practitioner_stats(self, prescriber_id: Optional[str] = None) -> List[Dict]:
        """Aggregate stats per prescriber."""
        sql = '''
            SELECT prescriber_id,
                   COUNT(*) as total_rx,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN prescriber_ack = 1 THEN 1 ELSE 0 END) as acked
            FROM prescriptions
        '''
        params = ()
        if prescriber_id:
            sql += ' WHERE prescriber_id = ?'
            params = (prescriber_id,)
        sql += ' GROUP BY prescriber_id'
        rows = self._execute(sql, params)
        return [
            {
                "prescriber_id": r[0],
                "total_prescriptions": r[1],
                "completed": r[2],
                "acknowledged": r[3],
            }
            for r in rows
        ]

    def monthly_volume(self, months: int = 12) -> List[Dict]:
        """Prescription volume by month (YYYY-MM)."""
        sql = '''
            SELECT substr(prescribed_date, 1, 7) as month,
                   COUNT(*) as rx_count,
                   COUNT(DISTINCT patient_id) as patients
            FROM prescriptions
            WHERE substr(prescribed_date, 1, 7) >= date('now', '-{} months')
            GROUP BY month
            ORDER BY month
        '''.format(months)
        rows = self._execute(sql)
        return [
            {"month": r[0], "prescriptions": r[1], "unique_patients": r[2]}
            for r in rows
        ]
