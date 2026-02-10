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
    Bidirectional sync: create facts from inventory items AND link them.

    This allows reasoning agents to cite inventory items using
    the same mechanism they use for document-extracted facts.
    Spec 03: Now creates bidirectional links (fact<->inventory).

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
        "linked": 0,
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

            # Spec 03: Bidirectional linking
            if fact_id:
                # Link fact -> inventory item
                fact = fact_store.get_fact(fact_id)
                if fact:
                    fact.inventory_item_id = item.item_id

                # Link inventory item -> fact
                if fact_id not in item.source_fact_ids:
                    item.source_fact_ids.append(fact_id)

                stats["linked"] += 1

            # Track by type
            if item.inventory_type not in stats["by_type"]:
                stats["by_type"][item.inventory_type] = 0
            stats["by_type"][item.inventory_type] += 1

        except Exception as e:
            logger.warning(f"Failed to sync {item.item_id}: {e}")
            stats["skipped"] += 1

    return stats


def reconcile_facts_and_inventory(
    fact_store: FactStore,
    inventory_store: InventoryStore,
    entity: str = "target",
    similarity_threshold: float = 0.8,
) -> Dict[str, int]:
    """Match unlinked facts to inventory items by name similarity.

    Extended to cover all domains -- not just applications.

    For facts that were created by LLM extraction (no inventory_item_id)
    and inventory items that were created by import (no source_fact_ids),
    attempt to match them and create bidirectional links.

    Args:
        fact_store: FactStore with potentially unlinked facts
        inventory_store: InventoryStore with potentially unlinked items
        entity: Entity filter ("target" or "buyer")
        similarity_threshold: Minimum similarity score (0.0-1.0) for matching

    Returns:
        Dict with keys: "matched", "unmatched_facts", "unmatched_items"
    """
    from difflib import SequenceMatcher

    stats = {"matched": 0, "unmatched_facts": 0, "unmatched_items": 0}

    # Domain -> inventory type mapping
    domain_type_pairs = [
        ("applications", "application"),
        ("infrastructure", "infrastructure"),
        ("organization", "organization"),
    ]

    for domain, inv_type in domain_type_pairs:
        domain_facts = [
            f for f in fact_store.get_entity_facts(entity, domain=domain)
            if not getattr(f, 'inventory_item_id', None)
        ]

        domain_items = [
            item for item in inventory_store.get_items(
                inventory_type=inv_type, entity=entity
            )
            if not item.source_fact_ids
        ]

        matched_item_ids = set()
        for fact in domain_facts:
            fact_name = fact.item.lower().strip()
            best_match = None
            best_score = 0.0

            for item in domain_items:
                if item.item_id in matched_item_ids:
                    continue

                item_name = item.name.lower().strip()
                score = SequenceMatcher(None, fact_name, item_name).ratio()

                # Boost score if secondary field also matches
                if inv_type == "application":
                    fact_vendor = fact.details.get("vendor", "").lower()
                    item_vendor = item.data.get("vendor", "").lower()
                    if fact_vendor and item_vendor:
                        vendor_score = SequenceMatcher(None, fact_vendor, item_vendor).ratio()
                        score = (score * 0.7) + (vendor_score * 0.3)
                elif inv_type == "infrastructure":
                    fact_env = fact.details.get("environment", "").lower()
                    item_env = item.data.get("environment", "").lower()
                    if fact_env and item_env:
                        env_score = SequenceMatcher(None, fact_env, item_env).ratio()
                        score = (score * 0.7) + (env_score * 0.3)

                if score > best_score:
                    best_score = score
                    best_match = item

            if best_match and best_score >= similarity_threshold:
                fact.inventory_item_id = best_match.item_id
                if fact.fact_id not in best_match.source_fact_ids:
                    best_match.source_fact_ids.append(fact.fact_id)
                matched_item_ids.add(best_match.item_id)
                stats["matched"] += 1
            else:
                stats["unmatched_facts"] += 1

        stats["unmatched_items"] += len(domain_items) - len(matched_item_ids)

    return stats


