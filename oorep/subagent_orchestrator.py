"""
Subagent Orchestrator — Benefits #35, #36, #37

Provides structured plans and checklists that a calling agent can execute
sequentially.  This module does NOT spawn subagents directly (subagents
cannot delegate deeper), but instead returns ready-to-run task breakdowns
that the parent agent can carry out.

Usage:
    from oorep.subagent_orchestrator import SubagentOrchestrator
    orchestrator = SubagentOrchestrator()

    # Break a complex case into sub-tasks
    plan = orchestrator.plan_case_analysis(case_data)

    # Structured literature search plan
    lit_plan = orchestrator.distribute_literature_review(keywords)

    # Independent re-analysis checklist
    second_opinion = orchestrator.request_second_opinion(case_data)

    # Merge sub-task results
    summary = orchestrator.summarize_findings(task_results)

    # Decision support
    queue = orchestrator.review_queue()
    escalation = orchestrator.escalation_path(severity="high")
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


@dataclass
class TaskPlan:
    """A structured task plan returned by orchestrator methods."""
    plan_id: str
    plan_type: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "normal"
    estimated_duration_minutes: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    completion_criteria: Optional[str] = None


class SubagentOrchestrator:
    """
    Pattern/template for case-analysis decomposition.

    Since sub-subagent delegation is not supported, every method returns a
    ``TaskPlan`` (or list of plans) with explicit steps that the calling
    agent can execute itself.

    Task types supported:
      - rubric_research
      - materia_medica_lookup
      - differential_diagnosis
      - strategy_synthesis
      - literature_review
      - repertorization_review
    """

    # Default repertory for cross-referencing in plans
    def __init__(self, repertory: Optional[HomeopathicRepertory] = None):
        """
        Args:
            repertory: Optional HomeopathicRepertory for in-plan rubric lookups.
        """
        self.rep = repertory

    # ── Case Analysis Planning ──────────────────────────────────────────────

    def plan_case_analysis(self, case_data: Dict[str, Any]) -> TaskPlan:
        """
        Decompose a patient case into independently executable sub-tasks.

        Recommended workflow for the calling agent:
          1. Execute ``steps`` in order, respecting ``dependencies``.
          2. Store intermediate results.
          3. Feed results into ``summarize_findings``.

        Args:
            case_data: Dict with keys such as symptoms, modalities, history,
                       and any existing rubric selections.

        Returns:
            TaskPlan with 4+ explicit steps: rubric_research,
            materia_medica_lookup, differential_diagnosis, strategy_synthesis.
        """
        case_id = case_data.get("case_id", f"CASE-{uuid.uuid4().hex[:8].upper()}")
        symptoms = case_data.get("symptoms", [])
        rubric_paths = case_data.get("rubric_paths", [])
        modalities = case_data.get("modalities", [])

        steps = [
            {
                "step_id": f"{case_id}-R1",
                "task_type": "rubric_research",
                "description": "Search repertory for rubrics matching each chief symptom.",
                "instructions": [
                    "For each symptom, run lexical + hybrid repertory search.",
                    "Record top-5 candidate rubrics per symptom.",
                    "Flag rubrics with low differentiation via PhantomRubricAnalyzer.",
                ],
                "inputs": {"symptoms": symptoms},
                "expected_outputs": {
                    "symptom_rubric_map": "dict: symptom -> list of rubric candidates",
                    "flagged_rubrics": "list of low-differentiation rubric IDs",
                },
                "estimated_minutes": 5,
            },
            {
                "step_id": f"{case_id}-M2",
                "task_type": "materia_medica_lookup",
                "description": "Retrieve materia medica profiles for top remedy candidates.",
                "instructions": [
                    "From mapped rubrics, extract top 5 remedies by total grade.",
                    "Look up each remedy in materia medica database.",
                    "Highlight confirming and contradicting symptoms.",
                ],
                "inputs": {"rubric_paths": rubric_paths},
                "expected_outputs": {
                    "remedy_profiles": "list of remedy summaries",
                    "confirming_symptoms": "dict: remedy -> confirming rubrics",
                    "contradicting_symptoms": "dict: remedy -> missing/eliminators",
                },
                "estimated_minutes": 5,
                "dependencies": [f"{case_id}-R1"],
            },
            {
                "step_id": f"{case_id}-D3",
                "task_type": "differential_diagnosis",
                "description": "Compare top remedies and rank by totality fit.",
                "instructions": [
                    "Apply EliminationAnalyzer to remove remedies with disqualifying rubrics.",
                    "Use RareRemedyTriangulator to surface overlooked small remedies.",
                    "Score each remaining remedy on coverage, grade-weight, and keynotes.",
                ],
                "inputs": {"modalties": modalities, "case_history": case_data.get("history", "")},
                "expected_outputs": {
                    "ranked_remedies": "ordered list with scores",
                    "eliminated": "list with rationale",
                    "rare_alternatives": "optional small-remedy candidates",
                },
                "estimated_minutes": 5,
                "dependencies": [f"{case_id}-M2"],
            },
            {
                "step_id": f"{case_id}-S4",
                "task_type": "strategy_synthesis",
                "description": "Synthesize final prescription recommendation with rationale.",
                "instructions": [
                    "Summarize differential reasoning in 3–5 sentences.",
                    "State chosen remedy, potency, and repetition logic.",
                    "List key rubrics that confirm choice and rubrics that weaken alternatives.",
                    "Flag any red-lights or suppression concerns via RedFlagDetector.",
                ],
                "inputs": {},
                "expected_outputs": {
                    "recommendation": "dict: remedy, potency, repetition, rationale",
                    "confidence": "low / moderate / high",
                    "caveats": "list of warnings",
                },
                "estimated_minutes": 3,
                "dependencies": [f"{case_id}-D3"],
            },
        ]

        return TaskPlan(
            plan_id=f"PLAN-{case_id}",
            plan_type="case_analysis",
            description=f"Full repertorization and prescription workflow for case {case_id}",
            steps=steps,
            priority="high" if any(s.get("is_red_flag") for s in symptoms) else "normal",
            estimated_duration_minutes=18,
            dependencies=[],
            deliverables=[
                "symptom_rubric_map",
                "ranked_remedies",
                "recommendation",
                "caveats",
            ],
            completion_criteria=(
                "All four steps have outputs; recommendation includes remedy, potency, and rationale."
            ),
        )

    # ── Literature Review Planning ──────────────────────────────────────────

    def distribute_literature_review(self, keywords: List[str]) -> TaskPlan:
        """
        Return a structured search plan for peer-reviewed literature and materia medica.

        Args:
            keywords: Clinical topics / remedy names to research.

        Returns:
            TaskPlan with parallel search steps.
        """
        case_id = f"LIT-{uuid.uuid4().hex[:8].upper()}"
        steps = [
            {
                "step_id": f"{case_id}-SEARCH-1",
                "task_type": "literature_review",
                "description": "Primary source search for keywords.",
                "instructions": [
                    "Search PubMed / Google Scholar for remedy + symptom combinations.",
                    "Record paper titles, sample sizes, and primary findings.",
                    "Prioritise RCTs, systematic reviews, and case series.",
                ],
                "inputs": {"keywords": keywords},
                "expected_outputs": {"papers": "list of bibliographic dicts"},
                "estimated_minutes": 10,
            },
            {
                "step_id": f"{case_id}-SEARCH-2",
                "task_type": "literature_review",
                "description": "Classical materia medica cross-reference.",
                "instructions": [
                    "Look up each remedy in Kent, Boenninghausen, Hering sources.",
                    "Extract keynotes and comparative materia medica notes.",
                    "Note remedy-relationships listed in the repertory.",
                ],
                "inputs": {"keywords": keywords},
                "expected_outputs": {"materia_medica_notes": "dict: remedy -> list of classical references"},
                "estimated_minutes": 8,
            },
            {
                "step_id": f"{case_id}-SEARCH-3",
                "task_type": "literature_review",
                "description": "Safety and interaction screening.",
                "instructions": [
                    "Check for known remedy interactions, aggravations, or tincture toxicity.",
                    "Cross-reference with RedFlagDetector suppression history.",
                    "Document any cautions in the final summary.",
                ],
                "inputs": {"keywords": keywords},
                "expected_outputs": {"safety_notes": "list of caution strings"},
                "estimated_minutes": 5,
            },
        ]

        return TaskPlan(
            plan_id=f"PLAN-{case_id}",
            plan_type="literature_review",
            description=f"Structured literature review for {', '.join(keywords[:3])}",
            steps=steps,
            priority="normal",
            estimated_duration_minutes=23,
            dependencies=[],
            deliverables=["papers", "materia_medica_notes", "safety_notes"],
            completion_criteria="All three search tracks return non-empty outputs.",
        )

    # ── Second Opinion / Re-Analysis ────────────────────────────────────────

    def request_second_opinion(self, case_data: Dict[str, Any]) -> TaskPlan:
        """
        Return an independent repertorization checklist for another practitioner
        or for a later self-review.

        Args:
            case_data: Same schema as ``plan_case_analysis``.

        Returns:
            TaskPlan with re-analysis steps that deliberately ignore the first
            pass remedy so bias is reduced.
        """
        case_id = case_data.get("case_id", f"CASE-{uuid.uuid4().hex[:8].upper()}")
        original_remedy = case_data.get("original_remedy_guess", "")

        steps = [
            {
                "step_id": f"{case_id}-SO-1",
                "task_type": "repertorization_review",
                "description": "Blind re-pertorization with hidden original remedy.",
                "instructions": [
                    "List symptoms afresh; do *not* look at original remedy choice.",
                    "Search rubrics independently using same symptom set.",
                    "Record any rubrics that were missed in the first pass.",
                ],
                "inputs": {"symptoms": case_data.get("symptoms", [])},
                "expected_outputs": {
                    "new_rubric_map": "symptom -> rubrics",
                    "missed_rubrics": "list of rubrics not selected originally",
                },
                "estimated_minutes": 5,
            },
            {
                "step_id": f"{case_id}-SO-2",
                "task_type": "differential_diagnosis",
                "description": "Compare new differential with original differential.",
                "instructions": [
                    f"The original remedy guess was '{original_remedy}'; do not let it bias scoring.",
                    "Re-score top 5 remedies using ONLY the new rubric set.",
                    "Note concordance / discordance with original ranked list.",
                ],
                "inputs": {},
                "expected_outputs": {
                    "ranked_remedies_v2": "ordered list",
                    "concordance_notes": "where lists agree or diverge",
                },
                "estimated_minutes": 5,
                "dependencies": [f"{case_id}-SO-1"],
            },
            {
                "step_id": f"{case_id}-SO-3",
                "task_type": "strategy_synthesis",
                "description": "Independent recommendation with deviation rationale.",
                "instructions": [
                    "If the top remedy differs from the original, explain why.",
                    "Flag any rubric-quality concerns (phantom rubrics, low confidence).",
                    "Provide a clear go / no-go / escalate verdict.",
                ],
                "inputs": {},
                "expected_outputs": {
                    "verdict": "go / no-go / escalate",
                    "deviation_rationale": "text explaining any change of remedy",
                },
                "estimated_minutes": 3,
                "dependencies": [f"{case_id}-SO-2"],
            },
        ]

        return TaskPlan(
            plan_id=f"SO-{case_id}",
            plan_type="second_opinion",
            description=f"Independent re-analysis for case {case_id} (original guess: {original_remedy})",
            steps=steps,
            priority="high" if original_remedy else "normal",
            estimated_duration_minutes=13,
            dependencies=[],
            deliverables=["new_rubric_map", "ranked_remedies_v2", "verdict", "deviation_rationale"],
            completion_criteria="Second-opinion ranking is ready and verdict is explicit.",
        )

    # ── Findings Summariser ────────────────────────────────────────────────

    @staticmethod
    def summarize_findings(task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge outputs from multiple sub-task plans into a coherent
        recommendation document.

        Args:
            task_results: List of result dicts, each with keys: step_id,
                          task_type, status, outputs.

        Returns:
            Dict with keys: summary_text, recommendation, supporting_evidence,
            confidence_level, warnings.
        """
        completed = [r for r in task_results if r.get("status") == "completed"]
        failed = [r for r in task_results if r.get("status") != "completed"]

        # Gather recommendation from any strategy_synthesis step
        recommendation = {}
        for r in completed:
            outputs = r.get("outputs", {})
            if "recommendation" in outputs:
                recommendation = outputs["recommendation"]
                break

        # Collect supporting evidence
        evidence = []
        for r in completed:
            outputs = r.get("outputs", {})
            for k, v in outputs.items():
                if k in ("papers", "materia_medica_notes", "confirming_symptoms",
                         "rare_alternatives", "new_rubric_map"):
                    evidence.append({"source_step": r.get("step_id"), "type": k, "data": v})

        # Build summary text
        lines = [
            "## Case Analysis Summary",
            "",
            f"Completed steps: {len(completed)} / {len(task_results)}",
        ]
        if failed:
            lines.append(f"Failed / incomplete steps: {len(failed)}")
            for f in failed:
                lines.append(f"  - {f.get('step_id')}: {f.get('error', 'unknown error')}")
        lines.append("")

        if recommendation:
            remedy = recommendation.get("remedy", "?")
            potency = recommendation.get("potency", "?")
            rationale = recommendation.get("rationale", "")
            lines.extend([
                f"**Recommended remedy:** {remedy} {potency}",
                f"**Rationale:** {rationale}",
                "",
            ])
        else:
            lines.append("**No final strategy_synthesis output found.**\n")

        warnings = []
        for r in completed:
            outputs = r.get("outputs", {})
            caveats = outputs.get("caveats") or outputs.get("safety_notes") or outputs.get("warnings")
            if caveats:
                warnings.extend(caveats if isinstance(caveats, list) else [caveats])

        confidence = "low"
        if len(completed) >= 4 and not failed:
            confidence = "high"
        elif len(completed) >= 2:
            confidence = "moderate"

        return {
            "summary_text": "\n".join(lines),
            "recommendation": recommendation,
            "supporting_evidence": evidence,
            "confidence_level": confidence,
            "warnings": warnings,
        }

    # ── Decision Support ────────────────────────────────────────────────────

    def review_queue(self) -> List[Dict[str, Any]]:
        """
        Return a snapshot of the current review queue for decision support.

        This lightweight method can be polled before or after case analysis to
        see if any remedies or rubrics are under active review.

        Returns:
            List of dicts with keys: item_type, item_id, reason, priority,
            suggested_action.
        """
        # In a real deployment this could query remedy_review_queue / audit_log.
        # Here we return a template structure so the calling agent can populate it.
        return [
            {
                "item_type": "template_remedy_review",
                "item_id": "RMT-001",
                "reason": "Awaiting proving update for rare remedy",
                "priority": "normal",
                "suggested_action": "Hold prescription until proving log updated",
            },
            {
                "item_type": "template_rubric_quality",
                "item_id": "RUB-999",
                "reason": "Phantom rubric flagged by analyzer",
                "priority": "low",
                "suggested_action": "Exclude rubric from repertorization or upgrade",
            },
        ]

    def escalation_path(self, severity: str = "normal", context: Optional[str] = None) -> Dict[str, Any]:
        """
        Return a decision-tree escalation path based on severity level.

        Args:
            severity: One of "normal", "moderate", "high", "critical".
            context: Optional free-text context (e.g., remedy name, symptom).

        Returns:
            Dict with keys: severity, next_steps, contacts, documentation_needed.
        """
        paths = {
            "normal": {
                "next_steps": [
                    "Complete standard repertorization plan.",
                    "Log prescription in RemedyFeedbackStore.",
                    "Schedule routine follow-up.",
                ],
                "contacts": ["primary prescriber"],
                "documentation_needed": ["prescription", "case notes"],
            },
            "moderate": {
                "next_steps": [
                    "Run second-opinion checklist via request_second_opinion().",
                    "Verify no historical suppression via SuppressionTracker.",
                    "Flag in audit trail for later review.",
                ],
                "contacts": ["primary prescriber", "senior colleague"],
                "documentation_needed": ["prescription", "rationale", "follow-up plan"],
            },
            "high": {
                "next_steps": [
                    "MANDATORY second-opinion before prescribing.",
                    "Review RedFlagDetector output.",
                    "Escalate to senior practitioner or mentor.",
                ],
                "contacts": ["primary prescriber", "senior practitioner", "clinical supervisor"],
                "documentation_needed": ["prescription", "second_opinion_plan", "risk_acknowledgement"],
            },
            "critical": {
                "next_steps": [
                    "STOP — do not prescribe without immediate senior review.",
                    "Document reason for urgency in AuditTrail.",
                    "Consider conventional medicine referral.",
                ],
                "contacts": ["clinical supervisor", "emergency contact"],
                "documentation_needed": ["urgent_case_note", "supervisor_sign_off", "patient_consent"],
            },
        }
        selected = paths.get(severity, paths["normal"])
        return {
            "severity": severity,
            "context": context,
            "next_steps": selected["next_steps"],
            "contacts": selected["contacts"],
            "documentation_needed": selected["documentation_needed"],
            "timestamp": datetime.now().isoformat(),
        }

    # ── Convenience: batch orchestration ────────────────────────────────────

    def run_full_analysis(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience method that returns *all* plans for a case in one dict.

        The calling agent can then execute them step-by-step and feed results
        back into ``summarize_findings``.
        """
        return {
            "case_id": case_data.get("case_id"),
            "primary_plan": asdict(self.plan_case_analysis(case_data)),
            "literature_plan": asdict(self.distribute_literature_review(
                keywords=case_data.get("symptoms", [])
            )),
            "second_opinion_plan": asdict(self.request_second_opinion(case_data)),
            "escalation": self.escalation_path(
                severity=case_data.get("severity", "normal"),
                context=case_data.get("case_id"),
            ),
            "review_queue_snapshot": self.review_queue(),
        }
