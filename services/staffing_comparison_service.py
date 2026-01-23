"""
Staffing Comparison Service

Compares actual staffing against benchmarks and generates comprehensive analysis.
Ties together census data, MSP data, shared services, and benchmarks.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

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

# Configurable defaults (Point 62)
DEFAULT_MSP_COST_PER_FTE = 100000  # Can be overridden
DEFAULT_CONTRACTOR_MARKUP = 1.3  # 30% markup for contractors
DEFAULT_MSP_MARKUP = 1.5  # 50% markup for MSP services

# Role equivalency mappings (Point 64)
ROLE_EQUIVALENCY_MAP = {
    # Common variations -> normalized role
    "sys admin": "systems administrator",
    "sysadmin": "systems administrator",
    "server admin": "systems administrator",
    "linux admin": "systems administrator",
    "windows admin": "systems administrator",
    "network admin": "network administrator",
    "net admin": "network administrator",
    "neteng": "network engineer",
    "devops": "devops engineer",
    "sre": "devops engineer",
    "site reliability": "devops engineer",
    "cloud admin": "cloud engineer",
    "aws admin": "cloud engineer",
    "azure admin": "cloud engineer",
    "help desk": "help desk technician",
    "helpdesk": "help desk technician",
    "it support": "help desk technician",
    "desktop support": "help desk technician",
    "sec analyst": "security analyst",
    "infosec analyst": "security analyst",
    "cyber analyst": "security analyst",
    "dba": "database administrator",
    "db admin": "database administrator",
    "developer": "software developer",
    "programmer": "software developer",
    "coder": "software developer",
    "software dev": "software developer",
    "ba": "business analyst",
    "pm": "project manager",
    "project mgr": "project manager",
}


class StaffingComparisonService:
    """
    Compares actual staffing to benchmarks and provides comprehensive analysis.
    """

    def __init__(
        self,
        benchmark_service: Optional[BenchmarkService] = None,
        msp_cost_per_fte: float = DEFAULT_MSP_COST_PER_FTE,
        contractor_markup: float = DEFAULT_CONTRACTOR_MARKUP,
        msp_markup: float = DEFAULT_MSP_MARKUP
    ):
        """
        Initialize with configurable cost parameters (Point 62).

        Args:
            benchmark_service: BenchmarkService instance
            msp_cost_per_fte: Cost per FTE for MSP resources
            contractor_markup: Markup factor for contractors vs FTE
            msp_markup: Markup factor for MSP services vs FTE
        """
        self.benchmark_service = benchmark_service or BenchmarkService()
        if not self.benchmark_service._loaded:
            self.benchmark_service.load_benchmarks()

        # Configurable cost parameters (Point 62)
        self.msp_cost_per_fte = msp_cost_per_fte
        self.contractor_markup = contractor_markup
        self.msp_markup = msp_markup

        # Role equivalency for matching (Point 64)
        self.role_equivalency_map = ROLE_EQUIVALENCY_MAP.copy()

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

    # =========================================================================
    # Confidence Intervals (Point 63)
    # =========================================================================

    def calculate_comparison_with_confidence(
        self,
        staff_by_category: Dict[str, int],
        benchmark: BenchmarkProfile,
        confidence_level: float = 0.9
    ) -> Dict[str, Any]:
        """
        Compare staffing with confidence intervals (Point 63).

        Returns comparison with low/mid/high estimates.
        """
        comparisons = []

        for category_name, bench_range in benchmark.expected_staffing.items():
            actual = staff_by_category.get(category_name, 0)

            # Calculate confidence interval range
            range_size = bench_range.max_value - bench_range.min_value
            midpoint = bench_range.typical_value

            # Confidence interval (using typical as center)
            margin = range_size * (1 - confidence_level) / 2
            ci_low = max(bench_range.min_value, midpoint - margin)
            ci_high = min(bench_range.max_value, midpoint + margin)

            # Variance analysis
            variance_from_low = actual - ci_low
            variance_from_mid = actual - midpoint
            variance_from_high = actual - ci_high

            # Status with confidence
            if actual < ci_low:
                status = "understaffed"
                confidence_status = "high_confidence"
            elif actual > ci_high:
                status = "overstaffed"
                confidence_status = "high_confidence"
            elif actual < bench_range.min_value:
                status = "understaffed"
                confidence_status = "moderate_confidence"
            elif actual > bench_range.max_value:
                status = "overstaffed"
                confidence_status = "moderate_confidence"
            else:
                status = "in_range"
                confidence_status = "high_confidence"

            comparisons.append({
                'category': category_name,
                'actual': actual,
                'benchmark_min': int(bench_range.min_value),
                'benchmark_typical': int(bench_range.typical_value),
                'benchmark_max': int(bench_range.max_value),
                'confidence_interval': {
                    'level': confidence_level,
                    'low': ci_low,
                    'high': ci_high
                },
                'variance': {
                    'from_low': variance_from_low,
                    'from_mid': variance_from_mid,
                    'from_high': variance_from_high
                },
                'status': status,
                'confidence_status': confidence_status
            })

        return {
            'comparisons': comparisons,
            'confidence_level': confidence_level,
            'benchmark_profile': benchmark.profile_name
        }

    # =========================================================================
    # Role Equivalency Mapping (Point 64)
    # =========================================================================

    def normalize_role_title(self, role_title: str) -> str:
        """
        Normalize a role title for comparison (Point 64).

        Maps non-standard titles to benchmark roles.
        """
        title_lower = role_title.lower().strip()

        # Direct match
        if title_lower in self.role_equivalency_map:
            return self.role_equivalency_map[title_lower]

        # Substring match
        for key, normalized in self.role_equivalency_map.items():
            if key in title_lower:
                return normalized

        # No mapping found, return original
        return role_title.lower()

    def map_roles_to_benchmarks(
        self,
        staff: List[StaffMember]
    ) -> Dict[str, List[StaffMember]]:
        """
        Group staff by normalized benchmark role.

        Returns dict mapping normalized role to list of staff.
        """
        role_groups = {}

        for member in staff:
            normalized = self.normalize_role_title(member.role_title)
            if normalized not in role_groups:
                role_groups[normalized] = []
            role_groups[normalized].append(member)

        return role_groups

    def add_role_equivalency(self, variation: str, normalized_role: str) -> None:
        """Add a custom role equivalency mapping."""
        self.role_equivalency_map[variation.lower()] = normalized_role.lower()

    # =========================================================================
    # Historical Trend Analysis (Point 65)
    # =========================================================================

    def compare_with_historical(
        self,
        current_staff_by_category: Dict[str, int],
        historical_staff_by_category: Dict[str, int],
        benchmark: BenchmarkProfile
    ) -> Dict[str, Any]:
        """
        Compare current vs historical staffing trends (Point 65).

        Args:
            current_staff_by_category: Current headcount by category
            historical_staff_by_category: Previous period headcount
            benchmark: Benchmark profile for context

        Returns:
            Trend analysis with recommendations
        """
        trends = []
        total_current = sum(current_staff_by_category.values())
        total_historical = sum(historical_staff_by_category.values())
        total_change = total_current - total_historical

        for category in set(current_staff_by_category.keys()) | set(historical_staff_by_category.keys()):
            current = current_staff_by_category.get(category, 0)
            historical = historical_staff_by_category.get(category, 0)
            change = current - historical

            # Calculate percent change
            pct_change = (change / historical * 100) if historical > 0 else (100 if current > 0 else 0)

            # Get benchmark context
            bench_range = benchmark.expected_staffing.get(category)
            benchmark_status = None
            if bench_range:
                if current < bench_range.min_value:
                    benchmark_status = "below_benchmark"
                elif current > bench_range.max_value:
                    benchmark_status = "above_benchmark"
                else:
                    benchmark_status = "within_benchmark"

            # Determine trend direction
            if change > 0:
                trend = "increasing"
            elif change < 0:
                trend = "decreasing"
            else:
                trend = "stable"

            # Generate insight
            insight = self._generate_trend_insight(
                category, change, pct_change, benchmark_status
            )

            trends.append({
                'category': category,
                'current': current,
                'historical': historical,
                'change': change,
                'percent_change': round(pct_change, 1),
                'trend': trend,
                'benchmark_status': benchmark_status,
                'insight': insight
            })

        return {
            'period_comparison': 'current vs historical',
            'total_current': total_current,
            'total_historical': total_historical,
            'total_change': total_change,
            'category_trends': trends,
            'recommendations': self._generate_trend_recommendations(trends)
        }

    def _generate_trend_insight(
        self,
        category: str,
        change: int,
        pct_change: float,
        benchmark_status: Optional[str]
    ) -> str:
        """Generate insight text for a category trend."""
        if change == 0:
            return f"{category.title()} staffing unchanged"

        direction = "increased" if change > 0 else "decreased"
        magnitude = abs(change)

        insight = f"{category.title()} {direction} by {magnitude} ({pct_change:+.0f}%)"

        if benchmark_status == "below_benchmark":
            if change < 0:
                insight += ". Now further below benchmark - risk increasing."
            else:
                insight += ". Moving toward benchmark but still below."
        elif benchmark_status == "above_benchmark":
            if change > 0:
                insight += ". Now further above benchmark."
            else:
                insight += ". Moving toward benchmark range."

        return insight

    def _generate_trend_recommendations(
        self,
        trends: List[Dict]
    ) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []

        # Check for significant decreases in critical areas
        critical_categories = ['security', 'infrastructure', 'leadership']
        for trend in trends:
            if trend['category'] in critical_categories and trend['change'] < -1:
                recommendations.append(
                    f"Investigate {trend['category']} staffing decrease - "
                    f"verify coverage not compromised"
                )

        # Check for rapid growth areas
        rapid_growth = [t for t in trends if t['percent_change'] > 25]
        if rapid_growth:
            cats = [t['category'] for t in rapid_growth]
            recommendations.append(
                f"Review rapid headcount growth in: {', '.join(cats)}"
            )

        # Check for areas still below benchmark despite growth
        growing_but_under = [
            t for t in trends
            if t['change'] > 0 and t.get('benchmark_status') == 'below_benchmark'
        ]
        if growing_but_under:
            cats = [t['category'] for t in growing_but_under]
            recommendations.append(
                f"Continue staffing growth in: {', '.join(cats)} - still below benchmark"
            )

        return recommendations