def promote_facts_to_inventory(
    fact_store: FactStore,
    inventory_store: InventoryStore,
    entity: str = "target",
    similarity_threshold: float = 0.8,
) -> Dict[str, Any]:
    """Promote unlinked LLM-extracted facts to InventoryItems.

    After discovery, some facts exist only in FactStore (extracted from
    unstructured prose by LLM agents). This function:
    1. Finds facts without inventory_item_id
    2. Attempts to match against existing InventoryItems
    3. Creates new InventoryItems for unmatched facts
    4. Establishes bidirectional links in all cases

    Args:
        fact_store: FactStore with all discovery facts
        inventory_store: InventoryStore (partially populated by deterministic parser)
        entity: Entity filter ("target" or "buyer")
        similarity_threshold: Minimum similarity for matching (0.0-1.0)

    Returns:
        Dict with promotion statistics:
        - matched: Facts linked to existing InventoryItems
        - promoted: New InventoryItems created from facts
        - quarantined: Facts with insufficient data for promotion
        - skipped: Facts already linked (had inventory_item_id)
        - by_domain: Breakdown by domain
    """
    from difflib import SequenceMatcher

    stats = {
        "matched": 0,
        "promoted": 0,
        "quarantined": 0,
        "skipped": 0,
        "by_domain": {},
    }

    # Domain -> inventory_type mapping
    domain_to_type = {
        "applications": "application",
        "infrastructure": "infrastructure",
        "organization": "organization",
    }

    # Get all entity-scoped facts
    entity_facts = fact_store.get_entity_facts(entity)

    for fact in entity_facts:
        domain = fact.domain

        # Skip domains that don't map to inventory types
        inv_type = domain_to_type.get(domain)
        if not inv_type:
            continue

        # Skip facts that already have an inventory link
        if fact.inventory_item_id:
            stats["skipped"] += 1
            continue

        # Track by domain
        if domain not in stats["by_domain"]:
            stats["by_domain"][domain] = {"matched": 0, "promoted": 0, "quarantined": 0}

        # Extract item name from fact
        item_name = fact.item
        if not item_name or len(item_name.strip()) < 2:
            stats["quarantined"] += 1
            stats["by_domain"][domain]["quarantined"] += 1
            logger.debug(f"Quarantined fact {fact.fact_id}: no usable item name")
            continue

        # Try to match against existing inventory items
        existing_items = inventory_store.get_items(
            inventory_type=inv_type, entity=entity, status="active"
        )

        best_match = None
        best_score = 0.0
        fact_name = item_name.lower().strip()

        for item in existing_items:
            item_name_lower = item.name.lower().strip()
            score = SequenceMatcher(None, fact_name, item_name_lower).ratio()

            # Boost score if vendor also matches (applications only)
            if inv_type == "application":
                fact_vendor = (fact.details or {}).get("vendor", "").lower()
                item_vendor = item.data.get("vendor", "").lower()
                if fact_vendor and item_vendor:
                    vendor_score = SequenceMatcher(None, fact_vendor, item_vendor).ratio()
                    score = (score * 0.7) + (vendor_score * 0.3)

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score >= similarity_threshold:
            # MATCH FOUND: Link fact to existing item
            fact.inventory_item_id = best_match.item_id
            if fact.fact_id not in best_match.source_fact_ids:
                best_match.source_fact_ids.append(fact.fact_id)

            stats["matched"] += 1
            stats["by_domain"][domain]["matched"] += 1
            logger.debug(
                f"Matched fact {fact.fact_id} -> item {best_match.item_id} "
                f"({best_score:.2f} similarity)"
            )

        else:
            # NO MATCH: Create new InventoryItem from fact
            inv_data = _build_inventory_data_from_fact(fact, inv_type)

            try:
                inv_item_id = inventory_store.add_item(
                    inventory_type=inv_type,
                    entity=entity,
                    data=inv_data,
                    source_file=fact.source_document or "",
                    source_type="discovery",
                    deal_id=fact_store.deal_id,
                )

                # Bidirectional linking
                fact.inventory_item_id = inv_item_id
                inv_item = inventory_store.get_item(inv_item_id)
                if inv_item and fact.fact_id not in inv_item.source_fact_ids:
                    inv_item.source_fact_ids.append(fact.fact_id)

                stats["promoted"] += 1
                stats["by_domain"][domain]["promoted"] += 1
                logger.debug(f"Promoted fact {fact.fact_id} -> new item {inv_item_id}")

            except Exception as e:
                stats["quarantined"] += 1
                stats["by_domain"][domain]["quarantined"] += 1
                logger.warning(f"Failed to promote fact {fact.fact_id}: {e}")

    logger.info(
        f"Fact promotion complete [{entity}]: "
        f"{stats['matched']} matched, {stats['promoted']} promoted, "
        f"{stats['quarantined']} quarantined, {stats['skipped']} skipped"
    )

    return stats


