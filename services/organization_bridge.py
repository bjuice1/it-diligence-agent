"""
Organization Bridge - Connects discovery facts to Organization UI.

Converts organization-domain facts from the IT DD pipeline into
OrganizationDataStore format for the web interface.
"""

import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from tools_v2.fact_store import FactStore, Fact
from models.organization_models import (
    StaffMember, RoleSummary, CategorySummary,
    MSPRelationship, MSPService, SharedServiceDependency,
    RoleCategory, EmploymentType, DependencyLevel,
    TSAItem, StaffingNeed
)
from models.organization_stores import (
    OrganizationDataStore, OrganizationAnalysisResult,
    MSPSummary, SharedServicesSummary, TotalITCostSummary
)

logger = logging.getLogger(__name__)


def gen_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _get_evidence_str(fact: Fact) -> str:
    """Extract evidence string from a Fact object."""
    if not fact.evidence:
        return ""
    if isinstance(fact.evidence, dict):
        return fact.evidence.get('exact_quote', '') or fact.evidence.get('source_section', '')
    return str(fact.evidence)


# Default salary estimates by category (used when not specified in facts)
DEFAULT_SALARIES = {
    RoleCategory.LEADERSHIP: 180000,
    RoleCategory.SECURITY: 140000,
    RoleCategory.APPLICATIONS: 120000,
    RoleCategory.DATA: 125000,
    RoleCategory.INFRASTRUCTURE: 110000,
    RoleCategory.PROJECT_MANAGEMENT: 115000,
    RoleCategory.SERVICE_DESK: 65000,
    RoleCategory.OTHER: 90000,
}


