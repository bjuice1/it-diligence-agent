"""
Services package for IT Due Diligence Agent.

Contains business logic services for:
- Benchmark comparison and matching
- Shared services analysis
- Staffing comparison
- Organization analysis pipeline
- Validation pipeline (coordinates validation layers)
- Extraction orchestrator (manages extract-validate-retry loop)
"""

from services.benchmark_service import BenchmarkService
from services.shared_services_analyzer import SharedServicesAnalyzer
from services.staffing_comparison_service import StaffingComparisonService
from services.organization_pipeline import OrganizationAnalysisPipeline
from services.validation_pipeline import (
    ValidationPipeline,
    ValidationPipelineResult,
    validate_domain,
    create_pipeline
)
from services.extraction_orchestrator import (
    ExtractionOrchestrator,
    ExtractionResult,
    ExtractionStatus,
    EscalationRecord,
    create_orchestrator,
    extract_with_validation
)

__all__ = [
    # Existing services
    'BenchmarkService',
    'SharedServicesAnalyzer',
    'StaffingComparisonService',
    'OrganizationAnalysisPipeline',

    # Validation Pipeline
    'ValidationPipeline',
    'ValidationPipelineResult',
    'validate_domain',
    'create_pipeline',

    # Extraction Orchestrator
    'ExtractionOrchestrator',
    'ExtractionResult',
    'ExtractionStatus',
    'EscalationRecord',
    'create_orchestrator',
    'extract_with_validation',
]
