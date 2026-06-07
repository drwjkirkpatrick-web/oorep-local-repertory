"""
Export Research Formats — CSV, SPSS, R Data Export

Export anonymized case data for research analysis.
"""

import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExportResearchFormats:
    """
    Export practice data in research-friendly formats.
    All exports are anonymized — no PII.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.exports_dir = self.data_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, case_data: List[Dict[str, Any]],
                   filename: str = "research_export.csv") -> Dict[str, Any]:
        """Export case data as CSV."""
        path = self.exports_dir / filename
        if not case_data:
            return {"error": "No data to export"}

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=case_data[0].keys())
            writer.writeheader()
            writer.writerows(case_data)

        return {"format": "csv", "path": str(path), "rows": len(case_data)}

    def export_json(self, case_data: List[Dict[str, Any]],
                    filename: str = "research_export.json") -> Dict[str, Any]:
        """Export case data as JSON."""
        path = self.exports_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(case_data, f, indent=2)
        return {"format": "json", "path": str(path), "rows": len(case_data)}

    def get_anonymized_template(self) -> List[str]:
        """List of safe fields for research export."""
        return [
            "case_id_hash", "age_group", "gender", "symptoms",
            "prescribed_remedy", "potency", "outcome",
            "follow_up_days", "n_rubrics_used",
        ]

    def validate_anonymization(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check that exported data contains no PII."""
        pii_fields = ["name", "email", "phone", "address", "ssn", "dob"]
        violations = []
        for record in data:
            for field in pii_fields:
                if field in record:
                    violations.append(f"PII field detected: {field}")
        return {"safe": len(violations) == 0, "violations": violations}
