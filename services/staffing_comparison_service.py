"""
Staffing Comparison Service

Compares actual staffing against benchmarks and generates comprehensive analysis.
Ties together census data, MSP data, shared services, and benchmarks.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from models.organization_models import (
    StaffMember,
    CompanyInfo,
    BenchmarkProfile,
    RoleCategory
)
from models.organization_stores import (
    OrganizationDataStore,
    StaffingComparisonResult,
    CategoryComparison,
    MissingRole,
    RatioComparison,
    TotalITCostSummary
)
from services.benchmark_service import BenchmarkService

logger = logging.getLogger(__name__)


class StaffingComparisonService:
    """
    Compares actual staffing to benchmarks and provides comprehensive analysis.
    """

    def __init__(self, benchmark_service: Optional[BenchmarkService] = None):
        self.benchmark_service = benchmark_service or BenchmarkService()
        if not self.benchmark_service._loaded:
            self.benchmark_service.load_benchmarks()

    def run_full_comparison(
        self,
        org_store: OrganizationDataStore,
        company_info: CompanyInfo
    ) -> StaffingComparisonResult:
        """
        Run a full staffing comparison against benchmarks.

        Args:
            org_store: Organization data store with staff, MSP, shared services
            company_info: Company information for benchmark matching

        Returns:
            Complete StaffingComparisonResult
        """
        # Match benchmark profile
        benchmark = self.benchmark_service.match_profile(
            company_info.revenue,
            company_info.employee_count,
            company_info.industry
        )

        if not benchmark:
            logger.warning("No benchmark profile matched, using defaults")
            profiles = self.benchmark_service.get_profiles()
            benchmark = profiles[0] if profiles else None

        if not benchmark:
            raise ValueError("No benchmark profiles available")

        # Get staff counts by category
        staff_by_category = self._count_staff_by_category(org_store.staff_members)

        # Run comparison
        result = self.benchmark_service.compare_staffing(
            staff_by_category,
            benchmark,
            company_info
        )

        # Add missing roles analysis
        result.missing_roles = self.benchmark_service.identify_missing_roles(
            org_store.staff_members,
            benchmark
        )

        # Enhance with MSP and shared services context
        result = self._enhance_with_outsourcing_context(result, org_store, benchmark)

        # Add key findings
        result.key_findings.extend(self._generate_key_findings(result, org_store))

        # Add recommendations
        result.recommendations.extend(self._generate_recommendations(result, org_store))

        return result

    def _count_staff_by_category(
        self,
        staff: List[StaffMember],
        entity: str = "target"
    ) -> Dict[str, int]:
        """Count staff by category for target entity."""
        counts = {}
        for s in staff:
            if s.entity != entity:
                continue
            cat = s.role_category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _enhance_with_outsourcing_context(
        self,
        result: StaffingComparisonResult,
        org_store: OrganizationDataStore,
        benchmark: BenchmarkProfile
    ) -> StaffingComparisonResult:
        """Enhance comparison results with MSP and shared services context."""

        # For understaffed categories, check if MSP or shared services covers the gap
        for comp in result.category_comparisons:
            if comp.status != "understaffed":
                continue

            # Check MSP coverage
            msp_fte = self._get_msp_fte_for_category(org_store, comp.category)
            ss_fte = self._get_shared_services_fte_for_category(org_store, comp.category)

            total_coverage = comp.actual_count + msp_fte + ss_fte

            if total_coverage >= comp.benchmark_min:
                comp.analysis = (
                    f"{comp.category_display}: Internal staff ({comp.actual_count}) appears low, "
                    f"but MSP provides ~{msp_fte:.1f} FTE and shared services ~{ss_fte:.1f} FTE. "
                    f"Total effective coverage: {total_coverage:.1f} FTE. "
                    f"Post-close risk if MSP/shared services not continuing."
                )
            else:
                comp.analysis = (
                    f"{comp.category_display}: Understaffed even including MSP ({msp_fte:.1f} FTE) "
                    f"and shared services ({ss_fte:.1f} FTE). Gap exists."
                )

        # Update missing roles with MSP context
        for missing in result.missing_roles:
            if self._role_covered_by_msp(org_store, missing.role_title):
                missing.current_coverage = "Covered by MSP (verify contract continuation)"
            elif self._role_covered_by_shared_services(org_store, missing.role_title):
                missing.current_coverage = "Covered by Parent/Shared Services (verify TSA)"

        return result

    def _get_msp_fte_for_category(
        self,
        org_store: OrganizationDataStore,
        category: str
    ) -> float:
        """Estimate MSP FTE coverage for a category."""
        category_keywords = {
            "infrastructure": ["infrastructure", "network", "server", "monitoring", "cloud"],
            "security": ["security", "soc", "siem", "edr", "vulnerability"],
            "service_desk": ["help desk", "service desk", "support", "desktop"],
            "applications": ["application", "erp", "development"],
            "data": ["database", "dba", "data"]
        }

        keywords = category_keywords.get(category, [])
        if not keywords:
            return 0.0

        total_fte = 0.0
        for msp in org_store.msp_relationships:
            if msp.entity != "target":
                continue
            for service in msp.services:
                svc_lower = service.service_name.lower()
                if any(kw in svc_lower for kw in keywords):
                    total_fte += service.fte_equivalent

        return total_fte

    def _get_shared_services_fte_for_category(
        self,
        org_store: OrganizationDataStore,
        category: str
    ) -> float:
        """Estimate shared services FTE for a category."""
        category_keywords = {
            "infrastructure": ["infrastructure", "network", "server", "cloud"],
            "security": ["security", "compliance", "identity"],
            "service_desk": ["help desk", "support"],
            "applications": ["application", "erp", "development"],
            "data": ["database", "dba", "data"]
        }

        keywords = category_keywords.get(category, [])
        if not keywords:
            return 0.0

        total_fte = 0.0
        for dep in org_store.shared_service_dependencies:
            svc_lower = dep.service_name.lower()
            if any(kw in svc_lower for kw in keywords):
                total_fte += dep.fte_equivalent

        return total_fte

    def _role_covered_by_msp(
        self,
        org_store: OrganizationDataStore,
        role_title: str
    ) -> bool:
        """Check if a role appears to be covered by MSP."""
        role_lower = role_title.lower()

        role_service_map = {
            "security": ["security", "soc", "siem"],
            "network": ["network", "monitoring"],
            "help desk": ["help desk", "service desk"],
            "dba": ["database"],
        }

        for role_kw, svc_keywords in role_service_map.items():
            if role_kw in role_lower:
                for msp in org_store.msp_relationships:
                    for svc in msp.services:
                        if any(kw in svc.service_name.lower() for kw in svc_keywords):
                            return True
        return False

    def _role_covered_by_shared_services(
        self,
        org_store: OrganizationDataStore,
        role_title: str
    ) -> bool:
        """Check if a role appears to be covered by shared services."""
        role_lower = role_title.lower()

        for dep in org_store.shared_service_dependencies:
            svc_lower = dep.service_name.lower()
            # Simple keyword overlap check
            if any(word in svc_lower for word in role_lower.split()):
                return True
        return False

    def _generate_key_findings(
        self,
        result: StaffingComparisonResult,
        org_store: OrganizationDataStore
    ) -> List[str]:
        """Generate key findings from the comparison."""
        findings = []

        # Critical missing roles
        critical_missing = result.get_critical_missing_roles()
        if critical_missing:
            roles = [r.role_title for r in critical_missing]
            findings.append(f"Critical roles missing: {', '.join(roles)}")

        # High MSP dependency
        if org_store.msp_summary and org_store.msp_summary.total_fte_equivalent > 5:
            findings.append(
                f"High MSP dependency: {org_store.msp_summary.total_fte_equivalent:.1f} FTE equivalent "
                f"(${org_store.msp_summary.total_annual_cost:,.0f}/yr)"
            )

        # Hidden headcount
        if org_store.hidden_headcount_need > 0:
            findings.append(
                f"Hidden headcount need: {org_store.hidden_headcount_need:.1f} FTE from shared services "
                f"that won't transfer"
            )

        # Key person concentration
        key_persons = org_store.get_key_persons()
        if len(key_persons) > 0:
            leadership_kp = [kp for kp in key_persons if kp.role_category == RoleCategory.LEADERSHIP]
            if leadership_kp:
                findings.append(f"{len(leadership_kp)} leadership position(s) flagged as key person risk")

        return findings

    def _generate_recommendations(
        self,
        result: StaffingComparisonResult,
        org_store: OrganizationDataStore
    ) -> List[str]:
        """Generate recommendations from the comparison."""
        recommendations = []

        # MSP contract review
        if org_store.msp_relationships:
            recommendations.append(
                "Review MSP contracts for termination clauses and expiration dates"
            )

        # TSA for shared services
        if org_store.shared_service_dependencies:
            non_transfer = [d for d in org_store.shared_service_dependencies if not d.will_transfer]
            if non_transfer:
                recommendations.append(
                    f"Negotiate TSA coverage for {len(non_transfer)} shared services "
                    "that won't transfer"
                )

        # Staffing for critical gaps
        critical_missing = result.get_critical_missing_roles()
        if critical_missing:
            recommendations.append(
                "Develop Day 1 staffing plan for critical role gaps"
            )

        # Key person retention
        key_persons = org_store.get_key_persons()
        if key_persons:
            recommendations.append(
                f"Develop retention plan for {len(key_persons)} key persons"
            )

        return recommendations

    def calculate_total_it_cost(
        self,
        org_store: OrganizationDataStore
    ) -> TotalITCostSummary:
        """Calculate complete IT cost summary."""
        return org_store.calculate_cost_summary()
