"""
Models package for IT Due Diligence Agent.

Contains data models for:
- Organization analysis (staffing, MSP, shared services, benchmarks)
- Future: Other domain models
"""

from models.organization_models import (
    EmploymentType,
    RoleCategory,
    DependencyLevel,
    StaffMember,
    RoleSummary,
    CategorySummary,
    MSPService,
    MSPRelationship,
    SharedServiceDependency,
    BenchmarkRange,
    ExpectedRole,
    BenchmarkProfile,
    TSAItem,
    StaffingNeed,
    CompanyInfo
)

from models.organization_stores import (
    OrganizationDataStore,
    CategoryComparison,
    MissingRole,
    OverstaffedArea,
    RatioComparison,
    StaffingComparisonResult,
    MSPSummary,
    SharedServicesSummary,
    TotalITCostSummary,
    OrganizationAnalysisResult
)

__all__ = [
    # Enums
    'EmploymentType',
    'RoleCategory',
    'DependencyLevel',
    # Core models
    'StaffMember',
    'RoleSummary',
    'CategorySummary',
    'MSPService',
    'MSPRelationship',
    'SharedServiceDependency',
    'BenchmarkRange',
    'ExpectedRole',
    'BenchmarkProfile',
    'TSAItem',
    'StaffingNeed',
    'CompanyInfo',
    # Stores and results
    'OrganizationDataStore',
    'CategoryComparison',
    'MissingRole',
    'OverstaffedArea',
    'RatioComparison',
    'StaffingComparisonResult',
    'MSPSummary',
    'SharedServicesSummary',
    'TotalITCostSummary',
    'OrganizationAnalysisResult'
]
