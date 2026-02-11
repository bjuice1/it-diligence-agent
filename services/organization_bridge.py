"""
Organization Bridge - Connects discovery facts to Organization UI.

Converts organization-domain facts from the IT DD pipeline into
OrganizationDataStore format for the web interface.
"""

import re
import uuid
import logging
import copy
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from stores.fact_store import FactStore, Fact
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

# Thread safety for FactStore modifications (P0 Fix: Concurrency)
# This lock protects assumption merge/rollback operations to prevent
# race conditions when multiple threads call build_organization_from_facts()
# concurrently with the same FactStore instance.
_fact_store_modification_lock = threading.RLock()


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


def build_organization_from_facts(
    fact_store: FactStore,
    target_name: str = "Target",
    deal_id: str = "",
    entity: str = "target",
    company_profile: Optional[Dict[str, Any]] = None,
    enable_assumptions: Optional[bool] = None
) -> Tuple[OrganizationDataStore, str]:
    """
    Build an OrganizationDataStore from organization-domain facts with adaptive extraction.

    Enhanced for spec 11: Detects hierarchy presence and generates assumptions
    when organizational structure data is missing or incomplete.

    THREAD SAFETY: This function modifies fact_store.facts in-place when assumptions
    are enabled. Concurrent calls with the same FactStore instance are protected by
    an internal lock, but this may cause performance bottlenecks. For best performance,
    use separate FactStore instances per request/thread, or disable assumptions in
    multi-threaded environments.

    Args:
        fact_store: The fact store containing organization facts
        target_name: Name of the target company
        deal_id: Deal ID for data isolation (passed to created objects)
        entity: "target" or "buyer" (which entity to analyze)
        company_profile: Optional company context (industry, headcount) for assumptions
        enable_assumptions: Override ENABLE_ORG_ASSUMPTIONS config flag

    Returns:
        Tuple of (OrganizationDataStore, status) where status is:
        - "success": Org data was found and built (observed only or FULL hierarchy)
        - "success_with_assumptions": Observed + assumed data merged
        - "success_fallback": Error in assumptions, fell back to observed only
        - "no_org_facts": Analysis ran but no org facts found
        - "no_facts": No facts at all in the store
        - "error": Unrecoverable error
    """
    from config_v2 import ENABLE_ORG_ASSUMPTIONS, ENABLE_BUYER_ORG_ASSUMPTIONS
    from config_v2 import LOG_ASSUMPTION_GENERATION, LOG_HIERARCHY_DETECTION

    # Try to get deal_id from fact_store if not provided
    if not deal_id and hasattr(fact_store, 'deal_id') and fact_store.deal_id:
        deal_id = fact_store.deal_id

    # Determine if assumptions are enabled
    assumptions_enabled = (
        enable_assumptions if enable_assumptions is not None
        else ENABLE_ORG_ASSUMPTIONS
    )

    # Check entity-specific flag for buyer assumptions
    if entity == "buyer" and not ENABLE_BUYER_ORG_ASSUMPTIONS:
        assumptions_enabled = False

    store = OrganizationDataStore()

    # Check if fact store has any facts at all
    total_facts = len(fact_store.facts) if fact_store.facts else 0
    if total_facts == 0:
        logger.warning("No facts at all in fact store")
        return store, "no_facts"

    # CRITICAL (P0 FIX #4): Validate entity field on facts during extraction (fail-fast)
    # Extract org facts AND validate entity in single pass for performance
    all_org_facts = []
    facts_missing_entity = []

    for fact in fact_store.facts:
        if fact.domain == "organization":
            # Validate entity immediately (fail-fast optimization)
            if not hasattr(fact, 'entity') or fact.entity is None or fact.entity == "":
                facts_missing_entity.append(fact.item)
            else:
                all_org_facts.append(fact)

    # Fail fast if any facts have missing entity
    if facts_missing_entity:
        logger.error(
            f"Found {len(facts_missing_entity)} org facts with missing entity field. "
            f"This indicates an upstream bug. Facts: {facts_missing_entity[:5]}"
        )
        raise ValueError(
            f"Entity validation failed: {len(facts_missing_entity)} org facts "
            f"have missing entity field. Cannot proceed with adaptive extraction."
        )

    # Now filter by entity (safe because we validated above)
    org_facts = [f for f in all_org_facts if f.entity == entity]

    if not org_facts:
        logger.warning(f"No organization facts found for entity: {entity} "
                      f"(has {len(all_org_facts)} org facts for other entities)")
        return store, "no_org_facts"

    # STEP 1: Detect hierarchy presence (spec 08) if assumptions enabled
    hierarchy_presence = None
    if assumptions_enabled:
        try:
            from services.org_hierarchy_detector import detect_hierarchy_presence, HierarchyPresenceStatus

            hierarchy_presence = detect_hierarchy_presence(fact_store, entity=entity)

            if LOG_HIERARCHY_DETECTION:
                logger.info(
                    f"Hierarchy detection for {entity}: {hierarchy_presence.status.value} "
                    f"(confidence: {hierarchy_presence.confidence:.2f}, "
                    f"roles: {hierarchy_presence.total_role_count}, "
                    f"reports_to: {hierarchy_presence.roles_with_reports_to})"
                )
        except Exception as e:
            logger.warning(f"Hierarchy detection failed for {entity}, skipping assumptions: {e}")
            hierarchy_presence = None
            assumptions_enabled = False  # Disable assumptions if detection fails

    # Track if assumptions were merged (P1 FIX #4: for rollback on staff creation failure)
    assumptions_merged_successfully = False
    assumptions_backup_for_staff_rollback = None

    # STEP 2 & 3: Generate and merge assumptions if needed (P0 FIX #5, #6: isolation + atomicity)
    if assumptions_enabled and hierarchy_presence:
        from services.org_hierarchy_detector import HierarchyPresenceStatus

        if hierarchy_presence.status in [HierarchyPresenceStatus.PARTIAL, HierarchyPresenceStatus.MISSING]:
            try:
                from services.org_assumption_engine import generate_org_assumptions

                # P2 FIX #8: Validate company_profile structure before passing to assumption engine
                validated_profile = company_profile
                if company_profile is not None:
                    if not isinstance(company_profile, dict):
                        logger.warning(
                            f"Invalid company_profile type: {type(company_profile).__name__}. "
                            f"Expected dict, using defaults instead."
                        )
                        validated_profile = None
                    elif 'industry' not in company_profile and 'headcount' not in company_profile:
                        logger.info(
                            f"company_profile missing 'industry' and 'headcount' keys for {entity}. "
                            f"Assumption engine will use defaults."
                        )

                # Generate assumptions
                assumptions = generate_org_assumptions(
                    fact_store=fact_store,
                    hierarchy_presence=hierarchy_presence,
                    entity=entity,
                    company_profile=validated_profile
                )

                if assumptions:
                    # P0 FIX #6: Backup for atomicity with thread safety
                    # Use deep copy to ensure backup is independent of fact_store.facts mutations
                    # Use lock to prevent concurrent modifications from corrupting state
                    with _fact_store_modification_lock:
                        # Deep copy the facts list to create independent backup
                        old_assumptions_backup = copy.deepcopy([
                            f for f in fact_store.facts
                            if (f.domain == "organization" and
                                f.entity == entity and
                                (f.details or {}).get('data_source') == 'assumed')
                        ])

                        # Track the original facts list reference to detect tampering
                        original_facts_id = id(fact_store.facts)

                        try:
                            # P0 FIX #3: Remove old assumptions (entity-scoped)
                            _remove_old_assumptions_from_fact_store(
                                fact_store=fact_store,
                                entity=entity
                            )

                            # P0 FIX #2: Merge with idempotency protection
                            _merge_assumptions_into_fact_store(
                                fact_store=fact_store,
                                assumptions=assumptions,
                                deal_id=deal_id,
                                entity=entity
                            )

                            # Refresh org_facts to include assumptions
                            org_facts = [f for f in fact_store.facts
                                       if f.domain == "organization" and f.entity == entity]

                            # Mark assumptions as successfully merged (P1 FIX #4)
                            assumptions_merged_successfully = True
                            assumptions_backup_for_staff_rollback = old_assumptions_backup

                            if LOG_ASSUMPTION_GENERATION:
                                logger.info(f"Generated and merged {len(assumptions)} assumptions for {entity}")

                        except Exception as e:
                            # P0 FIX #6: ROLLBACK on failure (thread-safe)
                            logger.error(f"Assumption merge failed for {entity}, rolling back: {e}")

                            # Verify facts list wasn't replaced (safety check)
                            if id(fact_store.facts) != original_facts_id:
                                logger.warning(
                                    f"FactStore.facts was replaced during merge "
                                    f"(id changed from {original_facts_id} to {id(fact_store.facts)}). "
                                    f"Rollback may be incomplete."
                                )

                            # Remove failed merge attempts
                            fact_store.facts = [
                                f for f in fact_store.facts
                                if not (f.domain == "organization" and
                                        f.entity == entity and
                                        (f.details or {}).get('data_source') == 'assumed')
                            ]

                            # Restore backup
                            fact_store.facts.extend(old_assumptions_backup)
                            raise  # Re-raise to trigger fallback

            except (ValueError, KeyError, AttributeError, TypeError) as e:
                # P2 FIX #7: Catch only expected/recoverable errors
                logger.error(f"Assumption generation failed for {entity} (recoverable), continuing with observed data only: {e}")
                # Continue with observed data only (graceful degradation)
            except Exception as e:
                # P2 FIX #7: Re-raise unexpected errors instead of swallowing them
                logger.exception(f"Unexpected error in assumption generation for {entity}: {e}")
                logger.error(f"This is a programming error, not a recoverable failure. Please investigate.")
                raise  # Re-raise to fail fast on unexpected errors

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

    # Build staff members from facts (P1 FIX #4: with rollback protection)
    # If staff creation fails after assumptions were merged, rollback the assumptions
    staff_members = []

    try:
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

    except Exception as e:
        # P1 FIX #4: Rollback assumptions if staff creation failed
        logger.error(f"Staff member creation failed for {entity}, rolling back assumptions: {e}")

        if assumptions_merged_successfully and assumptions_backup_for_staff_rollback is not None:
            with _fact_store_modification_lock:
                # Remove assumptions that were just merged
                fact_store.facts = [
                    f for f in fact_store.facts
                    if not (f.domain == "organization" and
                            f.entity == entity and
                            (f.details or {}).get('data_source') == 'assumed')
                ]

                # Restore old assumptions (if any existed)
                fact_store.facts.extend(assumptions_backup_for_staff_rollback)

                logger.info(f"Rolled back assumptions for {entity} due to staff creation failure")

        # Re-raise the exception
        raise

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

    # P2 FIX #9: Determine final status using explicit tracking (not FactStore inference)
    # We tracked assumptions_merged_successfully during the merge phase (line 234)
    # This is more reliable than scanning FactStore after the fact
    if assumptions_merged_successfully:
        status = "success_with_assumptions"
        logger.info(f"Built organization store with {len(staff_members)} staff "
                   f"(includes assumptions), "
                   f"{len(msp_relationships)} MSPs")
    else:
        status = "success"
        logger.info(f"Built organization store with {len(staff_members)} staff, {len(msp_relationships)} MSPs")

    logger.info(f"  FTEs: {store.total_internal_fte}, Contractors: {store.total_contractor}, "
               f"Total Comp: ${store.total_compensation:,.0f}")

    return store, status


