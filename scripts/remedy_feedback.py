#!/usr/bin/env python3
"""
Remedy Feedback & Outcome Tracking System
For homeopathic practice - tracks prescriptions and patient outcomes
"""

import sys
import json
import sqlite3
import uuid
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field

from json import JSONEncoder

# Try to import the repertory for rubric linking
try:
    from oorep.homeopathic_repertory import HomeopathicRepertory
except ImportError:
    HomeopathicRepertory = None

# Default data directory (override with --data-dir or env var OOREP_DATA_DIR)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "feedback.db"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


class DateTimeEncoder(JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@dataclass
class DynamicSymptom:
    """A symptom that can be tracked over time with state changes"""
    rubric_id: Optional[int]
    rubric_path: str
    initial_severity: int  # 1-5 scale
    current_severity: Optional[int] = None
    note: Optional[str] = None

    def to_dict(self):
        return {
            "rubric_id": self.rubric_id,
            "rubric_path": self.rubric_path,
            "initial_severity": self.initial_severity,
            "current_severity": self.current_severity,
            "note": self.note
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DynamicSymptom':
        return cls(
            rubric_id=data.get("rubric_id"),
            rubric_path=data["rubric_path"],
            initial_severity=data["initial_severity"],
            current_severity=data.get("current_severity"),
            note=data.get("note")
        )


@dataclass
class SymptomReport:
    """Follow-up symptom report - captures changes since last check"""
    report_id: str
    prescription_id: str
    timestamp: datetime
    symptoms: List[DynamicSymptom]  # Updated severities
    overall_status: str  # "improved", "unchanged", "worsened", "resolved"
    general_note: Optional[str] = None
    next_followup: Optional[datetime] = None

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "prescription_id": self.prescription_id,
            "timestamp": self.timestamp,
            "symptoms": [s.to_dict() for s in self.symptoms],
            "overall_status": self.overall_status,
            "general_note": self.general_note,
            "next_followup": self.next_followup
        }


@dataclass
class RemedyPrescription:
    """A prescribed remedy with full clinical context"""
    prescription_id: str
    patient_id: str  # Pseudonymized
    remedy_abbrev: str
    remedy_name: str
    potency: str
    prescriber_id: str  # Licensed practitioner
    prescriber_ack: bool  # Malpractice insurance + acknowledgment
    rubric_ids: List[int]  # Symptoms treated (OOREP rubrics)
    rubric_paths: List[str]
    dynamic_symptoms: List[Dict] = field(default_factory=list)  # For tracking
    status: str = "active"  # active, completed, discontinued
    prescribed_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None
    outcome_score: Optional[str] = None
    final_notes: Optional[str] = None

    def to_dict(self):
        return {
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "remedy_abbrev": self.remedy_abbrev,
            "remedy_name": self.remedy_name,
            "potency": self.potency,
            "prescriber_id": self.prescriber_id,
            "prescriber_ack": self.prescriber_ack,
            "rubric_ids": self.rubric_ids,
            "rubric_paths": self.rubric_paths,
            "dynamic_symptoms": self.dynamic_symptoms,
            "status": self.status,
            "prescribed_date": self.prescribed_date,
            "completed_date": self.completed_date,
            "outcome_score": self.outcome_score,
            "final_notes": self.final_notes
        }


class RemedyFeedbackStore:
    """SQLite-backed storage for remedy feedback and outcomes"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Prescriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                prescription_id TEXT PRIMARY KEY,
                patient_id TEXT,
                remedy_abbrev TEXT,
                remedy_name TEXT,
                potency TEXT,
                prescriber_id TEXT,
                prescriber_ack INTEGER,
                rubric_ids TEXT,
                rubric_paths TEXT,
                dynamic_symptoms TEXT,
                status TEXT,
                prescribed_date TEXT,
                completed_date TEXT,
                outcome_score TEXT,
                final_notes TEXT
            )
        ''')

        # Symptom reports table (follow-ups)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptom_reports (
                report_id TEXT PRIMARY KEY,
                prescription_id TEXT,
                timestamp TEXT,
                symptoms TEXT,
                overall_status TEXT,
                general_note TEXT,
                next_followup TEXT,
                FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id)
            )
        ''')

        # Indexes for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patient_id 
            ON prescriptions(patient_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_remedy 
            ON prescriptions(remedy_abbrev)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status 
            ON prescriptions(status)
        ''')

        conn.commit()
        conn.close()

    def add_prescription(self, rx: RemedyPrescription) -> str:
        """Save a new prescription"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO prescriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rx.prescription_id,
            rx.patient_id,
            rx.remedy_abbrev,
            rx.remedy_name,
            rx.potency,
            rx.prescriber_id,
            int(rx.prescriber_ack),
            json.dumps(rx.rubric_ids),
            json.dumps(rx.rubric_paths),
            json.dumps(rx.dynamic_symptoms),
            rx.status,
            rx.prescribed_date.isoformat(),
            rx.completed_date.isoformat() if rx.completed_date else None,
            rx.outcome_score,
            rx.final_notes
        ))

        conn.commit()
        conn.close()
        return rx.prescription_id

    def get_prescription(self, prescription_id: str) -> Optional[Dict]:
        """Retrieve a prescription by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM prescriptions WHERE prescription_id = ?', (prescription_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_prescription(row)

    def get_prescriptions_for_patient(self, patient_id: str) -> List[Dict]:
        """Get all prescriptions for a patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM prescriptions WHERE patient_id = ?', (patient_id,))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_prescription(row) for row in rows]

    def get_active_prescriptions(self) -> List[Dict]:
        """Get all active (non-completed) prescriptions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM prescriptions WHERE status = "active"')
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_prescription(row) for row in rows]

    def _row_to_prescription(self, row) -> Dict:
        """Convert DB row to prescription dict"""
        rubric_ids = json.loads(row[7]) if row[7] else []
        rubric_paths = json.loads(row[8]) if row[8] else []
        dynamic_symptoms = json.loads(row[9]) if row[9] else []

        return {
            "prescription_id": row[0],
            "patient_id": row[1],
            "remedy_abbrev": row[2],
            "remedy_name": row[3],
            "potency": row[4],
            "prescriber_id": row[5],
            "prescriber_ack": bool(row[6]),
            "rubric_ids": rubric_ids,
            "rubric_paths": rubric_paths,
            "dynamic_symptoms": dynamic_symptoms,
            "status": row[10],
            "prescribed_date": row[11],
            "completed_date": row[12],
            "outcome_score": row[13],
            "final_notes": row[14]
        }

    def add_symptom_report(self, report: SymptomReport) -> str:
        """Add a follow-up symptom report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO symptom_reports VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.report_id,
            report.prescription_id,
            report.timestamp.isoformat(),
            json.dumps([s.to_dict() for s in report.symptoms]),
            report.overall_status,
            report.general_note,
            report.next_followup.isoformat() if report.next_followup else None
        ))

        conn.commit()
        conn.close()
        return report.report_id

    def get_reports_for_prescription(self, prescription_id: str) -> List[Dict]:
        """Get all follow-up reports for a prescription"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM symptom_reports WHERE prescription_id = ? ORDER BY timestamp',
            (prescription_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            symptoms = json.loads(row[3]) if row[3] else []
            result.append({
                "report_id": row[0],
                "prescription_id": row[1],
                "timestamp": row[2],
                "symptoms": symptoms,
                "overall_status": row[4],
                "general_note": row[5],
                "next_followup": row[6]
            })
        return result

    def resolve_prescription(
        self, 
        prescription_id: str, 
        outcome_score: str,
        final_notes: Optional[str] = None
    ) -> bool:
        """Mark a prescription as completed with outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE prescriptions 
            SET status = 'completed',
                completed_date = ?,
                outcome_score = ?,
                final_notes = ?
            WHERE prescription_id = ?
        ''', (
            datetime.now().isoformat(),
            outcome_score,
            final_notes,
            prescription_id
        ))

        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def get_outcomes_summary(self) -> Dict[str, int]:
        """Get aggregate outcome statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT outcome_score, COUNT(*) 
            FROM prescriptions 
            WHERE status = 'completed' AND outcome_score IS NOT NULL
            GROUP BY outcome_score
        ''')
        results = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in results}

    def export_patient_data(self, patient_id: str) -> Dict:
        """Export complete data for a patient (for portability/backup)"""
        prescriptions = self.get_prescriptions_for_patient(patient_id)
        
        for p in prescriptions:
            p['followup_reports'] = self.get_reports_for_prescription(p['prescription_id'])
        
        return {
            "patient_id": patient_id,
            "export_date": datetime.now().isoformat(),
            "prescriptions": prescriptions
        }


