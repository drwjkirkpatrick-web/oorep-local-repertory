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
from .resampling_engine import ResamplingEngine
from .survival_analysis import SurvivalAnalysis
from .power_analysis import PowerAnalysis
from .meta_analysis_engine import MetaAnalysisEngine
from .inter_rater_reliability import InterRaterReliability
from .case_complexity_scorer import CaseComplexityScorer
from .repertory_pca import RepertoryPCA
from .outcome_comparator import OutcomeComparator
from .remedy_network_analysis import RemedyNetworkAnalyzer
from .outcome_predictor_stats import OutcomePredictorStats
from .symptom_severity_scorer import SymptomSeverityScorer
from .duplicate_remedy_detector import DuplicateRemedyDetector
from .clinical_tips_engine import ClinicalTipsEngine
from .author_filter import AuthorFilter
from .quick_symptom_lookup import QuickSymptomLookup
from .batch_protocol_builder import BatchProtocolBuilder
from .prescription_pdf_generator import PrescriptionPDFGenerator
from .appointment_scheduler import AppointmentScheduler
from .followup_prompt_generator import FollowUpPromptGenerator
from .automated_index_rebuilder import AutomatedIndexRebuilder
from .voice_to_text_audio_import import VoiceToTextAudioImport
from .inventory_manager import InventoryManager
from .patient_portal import PatientPortal
from .billing_integration import BillingIntegration
from .reverse_repertorization import ReverseRepertorization
from .constitutional_remedy_tracker import ConstitutionalRemedyTracker
from .posology_scheduler import PosologyScheduler
from .case_similarity_search import CaseSimilaritySearch
from .modality_matrix import ModalityMatrix
from .miasm_timeline import MiasmTimeline
from .case_summarizer import CaseSummarizer
from .rubric_quality_scorer import RubricQualityScorer
from .symptom_narrative_extractor import SymptomNarrativeExtractor
from .cross_reference_repertory import CrossReferenceRepertory
from .multi_language_display import MultiLanguageDisplay
from .sensation_method_integration import SensationMethodIntegration
from .proving_text_search import ProvingTextSearch
from .remedy_pictures import RemedyPictures
from .repertory_synthesis import RepertorySynthesis
from .polarity_analysis import PolarityAnalysis
from .therapeutic_pocket_book import TherapeuticPocketBook
from .cloud_sync_manager import CloudSyncManager
from .gamification_engine import GamificationEngine
from .social_community import SocialCommunity
from .mobile_app_native import MobileAppNative
from .global_stats_dashboard import GlobalStatsDashboard
from .export_research_formats import ExportResearchFormats

# Statistical Search Layer Improvements (v3.8) — Modules #111-120
from .bayesian_remedy_ranking import BayesianRemedyRanking, quick_rank
from .rubric_bandit_selector import RubricBanditSelector, quick_select
from .propensity_scored_prediction import PropensityScoredPrediction, quick_ipw_predict
from .rubric_discrimination_indices import RubricDiscriminationIndices, quick_indices
from .hierarchical_bayesian_similarity import HierarchicalBayesianSimilarity, quick_similar
from .cv_symptom_weights import CVSymptomWeightLearner, quick_learn_weights
from .sequential_remedy_testing import SequentialRemedyTesting, quick_sprt_test
from .gaussian_process_surrogate import GaussianProcessSurrogate, quick_gp_predict
from .causal_remedy_effects import CausalRemedyEffects, quick_ate
from .ensemble_retrieval_stacking import EnsembleRetrievalStacking, quick_ensemble

