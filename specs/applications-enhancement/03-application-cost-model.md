# Application Cost Model

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** 00-overview-applications-enhancement.md
**Enables:** 04-cost-engine-inventory-integration.md
**Estimated Scope:** 4-5 hours

---

## Overview

**Problem:** Current application cost model is a stub placeholder using naive $5K/app linear formula. No complexity tiers, no category awareness, no integration costs. Results in 2-10x underestimation.

**Solution:** Multi-tier complexity-based cost model with category multipliers, deployment type adjustments, and integration complexity modeling.

**Why this exists:** Applications typically represent 40-60% of M&A integration costs. Accurate cost estimation requires understanding that migrating SAP ERP ≠ migrating Slack.

---

## Architecture

### Current Model (Stub)

```python
# services/cost_engine/models.py
WorkItemType.APPLICATION_MIGRATION: CostModel(
    work_item_type=WorkItemType.APPLICATION_MIGRATION,
    base_cost=50000,
    drivers={
        'applications': CostDriver(
            name='applications',
            coefficient=5000,  # $5k per app - PLACEHOLDER
            unit='per application'
        )
    },
    description="Application migration and integration - PLACEHOLDER MODEL"
)
```

**Cost calculation:**
```
Cost = $50K + ($5K × app_count)
```

**Failures:**
- Treats all apps equally (ERP = chat tool = $5K)
- No complexity tiers
- No category awareness
- No deployment type (SaaS vs on-prem)
- No integration complexity (APIs, data migration, SSO)
- No deal type consideration (already fixed separately)

### Target Model (Multi-Tier)

```python
# Complexity tiers based on application attributes
ApplicationComplexity:
    SIMPLE = 0.5x      # Chat, collaboration, simple tools
    MEDIUM = 1.0x      # Standard business apps
    COMPLEX = 2.0x     # Integrated systems, custom platforms
    CRITICAL = 3.0x    # ERP, core business systems

# Category multipliers
CategoryMultiplier:
    erp = 2.5x               # Enterprise Resource Planning
    crm = 1.8x               # Customer Relationship Management
    financial = 2.0x         # Financial systems
    hr = 1.5x                # Human Resources
    collaboration = 0.8x     # Slack, Teams, email
    productivity = 0.6x      # Office tools
    custom = 2.0x            # Custom-built applications
    saas = 0.5x              # Simple SaaS (if standalone)
    infrastructure = 1.2x    # Monitoring, management tools

# Deployment type multipliers
DeploymentMultiplier:
    saas = 0.3x        # Subscription transfer, config migration
    on_prem = 1.5x     # Full replatform, hardware migration
    hybrid = 1.2x      # Partial cloud, partial on-prem
    custom = 2.0x      # Custom-built, no vendor support

# Integration complexity drivers
IntegrationComplexity:
    api_integrations = $2K per integration
    sso_integration = $5K (one-time)
    data_migration = $10K per 100GB
    custom_interfaces = $15K per interface
```

**Cost calculation:**
```
For each application:
    base_cost = $20K

    # Complexity tier
    complexity_multiplier = get_complexity(app.complexity)

    # Category multiplier
    category_multiplier = get_category_multiplier(app.category)

    # Deployment type
    deployment_multiplier = get_deployment_multiplier(app.deployment_type)

    # Deal type (from existing system)
    deal_multiplier = get_deal_type_multiplier(deal_type, 'application')

    # Integration costs
    integration_cost = (
        app.api_integrations * $2K +
        app.sso_required * $5K +
        app.data_volume_gb / 100 * $10K +
        app.custom_interfaces * $15K
    )

    # TSA cost for carveouts with parent-hosted apps
    tsa_cost = 0
    if deal_type == 'carveout' and app.hosted_by_parent:
        tsa_cost = $3K per month × tsa_duration_months

    # Total
    app_cost = (
        base_cost ×
        complexity_multiplier ×
        category_multiplier ×
        deployment_multiplier ×
        deal_multiplier
    ) + integration_cost + tsa_cost
```

**Example:**

```
SAP ERP (Target, Carveout):
    base: $20K
    complexity: 3.0x (critical)
    category: 2.5x (erp)
    deployment: 1.5x (on-prem)
    deal_type: 1.8x (carveout)
    integration: $10K (2 APIs) + $5K (SSO) + $50K (500GB data) = $65K
    tsa: $0 (not hosted by parent)

    Total = ($20K × 3.0 × 2.5 × 1.5 × 1.8) + $65K
          = $405K + $65K
          = $470K

Slack (Target, Acquisition):
    base: $20K
    complexity: 0.5x (simple)
    category: 0.8x (collaboration)
    deployment: 0.3x (saas)
    deal_type: 1.0x (acquisition)
    integration: $5K (SSO only)
    tsa: $0

    Total = ($20K × 0.5 × 0.8 × 0.3 × 1.0) + $5K
          = $2.4K + $5K
          = $7.4K

Ratio: SAP/Slack = $470K / $7.4K = 63x
```