class RemedyFeedback:
    """High-level interface for remedy feedback workflow"""

    def __init__(self):
        self.store = RemedyFeedbackStore()
        self.oorep = HomeopathicRepertory() if HomeopathicRepertory else None

    # ========== PRESCRIPTION WORKFLOW ==========

    def create_prescription(
        self,
        patient_id: str,
        remedy_abbrev: str,
        potency: str,
        prescriber_id: str,
        symptoms: List[str],  # Symptom descriptions (will be looked up in OOREP)
        prescriber_ack: bool = True,
        dynamic_symptoms: Optional[List[Dict]] = None
    ) -> dict:
        """
        Create a new prescription with OOREP rubric lookup.
        
        Args:
            patient_id: Pseudonymized patient identifier
            remedy_abbrev: OOREP remedy abbreviation (e.g., "Arsenicum", "Nux-v.")
            potency: Remedy potency (e.g., "30C", "200K")
            prescriber_id: Licensed practitioner ID
            symptoms: List of symptom strings to treat
            prescriber_ack: Practitioner acknowledgment of compliance
            dynamic_symptoms: Initial severity tracking for key symptoms
        
        Returns:
            Prescription dict with full details
        """
        # Lookup remedy in OOREP
        remedy = None
        if self.oorep:
            remedies = self.oorep.search_remedies(remedy_abbrev, limit=1)
            if remedies:
                remedy = remedies[0]

        # Lookup symptom rubrics
        rubric_ids = []
        rubric_paths = []
        if self.oorep and symptoms:
            for symptom in symptoms:
                results = self.oorep.search_rubrics(symptom, limit=3)
                for r in results:
                    if r['id'] not in rubric_ids:
                        rubric_ids.append(r['id'])
                        rubric_paths.append(r['fullpath'])

        # Build prescription
        rx = RemedyPrescription(
            prescription_id=str(uuid.uuid4())[:8],
            patient_id=patient_id,
            remedy_abbrev=remedy_abbrev,
            remedy_name=remedy.get('name', remedy_abbrev) if remedy else remedy_abbrev,
            potency=potency,
            prescriber_id=prescriber_id,
            prescriber_ack=prescriber_ack,
            rubric_ids=rubric_ids,
            rubric_paths=rubric_paths,
            dynamic_symptoms=dynamic_symptoms or []
        )

        self.store.add_prescription(rx)
        return rx.to_dict()

    def get_active_rx_for_patient(self, patient_id: str) -> List[Dict]:
        """Get active prescriptions for follow-up"""
        all_rx = self.store.get_active_prescriptions()
        return [rx for rx in all_rx if rx['patient_id'] == patient_id]

    # ========== FOLLOW-UP REPORTING ==========

    def add_followup_report(
        self,
        prescription_id: str,
        symptom_updates: List[Dict],  # [{"rubric_path": "...", "severity": 2}]
        overall_status: str,
        general_note: Optional[str] = None,
        next_followup_days: Optional[int] = None
    ) -> dict:
        """
        Record symptom changes at follow-up.
        
        Args:
            prescription_id: The prescription being reported on
            symptom_updates: List of {"rubric_path": str, "severity": int (1-5)}
            overall_status: "improved", "unchanged", "worsened", "resolved"
            general_note: Optional clinical note
            next_followup_days: Days until next follow-up
        
        Returns:
            Report dict
        """
        # Build dynamic symptoms from update dicts
        dynamic_symptoms = []
        for update in symptom_updates:
            dynamic_symptoms.append({
                "rubric_path": update["rubric_path"],
                "initial_severity": update.get("initial_severity", 3),
                "current_severity": update["severity"],
                "note": update.get("note")
            })

        report = SymptomReport(
            report_id=str(uuid.uuid4())[:8],
            prescription_id=prescription_id,
            timestamp=datetime.now(),
            symptoms=[],  # Using raw dict format
            overall_status=overall_status,
            general_note=general_note,
            next_followup=datetime.now() + (next_followup_days * 86400) if next_followup_days else None
        )

        # Store raw dict form for symptoms
        conn = sqlite3.connect(self.store.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO symptom_reports VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.report_id,
            report.prescription_id,
            report.timestamp.isoformat(),
            json.dumps(dynamic_symptoms),
            report.overall_status,
            report.general_note,
            report.next_followup.isoformat() if report.next_followup else None
        ))
        conn.commit()
        conn.close()

        return {
            "report_id": report.report_id,
            "prescription_id": prescription_id,
            "overall_status": overall_status,
            "next_followup": report.next_followup.isoformat() if report.next_followup else None
        }

    def resolve_with_outcome(
        self,
        prescription_id: str,
        outcome: str,  # "cured", "major_improvement", "improved", "unchanged", "worsened", "unknown"
        notes: Optional[str] = None
    ) -> bool:
        """Close a prescription with final outcome"""
        return self.store.resolve_prescription(
            prescription_id, 
            outcome, 
            notes
        )

    # ========== OUTCOMES & ANALYTICS ==========

    def get_patient_outcomes(self, patient_id: str) -> Dict:
        """Get outcome summary for a patient"""
        prescriptions = self.store.get_prescriptions_for_patient(patient_id)
        completed = [p for p in prescriptions if p['status'] == 'completed']
        
        if not completed:
            return {"message": "No completed prescriptions"}

        outcomes = self.store.get_outcomes_summary()
        return {
            "patient_id": patient_id,
            "total_prescriptions": len(prescriptions),
            "completed": len(completed),
            "outcomes": outcomes
        }

    def get_clinic_outcomes(self) -> Dict:
        """Get aggregate outcomes for the practice"""
        return {
            "summary": self.store.get_outcomes_summary(),
            "active_count": len(self.store.get_active_prescriptions())
        }


