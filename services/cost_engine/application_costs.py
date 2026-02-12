"""
Application Cost Model Helper Functions

Implements complexity classification, deployment type detection,
integration cost calculation, and TSA cost modeling for applications.

Part of: specs/applications-enhancement/03-application-cost-model.md
"""

from typing import Dict, Optional
from stores.inventory_item import InventoryItem

# =============================================================================
# COST MODEL CONSTANTS
# =============================================================================

# Complexity tier multipliers
COMPLEXITY_MULTIPLIERS = {
    'simple': 0.5,      # Basic tools, low risk (chat, collaboration)
    'medium': 1.0,      # Standard applications (default)
    'complex': 2.0,     # Integrated systems, custom platforms
    'critical': 3.0     # ERP, core business systems
}

# Deployment type multipliers
DEPLOYMENT_TYPE_MULTIPLIERS = {
    'saas': 0.3,        # Subscription transfer, config export/import
    'on_prem': 1.5,     # Hardware migration, network reconfiguration
    'hybrid': 1.2,      # Mix of cloud and on-prem components
    'custom': 2.0,      # Custom-built, self-hosted
    'cloud_iaas': 1.0,  # Cloud-hosted but not SaaS (IaaS/PaaS)
    'unknown': 1.0
}

# Integration cost drivers
INTEGRATION_COST_DRIVERS = {
    'api_integrations': {
        'cost_per_integration': 2000,
        'unit': 'per API integration'
    },
    'sso_integration': {
        'cost_per_app': 5000,
        'unit': 'per application (one-time)'
    },
    'data_migration': {
        'cost_per_100gb': 10000,
        'unit': 'per 100 GB of data'
    },
    'custom_interfaces': {
        'cost_per_interface': 15000,
        'unit': 'per custom integration (file feeds, etc.)'
    }
}

# Known SaaS vendors for deployment type detection
SAAS_VENDORS = [
    'salesforce', 'slack', 'microsoft 365', 'google workspace', 'office 365',
    'zoom', 'dropbox', 'box', 'asana', 'jira cloud', 'confluence cloud',
    'monday.com', 'notion', 'airtable', 'hubspot', 'zendesk', 'intercom',
    'workday', 'servicenow', 'snowflake', 'datadog', 'okta'
]

# TSA monthly cost by complexity tier
TSA_MONTHLY_COST_BASE = {
    'simple': 500,      # $500/month for simple apps
    'medium': 1500,     # $1,500/month for medium apps
    'complex': 3000,    # $3,000/month for complex apps
    'critical': 5000    # $5,000/month for critical apps
}


# =============================================================================
# COMPLEXITY CLASSIFICATION
# =============================================================================

def classify_complexity(app: InventoryItem) -> str:
    """
    Classify application complexity based on attributes.

    Priority:
    1. Explicit 'complexity' field from enrichment
    2. Infer from category (ERP → critical, etc.)
    3. Infer from user count and integrations
    4. Default to 'medium'

    Args:
        app: InventoryItem with application data

    Returns:
        "simple" | "medium" | "complex" | "critical"
    """
    # Explicit complexity from enrichment
    if app.data.get('complexity'):
        complexity = app.data['complexity'].lower()
        if complexity in COMPLEXITY_MULTIPLIERS:
            return complexity

    # Infer from category
    category = app.data.get('category', 'unknown').lower()

    # Critical applications (ERP, core systems)
    critical_categories = ['erp', 'financial', 'core_business', 'supply_chain', 'manufacturing']
    if category in critical_categories:
        return 'critical'

    # Complex applications (high user count, many integrations)
    users = _parse_user_count(app.data.get('users', 0))
    api_count = app.data.get('api_integrations', 0)

    if users > 1000 or api_count > 5:
        return 'complex'

    # Simple applications (low user count, SaaS, no integrations)
    deployment_type = app.data.get('deployment_type', 'unknown')
    simple_categories = ['collaboration', 'productivity', 'communication', 'file_sharing']

    if users < 50 and deployment_type == 'saas' and category in simple_categories:
        return 'simple'

    # Default to medium
    return 'medium'


def _parse_user_count(users) -> int:
    """Parse user count from various formats (int, string, range)."""
    if isinstance(users, int):
        return users

    if isinstance(users, str):
        # Extract number from strings like "500 users", "100-200", "~1000"
        import re
        # Try to find first number
        match = re.search(r'(\d+)', users.replace(',', ''))
        if match:
            return int(match.group(1))

    return 0


# =============================================================================
# DEPLOYMENT TYPE DETECTION
# =============================================================================