def build_organization_from_facts(fact_store: FactStore, target_name: str = "Target", deal_id: str = "") -> Tuple[OrganizationDataStore, str]:
    """
    Build an OrganizationDataStore from organization-domain facts.

    Args:
        fact_store: The fact store containing organization facts
        target_name: Name of the target company
        deal_id: Deal ID for data isolation (passed to created objects)

    Returns:
        Tuple of (OrganizationDataStore, status) where status is:
        - "success": Org data was found and built
        - "no_org_facts": Analysis ran but no org facts found
        - "no_facts": No facts at all in the store
    """
    # Try to get deal_id from fact_store if not provided
    if not deal_id and hasattr(fact_store, 'deal_id') and fact_store.deal_id:
        deal_id = fact_store.deal_id

    store = OrganizationDataStore()

    # Check if fact store has any facts at all
    total_facts = len(fact_store.facts) if fact_store.facts else 0
    if total_facts == 0:
        logger.warning("No facts at all in fact store")
        return store, "no_facts"

    # Get organization domain facts
    org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    if not org_facts:
        logger.warning(f"No organization facts found in fact store (has {total_facts} facts in other domains)")
        return store, "no_org_facts"

    # Process facts by category
    leadership_facts = [f for f in org_facts if f.category == "leadership"]
    central_it_facts = [f for f in org_facts if f.category == "central_it"]
    app_team_facts = [f for f in org_facts if f.category == "app_teams"]
    roles_facts = [f for f in org_facts if f.category == "roles"]
    outsourcing_facts = [f for f in org_facts if f.category == "outsourcing"]
    embedded_facts = [f for f in org_facts if f.category == "embedded_it"]
    key_individual_facts = [f for f in org_facts if f.category == "key_individuals"]
    skills_facts = [f for f in org_facts if f.category == "skills"]
    budget_facts = [f for f in org_facts if f.category == "budget"]

    # Extract authoritative total headcount from IT Budget fact (if available)
    authoritative_headcount = None
    for fact in budget_facts:
        details = fact.details or {}
        if 'total_it_headcount' in details:
            authoritative_headcount = details.get('total_it_headcount')
            logger.info(f"Found authoritative IT headcount from budget fact: {authoritative_headcount}")
            break

    # Also check for headcount in any fact's details (backup)
    if authoritative_headcount is None:
        for fact in org_facts:
            details = fact.details or {}
            if 'total_it_headcount' in details:
                authoritative_headcount = details.get('total_it_headcount')
                logger.info(f"Found authoritative IT headcount from fact {fact.item}: {authoritative_headcount}")
                break

    # Build staff members from facts
    staff_members = []

    # Process leadership
    for fact in leadership_facts:
        members = _create_staff_from_leadership_fact(fact, deal_id=deal_id)
        staff_members.extend(members)

    # Process central IT teams
    for fact in central_it_facts:
        members = _create_staff_from_team_fact(fact, RoleCategory.INFRASTRUCTURE, deal_id=deal_id)
        staff_members.extend(members)

    # Process app teams
    for fact in app_team_facts:
        members = _create_staff_from_team_fact(fact, RoleCategory.APPLICATIONS, deal_id=deal_id)
        staff_members.extend(members)

    # Process embedded IT
    for fact in embedded_facts:
        members = _create_staff_from_team_fact(fact, RoleCategory.OTHER, deal_id=deal_id)
        staff_members.extend(members)

    # Process roles (from Role & Compensation Breakdown table)
    for fact in roles_facts:
        members = _create_staff_from_role_fact(fact, deal_id=deal_id)
        staff_members.extend(members)

    # Process key individuals
    for fact in key_individual_facts:
        member = _create_staff_from_key_individual_fact(fact, deal_id=deal_id)
        if member:
            # Check if already added, update if so
            existing = next((s for s in staff_members if s.name == member.name), None)
            if existing:
                existing.is_key_person = True
                existing.key_person_reason = member.key_person_reason
            else:
                staff_members.append(member)

    store.staff_members = staff_members

    # Set authoritative headcount from IT Budget fact if found
    if authoritative_headcount is not None:
        store.authoritative_headcount = authoritative_headcount
        logger.info(f"Set authoritative headcount to {authoritative_headcount} (from IT Budget)")

    # Build MSP relationships from outsourcing facts
    msp_relationships = []
    for fact in outsourcing_facts:
        msp = _create_msp_from_fact(fact, deal_id=deal_id)
        if msp:
            msp_relationships.append(msp)

    store.msp_relationships = msp_relationships

    # Build category summaries
    store.category_summaries = _build_category_summaries(staff_members)

    # Build role summaries
    store.role_summaries = _build_role_summaries(staff_members)

    # Calculate totals using the store's internal method
    store._update_counts()

    logger.info(f"Built organization store with {len(staff_members)} staff, {len(msp_relationships)} MSPs")
    logger.info(f"  FTEs: {store.total_internal_fte}, Contractors: {store.total_contractor}, Total Comp: ${store.total_compensation:,.0f}")

    return store, "success"


def _create_staff_from_leadership_fact(fact: Fact, deal_id: str = "") -> List[StaffMember]:
    """Create StaffMembers from a leadership fact (may be aggregated)."""
    details = fact.details or {}
    members = []

    # Get deal_id from fact if not provided
    effective_deal_id = deal_id or getattr(fact, 'deal_id', '')

    # Check if this is aggregated data (has count field)
    count = _parse_headcount(details.get('count', 1))

    # Get cost info
    total_cost = details.get('total_cost')
    if total_cost and count > 0:
        per_person_cost = _parse_cost(total_cost) / count
    else:
        per_person_cost = DEFAULT_SALARIES[RoleCategory.LEADERSHIP]

    # Get domains/roles if specified
    domains = details.get('domains', [])

    name = details.get('name', 'Unknown')
    # Use fact.item for role title (Fact has item, not description)
    role_title = details.get('item', fact.item if fact.item else 'IT Leader')

    # If name is not specified and we have domains, use those
    if (name == 'Unknown' or not name) and domains:
        for i, domain in enumerate(domains[:count]):
            members.append(StaffMember(
                id=gen_id("STAFF"),
                name=f"{domain} Director",
                role_title=f"{domain} Director",
                role_category=RoleCategory.LEADERSHIP,
                department="IT Leadership",
                employment_type=EmploymentType.FTE,
                base_compensation=per_person_cost,
                location=details.get('location', 'Unknown'),
                entity=details.get('entity', 'target'),
                deal_id=effective_deal_id,
                notes=_get_evidence_str(fact) or str(details)
            ))
    else:
        # Create individual entries
        for i in range(count):
            if i == 0:
                member_name = name if name != 'Unknown' else "IT Director"
                member_role = role_title if role_title else "IT Director"
            else:
                member_name = f"IT Leader #{i+1}"
                member_role = f"IT Manager #{i+1}"

            members.append(StaffMember(
                id=gen_id("STAFF"),
                name=member_name,
                role_title=member_role,
                role_category=RoleCategory.LEADERSHIP,
                department="IT Leadership",
                employment_type=EmploymentType.FTE,
                base_compensation=per_person_cost,
                location=details.get('location', 'Unknown'),
                tenure_years=_parse_tenure(details.get('tenure')),
                reports_to=details.get('reports_to'),
                entity=details.get('entity', 'target'),
                deal_id=effective_deal_id,
                notes=_get_evidence_str(fact) or str(details)
            ))

    return members