def build_organization_from_inventory_store(
    inventory_store,
    target_name: str = "Target",
    deal_id: str = "",
) -> Tuple[OrganizationDataStore, str]:
    """Build OrganizationDataStore from InventoryStore organization items.

    This is the InventoryStore-based equivalent of build_organization_from_facts().
    Used when InventoryStore is populated (post Spec 01+02+03) to provide
    deduplicated, entity-scoped organization data.

    Args:
        inventory_store: InventoryStore with organization items
        target_name: Company name for display
        deal_id: Deal ID for filtering

    Returns:
        Tuple of (OrganizationDataStore, status_message)
    """
    store = OrganizationDataStore()
    store.target_name = target_name

    # Get org items scoped to target entity
    org_items = inventory_store.get_items(
        inventory_type="organization", entity="target", status="active"
    )

    if not org_items:
        return store, "no_org_items"

    staff_members = []

    for item in org_items:
        data = item.data if hasattr(item, 'data') and item.data else {}
        role = data.get("role", data.get("role_title", "Unknown Role"))
        team = data.get("team", "")
        headcount = _safe_int(data.get("headcount", ""))
        fte = _safe_float(data.get("fte", ""))
        location = data.get("location", "Unknown")
        reports_to = data.get("reports_to", "")
        name = data.get("name", "")
        department = data.get("department", "IT")

        # Determine role category from team/role name
        category = _determine_category_from_name(
            team if team else role, RoleCategory.OTHER
        )

        # Determine employment type
        emp_type_str = data.get("employment_type", "fte").lower()
        if emp_type_str in ("contractor", "contract"):
            emp_type = EmploymentType.CONTRACTOR
        else:
            emp_type = EmploymentType.FTE

        # Determine compensation
        base_comp = _safe_float(data.get("base_compensation", ""))
        if not base_comp:
            base_comp = float(DEFAULT_SALARIES.get(category, 100000))

        effective_headcount = headcount if headcount else 1
        effective_fte = fte if fte else float(effective_headcount)

        # Create one StaffMember per inventory item
        # (InventoryStore items are already deduplicated)
        # Note: StaffMember does not have 'team' or 'inventory_item_id' fields;
        # we store team info in department and item_id in notes.
        member = StaffMember(
            id=gen_id("STAFF"),
            role_title=role,
            name=name if name else role,
            role_category=category,
            department=team if team else department,
            employment_type=emp_type,
            base_compensation=base_comp,
            location=location,
            reports_to=reports_to if reports_to else None,
            entity=data.get("entity", "target"),
            deal_id=deal_id,
            notes=f"Source: inventory item {item.item_id}" if hasattr(item, 'item_id') else "Source: inventory",
        )
        staff_members.append(member)

    store.staff_members = staff_members

    # Build category and role summaries
    store.category_summaries = _build_category_summaries(staff_members)
    store.role_summaries = _build_role_summaries(staff_members)

    # Calculate totals using the store's internal method
    store._update_counts()

    status = f"Built org from {len(org_items)} inventory items"
    logger.info(status)

    return store, "success"