def detect_deployment_type(app: InventoryItem) -> str:
    """
    Detect deployment type from application attributes.

    Priority:
    1. Explicit 'deployment_type' field from enrichment
    2. Infer from known SaaS vendors
    3. Infer from category (custom → custom)
    4. Infer from hosted_by_parent flag
    5. Default to 'unknown'

    Args:
        app: InventoryItem with application data

    Returns:
        "saas" | "on_prem" | "hybrid" | "custom" | "cloud_iaas" | "unknown"
    """
    # Explicit field from enrichment
    if app.data.get('deployment_type'):
        dtype = app.data['deployment_type'].lower()
        if dtype in DEPLOYMENT_TYPE_MULTIPLIERS:
            return dtype

    # Infer from vendor
    vendor = app.data.get('vendor', '').lower()

    # Known SaaS vendors
    if any(saas_vendor in vendor for saas_vendor in SAAS_VENDORS):
        return 'saas'

    # Infer from category
    category = app.data.get('category', 'unknown').lower()

    if category == 'custom':
        return 'custom'

    # Hosted by parent (from inventory) implies on-prem or custom
    if app.data.get('hosted_by_parent'):
        return 'on_prem'  # Conservative assumption

    # Hosting field hints
    hosting = app.data.get('hosting', '').lower()
    if 'cloud' in hosting or 'saas' in hosting:
        return 'saas'
    if 'on-prem' in hosting or 'on prem' in hosting or 'premise' in hosting:
        return 'on_prem'
    if 'hybrid' in hosting:
        return 'hybrid'

    # Default unknown
    return 'unknown'


# =============================================================================
# INTEGRATION COST CALCULATION
# =============================================================================

def calculate_integration_costs(app: InventoryItem) -> Dict[str, int]:
    """
    Calculate integration-specific costs for application.

    Costs are additive on top of base migration cost.

    Args:
        app: InventoryItem with application data

    Returns:
        {
            'api_integration_cost': int,
            'sso_cost': int,
            'data_migration_cost': int,
            'custom_interface_cost': int,
            'total_integration_cost': int
        }
    """
    costs = {}

    # API integrations
    api_count = app.data.get('api_integrations', 0)
    costs['api_integration_cost'] = int(api_count) * INTEGRATION_COST_DRIVERS['api_integrations']['cost_per_integration']

    # SSO integration (boolean)
    sso_required = app.data.get('sso_required', False)
    costs['sso_cost'] = INTEGRATION_COST_DRIVERS['sso_integration']['cost_per_app'] if sso_required else 0

    # Data migration (based on volume)
    data_volume_gb = app.data.get('data_volume_gb', 0)
    costs['data_migration_cost'] = int((float(data_volume_gb) / 100) * INTEGRATION_COST_DRIVERS['data_migration']['cost_per_100gb'])

    # Custom interfaces
    custom_interfaces = app.data.get('custom_interfaces', 0)
    costs['custom_interface_cost'] = int(custom_interfaces) * INTEGRATION_COST_DRIVERS['custom_interfaces']['cost_per_interface']

    # Total
    costs['total_integration_cost'] = sum([
        costs['api_integration_cost'],
        costs['sso_cost'],
        costs['data_migration_cost'],
        costs['custom_interface_cost']
    ])

    return costs


# =============================================================================
# TSA COST FOR PARENT-HOSTED APPS (CARVEOUTS)
# =============================================================================

def calculate_tsa_cost(
    app: InventoryItem,
    deal_type: str,
    tsa_duration_months: int = 12
) -> Dict[str, int]:
    """
    Calculate TSA cost for parent-hosted applications in carveouts.

    TSA = Transition Service Agreement (parent continues hosting for fee)

    Only applies to carveouts/divestitures with hosted_by_parent=True.

    Args:
        app: InventoryItem with application data
        deal_type: Deal type (acquisition, carveout, divestiture, merger)
        tsa_duration_months: Duration of TSA in months (default 12)

    Returns:
        {
            'tsa_monthly_cost': int,
            'total_tsa_cost': int
        }
    """
    # Only applies to carveouts/divestitures
    if deal_type.lower() not in ['carveout', 'divestiture']:
        return {
            'tsa_monthly_cost': 0,
            'total_tsa_cost': 0
        }

    # Only if hosted by parent
    if not app.data.get('hosted_by_parent', False):
        return {
            'tsa_monthly_cost': 0,
            'total_tsa_cost': 0
        }

    # TSA cost = estimated monthly hosting + overhead
    # Based on complexity and user count
    complexity = classify_complexity(app)
    users = _parse_user_count(app.data.get('users', 0))

    # Monthly TSA cost model
    base_monthly = TSA_MONTHLY_COST_BASE.get(complexity, 1500)

    # User-based scaling (+50% per 1000 users)
    user_factor = 1 + (users / 1000) * 0.5

    monthly_tsa = int(base_monthly * user_factor)

    # Total over TSA duration
    total_tsa = monthly_tsa * tsa_duration_months

    return {
        'tsa_monthly_cost': monthly_tsa,
        'total_tsa_cost': total_tsa
    }


# =============================================================================
# MULTIPLIER GETTER FUNCTIONS
# =============================================================================

def get_complexity_multiplier(complexity: str) -> float:
    """Get multiplier for complexity tier."""
    return COMPLEXITY_MULTIPLIERS.get(complexity.lower(), 1.0)