def _create_staff_from_team_fact(fact: Fact, default_category: RoleCategory, deal_id: str = "") -> List[StaffMember]:
    """Create StaffMembers from a team fact."""
    details = fact.details or {}
    members = []

    # Get deal_id from fact if not provided
    effective_deal_id = deal_id or getattr(fact, 'deal_id', '')

    # Get team name from fact.item (e.g., "Applications Team")
    team_name = fact.item if fact.item else f"{default_category.display_name} Team"
    # Clean up team name for display (remove "Team" suffix if present)
    team_name_clean = team_name.replace(" Team", "").strip()

    headcount = _parse_headcount(details.get('headcount', details.get('count', details.get('fte_count', 1))))
    contractor_count = _parse_headcount(details.get('contractor_count', 0))

    # Calculate per-person compensation from total if available
    total_cost = details.get('total_personnel_cost') or details.get('total_cost') or details.get('personnel_cost')
    if total_cost and headcount > 0:
        per_person_cost = _parse_cost(total_cost) / headcount
    else:
        per_person_cost = DEFAULT_SALARIES.get(default_category, 100000)

    # Determine category from team name
    category = _determine_category_from_name(team_name, default_category)

    # Create staff members with proper role titles
    # Names are placeholders since we don't have individual names from VDR docs
    for i in range(min(headcount, 50)):  # Cap at 50 to avoid huge lists
        # Role title is the meaningful team/function name
        role_title = team_name

        # Name is a simple placeholder - the role_title carries the meaning
        if i == 0 and details.get('manager'):
            name = details.get('manager')
            role_title = f"{team_name_clean} Manager"
        else:
            # Use simple "Staff N" naming - role_title provides context
            name = f"Staff {i+1}"

        members.append(StaffMember(
            id=gen_id("STAFF"),
            name=name,
            role_title=role_title,
            role_category=category,
            department=team_name,
            employment_type=EmploymentType.FTE,
            base_compensation=per_person_cost,
            location=details.get('location', 'Unknown'),
            entity=details.get('entity', 'target'),
            deal_id=effective_deal_id,
            notes=_get_evidence_str(fact) or str(details)
        ))

    # Add contractors
    for i in range(min(contractor_count, 20)):  # Cap contractors
        members.append(StaffMember(
            id=gen_id("STAFF"),
            name=f"{team_name_clean} Contractor #{i+1}",
            role_title=f"{team_name_clean} Contractor",
            role_category=category,
            department=team_name,
            employment_type=EmploymentType.CONTRACTOR,
            base_compensation=int(per_person_cost * 1.3),  # Contractor premium
            location=details.get('location', 'Unknown'),
            entity=details.get('entity', 'target'),
            deal_id=effective_deal_id,
            notes=_get_evidence_str(fact) or str(details)
        ))

    return members


