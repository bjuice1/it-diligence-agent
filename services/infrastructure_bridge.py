"""
Infrastructure Bridge - Connects discovery facts to Infrastructure UI.

Converts infrastructure-domain facts from the IT DD pipeline into
structured inventory data for the web interface.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from tools_v2.fact_store import FactStore, Fact

logger = logging.getLogger(__name__)


class InfraCategory(Enum):
    """Infrastructure categories from discovery."""
    HOSTING = "hosting"
    COMPUTE = "compute"
    STORAGE = "storage"
    BACKUP_DR = "backup_dr"
    CLOUD = "cloud"
    LEGACY = "legacy"
    TOOLING = "tooling"
    ENDPOINTS = "endpoints"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        names = {
            "hosting": "Data Centers & Hosting",
            "compute": "Compute & Servers",
            "storage": "Storage Systems",
            "backup_dr": "Backup & DR",
            "cloud": "Cloud Infrastructure",
            "legacy": "Legacy Systems",
            "tooling": "Infrastructure Tooling",
            "endpoints": "End User Computing",
            "other": "Other Infrastructure"
        }
        return names.get(self.value, self.value.title())

    @property
    def icon(self) -> str:
        icons = {
            "hosting": "🏢",
            "compute": "🖥️",
            "storage": "💾",
            "backup_dr": "🔄",
            "cloud": "☁️",
            "legacy": "📟",
            "tooling": "🔧",
            "endpoints": "💻",
            "other": "📦"
        }
        return icons.get(self.value, "📦")


class HostingType(Enum):
    """Hosting/deployment type."""
    OWNED = "owned"
    COLOCATION = "colocation"
    CLOUD = "cloud"
    MSP = "msp"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class AssetStatus(Enum):
    """Asset status."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EOL = "eol"
    PLANNED = "planned"
    UNKNOWN = "unknown"


@dataclass
class InfrastructureItem:
    """A single infrastructure item in the inventory."""
    id: str
    name: str
    category: InfraCategory
    item_type: str = ""  # More specific type within category
    vendor: str = ""
    model: str = ""
    location: str = ""
    hosting_type: HostingType = HostingType.UNKNOWN
    capacity: str = ""  # e.g., "24 racks", "500TB", "1000 endpoints"
    utilization: str = ""
    count: int = 0
    annual_cost: float = 0.0
    support_status: str = ""
    status: AssetStatus = AssetStatus.UNKNOWN
    entity: str = "target"
    notes: str = ""
    evidence: str = ""
    fact_id: str = ""
    source_document: str = ""
    confidence_score: float = 0.0
    verified: bool = False
    # Additional details specific to category
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "category_display": self.category.display_name,
            "item_type": self.item_type,
            "vendor": self.vendor,
            "model": self.model,
            "location": self.location,
            "hosting_type": self.hosting_type.value,
            "capacity": self.capacity,
            "utilization": self.utilization,
            "count": self.count,
            "annual_cost": self.annual_cost,
            "support_status": self.support_status,
            "status": self.status.value,
            "entity": self.entity,
            "notes": self.notes,
            "evidence": self.evidence,
            "fact_id": self.fact_id,
            "source_document": self.source_document,
            "confidence_score": self.confidence_score,
            "verified": self.verified,
            "details": self.details
        }


@dataclass
class CategorySummary:
    """Summary of infrastructure in a category."""
    category: InfraCategory
    total_count: int = 0
    total_cost: float = 0.0
    items: List[InfrastructureItem] = field(default_factory=list)


@dataclass
class InfrastructureInventory:
    """Complete infrastructure inventory."""
    items: List[InfrastructureItem] = field(default_factory=list)
    by_category: Dict[str, CategorySummary] = field(default_factory=dict)
    total_count: int = 0
    total_cost: float = 0.0
    cloud_count: int = 0
    on_prem_count: int = 0
    data_centers: List[InfrastructureItem] = field(default_factory=list)
    cloud_platforms: List[InfrastructureItem] = field(default_factory=list)


def _get_evidence_str(fact: Fact) -> str:
    """Extract evidence string from a Fact object."""
    if not fact.evidence:
        return ""
    if isinstance(fact.evidence, dict):
        return fact.evidence.get('exact_quote', '') or fact.evidence.get('source_section', '')
    return str(fact.evidence)


def _parse_hosting_type(value: Any) -> HostingType:
    """Parse hosting type from various formats."""
    if not value:
        return HostingType.UNKNOWN
    val = str(value).lower()
    if "colo" in val:
        return HostingType.COLOCATION
    elif "cloud" in val:
        return HostingType.CLOUD
    elif "msp" in val or "managed" in val:
        return HostingType.MSP
    elif "owned" in val or "on-prem" in val or "on_prem" in val:
        return HostingType.OWNED
    elif "hybrid" in val:
        return HostingType.HYBRID
    return HostingType.UNKNOWN


def _parse_cost(value: Any) -> float:
    """Parse cost from various formats."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace('$', '').replace(',', '').strip()
        if cleaned.lower().endswith('k'):
            return float(cleaned[:-1]) * 1000
        elif cleaned.lower().endswith('m'):
            return float(cleaned[:-1]) * 1000000
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _parse_int(value: Any) -> int:
    """Parse integer from various formats."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        import re
        match = re.search(r'(\d+)', str(value).replace(',', ''))
        if match:
            return int(match.group(1))
    return 0


