"""
Services package for IT Due Diligence Agent.

Contains business logic services for:
- Benchmark comparison and matching
- Shared services analysis
- Staffing comparison
- Organization analysis pipeline
"""

from services.benchmark_service import BenchmarkService
from services.shared_services_analyzer import SharedServicesAnalyzer
from services.staffing_comparison_service import StaffingComparisonService
from services.organization_pipeline import OrganizationAnalysisPipeline

__all__ = [
    'BenchmarkService',
    'SharedServicesAnalyzer',
    'StaffingComparisonService',
    'OrganizationAnalysisPipeline'
]
