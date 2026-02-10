# Cost Model Primitives Specification

## The Problem We're Solving

Today: LLM assigns work items to 6 fixed buckets ($25K-$100K, etc.) via pattern matching.
Result: 4x ranges that don't survive IC scrutiny.

Tomorrow: Driver-based calculation with explicit inputs, defaults, and sensitivity.
Result: Numbers you can put in a model, with traceable assumptions.

---

## Architecture Overview

```
Extracted Facts (FactStore)
    ↓
Driver Extractor (pulls user counts, sites, etc. from facts)
    ↓
Work Item + Driver Binding (each work item knows what drivers it needs)
    ↓
Cost Catalog (unit prices, service ranges by complexity)
    ↓
Cost Calculator (driver × unit price × complexity factor)
    ↓
Scenario Engine (base / upside / stress)
    ↓
Cost Sheet (auditable, adjustable, model-ready)
```

---

## Core Data Structures

### 1. Drivers (extracted or assumed)

```python
@dataclass
class DealDrivers:
    """Extracted or assumed inputs that drive cost calculations."""

    # Scale drivers
    total_users: int = None           # Total employee count
    it_users: int = None              # IT staff count
    sites: int = None                 # Physical locations
    countries: int = None             # Regulatory jurisdictions

    # Application drivers
    total_apps: int = None
    erp_system: str = None            # "SAP", "Oracle", "NetSuite", etc.
    erp_users: int = None
    crm_system: str = None
    crm_users: int = None
    custom_apps: int = None
    saas_apps: int = None

    # Infrastructure drivers
    data_center_count: int = None
    server_count: int = None
    vm_count: int = None
    cloud_provider: str = None        # "AWS", "Azure", "GCP", "None"
    cloud_spend_annual: float = None
    storage_tb: float = None

    # Identity drivers
    identity_provider: str = None     # "Azure AD", "Okta", "On-prem AD"
    identity_shared_with_parent: bool = None
    mfa_deployed: bool = None
    pam_solution: str = None

    # Network drivers
    wan_type: str = None              # "MPLS", "SD-WAN", "Internet"
    wan_shared_with_parent: bool = None
    vpn_users: int = None

    # Security drivers
    edr_solution: str = None
    siem_solution: str = None
    soc_model: str = None             # "in-house", "mssp", "parent"

    # Timeline drivers
    tsa_months: int = 12              # Default assumption
    day1_date: str = None

    # Confidence tracking
    driver_sources: Dict[str, str] = field(default_factory=dict)
    # e.g., {"total_users": "F-ORG-023", "sites": "assumed_default"}
```

### 2. Work Item Types (enumerated, not free-form)

```python
class WorkItemType(Enum):
    """Standard work item types with associated cost models."""

    # Identity & Access
    IDENTITY_SEPARATION = "identity_separation"
    MFA_DEPLOYMENT = "mfa_deployment"
    PAM_IMPLEMENTATION = "pam_implementation"
    SSO_RECONFIGURATION = "sso_reconfiguration"

    # Applications
    ERP_MIGRATION = "erp_migration"
    ERP_STANDALONE_INSTANCE = "erp_standalone_instance"
    CRM_MIGRATION = "crm_migration"
    APP_RATIONALIZATION = "app_rationalization"
    SAAS_ACCOUNT_SEPARATION = "saas_account_separation"
    CUSTOM_APP_MIGRATION = "custom_app_migration"

    # Infrastructure
    DC_MIGRATION = "dc_migration"
    CLOUD_MIGRATION = "cloud_migration"
    CLOUD_ACCOUNT_SEPARATION = "cloud_account_separation"
    SERVER_MIGRATION = "server_migration"
    STORAGE_MIGRATION = "storage_migration"
    BACKUP_DR_STANDUP = "backup_dr_standup"

    # Network
    WAN_SEPARATION = "wan_separation"
    SDWAN_DEPLOYMENT = "sdwan_deployment"
    VPN_STANDUP = "vpn_standup"
    FIREWALL_DEPLOYMENT = "firewall_deployment"
    DNS_SEPARATION = "dns_separation"

    # Security
    EDR_DEPLOYMENT = "edr_deployment"
    SIEM_IMPLEMENTATION = "siem_implementation"
    VULN_MANAGEMENT_STANDUP = "vuln_management_standup"
    SOC_STANDUP = "soc_standup"
    SECURITY_POLICY_DEVELOPMENT = "security_policy_development"

    # End User Computing
    ENDPOINT_MIGRATION = "endpoint_migration"
    EMAIL_MIGRATION = "email_migration"
    COLLABORATION_MIGRATION = "collaboration_migration"

    # Organization
    IT_STAFF_AUGMENTATION = "it_staff_augmentation"
    MSP_ENGAGEMENT = "msp_engagement"
    PMO_STANDUP = "pmo_standup"

    # Data
    DATA_MIGRATION = "data_migration"
    DATA_SEPARATION = "data_separation"
    ANALYTICS_STANDUP = "analytics_standup"
```

