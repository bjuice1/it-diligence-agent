"""
Applications Bridge - Connects discovery facts to Applications UI.

Converts applications-domain facts from the IT DD pipeline into
structured inventory data for the web interface.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from stores.fact_store import FactStore, Fact
from services.field_normalizer import normalize_detail, normalize_category

logger = logging.getLogger(__name__)


class AppCategory(Enum):
    """Application categories from discovery."""
    ERP = "erp"
    CRM = "crm"
    CUSTOM = "custom"
    SAAS = "saas"
    HCM = "hcm"
    INTEGRATION = "integration"
    DATABASE = "database"
    VERTICAL = "vertical"
    PRODUCTIVITY = "productivity"
    FINANCE = "finance"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        names = {
            "erp": "ERP Systems",
            "crm": "CRM Platforms",
            "custom": "Custom Applications",
            "saas": "SaaS Applications",
            "hcm": "HCM/HR Systems",
            "integration": "Integration/Middleware",
            "database": "Databases & Analytics",
            "vertical": "Industry-Specific",
            "productivity": "Productivity Tools",
            "finance": "Finance & Accounting",
            "other": "Other Applications"
        }
        return names.get(self.value, self.value.title())

    @property
    def icon(self) -> str:
        icons = {
            "erp": "📊",
            "crm": "👥",
            "custom": "🔧",
            "saas": "☁️",
            "hcm": "👔",
            "integration": "🔗",
            "database": "🗄️",
            "vertical": "🏭",
            "productivity": "📝",
            "finance": "💰",
            "other": "📦"
        }
        return icons.get(self.value, "📦")


class DeploymentType(Enum):
    """Deployment models for applications."""
    ON_PREM = "on_prem"
    CLOUD = "cloud"
    HYBRID = "hybrid"
    SAAS = "saas"
    UNKNOWN = "unknown"


class Criticality(Enum):
    """Application criticality levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class ApplicationItem:
    """A single application in the inventory."""
    id: str
    name: str
    category: AppCategory
    vendor: str = ""
    version: str = ""
    deployment: DeploymentType = DeploymentType.UNKNOWN
    user_count: int = 0
    criticality: Criticality = Criticality.UNKNOWN
    modules: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    support_status: str = ""
    license_type: str = ""
    annual_cost: float = 0.0
    entity: str = "target"
    notes: str = ""
    evidence: str = ""
    fact_id: str = ""
    source_document: str = ""
    confidence_score: float = 0.0
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "category_display": self.category.display_name,
            "vendor": self.vendor,
            "version": self.version,
            "deployment": self.deployment.value,
            "user_count": self.user_count,
            "criticality": self.criticality.value,
            "modules": self.modules,
            "integrations": self.integrations,
            "support_status": self.support_status,
            "license_type": self.license_type,
            "annual_cost": self.annual_cost,
            "entity": self.entity,
            "notes": self.notes,
            "evidence": self.evidence,
            "fact_id": self.fact_id,
            "source_document": self.source_document,
            "confidence_score": self.confidence_score,
            "verified": self.verified
        }


@dataclass
class CategorySummary:
    """Summary of applications in a category."""
    category: AppCategory
    total_count: int = 0
    critical_count: int = 0
    total_users: int = 0
    total_cost: float = 0.0
    applications: List[ApplicationItem] = field(default_factory=list)


@dataclass
class ApplicationsInventory:
    """Complete applications inventory."""
    applications: List[ApplicationItem] = field(default_factory=list)
    by_category: Dict[str, CategorySummary] = field(default_factory=dict)
    total_count: int = 0
    critical_count: int = 0
    saas_count: int = 0
    on_prem_count: int = 0
    total_users: int = 0
    total_cost: float = 0.0


def _get_evidence_str(fact: Fact) -> str:
    """Extract evidence string from a Fact object."""
    if not fact.evidence:
        return ""
    if isinstance(fact.evidence, dict):
        return fact.evidence.get('exact_quote', '') or fact.evidence.get('source_section', '')
    return str(fact.evidence)


