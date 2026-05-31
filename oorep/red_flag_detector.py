"""
Red Flag Detector

Identifies symptom descriptions that contain keywords indicating a
condition requiring allopathic (conventional medical) referral.
This is a clinical safety layer, NOT a replacement for clinical judgment.

Usage:
    from oorep.red_flag_detector import RedFlagDetector
    detector = RedFlagDetector()
    result = detector.scan("chest pain radiating to left arm")
    print(result["hits"])
    detector.gate_repertorization(rubric_results)
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


# ── Built-in red flag keyword list ─────────────────────────────────────────
RED_FLAG_KEYWORDS: Dict[str, str] = {
    # Critical — immediate emergency referral
    "anaphylaxis": "critical",
    "anaphylactic shock": "critical",
    "airway obstruction": "critical",
    "unable to breathe": "critical",
    "unconscious": "critical",
    "unresponsive": "critical",
    "cardiac arrest": "critical",
    "severe chest pain": "critical",
    "crushing chest pain": "critical",
    "myocardial infarction": "critical",
    "heart attack": "critical",
    "stroke": "critical",
    "seizure": "critical",
    "status epilepticus": "critical",
    "severe bleeding": "critical",
    "hemorrhage": "critical",
    "hemorrhaging": "critical",
    "sudden severe headache": "critical",
    "thunderclap headache": "critical",
    "suicidal ideation": "critical",
    "suicidal thoughts": "critical",
    "acute psychosis": "critical",
    "delirium tremens": "critical",
    "overdose": "critical",
    "poisoning": "critical",
    # Urgent — same-day allopathic evaluation required
    "chest pain": "urgent",
    "shortness of breath": "urgent",
    "difficulty breathing": "urgent",
    "labored breathing": "urgent",
    "severe headache": "urgent",
    "worst headache": "urgent",
    "high fever": "urgent",
    "febrile seizure": "urgent",
    "dehydration": "urgent",
    "severe dehydration": "urgent",
    "bloody stool": "urgent",
    "blood in stool": "urgent",
    "bloody urine": "urgent",
    "blood in urine": "urgent",
    "black stool": "urgent",
    "vomiting blood": "urgent",
    "severe abdominal pain": "urgent",
    "rigid abdomen": "urgent",
    "severe back pain": "urgent",
    "loss of vision": "urgent",
    "sudden blindness": "urgent",
    "double vision": "urgent",
    "drooping face": "urgent",
    "facial droop": "urgent",
    "slurred speech": "urgent",
    "numbness one side": "urgent",
    "weakness one side": "urgent",
    "severe burns": "urgent",
    "fracture": "urgent",
    "broken bone": "urgent",
    "dislocation": "urgent",
    "severe infection": "urgent",
    "cellulitis": "urgent",
    "abscess": "urgent",
    "meningitis": "urgent",
    "encephalitis": "urgent",
    "ectopic pregnancy": "urgent",
    "severe hypertension": "urgent",
    "bp over 180": "urgent",
    "jaundice": "urgent",
    "yellow skin": "urgent",
    "severe anemia": "urgent",
    "rapid weight loss": "urgent",
    "neck stiffness": "urgent",
    "nuchal rigidity": "urgent",
    # Advisory — warrant allopathic workup or monitoring
    "persistent cough": "advisory",
    "chronic cough": "advisory",
    "coughing blood": "advisory",
    "blood in sputum": "advisory",
    "persistent fever": "advisory",
    "recurrent fever": "advisory",
    "night sweats": "advisory",
    "unexplained fatigue": "advisory",
    "persistent pain": "advisory",
    "lump": "advisory",
    "new mole": "advisory",
    "changing mole": "advisory",
    "irregular heartbeat": "advisory",
    "palpitations": "advisory",
    "swelling legs": "advisory",
    "edema": "advisory",
    "fainting": "advisory",
    "syncope": "advisory",
    "dizziness": "advisory",
    "memory loss": "advisory",
    "confusion": "advisory",
    "depression": "advisory",
    "anxiety attacks": "advisory",
    "seizure history": "advisory",
    "diabetes": "advisory",
    "insulin dependent": "advisory",
    "pregnancy": "advisory",
    "pregnant": "advisory",
    "immunocompromised": "advisory",
    "chemotherapy": "advisory",
    "radiation therapy": "advisory",
    "transplant": "advisory",
    "organ transplant": "advisory",
}


@dataclass
class RedFlagHit:
    keyword: str
    severity: str  # critical, urgent, advisory
    matched_text: str


class RedFlagDetector:
    """
    Scan free-text symptoms for red flag keywords that indicate the need
    for allopathic referral.

    Custom red flags can be added per-practitioner and are persisted in
    feedback.db so they survive across sessions.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(DEFAULT_DB)
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        # Load custom flags into memory
        self._custom_flags: Dict[str, str] = {}
        self._load_custom_flags()

    def _init_db(self):
        """Create custom_red_flags table in feedback.db."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_red_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                severity TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def _load_custom_flags(self):
        """Populate _custom_flags from the SQLite table."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT keyword, severity FROM custom_red_flags")
        for row in cursor.fetchall():
            self._custom_flags[row[0].lower()] = row[1]
        conn.close()

    # ── Public API ───────────────────────────────────────────────────────────

    def scan(self, symptoms_str: str) -> Dict:
        """
        Scan a symptoms string for red flag keywords.

        Args:
            symptoms_str: Free text describing the case symptoms.

        Returns:
            Dict with keys:
                has_red_flags: bool
                max_severity: 'critical' | 'urgent' | 'advisory' | None
                hits: list of RedFlagHit dicts
                recommendation: str — brief guidance text
        """
        text = (symptoms_str or "").lower()
        hits: List[RedFlagHit] = []
        merged = {**RED_FLAG_KEYWORDS, **self._custom_flags}
        for keyword, severity in merged.items():
            if keyword in text:
                hits.append(
                    RedFlagHit(
                        keyword=keyword,
                        severity=severity,
                        matched_text=text[max(0, text.find(keyword) - 10) : text.find(keyword) + len(keyword) + 10],
                    )
                )
        # Remove duplicate keyword hits
        seen = set()
        unique_hits = []
        for h in hits:
            if h.keyword not in seen:
                seen.add(h.keyword)
                unique_hits.append(h)
        hits = unique_hits

        if not hits:
            return {
                "has_red_flags": False,
                "max_severity": None,
                "hits": [],
                "recommendation": "No red flags detected. Proceed with standard homeopathic evaluation.",
            }

        severity_order = {"critical": 3, "urgent": 2, "advisory": 1}
        max_sev = max(hits, key=lambda h: severity_order.get(h.severity, 0)).severity

        recommendation = {
            "critical": "CRITICAL: Immediate allopathic / emergency referral recommended. Homeopathic care must not delay emergency treatment.",
            "urgent": "URGENT: Same-day allopathic evaluation strongly advised. Homeopathy may be used adjunctively with appropriate clinical oversight.",
            "advisory": "ADVISORY: Consider allopathic workup or monitoring. Homeopathy may proceed with awareness.",
        }.get(max_sev, "")

        return {
            "has_red_flags": True,
            "max_severity": max_sev,
            "hits": [asdict(h) for h in hits],
            "recommendation": recommendation,
        }

    def gate_repertorization(self, rubric_results: List[Dict]) -> Dict:
        """
        Gate-check repertorization results for red flags by scanning rubric
        fullpaths and any accompanying symptom text.

        Args:
            rubric_results: Typically the output of HomeopathicRepertory.repertorize()
                            or a list of dicts with keys like 'matches'.

        Returns:
            Gate dict with:
                proceed: bool — whether to allow repertorization unimpeded
                warnings: list of warning strings
                red_flag_summary: dict from scan()
        """
        # Collect all text from results
        texts: List[str] = []
        for entry in rubric_results:
            for match in entry.get("matches", []):
                rubric_text = match.get("rubric", "")
                query_text = match.get("query_symptom", "")
                if rubric_text:
                    texts.append(rubric_text)
                if query_text:
                    texts.append(query_text)
        combined = " ".join(texts)
        summary = self.scan(combined)

        warnings: List[str] = []
        proceed = True
        if summary["has_red_flags"]:
            warnings.append(summary["recommendation"])
            for h in summary["hits"]:
                warnings.append(f"  [{h['severity'].upper()}] Matched keyword: '{h['keyword']}'")
            if summary["max_severity"] == "critical":
                proceed = False
            elif summary["max_severity"] == "urgent":
                proceed = False  # Pause until practitioner acknowledges

        return {
            "proceed": proceed,
            "warnings": warnings,
            "red_flag_summary": summary,
        }

    def add_custom_red_flag(self, keyword: str, severity: str) -> bool:
        """
        Add a practitioner-defined red flag keyword.

        Args:
            keyword: The phrase to flag (case-insensitive match).
            severity: One of 'critical', 'urgent', 'advisory'.

        Returns:
            True if inserted (or already present with same severity).
        """
        severity = severity.lower().strip()
        if severity not in ("critical", "urgent", "advisory"):
            raise ValueError("severity must be critical, urgent, or advisory")
        kw = keyword.lower().strip()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO custom_red_flags (keyword, severity, created_at) VALUES (?, ?, datetime('now'))",
            (kw, severity),
        )
        conn.commit()
        conn.close()
        self._custom_flags[kw] = severity
        return True

    def list_custom_red_flags(self) -> List[Dict]:
        """Return all custom red flags from the database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT keyword, severity, created_at FROM custom_red_flags ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [
            {"keyword": r[0], "severity": r[1], "created_at": r[2]}
            for r in rows
        ]
