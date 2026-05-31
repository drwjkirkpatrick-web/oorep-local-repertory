"""OOREP local repertory package.

Grouped package layout:
- oorep/       Python API modules
- data/        OOREP JSON data exports
- indexes/     vector index artifacts
- tests/       regression tests
"""

from .homeopathic_repertory import HomeopathicRepertory, quick_search
from .clinical_rubric_mapper import ClinicalRubricMapper
from .rare_remedy_triangulator import RareRemedyTriangulator
from .remedy_comparator import RemedyComparator, compare_remedies_quick
from .srp_detector import SRPDetector, quick_analyze as srp_quick_analyze
from .phantom_rubric_analyzer import PhantomRubricAnalyzer, quick_phantoms
from .rubric_cooccurrence import RubricCooccurrenceEngine, top_remedy_pairs
from .private_rubrics import PrivateRubricManager, quick_create
from .patient_cohort_analytics import PatientCohortAnalytics
from .patient_case_manager import PatientCaseManager
from .practitioner_approval_gate import PractitionerApprovalGate, require_ack, ApprovalRequired
from .remedy_relationships import RemedyRelationships
from .red_flag_detector import RedFlagDetector
from .elimination_analysis import EliminationAnalyzer
from .potency_guidance import PotencyGuidance
from .acute_chronic_layer import AcuteChronicTagger
from .family_constellation import FamilyConstellation
from .suppression_tracker import SuppressionTracker
from .rubric_explorer import RubricExplorer

from .soap_assembler import SOAPAssembler
from .letter_generator import LetterGenerator
from .phi_scrubber import PHIScrubber
from .audit_trail import AuditTrail
from .kent_vs_boenninghausen import KentVsBoenninghausen
from .personality_engine_bridge import PersonalityEngineBridge
from .model_router import ModelRouter
from .student_training import StudentTraining
from .clinical_vignette_quiz import ClinicalVignetteQuiz
from .grand_rounds import GrandRounds
from .rubric_gap_analyzer import RubricGapAnalyzer
from .remedy_freshness_tracker import RemedyFreshnessTracker
from .subagent_orchestrator import SubagentOrchestrator

__all__ = [
    "HomeopathicRepertory",
    "quick_search",
    "ClinicalRubricMapper",
    "RareRemedyTriangulator",
    "RemedyComparator",
    "compare_remedies_quick",
    "SRPDetector",
    "PhantomRubricAnalyzer",
    "RubricCooccurrenceEngine",
    "top_remedy_pairs",
    "PrivateRubricManager",
    "quick_create",
    "PatientCohortAnalytics",
    "PatientCaseManager",
    "PractitionerApprovalGate",
    "require_ack",
    "ApprovalRequired",
    "RemedyRelationships",
    "RedFlagDetector",
    "EliminationAnalyzer",
    "PotencyGuidance",
    "AcuteChronicTagger",
    "FamilyConstellation",
    "SuppressionTracker",
    "RubricExplorer",
    "SOAPAssembler",
    "LetterGenerator",
    "PHIScrubber",
    "AuditTrail",
    "KentVsBoenninghausen",
    "PersonalityEngineBridge",
    "ModelRouter",
    "StudentTraining",
    "ClinicalVignetteQuiz",
    "GrandRounds",
    "RubricGapAnalyzer",
    "RemedyFreshnessTracker",
    "SubagentOrchestrator",
]