This 63x variance is realistic for ERP vs collaboration tool migration.

---

## Specification

### 1. Complexity Classification

**Automatic detection based on inventory attributes:**

```python
def classify_complexity(app: InventoryItem) -> str:
    """
    Classify application complexity based on attributes.

    Returns: "simple" | "medium" | "complex" | "critical"
    """
    # Explicit complexity from enrichment
    if app.data.get('complexity'):
        return app.data['complexity']

    # Infer from category and other attributes
    category = app.data.get('category', 'unknown')
    users = app.data.get('users', 0)

    # Critical applications (ERP, core systems)
    if category in ['erp', 'financial', 'core_business']:
        return 'critical'

    # Complex applications (high user count, integrations)
    if users > 1000 or app.data.get('api_integrations', 0) > 5:
        return 'complex'

    # Simple applications (low user count, SaaS, no integrations)
    if users < 50 and app.data.get('deployment_type') == 'saas':
        return 'simple'

    # Default to medium
    return 'medium'
```

**Complexity tier multipliers:**

```python
COMPLEXITY_MULTIPLIERS = {
    'simple': 0.5,      # Basic tools, low risk
    'medium': 1.0,      # Standard applications
    'complex': 2.0,     # Integrated systems
    'critical': 3.0     # Core business systems
}
```

### 2. Category Multipliers

**Integration with existing category mappings:**

```python
# Extends stores/app_category_mappings.py
CATEGORY_COST_MULTIPLIERS = {
    # High complexity, high business impact
    'erp': 2.5,
    'financial': 2.0,
    'crm': 1.8,
    'supply_chain': 2.2,
    'manufacturing': 2.0,

    # Medium complexity
    'hr': 1.5,
    'business_intelligence': 1.5,
    'data_analytics': 1.5,
    'custom': 2.0,              # Custom-built (no vendor support)
    'infrastructure': 1.2,

    # Lower complexity, often SaaS
    'collaboration': 0.8,
    'productivity': 0.6,
    'communication': 0.7,
    'file_sharing': 0.5,

    # Default
    'unknown': 1.0
}
```

**Rationale:**
- ERP/financial systems require extensive testing, data validation, regulatory compliance
- Collaboration tools often have simple migration paths (SaaS subscription transfer)
- Custom applications require code migration, no vendor support

### 3. Deployment Type Multipliers

**New field in inventory schema:**

```python
# InventoryItem.data['deployment_type']
DEPLOYMENT_TYPE_MULTIPLIERS = {
    'saas': 0.3,        # Subscription transfer, config export/import
    'on_prem': 1.5,     # Hardware migration, network reconfiguration
    'hybrid': 1.2,      # Mix of cloud and on-prem components
    'custom': 2.0,      # Custom-built, self-hosted
    'cloud_iaas': 1.0,  # Cloud-hosted but not SaaS (IaaS/PaaS)
    'unknown': 1.0
}
```

**Deployment type detection:**

```python
def detect_deployment_type(app: InventoryItem) -> str:
    """
    Detect deployment type from application attributes.

    Returns: "saas" | "on_prem" | "hybrid" | "custom" | "cloud_iaas" | "unknown"
    """
    # Explicit field from enrichment
    if app.data.get('deployment_type'):
        return app.data['deployment_type']

    # Infer from vendor and category
    vendor = app.data.get('vendor', '').lower()
    category = app.data.get('category', 'unknown')

    # Known SaaS vendors
    saas_vendors = [
        'salesforce', 'slack', 'microsoft 365', 'google workspace',
        'zoom', 'dropbox', 'box', 'asana', 'jira cloud'
    ]
    if any(v in vendor for v in saas_vendors):
        return 'saas'

    # Custom category implies custom deployment
    if category == 'custom':
        return 'custom'

    # Hosted by parent (from inventory) implies on-prem or custom
    if app.data.get('hosted_by_parent'):
        return 'on_prem'  # Conservative assumption

    # Default unknown
    return 'unknown'
```

### 4. Integration Complexity Modeling

**Integration cost drivers:**

