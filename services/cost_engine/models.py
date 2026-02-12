"""
Cost Model Definitions

8 core cost models for IT separation/integration work items.
Each model defines:
- Base services cost
- Per-unit costs (user, site, etc.)
- License costs (annual)
- Complexity multipliers
- Typical timeline
- Source/notes

Models are deterministic: cost = f(drivers, complexity, scenario)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# APPLICATION COST DATA MODELS (Doc 04: Inventory Integration)
# =============================================================================

@dataclass
class ApplicationCost:
    """Cost estimate for single application (Doc 04)."""
    app_name: str
    app_id: str
    complexity: str                    # simple/medium/complex/critical
    category: str                      # erp, crm, collaboration, etc.
    deployment_type: str               # saas, on_prem, hybrid, custom

    # Costs
    one_time_base: float              # Base migration cost (before integration)
    integration_costs: Dict[str, float] = field(default_factory=dict)  # Breakdown of integration costs
    integration_total: float = 0.0    # Sum of integration costs
    tsa_monthly: float = 0.0           # Monthly TSA (carveouts only)
    tsa_total: float = 0.0             # Total TSA over duration
    one_time_total: float = 0.0        # Base + integration
    grand_total: float = 0.0           # One-time + TSA

    # Transparency
    cost_breakdown: Dict[str, Any] = field(default_factory=dict)  # All multipliers and drivers


@dataclass
class ApplicationCostSummary:
    """Aggregate application costs for a deal (Doc 04)."""
    total_one_time: float           # Sum of all one-time costs
    total_tsa: float                # Sum of all TSA costs
    total_integration: float        # Sum of all integration costs
    app_costs: List[ApplicationCost] = field(default_factory=list)  # Per-app breakdown
    app_count: int = 0
    deal_type: str = "acquisition"
    entity: str = "target"

    @property
    def grand_total(self) -> float:
        """Total cost (one-time + TSA)."""
        return self.total_one_time + self.total_tsa

    def get_apps_by_complexity(self) -> Dict[str, List[ApplicationCost]]:
        """Group apps by complexity tier for reporting."""
        from collections import defaultdict
        by_complexity = defaultdict(list)
        for app_cost in self.app_costs:
            by_complexity[app_cost.complexity].append(app_cost)
        return dict(by_complexity)

    def get_top_cost_apps(self, n: int = 10) -> List[ApplicationCost]:
        """Get N most expensive applications."""
        return sorted(self.app_costs, key=lambda ac: ac.grand_total, reverse=True)[:n]


# =============================================================================
# ENUMS
# =============================================================================

class CostScenario(Enum):
    """Cost scenario for IC presentation."""
    UPSIDE = "upside"      # Best case (0.85x)
    BASE = "base"          # Expected case (1.0x)
    STRESS = "stress"      # Worst case (1.3x)


class Complexity(Enum):
    """Complexity level for adjustments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WorkItemType(Enum):
    """Types of work items that have cost models."""
    IDENTITY_SEPARATION = "identity_separation"
    EMAIL_MIGRATION = "email_migration"
    WAN_SEPARATION = "wan_separation"
    ENDPOINT_EDR = "endpoint_edr"
    SECURITY_OPS = "security_ops"
    ERP_STANDALONE = "erp_standalone"
    DC_HOSTING_EXIT = "dc_hosting_exit"
    PMO_TRANSITION = "pmo_transition"
    APPLICATION_MIGRATION = "application_migration"  # Doc 03: Per-app migration cost model


# =============================================================================
# SCENARIO MULTIPLIERS
# =============================================================================