def _parse_deployment(value: Any) -> DeploymentType:
    """Parse deployment type from various formats."""
    if not value:
        return DeploymentType.UNKNOWN
    val = str(value).lower().replace("-", "_").replace(" ", "_")
    if "saas" in val:
        return DeploymentType.SAAS
    elif "cloud" in val:
        return DeploymentType.CLOUD
    elif "hybrid" in val:
        return DeploymentType.HYBRID
    elif "prem" in val or "on_prem" in val:
        return DeploymentType.ON_PREM
    return DeploymentType.UNKNOWN


def _parse_criticality(value: Any) -> Criticality:
    """Parse criticality from various formats."""
    if not value:
        return Criticality.UNKNOWN
    val = str(value).lower()
    if "critical" in val:
        return Criticality.CRITICAL
    elif "high" in val:
        return Criticality.HIGH
    elif "medium" in val or "med" in val:
        return Criticality.MEDIUM
    elif "low" in val:
        return Criticality.LOW
    return Criticality.UNKNOWN


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


def _determine_category(fact: Fact) -> AppCategory:
    """Determine application category from fact using centralized normalizer."""
    raw_cat = fact.category or ""

    # Use centralized normalizer first (handles 60+ category variants)
    normalized = normalize_category(raw_cat)
    try:
        return AppCategory(normalized)
    except ValueError:
        pass

    # Fall back to item-name heuristics for truly unknown categories
    item_lower = (fact.item or "").lower()
    if any(k in item_lower for k in ['erp', 'sap', 'oracle', 'netsuite']):
        return AppCategory.ERP
    elif any(k in item_lower for k in ['salesforce', 'crm', 'hubspot']):
        return AppCategory.CRM
    elif any(k in item_lower for k in ['workday', 'adp', 'payroll', 'hr']):
        return AppCategory.HCM
    elif any(k in item_lower for k in ['mulesoft', 'integration', 'middleware', 'api']):
        return AppCategory.INTEGRATION
    elif any(k in item_lower for k in ['sql', 'database', 'postgres', 'mongo', 'snowflake']):
        return AppCategory.DATABASE
    return AppCategory.OTHER


def build_applications_inventory(fact_store: FactStore) -> Tuple[ApplicationsInventory, str]:
    """
    Build an ApplicationsInventory from applications-domain facts.

    Args:
        fact_store: The fact store containing application facts

    Returns:
        Tuple of (ApplicationsInventory, status) where status is:
        - "success": App data was found and built
        - "no_app_facts": Analysis ran but no app facts found
        - "no_facts": No facts at all in the store
    """
    inventory = ApplicationsInventory()

    # Check if fact store has any facts at all
    total_facts = len(fact_store.facts) if fact_store.facts else 0
    if total_facts == 0:
        logger.warning("No facts at all in fact store")
        return inventory, "no_facts"

    # Get applications domain facts
    app_facts = [f for f in fact_store.facts if f.domain == "applications"]

    if not app_facts:
        logger.warning(f"No applications facts found in fact store (has {total_facts} facts in other domains)")
        return inventory, "no_app_facts"

    # Build application items from facts
    applications = []
    for fact in app_facts:
        details = fact.details or {}

        app = ApplicationItem(
            id=fact.fact_id,
            name=fact.item or normalize_detail(details, 'vendor') or 'Unknown Application',
            category=_determine_category(fact),
            vendor=normalize_detail(details, 'vendor') or '',
            version=normalize_detail(details, 'version') or '',
            deployment=_parse_deployment(normalize_detail(details, 'deployment')),
            user_count=_parse_int(normalize_detail(details, 'user_count') or 0),
            criticality=_parse_criticality(normalize_detail(details, 'criticality')),
            modules=details.get('modules', []) if isinstance(details.get('modules'), list) else [],
            integrations=details.get('integrations', []) if isinstance(details.get('integrations'), list) else [],
            support_status=normalize_detail(details, 'support_model') or '',
            license_type=details.get('license_type', ''),
            annual_cost=_parse_cost(normalize_detail(details, 'annual_cost') or 0),
            entity=fact.entity or 'target',
            notes=str(details) if details else '',
            evidence=_get_evidence_str(fact),
            fact_id=fact.fact_id,
            source_document=fact.source_document or '',
            confidence_score=fact.confidence_score,
            verified=fact.verified
        )
        applications.append(app)

    inventory.applications = applications
    inventory.total_count = len(applications)
    inventory.critical_count = len([a for a in applications if a.criticality == Criticality.CRITICAL])
    inventory.saas_count = len([a for a in applications if a.deployment == DeploymentType.SAAS])
    inventory.on_prem_count = len([a for a in applications if a.deployment == DeploymentType.ON_PREM])
    inventory.total_users = sum(a.user_count for a in applications)
    inventory.total_cost = sum(a.annual_cost for a in applications)

    # Build category summaries
    for category in AppCategory:
        cat_apps = [a for a in applications if a.category == category]
        if cat_apps:
            inventory.by_category[category.value] = CategorySummary(
                category=category,
                total_count=len(cat_apps),
                critical_count=len([a for a in cat_apps if a.criticality == Criticality.CRITICAL]),
                total_users=sum(a.user_count for a in cat_apps),
                total_cost=sum(a.annual_cost for a in cat_apps),
                applications=cat_apps
            )

    logger.info(f"Built applications inventory with {len(applications)} apps")
    return inventory, "success"


