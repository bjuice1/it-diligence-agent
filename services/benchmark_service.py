"""
Benchmark Service

Provides functionality for:
- Loading benchmark profiles from JSON
- Matching companies to appropriate benchmark profiles
- Comparing actual staffing against benchmarks
- Identifying missing roles
- Compensation benchmarking
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from models.organization_models import (
    BenchmarkProfile,
    BenchmarkRange,
    ExpectedRole,
    RoleCategory,
    StaffMember,
    CompanyInfo
)
from models.organization_stores import (
    CategoryComparison,
    MissingRole,
    OverstaffedArea,
    RatioComparison,
    StaffingComparisonResult,
    CategorySummary
)

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_BENCHMARKS_DIR = Path(__file__).parent.parent / "data" / "benchmarks"
PROFILES_FILE = "benchmark_profiles.json"
COMPENSATION_FILE = "compensation_benchmarks.json"


class BenchmarkService:
    """
    Service for loading and applying benchmark profiles.

    Handles:
    - Loading benchmark data from JSON files
    - Matching companies to appropriate profiles
    - Running staffing comparisons
    - Identifying gaps and overstaffing
    """

    def __init__(self, benchmarks_dir: Optional[Path] = None):
        """
        Initialize the benchmark service.

        Args:
            benchmarks_dir: Directory containing benchmark JSON files.
                           Defaults to data/benchmarks.
        """
        self.benchmarks_dir = benchmarks_dir or DEFAULT_BENCHMARKS_DIR
        self._profiles: List[BenchmarkProfile] = []
        self._compensation_benchmarks: Dict = {}
        self._location_adjustments: Dict = {}
        self._industry_adjustments: Dict = {}
        self._loaded = False

    def load_benchmarks(self) -> bool:
        """
        Load benchmark data from JSON files.

        Returns:
            True if loaded successfully, False otherwise.
        """
        try:
            # Load profiles
            profiles_path = self.benchmarks_dir / PROFILES_FILE
            if profiles_path.exists():
                with open(profiles_path, 'r') as f:
                    data = json.load(f)

                self._profiles = []
                for p in data.get('profiles', []):
                    try:
                        profile = self._parse_profile(p)
                        self._profiles.append(profile)
                    except Exception as e:
                        logger.warning(f"Failed to parse profile {p.get('profile_id')}: {e}")

                logger.info(f"Loaded {len(self._profiles)} benchmark profiles")
            else:
                logger.warning(f"Profiles file not found: {profiles_path}")

            # Load compensation benchmarks
            comp_path = self.benchmarks_dir / COMPENSATION_FILE
            if comp_path.exists():
                with open(comp_path, 'r') as f:
                    comp_data = json.load(f)

                self._compensation_benchmarks = comp_data.get('compensation_benchmarks', {})
                self._location_adjustments = comp_data.get('location_adjustments', {})
                self._industry_adjustments = comp_data.get('industry_adjustments', {})

                logger.info(f"Loaded compensation benchmarks for {len(self._compensation_benchmarks)} categories")
            else:
                logger.warning(f"Compensation file not found: {comp_path}")

            self._loaded = True
            return True

        except Exception as e:
            logger.error(f"Failed to load benchmarks: {e}")
            return False

    def _parse_profile(self, data: Dict) -> BenchmarkProfile:
        """Parse a profile from JSON data."""
        # Parse expected staffing
        expected_staffing = {}
        for category, range_data in data.get('expected_staffing', {}).items():
            expected_staffing[category] = BenchmarkRange(
                min_value=range_data['min'],
                typical_value=range_data['typical'],
                max_value=range_data['max']
            )

        # Parse expected roles
        expected_roles = []
        for role_data in data.get('expected_roles', []):
            expected_roles.append(ExpectedRole(
                role_title=role_data['role_title'],
                category=RoleCategory.from_string(role_data['category']),
                importance=role_data.get('importance', 'medium'),
                typical_count=role_data.get('typical_count', 1),
                description=role_data.get('description'),
                alternatives=role_data.get('alternatives', [])
            ))

        # Parse ratios
        it_ratio = None
        if data.get('it_to_employee_ratio'):
            r = data['it_to_employee_ratio']
            it_ratio = BenchmarkRange(r['min'], r['typical'], r['max'])

        apps_ratio = None
        if data.get('apps_per_developer_ratio'):
            r = data['apps_per_developer_ratio']
            apps_ratio = BenchmarkRange(r['min'], r['typical'], r['max'])

        return BenchmarkProfile(
            profile_id=data['profile_id'],
            profile_name=data['profile_name'],
            description=data['description'],
            revenue_range_min=data['revenue_range_min'],
            revenue_range_max=data['revenue_range_max'],
            employee_range_min=data['employee_range_min'],
            employee_range_max=data['employee_range_max'],
            industries=data['industries'],
            expected_staffing=expected_staffing,
            expected_roles=expected_roles,
            it_to_employee_ratio=it_ratio,
            apps_per_developer_ratio=apps_ratio,
            notes=data.get('notes')
        )

    def get_profiles(self) -> List[BenchmarkProfile]:
        """Get all loaded benchmark profiles."""
        if not self._loaded:
            self.load_benchmarks()
        return self._profiles

    def get_profile_by_id(self, profile_id: str) -> Optional[BenchmarkProfile]:
        """Get a specific profile by ID."""
        if not self._loaded:
            self.load_benchmarks()

        for profile in self._profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def match_profile(
        self,
        revenue: float,
        employees: int,
        industry: str
    ) -> Optional[BenchmarkProfile]:
        """
        Find the best matching benchmark profile for a company.

        Args:
            revenue: Annual revenue in dollars
            employees: Total employee count
            industry: Industry classification

        Returns:
            Best matching BenchmarkProfile, or None if no match.
        """
        if not self._loaded:
            self.load_benchmarks()

        if not self._profiles:
            logger.warning("No benchmark profiles loaded")
            return None

        # Score each profile
        scored_profiles = []
        for profile in self._profiles:
            score = profile.match_score(revenue, employees, industry)
            if score > 0:
                scored_profiles.append((score, profile))

        if not scored_profiles:
            # Fall back to general profiles if no industry match
            for profile in self._profiles:
                if 'general' in profile.industries:
                    if profile.matches_company(revenue, employees, 'general'):
                        return profile

            logger.warning(f"No matching profile for revenue={revenue}, employees={employees}, industry={industry}")
            return None

        # Return highest scoring profile
        scored_profiles.sort(key=lambda x: x[0], reverse=True)
        best_match = scored_profiles[0][1]

        logger.info(f"Matched profile '{best_match.profile_name}' for {industry} company (score: {scored_profiles[0][0]})")
        return best_match

    def compare_staffing(
        self,
        staff_by_category: Dict[str, int],
        benchmark: BenchmarkProfile,
        company_info: Optional[CompanyInfo] = None
    ) -> StaffingComparisonResult:
        """
        Compare actual staffing counts against a benchmark profile.

        Args:
            staff_by_category: Dict mapping category name to headcount
            benchmark: The benchmark profile to compare against
            company_info: Optional company info for ratio calculations

        Returns:
            StaffingComparisonResult with detailed comparison
        """
        category_comparisons = []
        overstaffed_areas = []
        total_actual = 0
        total_expected_min = 0
        total_expected_typical = 0
        total_expected_max = 0

        # Compare each category
        for category_name, bench_range in benchmark.expected_staffing.items():
            actual = staff_by_category.get(category_name, 0)
            total_actual += actual
            total_expected_min += int(bench_range.min_value)
            total_expected_typical += int(bench_range.typical_value)
            total_expected_max += int(bench_range.max_value)

            variance = actual - int(bench_range.typical_value)
            status = bench_range.status(actual)

            # Generate analysis text
            if status == "understaffed":
                analysis = f"{category_name.title()} appears understaffed ({actual} vs expected {int(bench_range.min_value)}-{int(bench_range.max_value)}). May indicate MSP reliance or shared services."
            elif status == "overstaffed":
                analysis = f"{category_name.title()} above benchmark range ({actual} vs expected max {int(bench_range.max_value)}). May indicate complex environment or inefficiency."
                overstaffed_areas.append(OverstaffedArea(
                    category=category_name,
                    actual_count=actual,
                    expected_max=int(bench_range.max_value),
                    overage=actual - int(bench_range.max_value),
                    potential_reasons=["Complex environment", "Historical growth", "Pending attrition"],
                    recommendation="Investigate drivers. May be synergy opportunity post-close."
                ))
            else:
                analysis = f"{category_name.title()} staffing is within expected range."

            # Get display name
            try:
                category_enum = RoleCategory.from_string(category_name)
                display_name = category_enum.display_name
            except:
                display_name = category_name.replace('_', ' ').title()

            category_comparisons.append(CategoryComparison(
                category=category_name,
                category_display=display_name,
                actual_count=actual,
                benchmark_min=int(bench_range.min_value),
                benchmark_typical=int(bench_range.typical_value),
                benchmark_max=int(bench_range.max_value),
                variance=variance,
                status=status,
                analysis=analysis
            ))

        # Calculate ratio comparisons
        ratio_comparisons = []
        if company_info and benchmark.it_to_employee_ratio:
            it_ratio = total_actual / company_info.employee_count if company_info.employee_count > 0 else 0
            ratio_status = benchmark.it_to_employee_ratio.status(it_ratio)

            # Map status for ratio (different semantics)
            if it_ratio < benchmark.it_to_employee_ratio.min_value:
                ratio_status_text = "below"
                ratio_analysis = f"IT ratio ({it_ratio:.1%}) is below typical range. May indicate heavy outsourcing or understaffing."
            elif it_ratio > benchmark.it_to_employee_ratio.max_value:
                ratio_status_text = "above"
                ratio_analysis = f"IT ratio ({it_ratio:.1%}) is above typical range. May indicate complex IT needs or overstaffing."
            else:
                ratio_status_text = "in_range"
                ratio_analysis = f"IT ratio ({it_ratio:.1%}) is within expected range."

            ratio_comparisons.append(RatioComparison(
                ratio_name="IT to Employee Ratio",
                actual_value=it_ratio,
                benchmark_min=benchmark.it_to_employee_ratio.min_value,
                benchmark_typical=benchmark.it_to_employee_ratio.typical_value,
                benchmark_max=benchmark.it_to_employee_ratio.max_value,
                status=ratio_status_text,
                analysis=ratio_analysis
            ))

        # Determine overall status
        understaffed_count = sum(1 for c in category_comparisons if c.status == "understaffed")
        overstaffed_count = sum(1 for c in category_comparisons if c.status == "overstaffed")

        if understaffed_count > 0 and overstaffed_count > 0:
            overall_status = "mixed"
        elif understaffed_count > len(category_comparisons) / 2:
            overall_status = "understaffed"
        elif overstaffed_count > len(category_comparisons) / 2:
            overall_status = "overstaffed"
        else:
            overall_status = "aligned"

        # Generate key findings
        key_findings = []
        if overall_status == "understaffed":
            key_findings.append("Organization appears understaffed relative to benchmarks - investigate MSP/shared services dependencies")
        elif overall_status == "overstaffed":
            key_findings.append("Organization appears overstaffed - potential synergy opportunity")

        for comp in category_comparisons:
            if comp.status == "understaffed":
                key_findings.append(f"{comp.category_display}: {comp.actual_count} FTE vs expected {comp.benchmark_min}-{comp.benchmark_max}")

        # Generate recommendations
        recommendations = []
        if understaffed_count > 0:
            recommendations.append("Document MSP and shared services coverage for understaffed areas")
            recommendations.append("Assess post-close staffing needs if MSP/shared services not continuing")
        if overstaffed_count > 0:
            recommendations.append("Evaluate overstaffed areas for potential synergies")

        return StaffingComparisonResult(
            benchmark_profile_id=benchmark.profile_id,
            benchmark_profile_name=benchmark.profile_name,
            comparison_date=datetime.now().isoformat(),
            overall_status=overall_status,
            total_actual=total_actual,
            total_expected_min=total_expected_min,
            total_expected_typical=total_expected_typical,
            total_expected_max=total_expected_max,
            category_comparisons=category_comparisons,
            missing_roles=[],  # Populated by identify_missing_roles
            overstaffed_areas=overstaffed_areas,
            ratio_comparisons=ratio_comparisons,
            key_findings=key_findings,
            recommendations=recommendations
        )

    def identify_missing_roles(
        self,
        staff: List[StaffMember],
        benchmark: BenchmarkProfile
    ) -> List[MissingRole]:
        """
        Identify expected roles that are missing from the organization.

        Args:
            staff: List of actual staff members
            benchmark: Benchmark profile with expected roles

        Returns:
            List of MissingRole objects for gaps
        """
        missing_roles = []

        # Build set of actual role titles (normalized)
        actual_titles = set()
        for s in staff:
            actual_titles.add(s.role_title.lower().strip())

        # Check each expected role
        for expected in benchmark.expected_roles:
            # Check main title and alternatives
            titles_to_check = [expected.role_title.lower()] + [a.lower() for a in expected.alternatives]

            found = False
            for title in titles_to_check:
                # Fuzzy match - check if any actual title contains or is contained by expected
                for actual in actual_titles:
                    if title in actual or actual in title:
                        found = True
                        break
                if found:
                    break

            if not found:
                # Determine impact based on importance
                if expected.importance == "critical":
                    impact = "Critical capability gap - this role is essential for operations"
                    recommendation = "Immediate: Determine how this function is currently covered (MSP, shared services, or gap)"
                elif expected.importance == "high":
                    impact = "Significant capability gap - may impact operations or security"
                    recommendation = "Investigate coverage and plan for post-close staffing if needed"
                else:
                    impact = "Capability may be missing or covered by other roles"
                    recommendation = "Verify if responsibilities are covered elsewhere"

                missing_roles.append(MissingRole(
                    role_title=expected.role_title,
                    category=expected.category,
                    importance=expected.importance,
                    impact=impact,
                    recommendation=recommendation,
                    current_coverage="Unknown - requires investigation",
                    alternatives_checked=expected.alternatives
                ))

        # Sort by importance
        importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        missing_roles.sort(key=lambda r: importance_order.get(r.importance, 4))

        return missing_roles

    def get_compensation_benchmark(
        self,
        role_title: str,
        category: str,
        location_tier: str = "average",
        industry: str = "general"
    ) -> Optional[Dict]:
        """
        Get compensation benchmark for a role.

        Args:
            role_title: The role title to look up
            category: Role category (leadership, infrastructure, etc.)
            location_tier: Location tier for adjustment
            industry: Industry for adjustment

        Returns:
            Dict with p25, p50, p75 adjusted compensation, or None
        """
        if not self._loaded:
            self.load_benchmarks()

        # Find matching role in compensation benchmarks
        category_benchmarks = self._compensation_benchmarks.get(category, {})

        # Try exact match first
        role_key = None
        for key in category_benchmarks:
            if key.lower() == role_title.lower():
                role_key = key
                break

        # Try fuzzy match
        if not role_key:
            role_lower = role_title.lower()
            for key in category_benchmarks:
                if key.lower() in role_lower or role_lower in key.lower():
                    role_key = key
                    break

        if not role_key:
            return None

        base_comp = category_benchmarks[role_key]

        # Apply adjustments
        loc_mult = self._location_adjustments.get(location_tier, {}).get('multiplier', 1.0)
        ind_mult = self._industry_adjustments.get(industry, {}).get('multiplier', 1.0)
        total_mult = loc_mult * ind_mult

        return {
            'role_matched': role_key,
            'p25': int(base_comp['p25'] * total_mult),
            'p50': int(base_comp['p50'] * total_mult),
            'p75': int(base_comp['p75'] * total_mult),
            'location_adjustment': loc_mult,
            'industry_adjustment': ind_mult,
            'description': base_comp.get('description', '')
        }

    def assess_compensation(
        self,
        staff_member: StaffMember,
        location_tier: str = "average",
        industry: str = "general"
    ) -> Optional[Dict]:
        """
        Assess a staff member's compensation against benchmarks.

        Args:
            staff_member: The staff member to assess
            location_tier: Location tier for adjustment
            industry: Industry for adjustment

        Returns:
            Dict with assessment results, or None if no benchmark found
        """
        benchmark = self.get_compensation_benchmark(
            staff_member.role_title,
            staff_member.role_category.value,
            location_tier,
            industry
        )

        if not benchmark:
            return None

        comp = staff_member.base_compensation

        if comp < benchmark['p25']:
            status = "below_market"
            analysis = f"Compensation ${comp:,.0f} is below 25th percentile (${benchmark['p25']:,.0f}). Retention risk."
        elif comp > benchmark['p75']:
            status = "above_market"
            analysis = f"Compensation ${comp:,.0f} is above 75th percentile (${benchmark['p75']:,.0f}). May indicate tenure or specialized skills."
        elif comp < benchmark['p50']:
            status = "below_median"
            analysis = f"Compensation ${comp:,.0f} is below median (${benchmark['p50']:,.0f}). Monitor for retention."
        else:
            status = "at_market"
            analysis = f"Compensation ${comp:,.0f} is at or above market median."

        return {
            'staff_id': staff_member.id,
            'staff_name': staff_member.name,
            'role_title': staff_member.role_title,
            'actual_compensation': comp,
            'benchmark': benchmark,
            'status': status,
            'analysis': analysis,
            'percentile_estimate': self._estimate_percentile(comp, benchmark)
        }

    def _estimate_percentile(self, value: float, benchmark: Dict) -> int:
        """Estimate what percentile a value falls at."""
        if value <= benchmark['p25']:
            return 25
        elif value >= benchmark['p75']:
            return 75
        elif value <= benchmark['p50']:
            # Interpolate between p25 and p50
            range_size = benchmark['p50'] - benchmark['p25']
            position = value - benchmark['p25']
            return 25 + int((position / range_size) * 25) if range_size > 0 else 37
        else:
            # Interpolate between p50 and p75
            range_size = benchmark['p75'] - benchmark['p50']
            position = value - benchmark['p50']
            return 50 + int((position / range_size) * 25) if range_size > 0 else 62