SCENARIO_MULTIPLIERS = {
    CostScenario.UPSIDE: 0.85,
    CostScenario.BASE: 1.0,
    CostScenario.STRESS: 1.3,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LicenseComponent:
    """License cost component."""
    name: str
    per_user_annual: float = 0.0
    per_device_annual: float = 0.0
    flat_annual: float = 0.0
    notes: str = ""

    def calculate(self, users: int = 0, devices: int = 0) -> float:
        """Calculate annual license cost."""
        return (
            self.per_user_annual * users +
            self.per_device_annual * devices +
            self.flat_annual
        )


@dataclass
class CostModel:
    """
    Definition of a cost model for a work item type.

    Cost calculation:
    1. Base: base_services + (per_user * users) + (per_site * sites)
    2. Complexity: base * complexity_multiplier
    3. Licenses: sum of license components
    4. Scenario: total * scenario_multiplier
    """
    work_item_type: WorkItemType
    display_name: str
    tower: str  # Identity, Apps, Infra, Network, Security, EUC, PMO

    # One-time costs
    base_services_cost: float = 0.0
    per_user_cost: float = 0.0
    per_site_cost: float = 0.0
    per_server_cost: float = 0.0
    per_app_cost: float = 0.0

    # Complexity multipliers
    complexity_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "low": 0.8,
        "medium": 1.0,
        "high": 1.5,
    })

    # License components (annual recurring)
    licenses: List[LicenseComponent] = field(default_factory=list)

    # Timeline
    typical_months: int = 6

    # Metadata
    source: str = "internal_default"
    notes: str = ""
    assumptions: List[str] = field(default_factory=list)

    # Driver requirements
    required_drivers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'work_item_type': self.work_item_type.value,
            'display_name': self.display_name,
            'tower': self.tower,
            'base_services_cost': self.base_services_cost,
            'per_user_cost': self.per_user_cost,
            'per_site_cost': self.per_site_cost,
            'complexity_multipliers': self.complexity_multipliers,
            'licenses': [{'name': l.name, 'per_user_annual': l.per_user_annual} for l in self.licenses],
            'typical_months': self.typical_months,
            'source': self.source,
            'notes': self.notes,
        }


@dataclass
class CostEstimate:
    """Result of cost calculation."""
    work_item_type: str
    display_name: str
    tower: str

    # Entity dimension
    entity: str = "target"

    # One-time costs by scenario
    one_time_upside: float = 0.0
    one_time_base: float = 0.0
    one_time_stress: float = 0.0

    # Annual license costs
    annual_licenses: float = 0.0

    # Run rate delta (new ongoing costs minus current)
    run_rate_delta: float = 0.0

    # TSA costs (carveout-specific)
    tsa_costs: float = 0.0

    # Breakdown
    cost_breakdown: Dict[str, float] = field(default_factory=dict)

    # Assumptions used
    assumptions: List[str] = field(default_factory=list)

    # Drivers used
    drivers_used: Dict[str, Any] = field(default_factory=dict)

    # Complexity applied
    complexity: str = "medium"

    # Timeline
    estimated_months: int = 6

    def to_dict(self) -> Dict:
        return {
            'work_item_type': self.work_item_type,
            'display_name': self.display_name,
            'tower': self.tower,
            'entity': self.entity,
            'one_time': {
                'upside': self.one_time_upside,
                'base': self.one_time_base,
                'stress': self.one_time_stress,
            },
            'annual_licenses': self.annual_licenses,
            'run_rate_delta': self.run_rate_delta,
            'tsa_costs': self.tsa_costs,
            'cost_breakdown': self.cost_breakdown,
            'assumptions': self.assumptions,
            'drivers_used': self.drivers_used,
            'complexity': self.complexity,
            'estimated_months': self.estimated_months,
        }


# =============================================================================
# THE 8 CORE COST MODELS
# =============================================================================

COST_MODELS: Dict[WorkItemType, CostModel] = {}

# -----------------------------------------------------------------------------
# Model 1: Identity Separation
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.IDENTITY_SEPARATION] = CostModel(
    work_item_type=WorkItemType.IDENTITY_SEPARATION,
    display_name="Identity Separation",
    tower="Identity",

    # Services: AD standup, Azure AD config, migration
    base_services_cost=75_000,
    per_user_cost=15,  # Migration labor per user
    per_site_cost=5_000,  # Per-site AD config

    complexity_multipliers={
        "low": 0.7,    # Simple AD, single domain
        "medium": 1.0, # Standard multi-domain
        "high": 1.5,   # Complex with legacy trusts, custom GPOs
    },

    licenses=[
        LicenseComponent(
            name="Azure AD P2",
            per_user_annual=108,  # ~$9/user/month
            notes="Premium P2 for PIM, access reviews",
        ),
        LicenseComponent(
            name="Entra ID Governance",
            per_user_annual=84,  # ~$7/user/month
            notes="Lifecycle workflows, entitlement management",
        ),
    ],

    typical_months=4,
    source="internal_default",
    notes="Based on 10+ carveout engagements. Azure AD P2 list pricing.",
    assumptions=[
        "Azure AD P2 licensing for all users",
        "Assumes standard migration (no custom connectors)",
        "Excludes third-party MFA hardware",
    ],
    required_drivers=["total_users", "sites"],
)

