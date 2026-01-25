"""
Applications Bridge - Connects discovery facts to Applications UI.

Converts applications-domain facts from the IT DD pipeline into
structured inventory data for the web interface.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from tools_v2.fact_store import FactStore, Fact

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
            "database": "Databases",
            "vertical": "Industry-Specific",
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
    """Determine application category from fact."""
    cat = fact.category.lower() if fact.category else ""
    try:
        return AppCategory(cat)
    except ValueError:
        # Try to infer from item name
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
            name=fact.item or details.get('vendor', 'Unknown Application'),
            category=_determine_category(fact),
            vendor=details.get('vendor', ''),
            version=details.get('version', ''),
            deployment=_parse_deployment(details.get('deployment')),
            user_count=_parse_int(details.get('user_count', 0)),
            criticality=_parse_criticality(details.get('criticality')),
            modules=details.get('modules', []) if isinstance(details.get('modules'), list) else [],
            integrations=details.get('integrations', []) if isinstance(details.get('integrations'), list) else [],
            support_status=details.get('support_status', ''),
            license_type=details.get('license_type', ''),
            annual_cost=_parse_cost(details.get('annual_cost', 0)),
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