# v3.9 — Differential question engine & case-taking analytics
from .discriminant_rubric_selector import DiscriminantRubricSelector, quick_differential
from .information_theoretic_case_workup import CaseWorkupAnalyzer, quick_workup
from .adaptive_symptom_sequencer import AdaptiveSymptomSequencer, quick_sequence
from .latent_symptom_embedding import LatentSymptomEmbedder, quick_embed
from .confusion_matrix_differential import ConfusionMatrixDifferential, quick_confusion
from .k_nearest_proven_cases import KNearestProvenCases, HistoricalCase, quick_knn
from .bayesian_rubric_network import BayesianRubricNetwork, quick_network
from .symptom_cooccurrence_lift import SymptomCooccurrenceLift, quick_lift
from .active_learning_intake_tracker import ActiveLearningIntakeTracker, quick_intake_suggestion
from .remedy_confidence_calibration import RemedyConfidenceCalibrator, quick_calibrate

# v4.0 — Patient Intake System (10 modules for homeopathic case-taking)
from .patient_intake_engine import (
    PatientIntakeEngine, IntakeStatus, IntakeSession, CapturedSymptom, Modality, quick_intake
)
from .interview_question_bank import (
    InterviewQuestionBank, InterviewQuestion, QuestionPhase, QuestionDepth, QuestionType, quick_bank
)
from .chief_complaint_triager import (
    ChiefComplaintTriager, Urgency, ComplaintCategory, TriageResult, quick_triage
)
from .concomitant_detector import (
    ConcomitantDetector, ConcomitantAnalysis, ConcomitantSymptom, quick_concomitants
)
from .modality_extractor import (
    ModalityExtractor, ModalityAxis, ModalityDirection, ModalityGrid, CapturedModality, quick_modalities
)
from .causation_timeline_module import (
    CausationTimelineAnalyzer, Miasm, CausationReport, TimelineEvent, quick_causation
)
from .mental_emotional_prober import (
    MentalEmotionalProber, MentalEmotionalProfile, MentalSymptom, quick_mental_profile
)
from .generals_survey import (
    GeneralsSurvey, GeneralsProfile, GeneralSymptom, quick_generals
)
from .constitutional_snapshot import (
    ConstitutionalSnapshot, ConstitutionalProfile, ConstitutionalArchetypeMatch, quick_constitutional
)
from .intake_analyzer import (
    IntakeAnalyzer, CaseReport, CaseQuality, HeringDirection, quick_analyze
)

from .case_analysis_bridge import (
    CaseAnalysisBridge,
    CaseAnalysisReport,
    ConfusedPairAnalysis,
    DifferentiatingSyndrome,
    quick_analysis,
)