# -----------------------------------------------------------------------------
# Model 2: Email Migration
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.EMAIL_MIGRATION] = CostModel(
    work_item_type=WorkItemType.EMAIL_MIGRATION,
    display_name="Email Migration",
    tower="Apps",

    base_services_cost=50_000,
    per_user_cost=20,  # Mailbox migration labor

    complexity_multipliers={
        "low": 0.8,    # Simple mailbox-only
        "medium": 1.0, # With shared mailboxes, DLs
        "high": 1.4,   # Complex with archives, journaling, compliance
    },

    licenses=[
        LicenseComponent(
            name="M365 E3",
            per_user_annual=432,  # ~$36/user/month
            notes="Exchange Online + Office apps",
        ),
    ],

    typical_months=3,
    source="internal_default",
    notes="Assumes migration to new M365 tenant.",
    assumptions=[
        "New M365 tenant required",
        "Standard mailbox sizes (<50GB average)",
        "Migration window of 4-6 weeks",
    ],
    required_drivers=["total_users"],
)

# -----------------------------------------------------------------------------
# Model 3: WAN Separation
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.WAN_SEPARATION] = CostModel(
    work_item_type=WorkItemType.WAN_SEPARATION,
    display_name="WAN Separation",
    tower="Network",

    base_services_cost=100_000,  # Design, project management
    per_site_cost=15_000,  # Per-site cutover

    complexity_multipliers={
        "low": 0.8,    # SD-WAN, few sites
        "medium": 1.0, # MPLS, moderate sites
        "high": 1.6,   # Complex hybrid, many sites
    },

    licenses=[
        LicenseComponent(
            name="SD-WAN per site",
            flat_annual=3_600,  # $300/month per site average
            notes="Varies by bandwidth tier",
        ),
    ],

    typical_months=6,
    source="internal_default",
    notes="Assumes SD-WAN deployment. MPLS adds 30-50%.",
    assumptions=[
        "SD-WAN solution (not MPLS)",
        "Standard bandwidth (100Mbps-1Gbps per site)",
        "No international sites requiring special circuits",
    ],
    required_drivers=["sites", "wan_sites"],
)

# -----------------------------------------------------------------------------
# Model 4: Endpoint/EDR Deployment
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.ENDPOINT_EDR] = CostModel(
    work_item_type=WorkItemType.ENDPOINT_EDR,
    display_name="Endpoint & EDR Migration",
    tower="EUC",

    base_services_cost=30_000,
    per_user_cost=10,  # Per-device migration

    complexity_multipliers={
        "low": 0.8,    # Standard Windows fleet
        "medium": 1.0, # Mixed OS
        "high": 1.3,   # Legacy systems, compliance requirements
    },

    licenses=[
        LicenseComponent(
            name="CrowdStrike Falcon",
            per_device_annual=60,  # ~$5/device/month
            notes="Enterprise tier pricing",
        ),
    ],

    typical_months=3,
    source="internal_default",
    notes="Assumes CrowdStrike or similar. Defender included in M365 E5.",
    assumptions=[
        "Windows endpoints (Mac adds 10%)",
        "Standard deployment (no air-gapped systems)",
        "Excludes physical security agents",
    ],
    required_drivers=["endpoints", "total_users"],
)

# -----------------------------------------------------------------------------
# Model 5: Security Ops Standup
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.SECURITY_OPS] = CostModel(
    work_item_type=WorkItemType.SECURITY_OPS,
    display_name="Security Ops Standup",
    tower="Security",

    base_services_cost=150_000,  # SIEM setup, SOC design
    per_user_cost=5,  # Log source sizing

    complexity_multipliers={
        "low": 0.7,    # MSSP only
        "medium": 1.0, # Hybrid SOC
        "high": 1.5,   # Full in-house 24x7
    },

    licenses=[
        LicenseComponent(
            name="Microsoft Sentinel",
            per_user_annual=36,  # ~$3/user/month for log ingestion
            notes="Based on typical log volume per user",
        ),
        LicenseComponent(
            name="MSSP retainer",
            flat_annual=180_000,  # $15K/month
            notes="24x7 monitoring and response",
        ),
    ],

    typical_months=4,
    source="internal_default",
    notes="MSSP model. In-house SOC 2-3x this cost.",
    assumptions=[
        "MSSP for 24x7 monitoring",
        "Microsoft Sentinel SIEM",
        "Standard compliance (not FedRAMP/HIPAA)",
    ],
    required_drivers=["total_users"],
)