def get_deployment_multiplier(deployment_type: str) -> float:
    """Get multiplier for deployment type."""
    return DEPLOYMENT_TYPE_MULTIPLIERS.get(deployment_type.lower(), 1.0)


# =============================================================================
# PER-APPLICATION COST CALCULATION (Doc 04)
# =============================================================================

def calculate_application_cost(
    app: 'InventoryItem',
    deal_type: str,
    tsa_duration_months: int = 12
) -> 'ApplicationCost':
    """
    Calculate migration cost for single application using multi-tier model.

    Args:
        app: InventoryItem from inventory store
        deal_type: 'acquisition' | 'carveout' | 'divestiture'
        tsa_duration_months: TSA duration for carveouts (default 12)

    Returns:
        ApplicationCost with detailed breakdown
    """
    from services.cost_engine.models import ApplicationCost, get_deal_type_multiplier
    from stores.app_category_mappings import get_category_cost_multiplier

    # Classify complexity
    complexity = classify_complexity(app)
    complexity_multiplier = get_complexity_multiplier(complexity)

    # Get category multiplier
    category = app.data.get('category', 'unknown')
    category_multiplier = get_category_cost_multiplier(category)

    # Get deployment multiplier
    deployment_type = detect_deployment_type(app)
    deployment_multiplier = get_deployment_multiplier(deployment_type)

    # Get deal type multiplier (from existing deal-type awareness system)
    deal_multiplier = get_deal_type_multiplier(deal_type, 'application')

    # Base cost calculation
    base_cost = 20000  # $20K base per app
    one_time_base = int(
        base_cost *
        complexity_multiplier *
        category_multiplier *
        deployment_multiplier *
        deal_multiplier
    )

    # Integration costs
    integration_costs_dict = calculate_integration_costs(app)
    integration_total = integration_costs_dict['total_integration_cost']

    # TSA costs (carveouts only)
    tsa_result = calculate_tsa_cost(app, deal_type, tsa_duration_months)
    tsa_total = tsa_result['total_tsa_cost']
    tsa_monthly = tsa_result['tsa_monthly_cost']

    # Total
    one_time_total = one_time_base + integration_total
    grand_total = one_time_total + tsa_total

    return ApplicationCost(
        app_name=app.data.get('name', 'Unknown'),
        app_id=app.item_id,
        complexity=complexity,
        category=category,
        deployment_type=deployment_type,
        one_time_base=one_time_base,
        integration_costs=integration_costs_dict,
        integration_total=integration_total,
        tsa_monthly=tsa_monthly,
        tsa_total=tsa_total,
        one_time_total=one_time_total,
        grand_total=grand_total,
        cost_breakdown={
            'base_cost': base_cost,
            'complexity': complexity,
            'complexity_multiplier': complexity_multiplier,
            'category': category,
            'category_multiplier': category_multiplier,
            'deployment_type': deployment_type,
            'deployment_multiplier': deployment_multiplier,
            'deal_type': deal_type,
            'deal_multiplier': deal_multiplier,
            'one_time_base': one_time_base,
            **integration_costs_dict,
            'tsa_monthly': tsa_monthly,
            'tsa_total': tsa_total,
            'tsa_duration_months': tsa_duration_months
        }
    )


# =============================================================================
# AGGREGATE INVENTORY COST CALCULATION (Doc 04)
# =============================================================================

def calculate_application_costs_from_inventory(
    inventory_store: 'InventoryStore',
    deal_type: str = 'acquisition',
    entity: str = 'target',
    tsa_duration_months: int = 12
) -> 'ApplicationCostSummary':
    """
    Calculate total application migration costs from inventory.

    Args:
        inventory_store: InventoryStore instance
        deal_type: 'acquisition' | 'carveout' | 'divestiture'
        entity: 'target' | 'buyer'
        tsa_duration_months: TSA duration for carveouts (default 12)

    Returns:
        ApplicationCostSummary with per-app breakdown and totals
    """
    from services.cost_engine.models import ApplicationCostSummary

    # Get all applications for entity
    apps = inventory_store.get_items(
        inventory_type='application',
        entity=entity,
        status='active'
    )

    if not apps:
        return ApplicationCostSummary(
            total_one_time=0,
            total_tsa=0,
            total_integration=0,
            app_costs=[],
            app_count=0,
            deal_type=deal_type,
            entity=entity
        )

    app_costs = []

    for app in apps:
        # Calculate cost for this application
        app_cost = calculate_application_cost(
            app=app,
            deal_type=deal_type,
            tsa_duration_months=tsa_duration_months
        )
        app_costs.append(app_cost)

    # Aggregate
    total_one_time = sum(ac.one_time_total for ac in app_costs)
    total_tsa = sum(ac.tsa_total for ac in app_costs)
    total_integration = sum(ac.integration_total for ac in app_costs)

    return ApplicationCostSummary(
        total_one_time=total_one_time,
        total_tsa=total_tsa,
        total_integration=total_integration,
        app_costs=app_costs,
        app_count=len(apps),
        deal_type=deal_type,
        entity=entity
    )