def _parse_cost(cost_str: Any) -> float:
    """Parse cost from string like '$2,075,736' or number."""
    if cost_str is None:
        return 0.0
    if isinstance(cost_str, (int, float)):
        return float(cost_str)
    if isinstance(cost_str, str):
        # Remove $ and commas
        cleaned = cost_str.replace('$', '').replace(',', '').strip()
        # Handle 'k' suffix
        if cleaned.lower().endswith('k'):
            return float(cleaned[:-1]) * 1000
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _create_staff_from_role_fact(fact: Fact, deal_id: str = "") -> List[StaffMember]:
    """Create StaffMembers from a role fact (from Role & Compensation Breakdown table).

    Role facts have details like:
    - item: "Applications Manager"
    - team: "Applications"
    - level: "Manager"
    - count: 5
    - salary_range: "$125,000 - $165,000"
    - total_cost: "$893,065"
    """
    details = fact.details or {}
    members = []

    # Get deal_id from fact if not provided
    effective_deal_id = deal_id or getattr(fact, 'deal_id', '')

    role_title = fact.item if fact.item else "Unknown Role"
    team = details.get('team', 'IT')
    level = details.get('level', 'IC')
    count = _parse_headcount(details.get('count', 1))
    total_cost = _parse_cost(details.get('total_cost', 0))

    # Calculate per-person cost
    per_person_cost = total_cost / count if count > 0 and total_cost > 0 else 0

    # If no total_cost, try to parse from salary_range
    if per_person_cost == 0:
        salary_range = details.get('salary_range', '')
        if salary_range:
            # Parse "125,000 - $165,000" to get midpoint
            parts = salary_range.replace('$', '').replace(',', '').split('-')
            if len(parts) == 2:
                try:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    per_person_cost = (low + high) / 2
                except ValueError:
                    pass

    # Determine category from team name
    category = _determine_category_from_name(team, RoleCategory.OTHER)

    # Create staff members for this role
    for i in range(min(count, 50)):  # Cap at 50
        members.append(StaffMember(
            id=gen_id("STAFF"),
            name=f"{role_title} #{i+1}",
            role_title=role_title,
            role_category=category,
            department=team,
            employment_type=EmploymentType.FTE,
            base_compensation=int(per_person_cost) if per_person_cost > 0 else DEFAULT_SALARIES.get(category, 100000),
            location="Unknown",
            entity=details.get('entity', 'target'),
            deal_id=effective_deal_id,
            notes=f"Level: {level}. {_get_evidence_str(fact)}"
        ))

    return members


def _create_staff_from_key_individual_fact(fact: Fact, deal_id: str = "") -> Optional[StaffMember]:
    """Create a StaffMember from a key individual fact."""
    details = fact.details or {}

    # Get deal_id from fact if not provided
    effective_deal_id = deal_id or getattr(fact, 'deal_id', '')

    name = details.get('item', details.get('name', 'Key Individual'))
    role_title = details.get('role', name)

    return StaffMember(
        id=gen_id("STAFF"),
        name=name,
        role_title=role_title,
        role_category=RoleCategory.OTHER,
        department="IT",
        employment_type=EmploymentType.FTE,
        base_compensation=DEFAULT_SALARIES[RoleCategory.OTHER],
        tenure_years=_parse_tenure(details.get('tenure')),
        entity=details.get('entity', 'target'),
        deal_id=effective_deal_id,
        is_key_person=True,
        key_person_reason=details.get('unique_knowledge', fact.item),
        notes=_get_evidence_str(fact)
    )


