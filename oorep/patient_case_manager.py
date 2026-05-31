"""
Patient Case Manager

Hermes-session-integrated case manager. Queries and updates the
RemedyFeedbackStore across sessions so you can ask:

  - "What did I prescribe Mrs. J last month?"
  - "Show me all active prescriptions"
  - "What was our outcome with Arsenicum for anxiety?"

Usage:
    from oorep.patient_case_manager import PatientCaseManager
    pcm = PatientCaseManager()
    pcm.query_case("PT-001")
    pcm.list_active()
    pcm.ask_hermes("What did I prescribe PT-001?")
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from scripts.remedy_feedback import RemedyFeedback, RemedyFeedbackStore
except Exception:
    RemedyFeedback = None
    RemedyFeedbackStore = None


class PatientCaseManager:
    """
    Cross-session patient case manager.
    Bridges Hermes chat context to the feedback database.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if RemedyFeedback and not db_path:
            self.feedback = RemedyFeedback()
            self.store = self.feedback.store
        else:
            self.feedback = None
            self.store = None
            self._db_path = db_path

    # ── Case Retrieval ────────────────────────────────────────────────────

    def query_case(self, patient_id: str) -> Dict:
        """Get full case history for a patient."""
        if not self.feedback:
            return {"error": "Feedback store not available"}
        rxs = self.feedback.store.get_prescriptions_for_patient(patient_id)
        timeline = []
        for rx in rxs:
            reports = self.feedback.store.get_reports_for_prescription(rx["prescription_id"])
            timeline.append({
                "prescription": rx,
                "followups": reports,
                "followup_count": len(reports),
            })
        return {
            "patient_id": patient_id,
            "total_prescriptions": len(rxs),
            "timeline": timeline,
        }

    def list_active(self) -> List[Dict]:
        """Return all active prescriptions for follow-up awareness."""
        if not self.feedback:
            return []
        return self.feedback.store.get_active_prescriptions()

    def list_all_patients(self) -> List[str]:
        """Return all unique patient IDs seen in practice."""
        if not self.store:
            return []
        conn = sqlite3.connect(str(self.store.db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT patient_id FROM prescriptions ORDER BY patient_id')
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def remedy_outcome_summary(self, remedy_abbrev: str) -> Dict:
        """For a remedy, show summary of outcomes across all cases."""
        if not self.store:
            return {"error": "Store unavailable"}
        conn = sqlite3.connect(str(self.store.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            SELECT outcome_score, COUNT(*)
            FROM prescriptions
            WHERE remedy_abbrev = ? AND status = 'completed'
            GROUP BY outcome_score
        ''', (remedy_abbrev,))
        rows = cursor.fetchall()
        conn.close()
        total = sum(r[1] for r in rows)
        return {
            "remedy_abbrev": remedy_abbrev,
            "completed_cases": total,
            "outcome_distribution": {r[0]: r[1] for r in rows if r[0]},
        }

    def ask_hermes(self, question: str) -> str:
        """
        Natural-language query interpreter for case questions.
        
        Simple keyword-based; can be upgraded with LLM later.
        """
        q = question.lower()
        if "active" in q:
            active = self.list_active()
            if not active:
                return "No active prescriptions found."
            lines = [f"• {rx['remedy_abbrev']} {rx['potency']} — {rx['patient_id']} (since {rx['prescribed_date'][:10]})"
                     for rx in active[:20]]
            return f"Active prescriptions ({len(active)} total):\n" + "\n".join(lines)
        
        if "prescribed" in q or "what did" in q or "prescription" in q:
            # Try to extract patient_id from question
            # Very naive: split and try each token
            for token in q.split():
                # Accept alphanumeric with dashes (PT-001, etc.)
                if len(token) > 2:
                    case = self.query_case(token)
                    if case.get("timeline"):
                        lines = []
                        for entry in case["timeline"]:
                            rx = entry["prescription"]
                            lines.append(f"  {rx['prescribed_date'][:10]}: {rx['remedy_abbrev']} {rx['potency']} → {rx['status']}")
                        return f"Case {token} ({case['total_prescriptions']} prescriptions):\n" + "\n".join(lines)
            return "Please specify a patient ID (e.g., 'What did I prescribe PT-001?')."
        
        if "outcome" in q:
            for token in q.split():
                if len(token) > 2:
                    summary = self.remedy_outcome_summary(token)
                    if summary.get("completed_cases"):
                        dist = summary["outcome_distribution"]
                        parts = [f"{k}: {v}" for k, v in dist.items()]
                        return f"{summary['remedy_abbrev']} outcomes ({summary['completed_cases']} cases): " + ", ".join(parts)
            return "Please specify a remedy abbreviation (e.g., 'What is the outcome for Puls?')."
        
        return "I can answer questions about active prescriptions, case history, and remedy outcomes.\n"