def _build_inventory_data_from_fact(fact, inv_type: str) -> Dict[str, Any]:
    """Build InventoryItem data dict from a Fact's fields.

    Maps fact.item and fact.details to the appropriate schema
    fields for the inventory type.
    """
    details = fact.details or {}

    if inv_type == "application":
        data = {
            "name": fact.item,
            "vendor": details.get("vendor", ""),
            "version": details.get("version", ""),
            "hosting": details.get("deployment", "") or details.get("hosting", ""),
            "users": details.get("user_count", "") or details.get("users", ""),
            "cost": details.get("annual_cost", "") or details.get("cost", ""),
            "criticality": details.get("criticality", ""),
            "category": fact.category or "",
            "source_category": details.get("source_category", ""),
            "category_confidence": details.get("category_confidence", ""),
            "category_inferred_from": details.get("category_inferred_from", ""),
        }
    elif inv_type == "infrastructure":
        data = {
            "name": fact.item,
            "type": details.get("server_type", "") or details.get("type", ""),
            "os": details.get("operating_system", "") or details.get("os", ""),
            "environment": details.get("environment", ""),
            "ip": details.get("ip_address", "") or details.get("ip", ""),
            "location": details.get("location", "") or details.get("datacenter", ""),
            "cpu": details.get("cpu", "") or details.get("cpu_cores", ""),
            "memory": details.get("memory", ""),
            "storage": details.get("storage", ""),
            "role": details.get("role", "") or details.get("function", ""),
        }
    elif inv_type == "organization":
        data = {
            "role": details.get("role", fact.item),
            "name": details.get("person_name", "") or details.get("name", ""),
            "team": details.get("team", ""),
            "department": details.get("department", "IT"),
            "headcount": details.get("headcount", "") or details.get("total_headcount", ""),
            "fte": details.get("fte", ""),
            "location": details.get("location", ""),
            "reports_to": details.get("reports_to", ""),
            "responsibilities": details.get("responsibilities", ""),
        }
    else:
        data = {"name": fact.item}

    # Remove empty values
    return {k: v for k, v in data.items() if v}


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