def _create_msp_from_fact(fact: Fact, deal_id: str = "") -> Optional[MSPRelationship]:
    """Create an MSPRelationship from an outsourcing fact."""
    details = fact.details or {}

    # Get deal_id from fact if not provided
    effective_deal_id = deal_id or getattr(fact, 'deal_id', '')

    vendor_name = details.get('item', fact.item or 'Unknown Vendor')
    services_provided = details.get('services_provided', fact.item or 'Services')

    # Parse headcount/FTE equivalent
    headcount = _parse_headcount(details.get('headcount', details.get('fte_equivalent', 0)))

    # Parse contract type
    contract_type = details.get('contract_type', 'managed_service')

    # Determine dependency level
    if contract_type == 'managed_service':
        dependency = DependencyLevel.FULL
    elif contract_type == 'staff_aug':
        dependency = DependencyLevel.PARTIAL
    else:
        dependency = DependencyLevel.SUPPLEMENTAL

    # Create services list
    services = []
    if services_provided:
        services.append(MSPService(
            service_name=services_provided[:50] if len(services_provided) > 50 else services_provided,
            fte_equivalent=float(headcount) if headcount > 0 else 1.0,
            coverage="business_hours",
            criticality="high" if dependency == DependencyLevel.FULL else "medium",
            internal_backup=False,
            description=services_provided
        ))

    return MSPRelationship(
        id=gen_id("MSP"),
        vendor_name=vendor_name,
        services=services,
        contract_value_annual=0.0,  # Often not specified in docs
        contract_expiry=details.get('contract_expiry'),
        dependency_level=dependency,
        entity=details.get('entity', 'target'),
        deal_id=effective_deal_id,
        notes=_get_evidence_str(fact)
    )


def _determine_category_from_name(team_name: str, default: RoleCategory) -> RoleCategory:
    """Determine role category from team name."""
    name_lower = team_name.lower()

    if any(k in name_lower for k in ['infrastructure', 'server', 'network', 'datacenter', 'data center']):
        return RoleCategory.INFRASTRUCTURE
    elif any(k in name_lower for k in ['application', 'development', 'software', 'erp', 'crm']):
        return RoleCategory.APPLICATIONS
    elif any(k in name_lower for k in ['security', 'cyber', 'infosec', 'iam']):
        return RoleCategory.SECURITY
    elif any(k in name_lower for k in ['service desk', 'help desk', 'support', 'helpdesk']):
        return RoleCategory.SERVICE_DESK
    elif any(k in name_lower for k in ['data', 'analytics', 'database', 'bi ']):
        return RoleCategory.DATA
    elif any(k in name_lower for k in ['project', 'pmo', 'program']):
        return RoleCategory.PROJECT_MANAGEMENT
    elif any(k in name_lower for k in ['leadership', 'director', 'vp ', 'cio', 'cto']):
        return RoleCategory.LEADERSHIP

    return default


def _parse_headcount(value: Any) -> int:
    """Parse headcount from various formats."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        # Try to extract number
        match = re.search(r'(\d+)', str(value))
        if match:
            return int(match.group(1))
    return 0


def _parse_tenure(value: Any) -> Optional[float]:
    """Parse tenure years from various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Try to extract number of years
        match = re.search(r'(\d+(?:\.\d+)?)', value)
        if match:
            return float(match.group(1))
    return None


def _normalize_location(location: str) -> str:
    """Normalize location type."""
    loc_lower = location.lower()
    if 'offshore' in loc_lower:
        return 'offshore'
    elif 'nearshore' in loc_lower:
        return 'nearshore'
    elif 'onshore' in loc_lower or 'domestic' in loc_lower:
        return 'onshore'
    return 'not_stated'


def _build_category_summaries(staff: List[StaffMember]) -> Dict[str, CategorySummary]:
    """Build category summaries from staff list."""
    summaries = {}

    for category in RoleCategory:
        category_staff = [s for s in staff if s.role_category == category]
        if category_staff:
            fte_count = len([s for s in category_staff if s.employment_type == EmploymentType.FTE])
            contractor_count = len([s for s in category_staff if s.employment_type == EmploymentType.CONTRACTOR])
            total_comp = sum(s.total_compensation or 0 for s in category_staff)

            summaries[category.value] = CategorySummary(
                category=category,
                total_headcount=len(category_staff),
                fte_count=fte_count,
                contractor_count=contractor_count,
                total_compensation=total_comp,
                avg_compensation=total_comp / len(category_staff) if category_staff else 0,
                roles=[]  # Will be populated by role summaries
            )

    return summaries


