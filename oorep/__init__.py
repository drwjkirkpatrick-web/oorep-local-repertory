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
from .materia_medica import MateriaMedica
from .kingdom_taxonomy import KingdomTaxonomy
from .botanical_bridge import BotanicalBridge
from .genomic_hypothesis import GenomicHypothesis
from .flashcard_srs import FlashcardSRS
from .cron_tasks import CronTasks
from .cycles_and_segments import CyclesAndSegmentsEngine, RemedyCycle, CycleSegment

# New modules from overnight builds & recent sessions
from .clipboard_manager import ClipboardManager, ClipboardType, Clipboard, ClipboardRubric
from .patient_file_system import PatientFileSystem
from .analysis_manager import AnalysisManager
from .word_wrap_search import WordWrapSearch
from .master_score_engine import MasterScoreEngine, master_repertorize
from .family_grouping import FamilyGroupingEngine
from .edition_comparison import EditionComparisonEngine
from .outcome_prediction import OutcomePredictionEngine
from .multi_repertory import MultiRepertoryEngine
from .materia_medica_search import MateriaMedicaSearchEngine
from .mobile_api import OOREPApp
from .toxicology_layer import ToxicologyLayer
from .miasm_tracking import MiasmTracker
from .remedy_relationships_v2 import RemedyGraphEngine
from .keynote_autocomplete import KeynoteAutocompleteEngine
from .correlation_matrix import CorrelationMatrixEngine
from .followup_comparator import FollowupComparator
from .differential_diagnosis import DifferentialDiagnosisEngine
from .elimination_rubrics import EliminationEngine
from .graphic_analysis import GraphicAnalysisEngine
from .analysis_methods import AnalysisMethods, KentMethod, BoenninghausenMethod, BogerMethod, VithoulkasExpertSystem, MethodSwitcher
from .bibliographic_engine import BibliographicEngine

__all__ = [
    # Core
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
    "MateriaMedica",
    "KingdomTaxonomy",
    "BotanicalBridge",
    "GenomicHypothesis",
    "FlashcardSRS",
    "CronTasks",
    "CyclesAndSegmentsEngine",
    "RemedyCycle",
    "CycleSegment",
    # New
    "ClipboardManager",
    "ClipboardType",
    "Clipboard",
    "ClipboardRubric",
    "PatientFileSystem",
    "AnalysisManager",
    "WordWrapSearch",
    "MasterScoreEngine",
    "master_repertorize",
    "FamilyGroupingEngine",
    "EditionComparisonEngine",
    "OutcomePredictionEngine",
    "MultiRepertoryEngine",
    "MateriaMedicaSearchEngine",
    "OOREPApp",
    "ToxicologyLayer",
    "MiasmTracker",
    "RemedyGraphEngine",
    "KeynoteAutocompleteEngine",
    "CorrelationMatrixEngine",
    "FollowupComparator",
    "DifferentialDiagnosisEngine",
    "EliminationEngine",
    "GraphicAnalysisEngine",
    "AnalysisMethods",
    "KentMethod",
    "BoenninghausenMethod",
    "BogerMethod",
    "VithoulkasExpertSystem",
    "MethodSwitcher",
    "BibliographicEngine",
]