def build_organization_result_from_inventory_store(
    inventory_store,
    target_name: str = "Target",
    deal_id: str = "",
) -> Tuple['OrganizationAnalysisResult', str]:
    """Build a complete OrganizationAnalysisResult from InventoryStore.

    This is the InventoryStore-based equivalent of build_organization_result().
    Wraps build_organization_from_inventory_store() with summaries and benchmarks.

    Args:
        inventory_store: InventoryStore with organization items
        target_name: Company name for display
        deal_id: Deal ID for filtering

    Returns:
        Tuple of (OrganizationAnalysisResult, status)
    """
    from models.organization_stores import StaffingComparisonResult
    from datetime import datetime

    store, status = build_organization_from_inventory_store(
        inventory_store, target_name, deal_id=deal_id
    )

    # Calculate summaries
    msp_summary = _build_msp_summary(store.msp_relationships)
    shared_summary = SharedServicesSummary()
    cost_summary = _build_cost_summary(store)

    # Create placeholder benchmark comparison
    benchmark = StaffingComparisonResult(
        benchmark_profile_id="from_inventory",
        benchmark_profile_name=f"{target_name} Inventory Analysis",
        comparison_date=datetime.now().isoformat(),
        total_actual=len(store.staff_members),
        total_expected_min=0,
        total_expected_typical=0,
        total_expected_max=0,
        overall_status="analyzed" if status == "success" else "no_data"
    )

    headcount = store.get_target_headcount()
    logger.info(
        f"Inventory org result: headcount={headcount}, "
        f"staff_members={len(store.staff_members)}"
    )

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