def _build_role_summaries(staff: List[StaffMember]) -> Dict[str, RoleSummary]:
    """Build role summaries from staff list."""
    summaries = {}

    roles = set(s.role_title for s in staff)

    for role in roles:
        role_staff = [s for s in staff if s.role_title == role]
        if role_staff:
            compensations = [s.total_compensation or 0 for s in role_staff]
            summaries[role] = RoleSummary(
                role_title=role,
                role_category=role_staff[0].role_category,
                headcount=len(role_staff),
                total_compensation=sum(compensations),
                avg_compensation=sum(compensations) / len(role_staff),
                min_compensation=min(compensations),
                max_compensation=max(compensations),
                members=role_staff
            )

    return summaries


def build_organization_result(
    fact_store: FactStore,
    reasoning_store: Any = None,
    target_name: str = "Target",
    deal_id: str = ""
) -> Tuple[OrganizationAnalysisResult, str]:
    """
    Build a complete OrganizationAnalysisResult from facts.

    Args:
        fact_store: The fact store containing organization facts
        reasoning_store: Optional reasoning store for additional findings
        target_name: Name of the target company
        deal_id: Deal ID for data isolation

    Returns:
        Tuple of (OrganizationAnalysisResult, status) where status is:
        - "success": Org data was found and built
        - "no_org_facts": Analysis ran but no org facts found
        - "no_facts": No facts at all in the store
    """
    from models.organization_stores import StaffingComparisonResult
    from datetime import datetime

    store, status = build_organization_from_facts(fact_store, target_name, deal_id=deal_id)

    # Calculate summaries
    msp_summary = _build_msp_summary(store.msp_relationships)
    shared_summary = SharedServicesSummary()  # Would need shared service facts
    cost_summary = _build_cost_summary(store)

    # Create placeholder benchmark comparison
    benchmark = StaffingComparisonResult(
        benchmark_profile_id="from_analysis",
        benchmark_profile_name=f"{target_name} Analysis",
        comparison_date=datetime.now().isoformat(),
        total_actual=len(store.staff_members),
        total_expected_min=0,
        total_expected_typical=0,
        total_expected_max=0,
        overall_status="analyzed" if status == "success" else "no_data"
    )

    # Build the result - use authoritative headcount if available
    headcount = store.get_target_headcount()  # Uses authoritative_headcount if set
    logger.info(f"Final headcount for result: {headcount} (staff_members: {len(store.staff_members)}, authoritative: {store.authoritative_headcount})")

    result = OrganizationAnalysisResult(
        msp_summary=msp_summary,
        shared_services_summary=shared_summary,
        cost_summary=cost_summary,
        benchmark_comparison=benchmark,
        total_it_headcount=headcount,
        total_it_cost=store.total_compensation
    )

    # Add the data_store (expected by templates)
    result.data_store = store

    return result, status


def _build_msp_summary(msps: List[MSPRelationship]) -> MSPSummary:
    """Build MSP summary from relationships."""
    return MSPSummary(
        total_msp_count=len(msps),
        total_fte_equivalent=sum(m.total_fte_equivalent for m in msps),
        total_annual_cost=sum(m.contract_value_annual for m in msps),
        high_risk_count=len([m for m in msps if any(s.criticality == 'critical' for s in m.services)]),
        critical_services_count=sum(len([s for s in m.services if s.criticality == 'critical']) for m in msps),
        services_without_backup=sum(len([s for s in m.services if not s.internal_backup]) for m in msps)
    )


def _build_cost_summary(store: OrganizationDataStore) -> TotalITCostSummary:
    """Build cost summary from data store."""
    fte_staff = [s for s in store.staff_members if s.employment_type == EmploymentType.FTE]
    contractors = [s for s in store.staff_members if s.employment_type == EmploymentType.CONTRACTOR]

    summary = TotalITCostSummary(
        internal_staff_cost=sum(s.total_compensation or 0 for s in fte_staff),
        internal_fte_count=len(fte_staff),
        contractor_cost=sum(s.total_compensation or 0 for s in contractors),
        contractor_count=len(contractors),
        msp_cost=sum(m.contract_value_annual for m in store.msp_relationships),
        msp_fte_equivalent=sum(m.total_fte_equivalent for m in store.msp_relationships)
    )
    summary.calculate_totals()

    return summary