### 3. Cost Model per Work Item Type

```python
@dataclass
class CostModel:
    """Driver-based cost model for a work item type."""

    work_item_type: WorkItemType

    # License costs (per unit per period)
    license_drivers: List[LicenseDriver]

    # Services costs (one-time implementation)
    services_base: int                    # Base cost regardless of scale
    services_per_user: float = 0          # Additional per user
    services_per_site: float = 0          # Additional per site
    services_per_app: float = 0           # Additional per app
    services_complexity_multiplier: Dict[str, float] = None  # {"low": 0.8, "medium": 1.0, "high": 1.5}

    # Transition costs
    parallel_run_months: int = 0          # Typical parallel operation period
    parallel_run_monthly: float = 0       # Monthly cost during parallel

    # Timeline
    typical_duration_months: int = 3

    # Complexity signals (from facts)
    complexity_signals: Dict[str, str] = None  # signal → complexity level

    # What drivers are required vs optional
    required_drivers: List[str] = None
    optional_drivers: List[str] = None


@dataclass
class LicenseDriver:
    """License cost component."""
    name: str                             # "Azure AD P2", "CrowdStrike Falcon"
    unit: str                             # "user", "endpoint", "server"
    price_per_unit_monthly: float
    price_per_unit_annual: float = None   # If annual discount applies
    minimum_quantity: int = 1
```

---

## Example Cost Models

### Identity Separation (Carve-out from Parent AD)

```python
IDENTITY_SEPARATION_MODEL = CostModel(
    work_item_type=WorkItemType.IDENTITY_SEPARATION,

    license_drivers=[
        LicenseDriver(
            name="Azure AD Premium P2",
            unit="user",
            price_per_unit_monthly=9.00,
        ),
        LicenseDriver(
            name="Conditional Access (included in P2)",
            unit="user",
            price_per_unit_monthly=0,
        ),
    ],

    services_base=75_000,              # Base: design, setup, testing
    services_per_user=15,              # Per-user migration effort
    services_per_site=5_000,           # Per-site config (GPOs, etc.)

    services_complexity_multiplier={
        "low": 0.8,                    # Simple: single AD domain, <500 users
        "medium": 1.0,                 # Moderate: multiple domains, some custom apps
        "high": 1.5,                   # Complex: multi-forest, heavy LDAP integration
    },

    parallel_run_months=2,             # Typical dual-directory period
    parallel_run_monthly=10_000,       # Support costs during parallel

    typical_duration_months=4,

    complexity_signals={
        "multi_forest": "high",
        "ldap_integration": "high",
        "custom_apps_using_ad": "high",
        "single_domain": "low",
        "cloud_only_apps": "low",
    },

    required_drivers=["total_users", "identity_shared_with_parent"],
    optional_drivers=["sites", "custom_apps"],
)
```

### ERP Standalone Instance (SAP Carve-out)

```python
ERP_STANDALONE_SAP_MODEL = CostModel(
    work_item_type=WorkItemType.ERP_STANDALONE_INSTANCE,

    license_drivers=[
        LicenseDriver(
            name="SAP S/4HANA Cloud",
            unit="user",
            price_per_unit_monthly=200,  # Rough avg across license types
        ),
        # Or on-prem:
        LicenseDriver(
            name="SAP Named User License (on-prem)",
            unit="user",
            price_per_unit_annual=4_000,  # Varies wildly by negotiation
        ),
    ],

    services_base=400_000,             # Base implementation services
    services_per_user=200,             # Data migration, training per user
    services_complexity_multiplier={
        "low": 0.7,                    # Greenfield, standard config
        "medium": 1.0,                 # Some customization, moderate data
        "high": 2.0,                   # Heavy custom, complex data separation
    },

    parallel_run_months=3,
    parallel_run_monthly=50_000,       # Dual ERP support

    typical_duration_months=12,

    complexity_signals={
        "custom_abap": "high",
        "multiple_company_codes": "high",
        "intercompany_transactions": "high",
        "standard_config": "low",
        "single_company_code": "low",
    },

    required_drivers=["erp_users", "erp_system"],
    optional_drivers=["custom_apps", "countries"],
)
```

### Network Separation (WAN Disentanglement)