def _map_category_from_inventory(category_str: str) -> AppCategory:
    """Map inventory category string to AppCategory enum using centralized normalizer."""
    normalized = normalize_category(category_str)
    try:
        return AppCategory(normalized)
    except ValueError:
        return AppCategory.OTHER


def build_applications_from_inventory_store(inventory_store) -> Tuple[ApplicationsInventory, str]:
    """
    Build an ApplicationsInventory from InventoryStore data.

    Args:
        inventory_store: The InventoryStore containing application items

    Returns:
        Tuple of (ApplicationsInventory, status) where status is:
        - "success": App data was found and built
        - "no_apps": No application items in inventory
        - "no_data": No data at all in the store
    """
    inventory = ApplicationsInventory()

    if len(inventory_store) == 0:
        logger.warning("No items in inventory store")
        return inventory, "no_data"

    # Get application items from inventory store
    app_items = inventory_store.get_items(inventory_type="application", entity="target", status="active")

    if not app_items:
        logger.warning("No application items found in inventory store")
        return inventory, "no_apps"

    # Convert inventory items to ApplicationItem objects
    applications = []
    for item in app_items:
        data = item.data or {}

        app = ApplicationItem(
            id=item.item_id,
            name=item.name,
            category=_map_category_from_inventory(data.get('category', '')),
            vendor=normalize_detail(data, 'vendor') or '',
            version=normalize_detail(data, 'version') or '',
            deployment=_parse_deployment(normalize_detail(data, 'deployment')),
            user_count=_parse_int(normalize_detail(data, 'user_count') or 0),
            criticality=_parse_criticality(normalize_detail(data, 'criticality') or ''),
            modules=[],
            integrations=[],
            support_status=normalize_detail(data, 'support_model') or '',
            license_type='',
            annual_cost=item.cost or _parse_cost(normalize_detail(data, 'annual_cost') or 0),
            entity=item.entity or 'target',
            notes=str(data),
            evidence=f"{item.name} | {normalize_detail(data, 'vendor') or ''} | {data.get('category', '')} | {normalize_detail(data, 'deployment') or ''} | {normalize_detail(data, 'user_count') or ''} | ${item.cost or 0:,.0f}" if item.cost or normalize_detail(data, 'vendor') else "",
            fact_id='',
            source_document=item.source_file or '',
            confidence_score=1.0,
            verified=True
        )
        applications.append(app)

    inventory.applications = applications
    inventory.total_count = len(applications)
    inventory.critical_count = len([a for a in applications if a.criticality == Criticality.CRITICAL])
    inventory.saas_count = len([a for a in applications if a.deployment in [DeploymentType.SAAS, DeploymentType.CLOUD]])
    inventory.on_prem_count = len([a for a in applications if a.deployment in [DeploymentType.ON_PREM, DeploymentType.HYBRID]])
    inventory.total_users = sum(a.user_count for a in applications)
    inventory.total_cost = sum(a.annual_cost for a in applications)

    # Build category summaries
    for category in AppCategory:
        cat_apps = [a for a in applications if a.category == category]
        if cat_apps:
            inventory.by_category[category.value] = CategorySummary(
                category=category,
                total_count=len(cat_apps),
                critical_count=len([a for a in cat_apps if a.criticality == Criticality.CRITICAL]),
                total_users=sum(a.user_count for a in cat_apps),
                total_cost=sum(a.annual_cost for a in cat_apps),
                applications=cat_apps
            )

    logger.info(f"Built applications inventory from store with {len(applications)} apps")
    return inventory, "success"


