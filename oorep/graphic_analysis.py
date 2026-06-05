"""
Graphic Analysis / Visualization Data — Feature #17

Generate structured visualization data for repertorization results.
Remedy-vs-rubric heatmap matrices, kingdom pie charts, symptom coverage bar charts,
timeline data for follow-ups. JSON output consumable by any frontend.
No rendering — pure data generation.

Usage:
    from oorep.graphic_analysis import GraphicAnalysisEngine
    engine = GraphicAnalysisEngine(repertory_data, taxonomy_data)
    data = engine.heatmap(results)
    data = engine.kingdom_pie(results)
    data = engine.timeline(patient_history)
"""

import json
import math
from typing import Any, Dict, List, Optional
from collections import defaultdict


class GraphicAnalysisEngine:
    """
    Structured data generator for repertorization visualizations.
    Output is JSON-serializable dicts — no matplotlib, no SVG, no rendering.
    """

    def __init__(
        self,
        remedy_taxonomy: Optional[Dict[str, Any]] = None,
        rubric_data: Optional[List[Dict]] = None,
    ):
        self.taxonomy = remedy_taxonomy or {}
        self.rubric_data = rubric_data or []

    # ── Heatmap: remedy × rubric coverage ──────────────────────────────────

    def heatmap(
        self,
        results: List[Dict[str, Any]],
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate matrix data for a remedy-vs-rubric heatmap.
        Returns {rows: [remedy_abbrev], cols: [rubric_id], values: [[score]]}.
        """
        top = results[:top_n]
        remedies = [r.get("remedy", r.get("abbrev", str(i))) for i, r in enumerate(top)]

        # Collect all unique rubric IDs from results
        all_rubrics: List[str] = []
        for r in top:
            rub_ids = r.get("rubric_ids", r.get("matched_rubrics", []))
            if isinstance(rub_ids, list):
                for rid in rub_ids:
                    all_rubrics.append(str(rid))
            elif isinstance(rub_ids, (int, str)):
                all_rubrics.append(str(rub_ids))

        rubric_cols = list(dict.fromkeys(all_rubrics))  # preserve order, dedup
        max_cols = min(len(rubric_cols), 20)
        rubric_cols = rubric_cols[:max_cols]

        # Build score matrix
        values = []
        for r in top:
            row = []
            rub_ids = set(str(x) for x in r.get("rubric_ids", r.get("matched_rubrics", [])))
            for rid in rubric_cols:
                if rid in rub_ids:
                    # Use grade as cell intensity (1-3)
                    g = r.get("grade", r.get("max_grade", 1))
                    row.append(int(g))
                else:
                    row.append(0)
            values.append(row)

        return {
            "type": "heatmap",
            "rows": remedies,
            "cols": rubric_cols,
            "values": values,
            "max_value": 3,
            "min_value": 0,
            "title": f"Top {len(remedies)} Remedies × {len(rubric_cols)} Rubrics",
        }

    # ── Kingdom pie ─────────────────────────────────────────────────────────

    def kingdom_pie(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate kingdom distribution pie chart data.
        Remedies mapped to kingdom via taxonomy.
        """
        kingdom_counts: Dict[str, float] = defaultdict(float)
        total_score = 0.0

        for r in results:
            remedy = r.get("remedy", "")
            score = r.get("score", 0.0)
            if not remedy:
                continue
            # Look up taxonomy
            tax = self.taxonomy.get(remedy.upper(), {})
            kingdom = tax.get("kingdom", "Unknown")
            kingdom_counts[kingdom] += score
            total_score += score

        segments = []
        for kingdom, score in kingdom_counts.items():
            pct = (score / max(total_score, 1)) * 100
            segments.append({
                "label": kingdom,
                "value": round(score, 2),
                "percentage": round(pct, 1),
            })
        segments.sort(key=lambda s: s["value"], reverse=True)

        return {
            "type": "pie",
            "title": "Remedy Distribution by Kingdom",
            "segments": segments,
            "total_score": round(total_score, 2),
        }

    # ── Symptom coverage bar chart ───────────────────────────────────────────

    def symptom_coverage(
        self,
        results: List[Dict[str, Any]],
        symptom_set: List[str],
    ) -> Dict[str, Any]:
        """
        Bar chart data: symptom coverage by remedy.
        Each bar represents how many symptoms from the input set are covered.
        """
        bars = []
        for r in results[:10]:
            remedy = r.get("remedy", "")
            coverage = 0
            symptoms_covered = []
            for sym in symptom_set:
                if sym.lower() in str(r).lower():
                    coverage += 1
                    symptoms_covered.append(sym)
            bars.append({
                "label": remedy,
                "value": coverage,
                "total": len(symptom_set),
                "percentage": round(coverage / max(len(symptom_set), 1) * 100, 1),
                "symptoms": symptoms_covered,
            })

        return {
            "type": "bar",
            "title": "Symptom Coverage by Remedy",
            "x_axis_label": "Remedy",
            "y_axis_label": "Symptoms Covered",
            "bars": bars,
            "max": len(symptom_set),
        }

    # ── Timeline: prescription history ─────────────────────────────────────

    def timeline(
        self,
        prescription_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Timeline data for follow-up tracking.
        Input: list of {date, remedy, outcome_score, potency, notes}.
        Returns date-sorted timeline with outcomes.
        """
        events = sorted(
            prescription_history,
            key=lambda x: str(x.get("date", "")),
        )

        points = []
        for ev in events:
            points.append({
                "date": ev.get("date", ""),
                "title": f"{ev.get('remedy', '?')} {ev.get('potency', '')}",
                "outcome": ev.get("outcome_score", "unknown"),
                "notes": ev.get("notes", ""),
            })

        return {
            "type": "timeline",
            "title": "Patient Prescription History",
            "points": points,
            "start_date": points[0]["date"] if points else None,
            "end_date": points[-1]["date"] if points else None,
        }

    # ── Score distribution histogram ─────────────────────────────────────────

    def score_distribution(
        self,
        results: List[Dict[str, Any]],
        bins: int = 5,
    ) -> Dict[str, Any]:
        """
        Histogram data: remedy score distribution into bins.
        """
        scores = [r.get("score", 0.0) for r in results if r.get("score", 0.0) > 0]
        if not scores:
            return {"type": "histogram", "title": "Score Distribution", "bins": []}

        min_s = min(scores)
        max_s = max(scores)
        if max_s == min_s:
            return {"type": "histogram", "title": "Score Distribution", "bins": [{"range": f"{min_s}-{max_s}", "count": len(scores)}]}

        step = (max_s - min_s) / bins
        bin_counts = [0] * bins
        for s in scores:
            idx = min(int((s - min_s) / step), bins - 1)
            bin_counts[idx] += 1

        bins_data = []
        for i in range(bins):
            lo = round(min_s + i * step, 1)
            hi = round(min_s + (i + 1) * step, 1)
            bins_data.append({
                "label": f"{lo}-{hi}",
                "count": bin_counts[i],
                "min": lo,
                "max": hi,
            })

        return {
            "type": "histogram",
            "title": "Repertorization Score Distribution",
            "bins": bins_data,
        }

    # ── Integration helpers ────────────────────────────────────────────────

    def render_dashboard(
        self,
        results: List[Dict],
        symptoms: List[str],
        patient_history: List[Dict],
    ) -> Dict[str, Any]:
        """
        Generate all chart data at once for a dashboard view.
        Returns dict keyed by chart type.
        """
        return {
            "heatmap": self.heatmap(results),
            "kingdom_pie": self.kingdom_pie(results),
            "symptom_coverage": self.symptom_coverage(results, symptoms),
            "timeline": self.timeline(patient_history),
            "score_distribution": self.score_distribution(results),
        }

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 17,
            "feature_name": "Graphic Analysis / Visualization Data",
            "charts": ["heatmap", "pie", "bar", "timeline", "histogram"],
            "cold_start_capable": True,
            "version": "1.0",
        }