def _determine_category(fact: Fact) -> InfraCategory:
    """Determine infrastructure category from fact."""
    cat = fact.category.lower() if fact.category else ""

    # Map known categories
    category_map = {
        "hosting": InfraCategory.HOSTING,
        "compute": InfraCategory.COMPUTE,
        "storage": InfraCategory.STORAGE,
        "backup_dr": InfraCategory.BACKUP_DR,
        "backup": InfraCategory.BACKUP_DR,
        "dr": InfraCategory.BACKUP_DR,
        "cloud": InfraCategory.CLOUD,
        "legacy": InfraCategory.LEGACY,
        "tooling": InfraCategory.TOOLING,
        "endpoints": InfraCategory.ENDPOINTS,
        "euc": InfraCategory.ENDPOINTS
    }

    if cat in category_map:
        return category_map[cat]

    # Try to infer from item name
    item_lower = (fact.item or "").lower()
    if any(k in item_lower for k in ['data center', 'datacenter', 'colo', 'hosting']):
        return InfraCategory.HOSTING
    elif any(k in item_lower for k in ['server', 'vm', 'vmware', 'compute', 'hyper-v']):
        return InfraCategory.COMPUTE
    elif any(k in item_lower for k in ['storage', 'san', 'nas', 'netapp', 's3']):
        return InfraCategory.STORAGE
    elif any(k in item_lower for k in ['backup', 'disaster', 'recovery', 'dr ', 'veeam', 'commvault']):
        return InfraCategory.BACKUP_DR
    elif any(k in item_lower for k in ['aws', 'azure', 'gcp', 'cloud']):
        return InfraCategory.CLOUD
    elif any(k in item_lower for k in ['mainframe', 'legacy', 'as/400']):
        return InfraCategory.LEGACY
    elif any(k in item_lower for k in ['laptop', 'desktop', 'endpoint', 'vdi', 'citrix']):
        return InfraCategory.ENDPOINTS

    return InfraCategory.OTHER


def build_infrastructure_inventory(fact_store: FactStore) -> Tuple[InfrastructureInventory, str]:
    """
    Build an InfrastructureInventory from infrastructure-domain facts.

    Args:
        fact_store: The fact store containing infrastructure facts

    Returns:
        Tuple of (InfrastructureInventory, status) where status is:
        - "success": Infra data was found and built
        - "no_infra_facts": Analysis ran but no infra facts found
        - "no_facts": No facts at all in the store
    """
    inventory = InfrastructureInventory()

    # Check if fact store has any facts at all
    total_facts = len(fact_store.facts) if fact_store.facts else 0
    if total_facts == 0:
        logger.warning("No facts at all in fact store")
        return inventory, "no_facts"

    # Get infrastructure domain facts
    infra_facts = [f for f in fact_store.facts if f.domain == "infrastructure"]

    if not infra_facts:
        logger.warning(f"No infrastructure facts found in fact store (has {total_facts} facts in other domains)")
        return inventory, "no_infra_facts"

    # Build infrastructure items from facts
    items = []
    for fact in infra_facts:
        details = fact.details or {}
        category = _determine_category(fact)

        # Build capacity string based on category
        capacity = ""
        if category == InfraCategory.HOSTING:
            racks = details.get('capacity', {})
            if isinstance(racks, dict):
                capacity = f"{racks.get('racks', '')} racks"
            else:
                capacity = str(racks) if racks else ""
        elif category == InfraCategory.STORAGE:
            cap_gb = details.get('capacity_gb', 0)
            if cap_gb:
                capacity = f"{cap_gb:,} GB" if cap_gb < 1000 else f"{cap_gb/1000:.1f} TB"
        elif category == InfraCategory.COMPUTE:
            count = details.get('count', 0)
            if count:
                capacity = f"{count} servers/VMs"
        elif category == InfraCategory.CLOUD:
            accounts = details.get('accounts', 0)
            if accounts:
                capacity = f"{accounts} accounts"

        item = InfrastructureItem(
            id=fact.fact_id,
            name=fact.item or details.get('type', 'Unknown'),
            category=category,
            item_type=details.get('type', fact.category or ''),
            vendor=details.get('vendor', details.get('provider', '')),
            model=details.get('model', details.get('platform', '')),
            location=details.get('location', details.get('region', '')),
            hosting_type=_parse_hosting_type(details.get('type', details.get('hosting_model', ''))),
            capacity=capacity,
            utilization=str(details.get('utilization_%', '')) + '%' if details.get('utilization_%') else '',
            count=_parse_int(details.get('count', details.get('accounts', 1))),
            annual_cost=_parse_cost(details.get('annual_cost', details.get('annual_spend', 0))),
            support_status=details.get('support_status', ''),
            entity=fact.entity or 'target',
            notes=str(details) if details else '',
            evidence=_get_evidence_str(fact),
            fact_id=fact.fact_id,
            source_document=fact.source_document or '',
            confidence_score=fact.confidence_score,
            verified=fact.verified,
            details=details
        )
        items.append(item)

    inventory.items = items
    inventory.total_count = len(items)
    inventory.total_cost = sum(i.annual_cost for i in items)
    inventory.cloud_count = len([i for i in items if i.category == InfraCategory.CLOUD])
    inventory.on_prem_count = len([i for i in items if i.hosting_type in [HostingType.OWNED, HostingType.COLOCATION]])
    inventory.data_centers = [i for i in items if i.category == InfraCategory.HOSTING]
    inventory.cloud_platforms = [i for i in items if i.category == InfraCategory.CLOUD]

    # Build category summaries
    for category in InfraCategory:
        cat_items = [i for i in items if i.category == category]
        if cat_items:
            inventory.by_category[category.value] = CategorySummary(
                category=category,
                total_count=len(cat_items),
                total_cost=sum(i.annual_cost for i in cat_items),
                items=cat_items
            )

    logger.info(f"Built infrastructure inventory with {len(items)} items")
    return inventory, "success"