```python
WAN_SEPARATION_MODEL = CostModel(
    work_item_type=WorkItemType.WAN_SEPARATION,

    license_drivers=[
        LicenseDriver(
            name="SD-WAN per site",
            unit="site",
            price_per_unit_monthly=500,
        ),
        LicenseDriver(
            name="Internet circuit per site",
            unit="site",
            price_per_unit_monthly=1_500,
        ),
    ],

    services_base=50_000,              # Design, project management
    services_per_site=15_000,          # Per-site implementation
    services_complexity_multiplier={
        "low": 0.8,                    # Simple hub-spoke
        "medium": 1.0,                 # Regional hubs
        "high": 1.5,                   # Complex mesh, regulatory constraints
    },

    parallel_run_months=1,
    parallel_run_monthly=5_000,        # Dual connectivity testing

    typical_duration_months=3,

    complexity_signals={
        "mpls_shared": "medium",
        "parent_managed_firewall": "high",
        "internet_only_today": "low",
    },

    required_drivers=["sites", "wan_shared_with_parent"],
    optional_drivers=["countries", "vpn_users"],
)
```

---

## Cost Calculation Logic

```python
def calculate_work_item_cost(
    work_item_type: WorkItemType,
    drivers: DealDrivers,
    scenario: str = "base"  # "base", "upside", "stress"
) -> WorkItemCostEstimate:
    """
    Calculate cost for a work item using driver-based model.

    Returns estimate with explicit assumptions and missing driver flags.
    """
    model = COST_MODELS[work_item_type]

    # Check required drivers
    missing_drivers = []
    for driver_name in model.required_drivers:
        if getattr(drivers, driver_name) is None:
            missing_drivers.append(driver_name)

    # Use defaults for missing optional drivers
    assumptions = {}

    # Calculate license costs (annual)
    license_cost_annual = 0
    for lic in model.license_drivers:
        quantity = _get_quantity_for_unit(lic.unit, drivers)
        if quantity is None:
            quantity = _get_default_quantity(lic.unit)
            assumptions[f"{lic.name}_quantity"] = f"assumed {quantity} (driver missing)"

        if lic.price_per_unit_annual:
            license_cost_annual += quantity * lic.price_per_unit_annual
        else:
            license_cost_annual += quantity * lic.price_per_unit_monthly * 12

    # Calculate services costs (one-time)
    complexity = _determine_complexity(model, drivers)
    multiplier = model.services_complexity_multiplier.get(complexity, 1.0)

    services_cost = model.services_base * multiplier

    if model.services_per_user and drivers.total_users:
        services_cost += model.services_per_user * drivers.total_users * multiplier

    if model.services_per_site and drivers.sites:
        services_cost += model.services_per_site * drivers.sites * multiplier

    if model.services_per_app and drivers.total_apps:
        services_cost += model.services_per_app * drivers.total_apps * multiplier

    # Calculate transition costs
    transition_cost = model.parallel_run_months * model.parallel_run_monthly

    # Apply scenario adjustments
    scenario_multipliers = {
        "upside": 0.8,    # Things go well
        "base": 1.0,      # Expected case
        "stress": 1.4,    # Things go poorly
    }
    scenario_mult = scenario_multipliers.get(scenario, 1.0)

    # Total one-time cost
    one_time_total = (services_cost + transition_cost) * scenario_mult

    return WorkItemCostEstimate(
        work_item_type=work_item_type,
        scenario=scenario,

        # Costs
        license_annual=license_cost_annual,
        services_one_time=services_cost * scenario_mult,
        transition_one_time=transition_cost * scenario_mult,
        total_one_time=one_time_total,

        # Metadata
        complexity_assessed=complexity,
        assumptions=assumptions,
        missing_drivers=missing_drivers,
        driver_sources=drivers.driver_sources,
        duration_months=model.typical_duration_months,
    )
```

---

## Output Format (Model-Ready)

### Work Item Cost Sheet

```json
{
  "work_item": "identity_separation",
  "title": "Establish Standalone Identity Infrastructure",
  "triggered_by": ["F-IAM-003", "F-IAM-007"],

  "drivers_used": {
    "total_users": {"value": 850, "source": "F-ORG-012"},
    "sites": {"value": 4, "source": "F-INFRA-001"},
    "identity_shared_with_parent": {"value": true, "source": "F-IAM-003"}
  },

  "drivers_assumed": {
    "custom_apps": {"value": 5, "reason": "not found in documents, using default"}
  },

  "drivers_missing": [],

  "complexity": {
    "assessed": "medium",
    "signals_found": ["ldap_integration"],
    "multiplier": 1.0
  },

  "costs": {
    "license_annual": {
      "Azure AD P2": {"quantity": 850, "unit_price": 108, "total": 91800}
    },
    "services_one_time": {
      "base": 75000,
      "per_user": 12750,
      "per_site": 20000,
      "complexity_adjusted": 107750
    },
    "transition": {
      "parallel_months": 2,
      "monthly_cost": 10000,
      "total": 20000
    }
  },

  "scenarios": {
    "upside": {"one_time": 102200, "annual_run_rate_delta": 91800},
    "base": {"one_time": 127750, "annual_run_rate_delta": 91800},
    "stress": {"one_time": 178850, "annual_run_rate_delta": 91800}
  },

  "timeline": {
    "duration_months": 4,
    "phase": "Day_100"
  },

  "to_tighten_estimate": [
    "Confirm user count with HR data",
    "Identify custom apps using AD authentication",
    "Validate site count includes all remote offices"
  ]
}
```

