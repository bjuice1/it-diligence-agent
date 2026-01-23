"""
Organization Analysis Pipeline

Orchestrates the complete organization analysis flow:
1. Parse census data
2. Extract MSP information
3. Identify shared service dependencies
4. Match benchmark profile
5. Run comparisons
6. Generate findings and recommendations
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from models.organization_models import (
    StaffMember,
    CompanyInfo,
    BenchmarkProfile,
    RoleCategory
)
from models.organization_stores import (
    OrganizationDataStore,
    OrganizationAnalysisResult,
    StaffingComparisonResult
)
from parsers.census_parser import CensusParser
from parsers.msp_parser import MSPParser
from services.benchmark_service import BenchmarkService
from services.shared_services_analyzer import SharedServicesAnalyzer
from services.staffing_comparison_service import StaffingComparisonService

logger = logging.getLogger(__name__)


class OrganizationAnalysisPipeline:
    """
    Orchestrates complete organization analysis.

    Usage:
        pipeline = OrganizationAnalysisPipeline()
        result = pipeline.run_full_analysis(
            census_file="census.xlsx",
            facts=fact_list,
            company_info=company
        )
    """

    def __init__(self):
        self.census_parser = CensusParser()
        self.msp_parser = MSPParser()
        self.benchmark_service = BenchmarkService()
        self.shared_services_analyzer = SharedServicesAnalyzer()
        self.comparison_service = None  # Initialized after benchmark service loads

    def run_full_analysis(
        self,
        company_info: CompanyInfo,
        census_file: Optional[str] = None,
        staff_members: Optional[List[StaffMember]] = None,
        facts: Optional[List[Dict[str, Any]]] = None,
        msp_data: Optional[List[Dict]] = None,
        shared_services_data: Optional[List[Dict]] = None
    ) -> OrganizationAnalysisResult:
        """
        Run complete organization analysis.

        Args:
            company_info: Company information for benchmark matching
            census_file: Path to census Excel/CSV file (optional if staff_members provided)
            staff_members: Pre-parsed staff members (optional if census_file provided)
            facts: Fact store entries for MSP/shared services extraction
            msp_data: Manual MSP data (optional)
            shared_services_data: Manual shared services data (optional)

        Returns:
            OrganizationAnalysisResult with complete analysis
        """
        logger.info(f"Starting organization analysis for {company_info.name}")

        # Initialize store
        org_store = OrganizationDataStore()
        org_store.data_sources = []
        org_store.last_updated = datetime.now().isoformat()

        # Step 1: Load staff data
        if census_file:
            logger.info(f"Parsing census file: {census_file}")
            staff = self.census_parser.parse_file(census_file, entity=company_info.entity)
            for s in staff:
                org_store.add_staff_member(s)
            org_store.data_sources.append(f"Census: {Path(census_file).name}")
        elif staff_members:
            for s in staff_members:
                org_store.add_staff_member(s)
            org_store.data_sources.append("Staff data (provided)")

        # Step 2: Aggregate staffing data
        org_store.category_summaries = self.census_parser.aggregate_by_category(
            org_store.staff_members, entity=company_info.entity
        )

        # Step 3: Extract MSP relationships
        if facts:
            msps = self.msp_parser.parse_from_facts(facts, entity=company_info.entity)
            for msp in msps:
                org_store.add_msp_relationship(msp)
            if msps:
                org_store.data_sources.append(f"MSP data from facts ({len(msps)} vendors)")

        if msp_data:
            for msp_dict in msp_data:
                msp = self.msp_parser.create_relationship(**msp_dict)
                org_store.add_msp_relationship(msp)
            org_store.data_sources.append(f"MSP data (manual, {len(msp_data)} vendors)")

        # Step 4: Identify shared service dependencies
        if facts:
            deps = self.shared_services_analyzer.identify_dependencies(facts)
            for dep in deps:
                org_store.add_shared_service(dep)
            if deps:
                org_store.data_sources.append(f"Shared services from facts ({len(deps)} dependencies)")

        if shared_services_data:
            for ss_dict in shared_services_data:
                dep = self.shared_services_analyzer.create_dependency(**ss_dict)
                org_store.add_shared_service(dep)
            org_store.data_sources.append(f"Shared services (manual, {len(shared_services_data)} dependencies)")

        # Step 5: Load benchmarks and match profile
        self.benchmark_service.load_benchmarks()
        benchmark = self.benchmark_service.match_profile(
            company_info.revenue,
            company_info.employee_count,
            company_info.industry
        )
        org_store.active_benchmark = benchmark

        # Step 6: Run staffing comparison
        self.comparison_service = StaffingComparisonService(self.benchmark_service)
        comparison_result = self.comparison_service.run_full_comparison(org_store, company_info)
        org_store.benchmark_comparison = comparison_result

        # Step 7: Calculate cost summary
        org_store.calculate_cost_summary()

        # Step 8: Generate final result
        result = self._build_analysis_result(org_store, company_info, comparison_result)

        logger.info(f"Organization analysis complete: {len(result.risks)} risks, {len(result.hiring_recommendations)} hiring needs")

        return result

    def _build_analysis_result(
        self,
        org_store: OrganizationDataStore,
        company_info: CompanyInfo,
        comparison: StaffingComparisonResult
    ) -> OrganizationAnalysisResult:
        """Build the final analysis result."""

        result = OrganizationAnalysisResult(
            staffing_summary=self._build_staffing_summary(org_store),
            benchmark_comparison=comparison,
            msp_summary=org_store.msp_summary,
            shared_services_summary=org_store.shared_services_summary,
            cost_summary=org_store.cost_summary,
            total_it_headcount=org_store.get_target_headcount(),
            total_it_cost=org_store.cost_summary.total_true_cost if org_store.cost_summary else 0,
            hidden_headcount_need=org_store.hidden_headcount_need,
            data_sources=org_store.data_sources
        )

        # Generate risks
        result.risks = self._generate_risks(org_store, comparison)

        # Generate gaps
        result.gaps = self._generate_gaps(comparison)

        # Generate work items
        result.work_items = self._generate_work_items(org_store, comparison)

        # Generate TSA recommendations
        result.tsa_recommendations = self.shared_services_analyzer.generate_tsa_recommendations(
            org_store.shared_service_dependencies
        )

        # Generate hiring recommendations
        result.hiring_recommendations = self._generate_hiring_recommendations(org_store, comparison)

        # Calculate post-close staffing cost
        result.post_close_staffing_cost = sum(
            h.estimated_total_cost for h in result.hiring_recommendations
        )

        return result

    def _build_staffing_summary(self, org_store: OrganizationDataStore) -> Dict[str, Any]:
        """Build staffing summary dict."""
        return {
            'total_headcount': org_store.get_target_headcount(),
            'total_fte': org_store.total_internal_fte,
            'total_contractor': org_store.total_contractor,
            'total_compensation': org_store.total_compensation,
            'msp_fte_equivalent': org_store.total_msp_fte_equivalent,
            'shared_services_fte': org_store.total_shared_services_fte,
            'key_person_count': len(org_store.get_key_persons()),
            'by_category': {
                cat: {
                    'headcount': summary.total_headcount,
                    'compensation': summary.total_compensation
                }
                for cat, summary in org_store.category_summaries.items()
            }
        }

    def _generate_risks(
        self,
        org_store: OrganizationDataStore,
        comparison: StaffingComparisonResult
    ) -> List[Dict[str, Any]]:
        """Generate risk findings."""
        risks = []

        # Key person risks
        for kp in org_store.get_key_persons():
            if kp.role_category == RoleCategory.LEADERSHIP:
                severity = "high"
            elif kp.tenure_years and kp.tenure_years > 10:
                severity = "high"
            else:
                severity = "medium"

            risks.append({
                'id': f"RISK-KP-{kp.id}",
                'domain': 'organization',
                'title': f"Key Person Risk: {kp.name}",
                'description': f"{kp.name} ({kp.role_title}) flagged as key person. {kp.key_person_reason}",
                'severity': severity,
                'category': 'key_person_dependency'
            })

        # MSP dependency risks
        for msp in org_store.msp_relationships:
            if msp.risk_level in ['critical', 'high']:
                risks.append({
                    'id': f"RISK-MSP-{msp.id}",
                    'domain': 'organization',
                    'title': f"MSP Dependency Risk: {msp.vendor_name}",
                    'description': (
                        f"{msp.vendor_name} provides {msp.total_fte_equivalent:.1f} FTE equivalent of services. "
                        f"Risk level: {msp.risk_level}. Contract expires: {msp.contract_expiry or 'Unknown'}"
                    ),
                    'severity': msp.risk_level,
                    'category': 'vendor_dependency'
                })

        # Shared services risks
        for dep in org_store.shared_service_dependencies:
            if dep.criticality in ['critical', 'high'] and not dep.will_transfer:
                risks.append({
                    'id': f"RISK-SS-{dep.id}",
                    'domain': 'organization',
                    'title': f"Shared Service Gap: {dep.service_name}",
                    'description': (
                        f"{dep.service_name} from {dep.provider} will not transfer. "
                        f"Represents {dep.fte_equivalent} FTE. Urgency: {dep.urgency}"
                    ),
                    'severity': dep.criticality,
                    'category': 'shared_services_gap'
                })

        # Missing critical roles
        for missing in comparison.get_critical_missing_roles():
            risks.append({
                'id': f"RISK-ROLE-{missing.role_title.replace(' ', '_')}",
                'domain': 'organization',
                'title': f"Missing Critical Role: {missing.role_title}",
                'description': f"{missing.impact}. {missing.recommendation}",
                'severity': 'high',
                'category': 'capability_gap'
            })

        return risks

    def _generate_gaps(self, comparison: StaffingComparisonResult) -> List[Dict[str, Any]]:
        """Generate gap findings."""
        gaps = []

        for missing in comparison.missing_roles:
            gaps.append({
                'id': f"GAP-{missing.role_title.replace(' ', '_')}",
                'domain': 'organization',
                'category': 'missing_role',
                'description': f"Missing {missing.role_title} ({missing.importance} importance)",
                'importance': missing.importance,
                'current_coverage': missing.current_coverage
            })

        return gaps

    def _generate_work_items(
        self,
        org_store: OrganizationDataStore,
        comparison: StaffingComparisonResult
    ) -> List[Dict[str, Any]]:
        """Generate work items."""
        work_items = []

        # TSA negotiation
        if org_store.shared_service_dependencies:
            non_transfer = [d for d in org_store.shared_service_dependencies if not d.will_transfer]
            if non_transfer:
                work_items.append({
                    'id': 'WI-TSA-001',
                    'domain': 'organization',
                    'title': 'Negotiate TSA for Shared Services',
                    'description': f"Negotiate TSA coverage for {len(non_transfer)} shared services that won't transfer",
                    'phase': 'Day_1',
                    'cost_estimate': '25k_to_100k'
                })

        # MSP contract review
        if org_store.msp_relationships:
            work_items.append({
                'id': 'WI-MSP-001',
                'domain': 'organization',
                'title': 'MSP Contract Review',
                'description': f"Review {len(org_store.msp_relationships)} MSP contracts for assignment, termination, and renewal terms",
                'phase': 'Day_1',
                'cost_estimate': 'under_25k'
            })

        # Key person retention
        key_persons = org_store.get_key_persons()
        if key_persons:
            work_items.append({
                'id': 'WI-RET-001',
                'domain': 'organization',
                'title': 'Key Person Retention Planning',
                'description': f"Develop retention plans for {len(key_persons)} identified key persons",
                'phase': 'Day_1',
                'cost_estimate': 'under_25k'
            })

        # Hiring for gaps
        critical_missing = comparison.get_critical_missing_roles()
        if critical_missing:
            work_items.append({
                'id': 'WI-HIRE-001',
                'domain': 'organization',
                'title': 'Critical Role Hiring',
                'description': f"Hire for {len(critical_missing)} critical role gaps: {', '.join(r.role_title for r in critical_missing)}",
                'phase': 'Day_100',
                'cost_estimate': '100k_to_500k'
            })

        return work_items

    def _generate_hiring_recommendations(
        self,
        org_store: OrganizationDataStore,
        comparison: StaffingComparisonResult
    ) -> List:
        """Generate hiring recommendations."""
        from models.organization_models import StaffingNeed

        needs = []

        # From shared services
        ss_needs = self.shared_services_analyzer.generate_staffing_needs(
            org_store.shared_service_dependencies
        )
        needs.extend(ss_needs)

        # From missing critical roles
        for missing in comparison.get_critical_missing_roles():
            # Check if not already covered by shared services needs
            if any(n.role.lower() == missing.role_title.lower() for n in needs):
                continue

            salary = self._estimate_salary_for_role(missing.role_title, missing.category)

            needs.append(StaffingNeed(
                id=f"SN-BENCH-{missing.role_title.replace(' ', '_')}",
                role=missing.role_title,
                category=missing.category,
                fte_count=1.0,
                urgency="day_100",
                reason=f"Critical role gap identified in benchmark comparison",
                estimated_salary=salary,
                source="benchmark_gap"
            ))

        return needs

    def _estimate_salary_for_role(self, role_title: str, category: RoleCategory) -> float:
        """Estimate salary for a role."""
        comp = self.benchmark_service.get_compensation_benchmark(
            role_title, category.value
        )
        if comp:
            return comp['p50']

        # Fallback estimates
        if category == RoleCategory.LEADERSHIP:
            return 150000
        elif category in [RoleCategory.SECURITY, RoleCategory.DATA]:
            return 110000
        elif category in [RoleCategory.INFRASTRUCTURE, RoleCategory.APPLICATIONS]:
            return 95000
        else:
            return 75000