# v4.3 — Security Manager (comprehensive security layer)
from .security_manager import (
    SecurityManager,
    SecurityViolation,
    InputValidationError,
    SecurityFinding,
    RateLimitDecision,
    SessionInfo,
    IntegrityReport,
    sanitize,
    secure_token,
    get_security_manager,
)

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
    # Statistical Modules (v3.6)
    "OutcomePredictorStats",
    "RemedyNetworkAnalyzer",
    "OutcomeComparator",
    "RepertoryPCA",
    "CaseComplexityScorer",
    "InterRaterReliability",
    "MetaAnalysisEngine",
    "PowerAnalysis",
    "SurvivalAnalysis",
    "ResamplingEngine",
    # Feature Expansion Modules (v3.7) — 45 new features
    "SymptomSeverityScorer",
    "DuplicateRemedyDetector",
    "ClinicalTipsEngine",
    "AuthorFilter",
    "QuickSymptomLookup",
    "BatchProtocolBuilder",
    "PrescriptionPDFGenerator",
    "AppointmentScheduler",
    "FollowUpPromptGenerator",
    "AutomatedIndexRebuilder",
    "VoiceToTextAudioImport",
    "InventoryManager",
    "PatientPortal",
    "BillingIntegration",
    "ReverseRepertorization",
    "ConstitutionalRemedyTracker",
    "PosologyScheduler",
    "CaseSimilaritySearch",
    "ModalityMatrix",
    "MiasmTimeline",
    "CaseSummarizer",
    "RubricQualityScorer",
    "SymptomNarrativeExtractor",
    "CrossReferenceRepertory",
    "MultiLanguageDisplay",
    "SensationMethodIntegration",
    "ProvingTextSearch",
    "RemedyPictures",
    "RepertorySynthesis",
    "PolarityAnalysis",
    "TherapeuticPocketBook",
    "CloudSyncManager",
    "GamificationEngine",
    "SocialCommunity",
    "MobileAppNative",
    "GlobalStatsDashboard",
    "ExportResearchFormats",
    # Statistical Search Layer Improvements (v3.8) — 10 new modules
    "BayesianRemedyRanking",
    "quick_rank",
    "RubricBanditSelector",
    "quick_select",
    "PropensityScoredPrediction",
    "quick_ipw_predict",
    "RubricDiscriminationIndices",
    "quick_indices",
    "HierarchicalBayesianSimilarity",
    "quick_similar",
    "CVSymptomWeightLearner",
    "quick_learn_weights",
    "SequentialRemedyTesting",
    "quick_sprt_test",
    "GaussianProcessSurrogate",
    "quick_gp_predict",
    "CausalRemedyEffects",
    "quick_ate",
    "EnsembleRetrievalStacking",
    "quick_ensemble",
    # v3.9 — Differential question engine & case-taking analytics
    "DiscriminantRubricSelector",
    "quick_differential",
    "CaseWorkupAnalyzer",
    "quick_workup",
    "AdaptiveSymptomSequencer",
    "quick_sequence",
    "LatentSymptomEmbedder",
    "quick_embed",
    "ConfusionMatrixDifferential",
    "quick_confusion",
    "KNearestProvenCases",
    "HistoricalCase",
    "quick_knn",
    "BayesianRubricNetwork",
    "quick_network",
    "SymptomCooccurrenceLift",
    "quick_lift",
    "ActiveLearningIntakeTracker",
    "quick_intake_suggestion",
    "RemedyConfidenceCalibrator",
    "quick_calibrate",
    # v4.0 — Patient Intake System (10 modules for homeopathic case-taking)
    "PatientIntakeEngine",
    "IntakeStatus",
    "IntakeSession",
    "CapturedSymptom",
    "Modality",
    "quick_intake",
    "InterviewQuestionBank",
    "InterviewQuestion",
    "QuestionPhase",
    "QuestionDepth",
    "QuestionType",
    "quick_bank",
    "ChiefComplaintTriager",
    "Urgency",
    "ComplaintCategory",
    "TriageResult",
    "quick_triage",
    "ConcomitantDetector",
    "ConcomitantAnalysis",
    "ConcomitantSymptom",
    "quick_concomitants",
    "ModalityExtractor",
    "ModalityAxis",
    "ModalityDirection",
    "ModalityGrid",
    "CapturedModality",
    "quick_modalities",
    "CausationTimelineAnalyzer",
    "Miasm",
    "CausationReport",
    "TimelineEvent",
    "quick_causation",
    "MentalEmotionalProber",
    "MentalEmotionalProfile",
    "MentalSymptom",
    "quick_mental_profile",
    "GeneralsSurvey",
    "GeneralsProfile",
    "GeneralSymptom",
    "quick_generals",
    "ConstitutionalSnapshot",
    "ConstitutionalProfile",
    "ConstitutionalArchetypeMatch",
    "quick_constitutional",
    "IntakeAnalyzer",
    "CaseReport",
    "CaseQuality",
    "HeringDirection",
    "quick_analyze",
    "CaseAnalysisBridge",
    "CaseAnalysisReport",
    "ConfusedPairAnalysis",
    "DifferentiatingSyndrome",
    "quick_analysis",
    # v4.3 — Security Manager
    "SecurityManager",
    "SecurityViolation",
    "InputValidationError",
    "SecurityFinding",
    "RateLimitDecision",
    "SessionInfo",
    "IntegrityReport",
    "sanitize",
    "secure_token",
    "get_security_manager",
]