```python
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

def calculate_integration_costs(app: InventoryItem) -> Dict[str, int]:
    """
    Calculate integration-specific costs for application.

    Returns: {
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
    costs['api_integration_cost'] = api_count * 2000

    # SSO integration (boolean)
    sso_required = app.data.get('sso_required', False)
    costs['sso_cost'] = 5000 if sso_required else 0

    # Data migration (based on volume)
    data_volume_gb = app.data.get('data_volume_gb', 0)
    costs['data_migration_cost'] = (data_volume_gb / 100) * 10000

    # Custom interfaces
    custom_interfaces = app.data.get('custom_interfaces', 0)
    costs['custom_interface_cost'] = custom_interfaces * 15000

    # Total
    costs['total_integration_cost'] = sum([
        costs['api_integration_cost'],
        costs['sso_cost'],
        costs['data_migration_cost'],
        costs['custom_interface_cost']
    ])

    return costs
```

### 5. TSA Cost for Parent-Hosted Apps (Carveouts)

**Carveout-specific cost driver:**

```python
def calculate_tsa_cost(
    app: InventoryItem,
    deal_type: str,
    tsa_duration_months: int = 12
) -> int:
    """
    Calculate TSA cost for parent-hosted applications in carveouts.

    TSA = Transition Service Agreement (parent continues hosting for fee)

    Returns: Monthly TSA cost × duration
    """
    # Only applies to carveouts/divestitures
    if deal_type not in ['carveout', 'divestiture']:
        return 0

    # Only if hosted by parent
    if not app.data.get('hosted_by_parent', False):
        return 0

    # TSA cost = estimated monthly hosting + overhead
    # Base on complexity and user count
    users = app.data.get('users', 0)
    complexity = classify_complexity(app)

    # Monthly TSA cost model
    base_monthly = {
        'simple': 500,
        'medium': 1500,
        'complex': 3000,
        'critical': 5000
    }[complexity]

    # User-based scaling
    user_factor = 1 + (users / 1000) * 0.5  # +50% per 1000 users

    monthly_tsa = base_monthly * user_factor

    # Total over TSA duration
    return monthly_tsa * tsa_duration_months
```

### 6. Complete Cost Model Implementation

**CostModel definition:**

```python
# services/cost_engine/models.py

APPLICATION_MIGRATION_MODEL = CostModel(
    work_item_type=WorkItemType.APPLICATION_MIGRATION,
    base_cost=20000,  # Base per application
    drivers={
        'complexity': CostDriver(
            name='complexity',
            coefficient_map=COMPLEXITY_MULTIPLIERS,
            unit='complexity tier'
        ),
        'category': CostDriver(
            name='category',
            coefficient_map=CATEGORY_COST_MULTIPLIERS,
            unit='application category'
        ),
        'deployment_type': CostDriver(
            name='deployment_type',
            coefficient_map=DEPLOYMENT_TYPE_MULTIPLIERS,
            unit='deployment model'
        ),
        'api_integrations': CostDriver(
            name='api_integrations',
            coefficient=2000,
            unit='per integration'
        ),
        'sso_required': CostDriver(
            name='sso_required',
            coefficient=5000,
            unit='boolean (one-time)'
        ),
        'data_migration': CostDriver(
            name='data_migration',
            coefficient=100,  # Per GB (10K per 100GB)
            unit='per GB'
        ),
        'custom_interfaces': CostDriver(
            name='custom_interfaces',
            coefficient=15000,
            unit='per interface'
        ),
        'tsa_months': CostDriver(
            name='tsa_months',
            coefficient_map='complexity_based',  # Variable by complexity
            unit='per month (carveouts only)'
        )
    },
    description="Application migration with complexity tiers, category awareness, and integration costs"
)
```

---

## Verification Strategy

### Unit Tests