# -----------------------------------------------------------------------------
# Model 6: ERP Standalone Instance
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.ERP_STANDALONE] = CostModel(
    work_item_type=WorkItemType.ERP_STANDALONE,
    display_name="ERP Standalone Instance",
    tower="Apps",

    base_services_cost=500_000,  # Implementation services
    per_user_cost=200,  # Data migration, training

    complexity_multipliers={
        "low": 0.7,    # Simple NetSuite/small Oracle
        "medium": 1.0, # Standard SAP/Oracle
        "high": 2.0,   # Complex SAP with customizations
    },

    licenses=[
        LicenseComponent(
            name="SAP S/4HANA Cloud",
            per_user_annual=2_400,  # ~$200/user/month
            notes="Professional user. Self-service users ~$100/month",
        ),
    ],

    typical_months=12,
    source="internal_default",
    notes="Generic ERP. SAP vs Oracle vs NetSuite varies significantly.",
    assumptions=[
        "Cloud deployment (not on-prem)",
        "Standard modules (Finance, Supply Chain)",
        "Clean data migration (no legacy cleanup)",
    ],
    required_drivers=["erp_users", "erp_system"],
)

# -----------------------------------------------------------------------------
# Model 7: DC/Hosting Exit
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.DC_HOSTING_EXIT] = CostModel(
    work_item_type=WorkItemType.DC_HOSTING_EXIT,
    display_name="DC/Hosting Exit",
    tower="Infra",

    base_services_cost=100_000,  # Assessment, planning
    per_server_cost=5_000,  # Per-server migration

    complexity_multipliers={
        "low": 0.8,    # Lift-and-shift to cloud
        "medium": 1.0, # Refactor some workloads
        "high": 1.5,   # Complex legacy, mainframe
    },

    licenses=[
        LicenseComponent(
            name="Azure/AWS compute",
            flat_annual=120_000,  # $10K/month average
            notes="Highly variable based on workload",
        ),
    ],

    typical_months=9,
    source="internal_default",
    notes="Assumes cloud migration. Colo hosting is different model.",
    assumptions=[
        "Cloud destination (Azure/AWS)",
        "Standard server migration (no mainframe)",
        "3-year commit for cloud pricing",
    ],
    required_drivers=["servers", "vms", "data_centers"],
)

# -----------------------------------------------------------------------------
# Model 8: PMO/Transition Management
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.PMO_TRANSITION] = CostModel(
    work_item_type=WorkItemType.PMO_TRANSITION,
    display_name="PMO & Transition Management",
    tower="PMO",

    # PMO is typically a % of total program cost
    base_services_cost=250_000,  # Core PMO team
    per_site_cost=10_000,  # Per-site change management

    complexity_multipliers={
        "low": 0.8,    # Small scope
        "medium": 1.0, # Standard carveout
        "high": 1.3,   # Large, multi-region
    },

    licenses=[],  # No licenses

    typical_months=12,  # Spans full program
    source="internal_default",
    notes="PMO typically 10-15% of total program cost.",
    assumptions=[
        "Dedicated PM and 2 workstream leads",
        "Change management included",
        "12-month program duration",
    ],
    required_drivers=["sites", "total_users"],
)