def _safe_pct(numerator: int, denominator: int) -> float:
    """Calculate percentage safely."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _now_iso() -> str:
    """Current datetime as ISO string."""
    from datetime import datetime
    return datetime.now().isoformat()


def generate_inventory_audit(
    inventory_store: InventoryStore,
    fact_store: FactStore,
    deal_id: str = "",
) -> Dict[str, Any]:
    """Generate a comprehensive inventory audit report for a discovery run.

    Checks:
    1. Item counts by type and entity
    2. Linking coverage (facts with inventory links, items with fact links)
    3. Orphaned facts (no inventory item match)
    4. Orphaned items (no fact links)
    5. Duplicate detection (same name+entity, different IDs)
    6. Entity distribution (target vs buyer)
    7. Data completeness (missing required fields)

    Args:
        inventory_store: The InventoryStore to audit
        fact_store: The FactStore to cross-reference
        deal_id: Deal identifier for the report

    Returns:
        Dict containing the full audit report
    """
    report = {
        "deal_id": deal_id,
        "generated_at": _now_iso(),
        "inventory_counts": {},
        "fact_counts": {},
        "linking": {},
        "orphans": {},
        "duplicates": [],
        "data_quality": {},
        "overall_health": "unknown",
        "issues": [],
    }

    # 1. Inventory counts by type and entity
    for entity in ["target", "buyer"]:
        entity_counts = {}
        for inv_type in ["application", "infrastructure", "organization", "vendor"]:
            items = inventory_store.get_items(
                inventory_type=inv_type, entity=entity, status="active"
            )
            entity_counts[inv_type] = len(items)
        report["inventory_counts"][entity] = entity_counts

    # 2. Fact counts by domain and entity
    for entity in ["target", "buyer"]:
        entity_facts = {}
        for domain in ["applications", "infrastructure", "organization"]:
            facts = fact_store.get_entity_facts(entity, domain=domain)
            entity_facts[domain] = len(facts)
        report["fact_counts"][entity] = entity_facts

    # 3. Linking coverage
    all_items = inventory_store.get_items(status="active")
    linked_items = [i for i in all_items if i.source_fact_ids]
    unlinked_items = [i for i in all_items if not i.source_fact_ids]

    all_facts = fact_store.get_entity_facts("target")
    linked_facts = [f for f in all_facts if hasattr(f, 'inventory_item_id') and f.inventory_item_id]
    unlinked_facts = [f for f in all_facts if not (hasattr(f, 'inventory_item_id') and f.inventory_item_id)]

    report["linking"] = {
        "total_items": len(all_items),
        "linked_items": len(linked_items),
        "unlinked_items": len(unlinked_items),
        "item_link_rate": _safe_pct(len(linked_items), len(all_items)),
        "total_facts": len(all_facts),
        "linked_facts": len(linked_facts),
        "unlinked_facts": len(unlinked_facts),
        "fact_link_rate": _safe_pct(len(linked_facts), len(all_facts)),
    }

    # 4. Orphaned items (no fact links and no enrichment -- possibly stale)
    orphan_items = [
        {"item_id": i.item_id, "name": i.name, "type": i.inventory_type, "entity": i.entity}
        for i in unlinked_items
        if not i.is_enriched
    ]
    report["orphans"] = {
        "items": orphan_items[:20],  # Cap at 20 for readability
        "item_count": len(orphan_items),
        "fact_count": len(unlinked_facts),
    }

    # 5. Duplicate detection (same name+entity, different IDs)
    seen = {}
    for item in all_items:
        key = (item.name.lower().strip(), item.entity, item.inventory_type)
        if key in seen:
            report["duplicates"].append({
                "name": item.name,
                "entity": item.entity,
                "type": item.inventory_type,
                "id_a": seen[key],
                "id_b": item.item_id,
            })
        else:
            seen[key] = item.item_id

    # 6. Data quality -- check for missing required fields
    quality_issues = []
    for item in all_items:
        missing = []
        if not item.name or item.name == "Unknown":
            missing.append("name")
        if item.inventory_type == "application":
            if not item.data.get("vendor"):
                missing.append("vendor")
        elif item.inventory_type == "infrastructure":
            if not item.data.get("environment"):
                missing.append("environment")
        elif item.inventory_type == "organization":
            if not item.data.get("role"):
                missing.append("role")

        if missing:
            quality_issues.append({
                "item_id": item.item_id,
                "name": item.name,
                "missing_fields": missing,
            })

    report["data_quality"] = {
        "items_with_missing_fields": len(quality_issues),
        "details": quality_issues[:20],  # Cap for readability
    }

    # 7. Overall health assessment
    issues = []
    if report["linking"]["item_link_rate"] < 50:
        issues.append(f"Low item link rate: {report['linking']['item_link_rate']}%")
    if len(report["duplicates"]) > 0:
        issues.append(f"{len(report['duplicates'])} duplicate items detected")
    if report["orphans"]["item_count"] > 10:
        issues.append(f"{report['orphans']['item_count']} orphaned items (no fact links)")
    if report["data_quality"]["items_with_missing_fields"] > 5:
        issues.append(f"{report['data_quality']['items_with_missing_fields']} items missing required fields")

    report["issues"] = issues
    if not issues:
        report["overall_health"] = "healthy"
    elif len(issues) <= 2:
        report["overall_health"] = "fair"
    else:
        report["overall_health"] = "needs_attention"

    return report


def save_inventory_audit(
    report: Dict[str, Any],
    deal_id: str = "",
    output_dir: str = "",
) -> str:
    """Save inventory audit report to JSON file.

    Args:
        report: Audit report dict from generate_inventory_audit()
        deal_id: Deal ID for path construction
        output_dir: Override output directory (default: output/deals/{deal_id}/)

    Returns:
        Path to the saved report file
    """
    import json
    from pathlib import Path

    if not output_dir:
        output_dir = f"output/deals/{deal_id}" if deal_id else "output"

    path = Path(output_dir) / "inventory_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Saved inventory audit to {path}")
    return str(path)