```python
# tests/unit/test_application_cost_model.py

def test_simple_saas_app_low_cost():
    """Simple SaaS collaboration tool has minimal migration cost."""
    app = InventoryItem(
        item_id="APP-001",
        inventory_type="application",
        entity="target",
        data={
            'name': 'Slack',
            'category': 'collaboration',
            'complexity': 'simple',
            'deployment_type': 'saas',
            'users': 500
        }
    )

    cost = calculate_application_cost(app, deal_type='acquisition')

    # Base $20K × 0.5 (simple) × 0.8 (collab) × 0.3 (saas) × 1.0 (acquisition)
    expected = 20000 * 0.5 * 0.8 * 0.3 * 1.0
    assert cost.one_time_base == pytest.approx(expected, rel=0.05)
    assert cost.one_time_base < 5000  # Should be <$5K

def test_critical_erp_on_prem_high_cost():
    """Critical on-prem ERP has high migration cost."""
    app = InventoryItem(
        item_id="APP-002",
        inventory_type="application",
        entity="target",
        data={
            'name': 'SAP ERP',
            'category': 'erp',
            'complexity': 'critical',
            'deployment_type': 'on_prem',
            'users': 5000,
            'api_integrations': 10,
            'sso_required': True,
            'data_volume_gb': 500
        }
    )

    cost = calculate_application_cost(app, deal_type='carveout')

    # Base: $20K × 3.0 (critical) × 2.5 (erp) × 1.5 (on-prem) × 1.8 (carveout)
    # = $405K
    # Integration: 10×$2K + $5K + 500/100×$10K = $20K + $5K + $50K = $75K
    # Total ~$480K

    assert cost.one_time_base > 400000
    assert cost.one_time_base < 600000

def test_tsa_cost_for_parent_hosted_carveout():
    """Parent-hosted app in carveout incurs TSA costs."""
    app = InventoryItem(
        item_id="APP-003",
        inventory_type="application",
        entity="target",
        data={
            'name': 'Shared ERP',
            'category': 'erp',
            'complexity': 'critical',
            'hosted_by_parent': True,
            'users': 1000
        }
    )

    cost = calculate_application_cost(
        app,
        deal_type='carveout',
        tsa_duration_months=12
    )

    # TSA should be present
    assert cost.tsa_monthly_cost > 0
    assert cost.total_tsa_cost == cost.tsa_monthly_cost * 12

def test_no_tsa_for_acquisition():
    """Acquisitions don't incur TSA costs even if hosted by parent."""
    app = InventoryItem(
        item_id="APP-004",
        inventory_type="application",
        entity="target",
        data={
            'name': 'Shared App',
            'hosted_by_parent': True,
            'complexity': 'medium'
        }
    )

    cost = calculate_application_cost(app, deal_type='acquisition')

    assert cost.total_tsa_cost == 0

def test_category_multiplier_variance():
    """Different categories have different cost multipliers."""
    base_app_data = {
        'complexity': 'medium',
        'deployment_type': 'cloud_iaas',
        'users': 500
    }

    # ERP should cost 2.5x more than collaboration
    erp_app = InventoryItem(
        item_id="APP-ERP",
        inventory_type="application",
        entity="target",
        data={**base_app_data, 'category': 'erp'}
    )

    collab_app = InventoryItem(
        item_id="APP-COLLAB",
        inventory_type="application",
        entity="target",
        data={**base_app_data, 'category': 'collaboration'}
    )

    erp_cost = calculate_application_cost(erp_app, 'acquisition')
    collab_cost = calculate_application_cost(collab_app, 'acquisition')

    # ERP multiplier 2.5 / collaboration multiplier 0.8 = 3.125x
    ratio = erp_cost.one_time_base / collab_cost.one_time_base
    assert ratio == pytest.approx(2.5 / 0.8, rel=0.05)
```

### Integration Tests

```python
# tests/integration/test_application_cost_end_to_end.py

def test_deal_cost_varies_by_app_portfolio():
    """Deal with complex apps costs more than simple app portfolio."""
    inv_store_complex = InventoryStore(deal_id="complex")
    inv_store_simple = InventoryStore(deal_id="simple")

    # Complex portfolio: ERP, CRM, custom apps
    inv_store_complex.add_item(
        inventory_type='application',
        entity='target',
        data={'name': 'SAP', 'category': 'erp', 'complexity': 'critical'}
    )
    inv_store_complex.add_item(
        inventory_type='application',
        entity='target',
        data={'name': 'Salesforce', 'category': 'crm', 'complexity': 'complex'}
    )

    # Simple portfolio: Slack, Zoom, Google Workspace
    for app in ['Slack', 'Zoom', 'Google Workspace']:
        inv_store_simple.add_item(
            inventory_type='application',
            entity='target',
            data={'name': app, 'category': 'collaboration', 'complexity': 'simple'}
        )

    # Calculate deal costs
    complex_cost = calculate_deal_application_costs(inv_store_complex, 'acquisition')
    simple_cost = calculate_deal_application_costs(inv_store_simple, 'acquisition')

    # Complex portfolio should cost significantly more (5-10x)
    assert complex_cost.total_one_time > simple_cost.total_one_time * 5
```

### Manual Verification

**Test scenarios:**

1. **Create deal with 10 simple SaaS apps**
   - ✅ Total cost should be <$100K
   - ✅ Individual apps <$10K each

2. **Create deal with 1 critical ERP on-prem**
   - ✅ Total cost should be >$300K
   - ✅ Cost breakdown shows complexity/category/deployment multipliers

