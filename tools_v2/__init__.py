"""
V2 Tools Module

Discovery-Reasoning split architecture tools:
- FactStore: Central fact storage with unique IDs
- ReasoningStore: Findings storage with fact citations
- Discovery Tools: Fact extraction (create_inventory_entry, flag_gap)
- Reasoning Tools: Analysis with fact citations
- Coverage: Coverage checklists and quality scoring

Three-Stage Reasoning Architecture:
- Stage 1: LLM interprets facts and identifies considerations
- Stage 2: Rule-base matches activities and calculates costs
- Stage 3: LLM validates the analysis

Main Entry Points:
- analyze_deal(): Run analysis on a deal
- create_analysis_session(): Create refinement session for iterative analysis
"""

from stores.fact_store import FactStore, Fact, Gap
from tools_v2.discovery_tools import DISCOVERY_TOOLS, execute_discovery_tool
from tools_v2.reasoning_tools import (
    REASONING_TOOLS,
    execute_reasoning_tool,
    ReasoningStore,
    Risk,
    StrategicConsideration,
    WorkItem,
    Recommendation,
    COST_RANGES,
    COST_RANGE_VALUES
)
from tools_v2.coverage import (
    COVERAGE_CHECKLISTS,
    CoverageAnalyzer,
    DomainCoverage,
    CategoryCoverage,
    ChecklistItem
)
from tools_v2.vdr_generator import (
    VDRGenerator,
    VDRRequest,
    VDRRequestPack,
    SUGGESTED_DOCUMENTS
)
from tools_v2.synthesis import (
    SynthesisAnalyzer,
    ConsistencyIssue,
    RelatedFinding
)
from tools_v2.evidence_query import (
    EvidenceType,
    Evidence,
    EvidenceStore,
    EvidenceIndex,
    QueryBuilder,
    import_from_fact_store
)
from tools_v2.table_generators import (
    RiskRow,
    SynergyRow,
    RiskSeverity,
    generate_risk_table,
    generate_synergy_table
)

# Three-Stage Reasoning Architecture
from tools_v2.analysis_pipeline import (
    analyze_deal,
    create_analysis_session,
    AnalysisMode,
    AnalysisResult,
)
from tools_v2.three_stage_reasoning import (
    run_three_stage_analysis,
    ThreeStageOutput,
    IdentifiedConsideration,
    MatchedActivity,
    ValidationResult,
    stage1_identify_considerations,
    stage2_match_activities,
    stage3_validate,
)
from tools_v2.three_stage_refinement import (
    ThreeStageRefinementSession,
    create_refinement_session,
)
from tools_v2.reasoning_orchestrator import (
    ReasoningOrchestrator,
    OrchestratorConfig,
    quick_analyze,
)

# Validation components
from tools_v2.evidence_verifier import (
    EvidenceVerifier,
    VerificationResult,
    verify_quote_exists,
)
from tools_v2.category_validator import (
    CategoryValidator,
    CategoryValidationResult,
)
from tools_v2.domain_validator import (
    DomainValidator,
    DomainValidationResult,
)
from tools_v2.cross_domain_validator import (
    CrossDomainValidator,
    CrossDomainValidationResult,
    ConsistencyCheck,
)
from tools_v2.adversarial_reviewer import (
    AdversarialReviewer,
    AdversarialReviewResult,
    AdversarialFinding,
    FindingType,
)

# Phase 5: Document Parsing & Preprocessing
from tools_v2.document_preprocessor import (
    DocumentPreprocessor,
    preprocess_document,
)
from tools_v2.numeric_normalizer import (
    normalize_numeric,
    normalize_cost,
    normalize_count,
    normalize_percentage,
    is_null_value,
)
from tools_v2.table_chunker import (
    TableAwareChunker,
    Chunk,
    chunk_document,
    chunk_with_context,
)
from tools_v2.table_parser import (
    DeterministicTableParser,
    ParsedTable,
    TableCell,
    parse_table,
    parse_tables,
    extract_table_data,
)

__all__ = [
    # Fact Store
    'FactStore',
    'Fact',
    'Gap',
    # Reasoning Store
    'ReasoningStore',
    'Risk',
    'StrategicConsideration',
    'WorkItem',
    'Recommendation',
    # Cost estimation
    'COST_RANGES',
    'COST_RANGE_VALUES',
    # Coverage
    'COVERAGE_CHECKLISTS',
    'CoverageAnalyzer',
    'DomainCoverage',
    'CategoryCoverage',
    'ChecklistItem',
    # VDR Generator
    'VDRGenerator',
    'VDRRequest',
    'VDRRequestPack',
    'SUGGESTED_DOCUMENTS',
    # Synthesis
    'SynthesisAnalyzer',
    'ConsistencyIssue',
    'RelatedFinding',
    # Tools
    'DISCOVERY_TOOLS',
    'REASONING_TOOLS',
    'execute_discovery_tool',
    'execute_reasoning_tool',
    # Evidence Query
    'EvidenceType',
    'Evidence',
    'EvidenceStore',
    'EvidenceIndex',
    'QueryBuilder',
    'import_from_fact_store',
    # Table Generators
    'RiskRow',
    'SynergyRow',
    'RiskSeverity',
    'generate_risk_table',
    'generate_synergy_table',
    # Analysis Pipeline (Three-Stage Reasoning)
    'analyze_deal',
    'create_analysis_session',
    'AnalysisMode',
    'AnalysisResult',
    # Three-Stage Reasoning
    'run_three_stage_analysis',
    'ThreeStageOutput',
    'IdentifiedConsideration',
    'MatchedActivity',
    'ValidationResult',
    'stage1_identify_considerations',
    'stage2_match_activities',
    'stage3_validate',
    # Refinement Session
    'ThreeStageRefinementSession',
    'create_refinement_session',
    # Orchestrator
    'ReasoningOrchestrator',
    'OrchestratorConfig',
    'quick_analyze',
    # Validation - Evidence Verifier
    'EvidenceVerifier',
    'VerificationResult',
    'verify_quote_exists',
    # Validation - Category Validator
    'CategoryValidator',
    'CategoryValidationResult',
    # Validation - Domain Validator
    'DomainValidator',
    'DomainValidationResult',
    # Validation - Cross-Domain Validator
    'CrossDomainValidator',
    'CrossDomainValidationResult',
    'ConsistencyCheck',
    # Validation - Adversarial Reviewer
    'AdversarialReviewer',
    'AdversarialReviewResult',
    'AdversarialFinding',
    'FindingType',
    # Phase 5: Document Parsing & Preprocessing
    'DocumentPreprocessor',
    'preprocess_document',
    'normalize_numeric',
    'normalize_cost',
    'normalize_count',
    'normalize_percentage',
    'is_null_value',
    'TableAwareChunker',
    'Chunk',
    'chunk_document',
    'chunk_with_context',
    'DeterministicTableParser',
    'ParsedTable',
    'TableCell',
    'parse_table',
    'parse_tables',
    'extract_table_data',
]
