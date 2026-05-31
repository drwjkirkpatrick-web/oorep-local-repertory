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
]