3. **Create carveout deal with parent-hosted app**
   - ✅ TSA costs appear in cost summary
   - ✅ TSA duration configurable (default 12 months)

4. **Compare acquisition vs carveout for same app portfolio**
   - ✅ Carveout costs 1.5-2x more (deal_type multiplier)
   - ✅ TSA costs only appear in carveout

5. **Review cost breakdown for transparency**
   - ✅ Each multiplier shown with justification
   - ✅ Integration costs itemized separately

---

## Benefits

### Cost Accuracy
- **Variance by complexity:** 63x difference between ERP and collaboration tool (realistic)
- **Category awareness:** Financial systems cost more than productivity tools
- **Deployment matters:** SaaS migration 5x cheaper than on-prem replatform
- **Integration costs:** API, SSO, data migration explicitly modeled

### Stakeholder Confidence
- **Transparent:** Cost breakdown shows all multipliers and assumptions
- **Defensible:** Can explain why SAP costs $500K and Slack costs $8K
- **Refinable:** Multipliers can be adjusted based on historical actuals

### Business Value
- **Budget planning:** Realistic estimates for M&A budgets
- **Deal prioritization:** Understand IT cost implications upfront
- **Risk assessment:** High-cost apps flagged for deeper diligence

---

## Expectations

### Success Criteria

- [ ] Cost estimates vary 5-10x between simple and critical applications
- [ ] ERP/financial systems consistently cost >$300K in carveouts
- [ ] SaaS collaboration tools consistently cost <$10K in acquisitions
- [ ] TSA costs appear only for carveouts with parent-hosted apps
- [ ] Cost breakdown transparency: all multipliers visible in UI
- [ ] Validation against 5-10 historical deals: <±30% variance

### Assumptions to Validate

**A2 (enrichment success):** Verify enrichment populates category, complexity, deployment_type fields
- **Test:** Query 5-10 recent analysis runs, check field coverage
- **If <70% coverage:** Improve enrichment prompts or add manual review step

**A6 (cost variance acceptable):** Stakeholders accept ±30% estimate variance
- **Test:** Review with finance team, get sign-off on model
- **If rejected:** Increase model complexity (more tiers, more drivers)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Multipliers inaccurate | Medium | High | Validate against 5-10 historical deals; adjust based on actual variance |
| Enrichment fields missing | Medium | Medium | Tested in assumption A2; add defaults if fields sparse |
| Model too complex for users | Low | Medium | Cost breakdown UI explains each multiplier clearly |
| TSA duration assumption wrong | Medium | Medium | Make configurable per deal; default 12 months |
| Integration costs underestimated | Medium | High | Conservative assumptions (higher coefficients); review quarterly |

---

## Results Criteria

### Acceptance Criteria

1. **Cost model implemented** with all multipliers and drivers
2. **Complexity classification** automatic from inventory attributes
3. **Category multipliers** integrated with existing category mappings
4. **Deployment type detection** functional with fallbacks
5. **Integration costs** calculated from inventory metadata
6. **TSA costs** triggered for carveouts with hosted_by_parent=True
7. **All unit tests passing** (15+ tests covering all scenarios)
8. **Cost breakdown transparent** (all multipliers visible)

### Implementation Checklist

**Files to modify:**

- [ ] `services/cost_engine/models.py`
  - Replace APPLICATION_MIGRATION stub with full model
  - Add COMPLEXITY_MULTIPLIERS, CATEGORY_COST_MULTIPLIERS, DEPLOYMENT_TYPE_MULTIPLIERS

- [ ] `services/cost_engine/calculator.py`
  - Modify to accept InventoryItem instead of just DealDrivers
  - Add integration cost calculation
  - Add TSA cost calculation

- [ ] `stores/app_category_mappings.py`
  - Add CATEGORY_COST_MULTIPLIERS (integrate with existing mappings)

- [ ] `tests/unit/test_application_cost_model.py` (new file)
  - 15+ unit tests for cost calculations

**Files to create:**

- [ ] `services/cost_engine/application_costs.py` (optional - helper functions)
  - `classify_complexity()`
  - `detect_deployment_type()`
  - `calculate_integration_costs()`
  - `calculate_tsa_cost()`

---

## Related Documents

- **00-overview-applications-enhancement.md** - Architecture overview
- **04-cost-engine-inventory-integration.md** - Integration with InventoryStore (next)
- `specs/deal-type-awareness/03-conditional-logic.md` - Deal type multipliers
- `stores/app_category_mappings.py` - Existing category taxonomy

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 04-cost-engine-inventory-integration.md (depends on this)