def _safe_int(value) -> int:
    """Safely convert to int, returning 0 on failure."""
    if not value:
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def _safe_float(value) -> float:
    """Safely convert to float, returning 0.0 on failure."""
    if not value:
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


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
    deal_id: str = "",
    entity: str = "target"
) -> Tuple[OrganizationAnalysisResult, str]:
    """
    Build a complete OrganizationAnalysisResult from facts.

    Args:
        fact_store: The fact store containing organization facts
        reasoning_store: Optional reasoning store for additional findings
        target_name: Name of the target company
        deal_id: Deal ID for data isolation
        entity: "target" or "buyer" (default: "target")

    Returns:
        Tuple of (OrganizationAnalysisResult, status) where status is:
        - "success": Org data was found and built
        - "no_org_facts": Analysis ran but no org facts found
        - "no_facts": No facts at all in the store
    """
    from models.organization_stores import StaffingComparisonResult
    from datetime import datetime

    # P1 FIX #6: Pass entity explicitly to prevent silent misattribution
    store, status = build_organization_from_facts(
        fact_store,
        target_name=target_name,
        deal_id=deal_id,
        entity=entity
    )

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


# =============================================================================
# ADAPTIVE ORGANIZATION EXTRACTION (Spec 11)
# =============================================================================
# Helper functions for assumption-based organization extraction when
# hierarchy data is partial or missing.