### Deal-Level Cost Summary

```json
{
  "deal_name": "AcmeCo Carve-out",
  "deal_type": "carveout",
  "as_of": "2024-01-15",

  "one_time_costs_by_tower": {
    "identity": {"upside": 102200, "base": 127750, "stress": 178850},
    "applications": {"upside": 480000, "base": 650000, "stress": 910000},
    "infrastructure": {"upside": 220000, "base": 310000, "stress": 434000},
    "network": {"upside": 145000, "base": 195000, "stress": 273000},
    "security": {"upside": 85000, "base": 115000, "stress": 161000},
    "euc": {"upside": 62000, "base": 85000, "stress": 119000},
    "pmo": {"upside": 120000, "base": 150000, "stress": 210000}
  },

  "totals": {
    "upside": 1214200,
    "base": 1632750,
    "stress": 2285850
  },

  "run_rate_delta_annual": {
    "licenses_new": 425000,
    "services_new": 180000,
    "parent_cost_eliminated": -150000,
    "net_change": 455000
  },

  "tsa_exposure": {
    "services_requiring_tsa": 6,
    "total_monthly_tsa_cost": 125000,
    "assumed_duration_months": 12,
    "tsa_total": 1500000
  },

  "top_10_assumptions": [
    {"assumption": "850 total users", "source": "F-ORG-012", "impact": "high"},
    {"assumption": "SAP separation takes 12 months", "source": "default", "impact": "high"},
    {"assumption": "4 physical sites", "source": "F-INFRA-001", "impact": "medium"},
    {"assumption": "Medium complexity identity separation", "source": "calculated", "impact": "medium"},
    {"assumption": "No legacy LDAP apps", "source": "not found", "impact": "medium"},
    {"assumption": "SD-WAN replaces MPLS", "source": "default", "impact": "medium"},
    {"assumption": "Cloud-first infrastructure target", "source": "assumed", "impact": "medium"},
    {"assumption": "TSA at market rates", "source": "default", "impact": "high"},
    {"assumption": "No data commingling in shared DBs", "source": "not found", "impact": "high"},
    {"assumption": "12-month TSA duration", "source": "default", "impact": "high"}
  ],

  "confidence": {
    "overall": "medium",
    "rationale": "Core drivers extracted from documents. Key assumptions on ERP complexity and TSA duration unvalidated."
  },

  "to_improve_estimate": [
    "Validate SAP separation complexity with target IT team",
    "Confirm TSA pricing with parent",
    "Obtain detailed site list with user counts per site",
    "Clarify data commingling in shared databases",
    "Get license inventory for accurate renewal costs"
  ]
}
```

---

## Implementation Phases

### Phase 1: Cost Catalog + Driver Extraction
- Define 15-20 standard work item types with cost models
- Build driver extractor that pulls values from FactStore
- Output: deterministic cost sheet per work item

### Phase 2: Scenario Engine + Complexity Scoring
- Add upside/base/stress multipliers
- Implement complexity signal detection from facts
- Output: three-scenario estimates with assumptions

### Phase 3: TSA Economics
- TSA duration sensitivity (12/18/24 months)
- Monthly TSA cost by service type
- One-time vs run-rate separation

### Phase 4: Learning Loop
- Track actuals post-close
- Adjust cost models based on real outcomes
- Build benchmark database across deals

---

## What This Enables

1. **Defensible numbers**: Every cost traces to drivers × unit prices × complexity
2. **Transparent assumptions**: Seniors can see and adjust any input
3. **Scenario modeling**: Base/upside/stress for IC presentation
4. **Missing data as feature**: "To tighten this estimate, get X" is useful output
5. **Auditability**: Each line item shows driver source (fact ID or "assumed")
6. **Benchmarking**: Same model structure across deals enables comparison
7. **Learning**: Post-close actuals can calibrate models over time

This is the bridge from "IC-ready scoping" to "bankable estimates."
