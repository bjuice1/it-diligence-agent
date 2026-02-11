"""
Shared helpers for organization views.

Provides a unified way to get organization data from the organization_bridge,
ensuring all org views use StaffMember objects with individual names, costs, and hierarchy.
"""
from typing import Any, Optional, Tuple
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.organization_bridge import build_organization_from_facts
from models.organization_stores import OrganizationDataStore


def get_organization_data_store(fact_store: Any, entity: str = "target") -> Tuple[Optional[OrganizationDataStore], str]:
    """
    Get OrganizationDataStore from fact_store via the organization bridge.

    This function calls the organization_bridge to transform aggregated fact data
    into individual StaffMember objects with names, compensation, and hierarchy.

    Args:
        fact_store: FactStore containing organization domain facts
        entity: "target" or "buyer" (default: "target")

    Returns:
        Tuple of (OrganizationDataStore, status) where status is:
        - "success": Data was found and built successfully
        - "no_org_facts": Analysis ran but no organization facts found
        - "no_facts": No facts at all in the fact_store
    """
    if not fact_store:
        return None, "no_facts"

    if not hasattr(fact_store, 'facts') or not fact_store.facts:
        return None, "no_facts"

    # Check if there are any organization facts
    org_facts = [f for f in fact_store.facts if f.domain == "organization"]
    if not org_facts:
        return None, "no_org_facts"

    # Call the bridge to build OrganizationDataStore with StaffMember objects
    # P1 FIX #6: Pass entity explicitly to prevent silent misattribution
    try:
        store, status = build_organization_from_facts(
            fact_store,
            entity=entity,
            deal_id=getattr(fact_store, 'deal_id', '')
        )
        return store, status
    except Exception as e:
        return None, f"error: {str(e)}"