def _remove_old_assumptions_from_fact_store(
    fact_store: FactStore,
    entity: str
) -> int:
    """
    Remove old assumptions for an entity from FactStore.

    CRITICAL (P0 FIX #3): Prevents stale assumptions from polluting
    inventory when source data is updated or assumptions re-generated.

    Thread Safety: This function must be called within _fact_store_modification_lock
    to prevent concurrent modifications. Uses in-place list modification to
    preserve backup references.

    Args:
        fact_store: FactStore to clean
        entity: "target" or "buyer"

    Returns:
        Number of assumptions removed
    """
    original_count = len(fact_store.facts)

    # In-place removal to preserve list identity (thread-safe with lock)
    # Using list comprehension + slice assignment instead of reassignment
    facts_to_keep = [
        f for f in fact_store.facts
        if not (f.domain == "organization" and
                f.entity == entity and
                (f.details or {}).get('data_source') == 'assumed')
    ]

    # Replace contents in-place (preserves list object identity)
    fact_store.facts[:] = facts_to_keep

    # P1 FIX #5: Clear assumed fact index for this entity (index maintenance)
    if hasattr(fact_store, '_assumed_fact_keys_by_entity'):
        if entity in fact_store._assumed_fact_keys_by_entity:
            fact_store._assumed_fact_keys_by_entity[entity].clear()
            logger.debug(f"Cleared assumed fact index for {entity}")

    removed_count = original_count - len(fact_store.facts)

    if removed_count > 0:
        logger.info(f"Removed {removed_count} old assumptions for {entity} (cleanup)")

    return removed_count


def _merge_assumptions_into_fact_store(
    fact_store: FactStore,
    assumptions: List,  # List[OrganizationAssumption]
    deal_id: str,
    entity: str
) -> None:
    """
    Merge synthetic assumptions into FactStore as Fact objects.

    CRITICAL (P0 FIX #2): Includes idempotency protection to prevent
    duplicate assumptions if bridge is called multiple times.

    Thread Safety: This function must be called within _fact_store_modification_lock
    to prevent concurrent modifications from corrupting the idempotency check.

    This allows downstream extraction logic to treat assumptions
    the same as observed facts (unified processing).

    Args:
        fact_store: FactStore to merge into
        assumptions: List of OrganizationAssumption objects
        deal_id: Deal ID for fact tagging
        entity: "target" or "buyer"
    """
    # IDEMPOTENCY CHECK: Query index for O(1) lookup (P1 FIX #5: O(N) → O(1))
    # Before: Linear scan through all facts (O(N) where N = total facts)
    # After: Direct index lookup (O(1) where K = assumed facts for entity)
    existing_assumption_keys = fact_store.get_assumed_fact_keys(entity)

    logger.debug(f"Found {len(existing_assumption_keys)} existing assumptions for {entity} (via index)")

    # Filter out assumptions that already exist
    new_assumptions = []
    duplicate_count = 0

    for assumption in assumptions:
        key = f"{assumption.category}:{assumption.item}"
        if key in existing_assumption_keys:
            duplicate_count += 1
            logger.debug(f"Skipping duplicate assumption: {assumption.item}")
        else:
            new_assumptions.append(assumption)

    if duplicate_count > 0:
        logger.info(f"Skipped {duplicate_count} duplicate assumptions (idempotency protection)")

    # Merge only new assumptions
    for assumption in new_assumptions:
        # Convert assumption to fact dict
        fact_dict = assumption.to_fact(deal_id)

        # Add to fact store using add_fact method
        fact_store.add_fact(
            domain=fact_dict['domain'],
            category=fact_dict['category'],
            item=fact_dict['item'],
            details=fact_dict['details'],
            status=fact_dict['status'],
            evidence=fact_dict['evidence'],
            entity=fact_dict['entity']
        )

    logger.info(f"Merged {len(new_assumptions)} new assumptions into FactStore "
                f"(skipped {duplicate_count} duplicates)")