def merge_inventories(primary: ApplicationsInventory, secondary: ApplicationsInventory) -> ApplicationsInventory:
    """
    Merge two ApplicationsInventory objects, deduplicating by app name.

    The primary inventory takes precedence. Secondary apps are added if they
    don't already exist, and missing attributes on primary apps are filled
    from matching secondary apps.

    Args:
        primary: Primary inventory (higher priority)
        secondary: Secondary inventory (fills gaps)

    Returns:
        Merged ApplicationsInventory
    """
    # Index primary apps by normalized name
    by_name: Dict[str, ApplicationItem] = {}
    merged_apps: List[ApplicationItem] = []

    for app in primary.applications:
        key = app.name.lower().strip()
        by_name[key] = app
        merged_apps.append(app)

    # Process secondary apps
    for app in secondary.applications:
        key = app.name.lower().strip()
        if key in by_name:
            # Fill missing attributes from secondary
            existing = by_name[key]
            if not existing.vendor and app.vendor:
                existing.vendor = app.vendor
            if not existing.version and app.version:
                existing.version = app.version
            if existing.deployment == DeploymentType.UNKNOWN and app.deployment != DeploymentType.UNKNOWN:
                existing.deployment = app.deployment
            if existing.user_count == 0 and app.user_count > 0:
                existing.user_count = app.user_count
            if existing.criticality == Criticality.UNKNOWN and app.criticality != Criticality.UNKNOWN:
                existing.criticality = app.criticality
            if existing.annual_cost == 0.0 and app.annual_cost > 0.0:
                existing.annual_cost = app.annual_cost
            if not existing.support_status and app.support_status:
                existing.support_status = app.support_status
            if not existing.source_document and app.source_document:
                existing.source_document = app.source_document
        else:
            # New app from secondary source
            by_name[key] = app
            merged_apps.append(app)

    # Rebuild inventory with merged apps
    inventory = ApplicationsInventory()
    inventory.applications = merged_apps
    inventory.total_count = len(merged_apps)
    inventory.critical_count = len([a for a in merged_apps if a.criticality == Criticality.CRITICAL])
    inventory.saas_count = len([a for a in merged_apps if a.deployment in [DeploymentType.SAAS, DeploymentType.CLOUD]])
    inventory.on_prem_count = len([a for a in merged_apps if a.deployment in [DeploymentType.ON_PREM, DeploymentType.HYBRID]])
    inventory.total_users = sum(a.user_count for a in merged_apps)
    inventory.total_cost = sum(a.annual_cost for a in merged_apps)

    # Build category summaries
    for category in AppCategory:
        cat_apps = [a for a in merged_apps if a.category == category]
        if cat_apps:
            inventory.by_category[category.value] = CategorySummary(
                category=category,
                total_count=len(cat_apps),
                critical_count=len([a for a in cat_apps if a.criticality == Criticality.CRITICAL]),
                total_users=sum(a.user_count for a in cat_apps),
                total_cost=sum(a.annual_cost for a in cat_apps),
                applications=cat_apps
            )

    logger.info(f"Merged inventories: {primary.total_count} + {secondary.total_count} -> {inventory.total_count} apps")
    return inventory
