"""
Inventory Integration Module

Connects the Inventory System to the reasoning pipeline.
Provides inventory context to agents and links findings to items.

Key responsibilities:
1. Format inventory for agent consumption
2. Map inventory types to domains
3. Create fact-like entries from inventory for citation
4. Link findings back to inventory items
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem
from stores.fact_store import FactStore

logger = logging.getLogger(__name__)

# Map inventory types to discovery/reasoning domains
INVENTORY_TO_DOMAIN = {
    "application": "applications",
    "infrastructure": "infrastructure",
    "organization": "organization",
    "vendor": "applications",  # Vendor contracts often relate to applications
}

# Map domains back to inventory types
DOMAIN_TO_INVENTORY = {
    "applications": ["application", "vendor"],
    "infrastructure": ["infrastructure"],
    "organization": ["organization"],
    "network": ["infrastructure"],
    "cybersecurity": ["application", "infrastructure"],
    "identity_access": ["application", "infrastructure"],
}


@dataclass
class InventoryContext:
    """
    Formatted inventory context for reasoning agents.
    """
    domain: str
    items: List[InventoryItem] = field(default_factory=list)
    formatted_text: str = ""
    item_count: int = 0

    # Stats
    enriched_count: int = 0
    flagged_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "item_count": self.item_count,
            "enriched_count": self.enriched_count,
            "flagged_count": self.flagged_count,
            "formatted_text": self.formatted_text,
        }


def get_inventory_for_domain(
    inventory_store: InventoryStore,
    domain: str,
    entity: str = "target",
) -> InventoryContext:
    """
    Get inventory items relevant to a specific domain.

    Args:
        inventory_store: The inventory store
        domain: Reasoning domain (applications, infrastructure, etc.)
        entity: "target" or "buyer"

    Returns:
        InventoryContext with items and formatted text
    """
    context = InventoryContext(domain=domain)

    # Get relevant inventory types for this domain
    inv_types = DOMAIN_TO_INVENTORY.get(domain, [])

    for inv_type in inv_types:
        items = inventory_store.get_items(
            inventory_type=inv_type,
            entity=entity,
            status="active"
        )
        context.items.extend(items)

    context.item_count = len(context.items)
    context.enriched_count = sum(1 for i in context.items if i.is_enriched)
    context.flagged_count = sum(1 for i in context.items if i.needs_investigation)

    # Format for agent consumption
    context.formatted_text = format_inventory_for_agent(context.items, domain)

    return context


def format_inventory_for_agent(
    items: List[InventoryItem],
    domain: str,
) -> str:
    """
    Format inventory items as text for injection into agent prompts.

    Format designed to be parseable and citable:
    - Each item has an ID that can be referenced
    - Key fields are labeled clearly
    - Enrichment notes included if available
    """
    if not items:
        return f"No {domain} inventory items available."

    lines = [f"## {domain.upper()} INVENTORY ({len(items)} items)"]
    lines.append("")
    lines.append("Reference these items by ID when creating findings.")
    lines.append("")

    for item in items:
        lines.append(f"### [{item.item_id}] {item.display_name}")

        # Core fields based on type
        if item.inventory_type == "application":
            _format_application(item, lines)
        elif item.inventory_type == "infrastructure":
            _format_infrastructure(item, lines)
        elif item.inventory_type == "organization":
            _format_organization(item, lines)
        elif item.inventory_type == "vendor":
            _format_vendor(item, lines)

        # Enrichment if available
        if item.is_enriched:
            note = item.enrichment.get("note", "")
            if note:
                lines.append(f"  **Description**: {note}")
            category = item.enrichment.get("llm_category", "")
            if category:
                lines.append(f"  **Category**: {category}")

        # Flag if needs investigation
        if item.needs_investigation:
            lines.append(f"  ⚠️ **FLAGGED**: Needs investigation")

        lines.append("")

    return "\n".join(lines)


def _format_application(item: InventoryItem, lines: List[str]) -> None:
    """Format application-specific fields."""
    data = item.data

    if data.get("vendor"):
        lines.append(f"  **Vendor**: {data['vendor']}")
    if data.get("version"):
        lines.append(f"  **Version**: {data['version']}")
    if data.get("hosting"):
        lines.append(f"  **Hosting**: {data['hosting']}")
    if data.get("users"):
        lines.append(f"  **Users**: {data['users']}")
    if data.get("cost"):
        lines.append(f"  **Cost**: {data['cost']}")
    if data.get("criticality"):
        lines.append(f"  **Criticality**: {data['criticality']}")


def _format_infrastructure(item: InventoryItem, lines: List[str]) -> None:
    """Format infrastructure-specific fields."""
    data = item.data

    if data.get("type"):
        lines.append(f"  **Type**: {data['type']}")
    if data.get("os"):
        lines.append(f"  **OS**: {data['os']}")
    if data.get("environment"):
        lines.append(f"  **Environment**: {data['environment']}")
    if data.get("ip"):
        lines.append(f"  **IP**: {data['ip']}")
    if data.get("location"):
        lines.append(f"  **Location**: {data['location']}")
    if data.get("cpu"):
        lines.append(f"  **CPU**: {data['cpu']}")
    if data.get("memory"):
        lines.append(f"  **Memory**: {data['memory']}")


def _format_organization(item: InventoryItem, lines: List[str]) -> None:
    """Format organization-specific fields."""
    data = item.data

    if data.get("role") or data.get("title"):
        lines.append(f"  **Role**: {data.get('role') or data.get('title')}")
    if data.get("team"):
        lines.append(f"  **Team**: {data['team']}")
    if data.get("headcount"):
        lines.append(f"  **Headcount**: {data['headcount']}")
    if data.get("reports_to"):
        lines.append(f"  **Reports To**: {data['reports_to']}")


def _format_vendor(item: InventoryItem, lines: List[str]) -> None:
    """Format vendor-specific fields."""
    data = item.data

    if data.get("contract_type"):
        lines.append(f"  **Contract Type**: {data['contract_type']}")
    if data.get("start_date"):
        lines.append(f"  **Start Date**: {data['start_date']}")
    if data.get("end_date"):
        lines.append(f"  **End Date**: {data['end_date']}")
    if data.get("acv"):
        lines.append(f"  **ACV**: {data['acv']}")
    if data.get("tcv"):
        lines.append(f"  **TCV**: {data['tcv']}")


def sync_inventory_to_facts(
    inventory_store: InventoryStore,
    fact_store: FactStore,
    entity: str = "target",
    source_file: str = "inventory_import",
) -> Dict[str, int]:
    """
    Sync inventory items to FactStore for citation tracking.

    This allows reasoning agents to cite inventory items using
    the same mechanism they use for document-extracted facts.

    Args:
        inventory_store: Source inventory
        fact_store: Target fact store
        entity: "target" or "buyer"
        source_file: Source attribution

    Returns:
        Dict with sync statistics
    """
    stats = {
        "synced": 0,
        "skipped": 0,
        "by_type": {},
    }

    # Build set of existing item names for deduplication
    existing_items = set()
    for fact in fact_store.get_entity_facts(entity):
        if hasattr(fact, 'item'):
            existing_items.add(fact.item.lower())

    for item in inventory_store.get_items(entity=entity, status="active"):
        # Map inventory type to domain
        domain = INVENTORY_TO_DOMAIN.get(item.inventory_type, "applications")

        # Check if already exists in fact store
        if item.name.lower() in existing_items:
            stats["skipped"] += 1
            continue

        # Create fact from inventory item
        details = dict(item.data)
        details["inventory_id"] = item.item_id
        details["inventory_type"] = item.inventory_type

        if item.is_enriched:
            details["enrichment_note"] = item.enrichment.get("note", "")

        try:
            fact_id = fact_store.add_fact(
                domain=domain,
                category=_get_category_for_item(item),
                item=item.name,
                details=details,
                status="documented",  # Inventory items are documented by definition
                evidence={
                    "exact_quote": f"From inventory: {item.display_name}",
                    "source_section": "Imported Inventory",
                    "inventory_id": item.item_id,
                },
                entity=entity,
                source_document=source_file,
            )
            stats["synced"] += 1

            # Track by type
            if item.inventory_type not in stats["by_type"]:
                stats["by_type"][item.inventory_type] = 0
            stats["by_type"][item.inventory_type] += 1

        except Exception as e:
            logger.warning(f"Failed to sync {item.item_id}: {e}")
            stats["skipped"] += 1

    return stats


def _get_category_for_item(item: InventoryItem) -> str:
    """Determine fact category based on inventory item."""
    data = item.data

    if item.inventory_type == "application":
        # Try to categorize by hosting/type
        hosting = str(data.get("hosting", "")).lower()
        if "saas" in hosting:
            return "saas"
        elif "cloud" in hosting:
            return "cloud_applications"
        else:
            return "on_premises"

    elif item.inventory_type == "infrastructure":
        server_type = str(data.get("type", "")).lower()
        if "database" in server_type or "db" in server_type:
            return "databases"
        elif "web" in server_type:
            return "web_servers"
        else:
            return "compute"

    elif item.inventory_type == "organization":
        return "staffing"

    elif item.inventory_type == "vendor":
        return "vendors"

    return "general"


def link_finding_to_inventory(
    finding: Dict[str, Any],
    inventory_store: InventoryStore,
) -> Dict[str, Any]:
    """
    Enhance a finding with links to related inventory items.

    Searches finding text for inventory item references (by ID or name)
    and adds structured links.

    Args:
        finding: Finding dict with description/details
        inventory_store: Inventory store to search

    Returns:
        Enhanced finding with inventory_links
    """
    import re

    finding = dict(finding)  # Don't mutate input

    links = []
    linked_ids = set()
    text = str(finding.get("description", "")) + " " + str(finding.get("details", ""))

    # Search for item ID references (I-APP-xxxxxx format)
    # The ID pattern matches the format from id_generator: I-{PREFIX}-{6 hex chars}
    id_pattern = r"I-[A-Z]{3}-[a-f0-9]{6}"
    for match in re.finditer(id_pattern, text, re.IGNORECASE):
        item_id = match.group(0)
        # Try both as-is and uppercased
        item = inventory_store.get_item(item_id) or inventory_store.get_item(item_id.upper())
        if item and item.item_id not in linked_ids:
            links.append({
                "item_id": item.item_id,
                "name": item.name,
                "type": item.inventory_type,
            })
            linked_ids.add(item.item_id)

    # Search for item names
    for item in inventory_store.get_items():
        if item.name.lower() in text.lower() and item.item_id not in linked_ids:
            links.append({
                "item_id": item.item_id,
                "name": item.name,
                "type": item.inventory_type,
            })
            linked_ids.add(item.item_id)

    if links:
        finding["inventory_links"] = links

    return finding


def get_inventory_summary(
    inventory_store: InventoryStore,
    entity: str = "target",
) -> Dict[str, Any]:
    """
    Get a summary of inventory for deal context.

    This can be included in reasoning agent prompts to give
    high-level context about the target's IT landscape.
    """
    summary = {
        "entity": entity,
        "totals": {},
        "highlights": [],
    }

    for inv_type in ["application", "infrastructure", "organization", "vendor"]:
        items = inventory_store.get_items(inventory_type=inv_type, entity=entity)
        active = [i for i in items if i.is_active]

        summary["totals"][inv_type] = {
            "count": len(active),
            "enriched": sum(1 for i in active if i.is_enriched),
            "flagged": sum(1 for i in active if i.needs_investigation),
        }

        # Add highlights
        if inv_type == "application":
            # High-cost applications
            high_cost = sorted(
                [i for i in active if i.cost and i.cost > 50000],
                key=lambda x: x.cost or 0,
                reverse=True
            )[:3]
            for app in high_cost:
                summary["highlights"].append(
                    f"High-cost app: {app.name} (${app.cost:,.0f})"
                )

            # Critical applications
            critical = [i for i in active if i.criticality and "critical" in str(i.criticality).lower()]
            if critical:
                summary["highlights"].append(
                    f"{len(critical)} critical applications identified"
                )

        elif inv_type == "infrastructure":
            # Count by environment
            prod = [i for i in active if "prod" in str(i.data.get("environment", "")).lower()]
            if prod:
                summary["highlights"].append(
                    f"{len(prod)} production infrastructure items"
                )

    return summary