# ========== CONVENIENCE FUNCTIONS ==========

def quick_record_followup(
    prescription_id: str,
    improved_symptoms: List[str] = None,
    unchanged_symptoms: List[str] = None,
    new_symptoms: List[str] = None,
    overall: str = "improved"
) -> dict:
    """
    Simple one-line follow-up recording.
    
    Example:
        quick_record_followup("abc12345", 
            improved=["headache morning", "fatigue"],
            unchanged=["thirst"],
            overall="improved")
    """
    updates = []
    
    if improved_symptoms:
        for s in improved_symptoms:
            updates.append({"rubric_path": s, "severity": 1, "note": "improved"})
    
    if unchanged_symptoms:
        for s in unchanged_symptoms:
            updates.append({"rubric_path": s, "severity": 3, "note": "unchanged"})
    
    if new_symptoms:
        for s in new_symptoms:
            updates.append({"rubric_path": s, "severity": 3, "note": "new"})
    
    fb = RemedyFeedback()
    return fb.add_followup_report(
        prescription_id=prescription_id,
        symptom_updates=updates,
        overall_status=overall
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remedy Feedback & Outcome Tracking")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help="Create a prescription")
    p_create.add_argument("--patient-id", required=True)
    p_create.add_argument("--remedy", required=True)
    p_create.add_argument("--potency", default="30C")
    p_create.add_argument("--symptoms", nargs="+", required=True)
    p_create.add_argument("--prescriber", default="practitioner")

    p_followup = sub.add_parser("followup", help="Record a follow-up")
    p_followup.add_argument("--prescription-id", required=True)
    p_followup.add_argument("--status", choices=["cured", "major_improvement", "improved", "unchanged", "worsened", "unknown"], required=True)
    p_followup.add_argument("--note", default="")

    p_stats = sub.add_parser("stats", help="Show clinic outcome statistics")

    p_demo = sub.add_parser("demo", help="Run a demo prescription/followup cycle")

    args = parser.parse_args()

    if args.command == "demo":
        # Demo / quick test
        print("Remedy Feedback System - Demo")
        print("=" * 40)
        fb = RemedyFeedback()
        print("\n1. Creating prescription...")
        rx = fb.create_prescription(
            patient_id="PT-001",
            remedy_abbrev="Arsenicum",
            potency="30C",
            prescriber_id="DR-SMITH",
            symptoms=["anxiety health", "restlessness evening", "thirst small quantities"]
        )
        print(f"   Prescription ID: {rx['prescription_id']}")
        print(f"   Remedy: {rx['remedy_name']} ({rx['remedy_abbrev']})")
        print(f"   Rubrics: {rx['rubric_paths'][:2]}...")
        print("\n2. Recording follow-up...")
        report = fb.add_followup_report(
            prescription_id=rx['prescription_id'],
            symptom_updates=[
                {"rubric_path": "anxiety health", "severity": 2, "note": "much better"},
                {"rubric_path": "thirst small quantities", "severity": 1, "note": "resolved"}
            ],
            overall_status="improved",
            general_note="Patient reports better sleep, less anxiety"
        )
        print(f"   Report ID: {report['report_id']}")
        print(f"   Status: {report['overall_status']}")
        print("\n3. Clinic outcomes...")
        outcomes = fb.get_clinic_outcomes()
        print(f"   {outcomes}")
        print("\n" + "=" * 40)

    elif args.command == "create":
        fb = RemedyFeedback()
        rx = fb.create_prescription(
            patient_id=args.patient_id,
            remedy_abbrev=args.remedy,
            potency=args.potency,
            prescriber_id=args.prescriber,
            symptoms=args.symptoms,
        )
        print(json.dumps(rx, indent=2, cls=DateTimeEncoder))

    elif args.command == "followup":
        fb = RemedyFeedback()
        # Interactive follow-up for simplicity
        updates = []
        print("Enter symptom updates (rubric_path severity[1-5] note), blank line to finish:")
        while True:
            line = input("> ").strip()
            if not line:
                break
            parts = line.split(None, 2)
            if len(parts) >= 2:
                updates.append({
                    "rubric_path": parts[0],
                    "severity": int(parts[1]),
                    "note": parts[2] if len(parts) > 2 else "",
                })
        report = fb.add_followup_report(
            prescription_id=args.prescription_id,
            symptom_updates=updates,
            overall_status=args.status,
            general_note=args.note,
        )
        print(json.dumps(report, indent=2, cls=DateTimeEncoder))

    elif args.command == "stats":
        fb = RemedyFeedback()
        print(json.dumps(fb.get_clinic_outcomes(), indent=2))

    else:
        parser.print_help()
    print("Demo complete.")