# -----------------------------------------------------------------------------
# Model 9: Application Migration (Doc 03: Multi-Tier Cost Model)
# -----------------------------------------------------------------------------
COST_MODELS[WorkItemType.APPLICATION_MIGRATION] = CostModel(
    work_item_type=WorkItemType.APPLICATION_MIGRATION,
    display_name="Application Migration & Integration",
    tower="Applications",

    # Base cost per application
    base_services_cost=20_000,  # Base migration effort per app

    # NOTE: This model uses multipliers, not per-unit costs
    # Cost is calculated per-application based on:
    # - Complexity tier (simple 0.5x, medium 1.0x, complex 2.0x, critical 3.0x)
    # - Category (ERP 2.5x, CRM 1.8x, collaboration 0.8x, etc.)
    # - Deployment type (SaaS 0.3x, on-prem 1.5x, custom 2.0x)
    # - Deal type (acquisition 1.0x, carveout 1.8x, divestiture 2.2x)
    # + Integration costs (APIs, SSO, data migration, custom interfaces)
    # + TSA costs (carveouts only, for parent-hosted apps)

    # Complexity multipliers (applied to base cost)
    complexity_multipliers={
        "low": 0.5,    # Simple SaaS tools (chat, collaboration)
        "medium": 1.0, # Standard business applications
        "high": 2.0,   # Integrated systems, custom platforms
    },

    # No per-unit costs - cost is per-application calculated from inventory
    # using the APPLICATION_MIGRATION_COST_CALCULATOR in calculator.py

    licenses=[],  # Application-specific licenses calculated separately

    typical_months=6,  # 6-month average migration timeline
    source="spec:applications-enhancement/03-application-cost-model.md",
    notes=(
        "Multi-tier cost model with complexity, category, and deployment multipliers. "
        "Cost calculated per-application from InventoryStore. "
        "See services/cost_engine/application_costs.py for detailed logic."
    ),
    assumptions=[
        "Base cost $20K per application",
        "Complexity tiers: simple 0.5x, medium 1.0x, complex 2.0x, critical 3.0x",
        "Category multipliers: ERP 2.5x, CRM 1.8x, collaboration 0.8x, etc.",
        "Deployment multipliers: SaaS 0.3x, on-prem 1.5x, custom 2.0x",
        "Integration costs: $2K per API, $5K for SSO, $10K per 100GB data",
        "TSA costs: $500-$5K/month for carveouts with parent-hosted apps",
    ],
    required_drivers=["applications"],  # Count from inventory
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_model(work_item_type: str) -> Optional[CostModel]:
    """Get a cost model by work item type string."""
    try:
        wit = WorkItemType(work_item_type)
        return COST_MODELS.get(wit)
    except ValueError:
        logger.warning(f"Unknown work item type: {work_item_type}")
        return None


def get_all_models() -> List[CostModel]:
    """Get all cost models."""
    return list(COST_MODELS.values())


def get_models_by_tower(tower: str) -> List[CostModel]:
    """Get all cost models for a tower."""
    return [m for m in COST_MODELS.values() if m.tower.lower() == tower.lower()]


def get_tower_summary() -> Dict[str, int]:
    """Get count of models per tower."""
    summary = {}
    for model in COST_MODELS.values():
        tower = model.tower
        summary[tower] = summary.get(tower, 0) + 1
    return summary


# =============================================================================
# DEAL TYPE COST MULTIPLIERS
# =============================================================================

# Deal Type Cost Multipliers
# Applied to base effort estimates based on deal structure

DEAL_TYPE_MULTIPLIERS = {
    'acquisition': {
        # Acquisition = consolidation path (baseline)
        'identity_separation': 1.0,        # Extend existing IAM
        'application_migration': 1.0,      # Migrate to buyer infra
        'infrastructure_consolidation': 1.0,
        'network_integration': 1.0,
        'cybersecurity_harmonization': 1.0,
        'org_restructuring': 1.0
    },
    'carveout': {
        # Carve-out = build standalone systems (HIGHER costs)
        'identity_separation': 2.5,        # Build NEW IAM from scratch
        'application_migration': 1.8,      # Standup new environments
        'infrastructure_consolidation': 2.0,  # Build new datacenter/cloud
        'network_integration': 2.2,        # New WAN/connectivity
        'cybersecurity_harmonization': 1.9,   # New security stack
        'org_restructuring': 1.6           # More disruption to target
    },
    'divestiture': {
        # Divestiture = clean separation (HIGHEST costs)
        'identity_separation': 3.0,        # Full identity extraction
        'application_migration': 2.2,      # Extract from shared systems
        'infrastructure_consolidation': 2.5,
        'network_integration': 2.8,        # Complex untangling
        'cybersecurity_harmonization': 2.3,
        'org_restructuring': 2.0           # Maximum disruption
    }
}


def get_deal_type_multiplier(deal_type: str, work_item_category: str) -> float:
    """
    Get cost multiplier for a work item category based on deal type.

    Args:
        deal_type: One of ['acquisition', 'carveout', 'divestiture']
        work_item_category: Category key from DEAL_TYPE_MULTIPLIERS

    Returns:
        Multiplier (1.0 = baseline, >1.0 = higher complexity)

    Raises:
        ValueError: If deal_type or category invalid
    """
    if deal_type not in DEAL_TYPE_MULTIPLIERS:
        raise ValueError(f"Invalid deal_type: {deal_type}. Must be one of {list(DEAL_TYPE_MULTIPLIERS.keys())}")

    multipliers = DEAL_TYPE_MULTIPLIERS[deal_type]

    # Map work item categories to multiplier keys
    # (Work items may have different naming than multiplier keys)
    category_mapping = {
        'identity': 'identity_separation',
        'application': 'application_migration',
        'applications': 'application_migration',
        'infrastructure': 'infrastructure_consolidation',
        'network': 'network_integration',
        'cybersecurity': 'cybersecurity_harmonization',
        'organization': 'org_restructuring',
        'org': 'org_restructuring'
    }

    multiplier_key = category_mapping.get(work_item_category.lower(), 'infrastructure_consolidation')
    return multipliers.get(multiplier_key, 1.0)
