"""
IT DD Cost Model

Comprehensive cost estimation for IT due diligence covering:
1. Buyer One-Time Costs (separation/integration)
2. TSA Exit Costs (what buyer pays to become independent)
3. Run-Rate Impact (Year 1 vs Year 2+)

Philosophy:
- Anchors from market benchmarks (defensible)
- Adjustments from extracted facts (company-specific)
- TSA service pricing excluded (seller provides)
- TSA EXIT costs included (buyer's cost to become independent)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import json
import hashlib


# =============================================================================
# COST ANCHORS - Market Benchmarks
# =============================================================================

COST_ANCHORS = {
    # === ONE-TIME SEPARATION COSTS ===

    # License & Vendor
    "license_microsoft": {
        "name": "Microsoft License Transition",
        "unit": "per_user",
        "anchor": (180, 400),  # Annual per user
        "description": "Standalone M365 E3/E5 vs parent EA pricing"
    },
    "license_erp": {
        "name": "ERP License Transition",
        "unit": "per_user",
        "anchor": (1500, 4000),  # Annual per user
        "description": "SAP/Oracle standalone licensing"
    },
    "vendor_contract_transition": {
        "name": "Vendor Contract Transition",
        "unit": "per_vendor",
        "anchor": (15000, 50000),  # Per major vendor
        "description": "Legal, procurement, negotiation effort per vendor"
    },

    # Identity & Access
    "identity_separation": {
        "name": "Identity Separation",
        "unit": "fixed_by_size",
        "anchor_small": (100000, 300000),   # <1000 users
        "anchor_medium": (300000, 800000),  # 1000-5000 users
        "anchor_large": (800000, 2000000),  # >5000 users
        "description": "New AD/Azure AD/Okta + user migration"
    },

    # Applications
    "app_migration_simple": {
        "name": "Application Migration (Simple/SaaS)",
        "unit": "per_app",
        "anchor": (10000, 40000),
        "description": "SaaS reconfig, simple app migration"
    },
    "app_migration_moderate": {
        "name": "Application Migration (Moderate)",
        "unit": "per_app",
        "anchor": (50000, 150000),
        "description": "On-prem app with some customization"
    },
    "app_migration_complex": {
        "name": "Application Migration (Complex)",
        "unit": "per_app",
        "anchor": (200000, 600000),
        "description": "Highly customized, integrated apps"
    },
    "erp_separation": {
        "name": "ERP Separation/Migration",
        "unit": "fixed_by_size",
        "anchor_small": (500000, 1500000),
        "anchor_medium": (1500000, 4000000),
        "anchor_large": (4000000, 12000000),
        "description": "ERP instance separation or migration"
    },

    # Infrastructure
    "dc_migration": {
        "name": "Data Center Migration",
        "unit": "per_dc",
        "anchor": (200000, 800000),
        "description": "Per data center migration/exit"
    },
    "cloud_migration": {
        "name": "Cloud Migration (Lift & Shift)",
        "unit": "per_server",
        "anchor": (3000, 10000),
        "description": "Per server cloud migration"
    },
    "storage_migration": {
        "name": "Storage/Data Migration",
        "unit": "per_tb",
        "anchor": (500, 2000),
        "description": "Data migration per TB"
    },

    # Network
    "network_separation": {
        "name": "Network Separation",
        "unit": "fixed_by_complexity",
        "anchor_simple": (50000, 150000),
        "anchor_moderate": (150000, 400000),
        "anchor_complex": (400000, 1000000),
        "description": "WAN, firewall, VPN separation"
    },
    "wan_setup": {
        "name": "WAN/SDWAN Setup",
        "unit": "per_site",
        "anchor": (5000, 20000),
        "description": "Per site network setup"
    },

    # Security
    "security_remediation": {
        "name": "Security Remediation",
        "unit": "fixed_by_gaps",
        "anchor_minimal": (50000, 150000),
        "anchor_moderate": (150000, 500000),
        "anchor_significant": (500000, 1500000),
        "description": "Security gap remediation"
    },
    "security_tool_deployment": {
        "name": "Security Tool Deployment",
        "unit": "per_tool",
        "anchor": (30000, 100000),
        "description": "New security tool implementation"
    },

    # Data
    "data_segregation": {
        "name": "Data Segregation",
        "unit": "fixed_by_complexity",
        "anchor_simple": (75000, 200000),
        "anchor_moderate": (200000, 600000),
        "anchor_complex": (600000, 1500000),
        "description": "Data separation, ETL, validation"
    },

    # PMO & Change Management
    "pmo_overhead": {
        "name": "PMO / Project Management",
        "unit": "percentage",
        "anchor": (0.10, 0.15),  # 10-15% of total
        "description": "Project management overhead"
    },
    "change_management": {
        "name": "Change Management & Training",
        "unit": "per_user",
        "anchor": (50, 150),
        "description": "Training, communications, adoption"
    },

    # === TSA EXIT COSTS ===
    # What buyer pays to BUILD capability to get off TSA

    "tsa_exit_identity": {
        "name": "TSA Exit: Identity Services",
        "unit": "fixed_by_size",
        "anchor_small": (150000, 400000),
        "anchor_medium": (400000, 900000),
        "anchor_large": (900000, 2000000),
        "description": "Build standalone identity to exit TSA"
    },
    "tsa_exit_email": {
        "name": "TSA Exit: Email & Collaboration",
        "unit": "per_user",
        "anchor": (15, 40),  # One-time migration cost per user
        "description": "Email migration to exit TSA"
    },
    "tsa_exit_service_desk": {
        "name": "TSA Exit: Service Desk",
        "unit": "fixed_plus_per_user",
        "anchor_fixed": (100000, 300000),  # Setup
        "anchor_per_user": (20, 50),  # Transition per user
        "description": "Establish service desk capability"
    },
    "tsa_exit_infrastructure": {
        "name": "TSA Exit: Infrastructure",
        "unit": "fixed_by_size",
        "anchor_small": (200000, 500000),
        "anchor_medium": (500000, 1500000),
        "anchor_large": (1500000, 4000000),
        "description": "Build/migrate infrastructure to exit TSA"
    },
    "tsa_exit_network": {
        "name": "TSA Exit: Network Services",
        "unit": "per_site",
        "anchor": (8000, 25000),
        "description": "Network cutover per site"
    },
    "tsa_exit_security": {
        "name": "TSA Exit: Security Services",
        "unit": "fixed",
        "anchor": (150000, 500000),
        "description": "Establish security operations capability"
    },
    "tsa_exit_erp_support": {
        "name": "TSA Exit: ERP Support",
        "unit": "fixed",
        "anchor": (100000, 400000),
        "description": "Transition ERP support to standalone"
    },
}


# =============================================================================
# RUN-RATE ANCHORS - Ongoing Annual Costs
# =============================================================================

RUN_RATE_ANCHORS = {
    # Licensing (annual per user)
    "runrate_microsoft": {
        "name": "Microsoft 365 Licensing",
        "unit": "per_user_annual",
        "anchor_e3": (396, 432),      # E3 ~$33-36/user/month
        "anchor_e5": (684, 756),      # E5 ~$57-63/user/month
        "description": "Annual M365 licensing"
    },
    "runrate_erp_license": {
        "name": "ERP Licensing (Annual)",
        "unit": "per_user_annual",
        "anchor_tier1": (2000, 5000),   # SAP, Oracle
        "anchor_tier2": (1200, 2500),   # NetSuite, Dynamics
        "anchor_tier3": (600, 1200),    # Sage, QuickBooks Enterprise
        "description": "Annual ERP licensing"
    },

    # Infrastructure (annual)
    "runrate_cloud_hosting": {
        "name": "Cloud Hosting (Annual)",
        "unit": "per_server_annual",
        "anchor": (6000, 18000),  # $500-1500/month per server equivalent
        "description": "Annual cloud infrastructure"
    },
    "runrate_network": {
        "name": "Network Services (Annual)",
        "unit": "per_site_annual",
        "anchor": (12000, 36000),  # $1K-3K/month per site
        "description": "WAN/SDWAN/Internet per site"
    },

    # Security (annual)
    "runrate_security_tools": {
        "name": "Security Tool Stack (Annual)",
        "unit": "per_user_annual",
        "anchor_basic": (50, 100),     # Basic: AV, firewall
        "anchor_moderate": (100, 200),  # + EDR, email security
        "anchor_advanced": (200, 400),  # + SIEM, SOAR, MDR
        "description": "Annual security tooling"
    },
    "runrate_mdr_soc": {
        "name": "MDR/SOC Services (Annual)",
        "unit": "fixed_by_size",
        "anchor_small": (100000, 200000),
        "anchor_medium": (200000, 500000),
        "anchor_large": (500000, 1200000),
        "description": "Managed detection & response"
    },

    # Support (annual)
    "runrate_msp": {
        "name": "MSP/Managed Services (Annual)",
        "unit": "per_user_annual",
        "anchor_basic": (600, 1200),    # $50-100/user/month basic
        "anchor_full": (1800, 3600),    # $150-300/user/month full
        "description": "Outsourced IT support"
    },
    "runrate_internal_it": {
        "name": "Internal IT Staff (Annual)",
        "unit": "per_fte",
        "anchor": (120000, 180000),  # Fully loaded cost per IT FTE
        "description": "Internal IT headcount cost"
    },

    # Applications (annual)
    "runrate_saas_portfolio": {
        "name": "SaaS Portfolio (Annual)",
        "unit": "per_user_annual",
        "anchor_light": (500, 1000),    # Minimal SaaS
        "anchor_moderate": (1000, 2500), # Typical
        "anchor_heavy": (2500, 5000),   # SaaS-heavy org
        "description": "Total SaaS spend per user"
    },
}


# =============================================================================
# RUN-RATE DELTA PATTERNS
# =============================================================================

RUN_RATE_DELTAS = {
    # What changes post-separation?
    "license_uplift": {
        "trigger_patterns": ["parent enterprise agreement", "volume discount", "bundled license"],
        "impact": "increase",
        "delta_percent": (0.30, 0.50),  # 30-50% increase losing EA discount
        "affects": ["runrate_microsoft", "runrate_erp_license"],
        "description": "Loss of parent volume discount"
    },
    "msp_new": {
        "trigger_patterns": ["parent service desk", "corporate it support", "shared helpdesk"],
        "impact": "new_cost",
        "description": "New MSP contract required post-separation"
    },
    "security_gap": {
        "trigger_patterns": ["no siem", "no edr", "security gaps", "no mdr"],
        "impact": "new_cost",
        "description": "Security tools needed post-separation"
    },
    "cloud_efficiency": {
        "trigger_patterns": ["cloud optimization", "rightsizing", "reserved instances"],
        "impact": "decrease",
        "delta_percent": (0.15, 0.30),  # 15-30% savings potential
        "affects": ["runrate_cloud_hosting"],
        "description": "Cloud cost optimization opportunity"
    },
}


# =============================================================================
# VOLUME DISCOUNT CURVES
# =============================================================================
# At scale, per-unit costs decrease due to:
# - Vendor volume discounts
# - Economies of scale in implementation
# - Shared infrastructure/tools across users
#
# Format: List of (threshold, multiplier) tuples
# Applied in order - first matching threshold wins

VOLUME_DISCOUNT_CURVES = {
    # Per-user costs (licenses, training, support)
    "per_user": [
        (0, 1.0),        # 0-99 users: full price
        (100, 0.95),     # 100-499: 5% discount
        (500, 0.85),     # 500-999: 15% discount
        (1000, 0.75),    # 1000-2499: 25% discount
        (2500, 0.65),    # 2500-4999: 35% discount
        (5000, 0.55),    # 5000+: 45% discount (enterprise)
    ],

    # Per-application costs (migration, integration)
    "per_app": [
        (0, 1.0),        # 0-9 apps: full price
        (10, 0.90),      # 10-24: 10% discount (tooling amortization)
        (25, 0.80),      # 25-49: 20% discount
        (50, 0.70),      # 50-99: 30% discount
        (100, 0.60),     # 100+: 40% discount (factory approach)
    ],

    # Per-site costs (network, WAN)
    "per_site": [
        (0, 1.0),        # 0-4 sites: full price
        (5, 0.90),       # 5-14: 10% discount
        (15, 0.80),      # 15-29: 20% discount
        (30, 0.70),      # 30-49: 30% discount
        (50, 0.60),      # 50+: 40% discount
    ],

    # Per-server costs (migration, cloud)
    "per_server": [
        (0, 1.0),        # 0-24 servers: full price
        (25, 0.90),      # 25-99: 10% discount
        (100, 0.80),     # 100-249: 20% discount
        (250, 0.70),     # 250-499: 30% discount
        (500, 0.60),     # 500+: 40% discount
    ],

    # Per-vendor costs (contract transitions)
    "per_vendor": [
        (0, 1.0),        # 0-4 vendors: full price
        (5, 0.85),       # 5-9: 15% discount (procurement efficiency)
        (10, 0.75),      # 10+: 25% discount
    ],
}


def get_volume_discount(unit_type: str, quantity: int) -> float:
    """
    Get the volume discount multiplier for a given quantity.

    Args:
        unit_type: Type of unit (per_user, per_app, per_site, per_server, per_vendor)
        quantity: Number of units

    Returns:
        Multiplier (0.0-1.0) to apply to unit cost
    """
    curve = VOLUME_DISCOUNT_CURVES.get(unit_type)
    if not curve:
        return 1.0  # No discount if unit type not found

    # Find the appropriate tier
    multiplier = 1.0
    for threshold, mult in curve:
        if quantity >= threshold:
            multiplier = mult
        else:
            break

    return multiplier


# =============================================================================
# REGIONAL COST MULTIPLIERS
# =============================================================================
# Labor costs vary significantly by region. These multipliers adjust
# cost estimates based on where the work will be performed.
#
# Base = US East Coast (1.0)

REGIONAL_MULTIPLIERS = {
    # United States
    "us_east": 1.0,           # Base: NYC, Boston, DC
    "us_west": 1.15,          # SF, Seattle, LA (15% premium)
    "us_midwest": 0.85,       # Chicago, Denver, Dallas
    "us_south": 0.80,         # Atlanta, Austin, Charlotte

    # Europe
    "uk": 1.10,               # London, Manchester
    "western_europe": 1.05,   # Germany, France, Netherlands
    "eastern_europe": 0.50,   # Poland, Czech Republic, Romania
    "nordics": 1.20,          # Sweden, Norway, Denmark, Finland

    # Asia Pacific
    "india": 0.35,            # Major IT hub, significant savings
    "india_tier1": 0.40,      # Bangalore, Mumbai, Delhi
    "india_tier2": 0.30,      # Pune, Hyderabad, Chennai
    "philippines": 0.40,      # Growing IT services hub
    "singapore": 1.05,        # Premium APAC hub
    "australia": 1.10,        # Sydney, Melbourne
    "japan": 1.15,            # Tokyo

    # Latin America
    "mexico": 0.55,           # Nearshore, same timezone
    "brazil": 0.50,           # Sao Paulo
    "costa_rica": 0.50,       # Growing tech hub
    "argentina": 0.45,        # Buenos Aires

    # Other
    "israel": 1.05,           # Strong tech sector
    "south_africa": 0.45,     # Cape Town tech hub
    "canada": 0.90,           # Toronto, Vancouver

    # Special categories
    "offshore": 0.40,         # Generic offshore (use specific region if known)
    "nearshore": 0.55,        # Generic nearshore (Latin America)
    "global_delivery": 0.60,  # Blended rate (onshore + offshore mix)
}

# Labor mix assumptions for different work types
LABOR_MIX_BY_WORK_TYPE = {
    # Format: {work_type: {"onshore": %, "nearshore": %, "offshore": %}}
    "strategy": {"onshore": 1.0, "nearshore": 0.0, "offshore": 0.0},
    "architecture": {"onshore": 0.8, "nearshore": 0.1, "offshore": 0.1},
    "project_management": {"onshore": 0.7, "nearshore": 0.2, "offshore": 0.1},
    "development": {"onshore": 0.3, "nearshore": 0.3, "offshore": 0.4},
    "testing": {"onshore": 0.2, "nearshore": 0.3, "offshore": 0.5},
    "migration": {"onshore": 0.4, "nearshore": 0.3, "offshore": 0.3},
    "support": {"onshore": 0.3, "nearshore": 0.3, "offshore": 0.4},
    "infrastructure": {"onshore": 0.5, "nearshore": 0.3, "offshore": 0.2},
}


def get_regional_multiplier(region: str) -> float:
    """
    Get the cost multiplier for a region.

    Args:
        region: Region code (e.g., "us_east", "india", "uk")

    Returns:
        Multiplier to apply to base cost
    """
    return REGIONAL_MULTIPLIERS.get(region.lower(), 1.0)


def get_blended_rate_multiplier(
    work_type: str,
    onshore_region: str = "us_east",
    nearshore_region: str = "mexico",
    offshore_region: str = "india"
) -> float:
    """
    Calculate blended rate multiplier based on work type and delivery mix.

    Args:
        work_type: Type of work (development, testing, migration, etc.)
        onshore_region: Region for onshore work
        nearshore_region: Region for nearshore work
        offshore_region: Region for offshore work

    Returns:
        Blended multiplier based on labor mix
    """
    mix = LABOR_MIX_BY_WORK_TYPE.get(work_type, {"onshore": 1.0, "nearshore": 0.0, "offshore": 0.0})

    onshore_mult = get_regional_multiplier(onshore_region)
    nearshore_mult = get_regional_multiplier(nearshore_region)
    offshore_mult = get_regional_multiplier(offshore_region)

    blended = (
        mix["onshore"] * onshore_mult +
        mix["nearshore"] * nearshore_mult +
        mix["offshore"] * offshore_mult
    )

    return blended


# =============================================================================
# ACQUISITION-SPECIFIC COST ANCHORS
# =============================================================================

ACQUISITION_COSTS = {
    # Integration costs (buyer brings target into their environment)
    "integration_identity": {
        "name": "Identity Integration",
        "unit": "fixed_by_size",
        "anchor_small": (75000, 200000),
        "anchor_medium": (200000, 500000),
        "anchor_large": (500000, 1200000),
        "description": "Integrate target users into buyer's directory"
    },
    "integration_email": {
        "name": "Email/Collaboration Integration",
        "unit": "per_user",
        "anchor": (15, 40),  # Per user migration
        "description": "Migrate target to buyer's email platform"
    },
    "integration_network": {
        "name": "Network Integration",
        "unit": "per_site",
        "anchor": (10000, 35000),
        "description": "Connect target sites to buyer network"
    },
    "integration_security": {
        "name": "Security Stack Integration",
        "unit": "per_user",
        "anchor": (20, 60),
        "description": "Deploy buyer's security tools to target"
    },

    # Day-1 connectivity
    "day1_connectivity": {
        "name": "Day-1 Connectivity",
        "unit": "fixed",
        "anchor": (50000, 200000),
        "description": "Minimum viable connectivity for Day-1"
    },
    "day1_communications": {
        "name": "Day-1 Communications Setup",
        "unit": "fixed",
        "anchor": (25000, 75000),
        "description": "Email forwarding, basic collaboration"
    },

    # Dual-running costs
    "dual_run_systems": {
        "name": "Dual-Run Period (per month)",
        "unit": "percentage_of_runrate",
        "anchor": (0.08, 0.12),  # 8-12% of combined run-rate per month
        "description": "Cost of running parallel systems during integration"
    },

    # ERP consolidation
    "erp_consolidation": {
        "name": "ERP Consolidation",
        "unit": "fixed_by_size",
        "anchor_small": (1000000, 3000000),
        "anchor_medium": (3000000, 8000000),
        "anchor_large": (8000000, 20000000),
        "description": "Full ERP consolidation to single platform"
    },

    # Application rationalization
    "app_rationalization": {
        "name": "Application Rationalization",
        "unit": "per_app_retired",
        "anchor": (20000, 60000),
        "description": "Cost to retire/consolidate redundant apps"
    },
}


# =============================================================================
# RISK FLAGS
# =============================================================================

RISK_FLAGS = {
    "technical_debt": {
        "patterns": ["technical debt", "legacy code", "unsupported", "end of life", "eol"],
        "severity": "high",
        "cost_impact": "add_contingency",
        "impact_range": (0.10, 0.20),  # Add 10-20% contingency
        "description": "Technical debt increases project risk and cost overruns"
    },
    "key_person_dependency": {
        "patterns": ["single point of failure", "key person", "one person knows", "tribal knowledge"],
        "severity": "high",
        "cost_impact": "add_contingency",
        "impact_range": (0.10, 0.15),
        "description": "Key person dependencies create execution risk"
    },
    "vendor_lock_in": {
        "patterns": ["vendor lock-in", "proprietary", "single vendor", "no portability"],
        "severity": "medium",
        "cost_impact": "add_contingency",
        "impact_range": (0.05, 0.10),
        "description": "Vendor lock-in limits options and increases costs"
    },
    "data_quality": {
        "patterns": ["data quality issues", "dirty data", "no master data", "duplicate records"],
        "severity": "high",
        "cost_impact": "add_fixed",
        "impact_range": (100000, 500000),
        "description": "Data quality issues add significant remediation cost"
    },
    "integration_complexity": {
        "patterns": ["point-to-point", "spaghetti", "no integration layer", "custom integrations"],
        "severity": "medium",
        "cost_impact": "multiply",
        "impact_range": (1.15, 1.30),  # 15-30% increase on integration work
        "description": "Complex integrations increase migration difficulty"
    },
    "compliance_gaps": {
        "patterns": ["compliance gap", "audit finding", "regulatory issue", "failed audit"],
        "severity": "high",
        "cost_impact": "add_fixed",
        "impact_range": (200000, 1000000),
        "description": "Compliance gaps require immediate remediation"
    },
    "cybersecurity_incident": {
        "patterns": ["breach", "incident", "ransomware", "compromised"],
        "severity": "critical",
        "cost_impact": "add_fixed",
        "impact_range": (500000, 3000000),
        "description": "Recent security incidents require extensive remediation"
    },
    "contract_constraints": {
        "patterns": ["non-assignable", "change of control", "termination clause", "consent required"],
        "severity": "medium",
        "cost_impact": "add_contingency",
        "impact_range": (0.05, 0.15),
        "description": "Contract constraints may force renegotiation or replacement"
    },
}


# =============================================================================
# TIMELINE IMPLICATIONS
# =============================================================================

TIMELINE_DRIVERS = {
    "identity_separation": {
        "typical_duration_months": (3, 6),
        "accelerators": ["cloud identity", "modern stack", "existing separation"],
        "blockers": ["complex federation", "legacy systems", "regulatory approval"],
        "critical_path": True,
        "description": "Identity is Day-1 critical and often on critical path"
    },
    "erp_separation": {
        "typical_duration_months": (9, 18),
        "accelerators": ["cloud erp", "clean data", "standard config"],
        "blockers": ["heavy customization", "data quality", "shared master data"],
        "critical_path": True,
        "description": "ERP separation/migration often longest workstream"
    },
    "network_separation": {
        "typical_duration_months": (3, 6),
        "accelerators": ["sdwan ready", "cloud-first", "simple topology"],
        "blockers": ["complex wan", "shared infrastructure", "regulatory"],
        "critical_path": True,
        "description": "Network is Day-1 critical"
    },
    "application_migration": {
        "typical_duration_months": (6, 12),
        "accelerators": ["saas-heavy", "standard apps", "documented"],
        "blockers": ["custom apps", "no documentation", "integrations"],
        "critical_path": False,
        "description": "Can often be phased post-Day-1"
    },
    "security_remediation": {
        "typical_duration_months": (3, 9),
        "accelerators": ["mature baseline", "clear gaps", "budget approved"],
        "blockers": ["significant gaps", "no baseline", "cultural resistance"],
        "critical_path": False,
        "description": "Can run in parallel but may be pre-close requirement"
    },
}


# =============================================================================
# ADJUSTMENT RULES
# =============================================================================

@dataclass
class AdjustmentRule:
    """Rule that adjusts costs based on facts."""
    rule_id: str
    name: str
    fact_patterns: List[str]
    affected_categories: List[str]
    adjustment_type: str  # "multiply" or "add_fixed"
    adjustment_value: float
    rationale: str


ADJUSTMENT_RULES = [
    # Industry complexity
    AdjustmentRule(
        rule_id="IND-HEALTH",
        name="Healthcare Industry",
        fact_patterns=["healthcare", "hipaa", "phi", "medical", "hospital", "health system"],
        affected_categories=["all"],
        adjustment_type="multiply",
        adjustment_value=1.25,
        rationale="Healthcare/HIPAA requirements add ~25% complexity"
    ),
    AdjustmentRule(
        rule_id="IND-FINSERV",
        name="Financial Services",
        fact_patterns=["financial services", "banking", "insurance", "sox", "pci", "finra"],
        affected_categories=["all"],
        adjustment_type="multiply",
        adjustment_value=1.20,
        rationale="Financial services regulations add ~20% complexity"
    ),

    # Geographic complexity
    AdjustmentRule(
        rule_id="GEO-GLOBAL",
        name="Global Operations",
        fact_patterns=["global", "international", "multi-region", "emea", "apac", "data residency"],
        affected_categories=["infrastructure", "network", "data", "identity"],
        adjustment_type="multiply",
        adjustment_value=1.20,
        rationale="Global operations add ~20% for data residency and regional requirements"
    ),

    # Cloud maturity
    AdjustmentRule(
        rule_id="CLOUD-HIGH",
        name="High Cloud Adoption (>60%)",
        fact_patterns=[">60% cloud", "cloud-first", "cloud-native", "primarily saas", "modern stack"],
        affected_categories=["infrastructure", "dc_migration"],
        adjustment_type="multiply",
        adjustment_value=0.70,
        rationale="High cloud adoption reduces infrastructure migration by ~30%"
    ),
    AdjustmentRule(
        rule_id="CLOUD-LOW",
        name="Low Cloud Adoption (<30%)",
        fact_patterns=["<30% cloud", "on-prem heavy", "legacy infrastructure", "mainframe", "data center heavy"],
        affected_categories=["infrastructure", "dc_migration", "tsa_exit"],
        adjustment_type="multiply",
        adjustment_value=1.30,
        rationale="Heavy on-prem footprint adds ~30% migration complexity"
    ),

    # ERP complexity
    AdjustmentRule(
        rule_id="ERP-DUAL",
        name="Multiple ERP Systems",
        fact_patterns=["dual erp", "multiple erp", "two erp", "sap and oracle", "sap and netsuite"],
        affected_categories=["erp", "applications", "data"],
        adjustment_type="multiply",
        adjustment_value=1.40,
        rationale="Multiple ERPs add ~40% complexity"
    ),
    AdjustmentRule(
        rule_id="ERP-LEGACY",
        name="Legacy ERP",
        fact_patterns=["ecc 6.0", "end of support", "legacy erp", "oracle ebs", "jd edwards", "unsupported"],
        affected_categories=["erp", "applications"],
        adjustment_type="multiply",
        adjustment_value=1.35,
        rationale="Legacy ERP adds ~35% risk and complexity"
    ),
    AdjustmentRule(
        rule_id="ERP-MODERN",
        name="Modern Cloud ERP",
        fact_patterns=["s/4hana cloud", "netsuite", "workday", "cloud erp", "saas erp"],
        affected_categories=["erp", "applications"],
        adjustment_type="multiply",
        adjustment_value=0.85,
        rationale="Modern cloud ERP reduces complexity by ~15%"
    ),

    # Application complexity
    AdjustmentRule(
        rule_id="APP-HIGH-COUNT",
        name="Large Application Portfolio (>50)",
        fact_patterns=[">50 applications", ">50 apps", "large app portfolio", "75 applications", "100 applications"],
        affected_categories=["applications", "data"],
        adjustment_type="multiply",
        adjustment_value=1.25,
        rationale="Large app portfolio adds ~25% migration effort"
    ),
    AdjustmentRule(
        rule_id="APP-CUSTOM",
        name="Heavy Customization",
        fact_patterns=["custom applications", "custom code", "heavily customized", "bespoke", "in-house developed"],
        affected_categories=["applications"],
        adjustment_type="multiply",
        adjustment_value=1.30,
        rationale="Custom applications add ~30% complexity"
    ),

    # Security posture
    AdjustmentRule(
        rule_id="SEC-MATURE",
        name="Mature Security Posture",
        fact_patterns=["soc 2", "iso 27001", "mature security", "zero trust", "mfa deployed", "modern security"],
        affected_categories=["security"],
        adjustment_type="multiply",
        adjustment_value=0.70,
        rationale="Mature security reduces remediation by ~30%"
    ),
    AdjustmentRule(
        rule_id="SEC-GAPS",
        name="Security Gaps Identified",
        fact_patterns=["security gaps", "no mfa", "no siem", "audit findings", "compliance gaps", "no edr"],
        affected_categories=["security"],
        adjustment_type="multiply",
        adjustment_value=1.40,
        rationale="Security gaps require ~40% more remediation"
    ),

    # Outsourcing
    AdjustmentRule(
        rule_id="OUT-HIGH",
        name="High Outsourcing (>40%)",
        fact_patterns=[">40% outsourced", "heavily outsourced", "msp dependent", "managed services heavy"],
        affected_categories=["tsa_exit", "service_desk"],
        adjustment_type="multiply",
        adjustment_value=1.25,
        rationale="High outsourcing adds ~25% TSA exit complexity"
    ),

    # Data complexity
    AdjustmentRule(
        rule_id="DATA-COMPLEX",
        name="Complex Data Environment",
        fact_patterns=["data warehouse", "data lake", "big data", "multiple databases", "analytics platform"],
        affected_categories=["data"],
        adjustment_type="multiply",
        adjustment_value=1.35,
        rationale="Complex data environment adds ~35% migration effort"
    ),

    # Infrastructure constraints
    AdjustmentRule(
        rule_id="DC-LEASE",
        name="DC Lease Constraint",
        fact_patterns=["non-cancellable", "lease constraint", "lease obligation", "owned data center"],
        affected_categories=["infrastructure"],
        adjustment_type="add_fixed",
        adjustment_value=1000000,
        rationale="DC lease constraint adds ~$1M stranded cost risk"
    ),

    # Scale factors
    AdjustmentRule(
        rule_id="SCALE-LARGE",
        name="Large Organization (>5000)",
        fact_patterns=[">5000 employees", ">5,000", "large organization", "enterprise"],
        affected_categories=["identity", "email", "change_management"],
        adjustment_type="multiply",
        adjustment_value=1.15,
        rationale="Large scale adds ~15% to user-impacting workstreams"
    ),
    AdjustmentRule(
        rule_id="SCALE-SMALL",
        name="Small Organization (<500)",
        fact_patterns=["<500 employees", "small organization", "startup", "smb"],
        affected_categories=["identity", "email", "change_management"],
        adjustment_type="multiply",
        adjustment_value=0.80,
        rationale="Smaller scale reduces complexity by ~20%"
    ),
]


# =============================================================================
# TSA EXPOSURE PATTERNS
# =============================================================================

TSA_EXPOSURE_PATTERNS = {
    "identity": {
        "patterns": ["parent ad", "parent azure", "corporate okta", "federated identity",
                    "shared identity", "parent sso", "corporate directory"],
        "service": "Identity & Authentication",
        "typical_duration_months": (6, 12),
        "criticality": "Day-1 Critical",
        "exit_cost_anchor": "tsa_exit_identity"
    },
    "email": {
        "patterns": ["parent email", "corporate exchange", "shared microsoft 365",
                    "parent m365", "corporate email", "parent tenant"],
        "service": "Email & Collaboration",
        "typical_duration_months": (3, 6),
        "criticality": "Day-1 Critical",
        "exit_cost_anchor": "tsa_exit_email"
    },
    "service_desk": {
        "patterns": ["parent service desk", "corporate helpdesk", "shared itsm",
                    "parent support", "corporate it support"],
        "service": "Service Desk / IT Support",
        "typical_duration_months": (6, 12),
        "criticality": "Day-1 Important",
        "exit_cost_anchor": "tsa_exit_service_desk"
    },
    "infrastructure": {
        "patterns": ["parent data center", "shared hosting", "corporate infrastructure",
                    "parent-hosted", "shared servers", "parent network"],
        "service": "Infrastructure & Hosting",
        "typical_duration_months": (12, 18),
        "criticality": "Day-1 Critical",
        "exit_cost_anchor": "tsa_exit_infrastructure"
    },
    "network": {
        "patterns": ["parent wan", "corporate network", "shared mpls",
                    "parent vpn", "corporate firewall"],
        "service": "Network Services",
        "typical_duration_months": (6, 12),
        "criticality": "Day-1 Critical",
        "exit_cost_anchor": "tsa_exit_network"
    },
    "security": {
        "patterns": ["parent soc", "corporate security", "shared siem",
                    "parent-managed security"],
        "service": "Security Operations",
        "typical_duration_months": (6, 12),
        "criticality": "Day-1 Critical",
        "exit_cost_anchor": "tsa_exit_security"
    },
    "erp_support": {
        "patterns": ["parent erp support", "shared erp", "corporate sap",
                    "parent-managed erp", "shared oracle"],
        "service": "ERP Support",
        "typical_duration_months": (12, 24),
        "criticality": "Day-1 Important",
        "exit_cost_anchor": "tsa_exit_erp_support"
    },
}


# =============================================================================
# COST MODEL CLASS
# =============================================================================

@dataclass
class CostLineItem:
    """A single line item in the cost estimate."""
    category: str
    name: str
    anchor_range: Tuple[float, float]
    adjusted_range: Tuple[float, float]
    adjustments_applied: List[str]
    facts_used: List[str]


@dataclass
class TSAExposureItem:
    """A TSA-exposed service with exit cost."""
    service: str
    criticality: str
    typical_duration_months: Tuple[int, int]
    exit_cost_range: Tuple[float, float]
    supporting_facts: List[str]


class CostModel:
    """
    Comprehensive IT DD cost model.

    Produces:
    1. Buyer one-time costs (separation)
    2. TSA exit costs (to become independent)
    3. Run-rate impact estimates

    Determinism:
    - Rules are processed in sorted order by rule_id
    - Facts are normalized and sorted before matching
    - Same inputs always produce same outputs
    - Cache integration for repeated calculations
    """

    def __init__(self, use_cache: bool = True, cache_ttl: int = None):
        """
        Initialize the cost model.

        Args:
            use_cache: Whether to use cost estimate cache (default: True)
            cache_ttl: Cache TTL in seconds (None = no expiration)
        """
        self.anchors = COST_ANCHORS
        # Sort rules by rule_id for deterministic processing
        self.rules = sorted(ADJUSTMENT_RULES, key=lambda r: r.rule_id)
        self.tsa_patterns = TSA_EXPOSURE_PATTERNS
        self.runrate_anchors = RUN_RATE_ANCHORS
        self.runrate_deltas = RUN_RATE_DELTAS
        self.acquisition_costs = ACQUISITION_COSTS
        self.risk_flags = RISK_FLAGS
        self.timeline_drivers = TIMELINE_DRIVERS
        self._matched_rules: List[AdjustmentRule] = []
        self._use_cache = use_cache
        self._cache_ttl = cache_ttl
        self._cache = None

    def _get_cache(self):
        """Get or create the cost cache."""
        if self._cache is None and self._use_cache:
            from tools_v2.cost_cache import get_cost_cache
            self._cache = get_cost_cache(ttl_seconds=self._cache_ttl)
        return self._cache

    def _normalize_facts(self, facts: List[Dict]) -> List[Dict]:
        """
        Normalize facts for deterministic processing.

        - Sorts by content
        - Normalizes strings
        - Assigns deterministic IDs if missing
        """
        normalized = []
        for i, fact in enumerate(facts):
            content = fact.get("content", "")
            if isinstance(content, str):
                content = content.strip()

            # Ensure each fact has an ID
            fact_id = fact.get("fact_id") or f"F-{i:04d}"

            normalized.append({
                **fact,
                "content": content,
                "fact_id": fact_id,
            })

        # Sort by content for deterministic ordering
        normalized.sort(key=lambda f: (
            f.get("content", "").lower() if isinstance(f.get("content", ""), str) else "",
            f.get("fact_id", "")
        ))

        return normalized

    def match_facts_to_rules(self, facts: List[Dict]) -> List[Tuple[AdjustmentRule, List[str]]]:
        """
        Match facts to adjustment rules.

        Deterministic behavior:
        - Facts are normalized and sorted first
        - Rules are processed in sorted order by rule_id
        - Matching fact IDs are sorted for consistent ordering
        """
        # Normalize facts for deterministic matching
        normalized_facts = self._normalize_facts(facts)

        matched = []
        # Rules are already sorted by rule_id in __init__
        for rule in self.rules:
            matching_facts = []
            for fact in normalized_facts:
                content = fact.get("content", "")
                if isinstance(content, str):
                    content = content.lower()
                else:
                    content = str(content).lower()

                for pattern in rule.fact_patterns:
                    if pattern.lower() in content:
                        matching_facts.append(fact.get("fact_id", "unknown"))
                        break

            if matching_facts:
                # Sort matching facts for deterministic ordering
                matched.append((rule, sorted(set(matching_facts))))

        self._matched_rules = [m[0] for m in matched]
        return matched

    def identify_tsa_exposure(self, facts: List[Dict]) -> List[Dict]:
        """Identify TSA-exposed services from facts."""
        exposures = []
        for category, config in self.tsa_patterns.items():
            matching_facts = []
            for fact in facts:
                content = fact.get("content", "").lower()
                for pattern in config["patterns"]:
                    if pattern.lower() in content:
                        matching_facts.append(fact.get("fact_id", "unknown"))
                        break
            if matching_facts:
                exposures.append({
                    "category": category,
                    "service": config["service"],
                    "criticality": config["criticality"],
                    "typical_duration_months": config["typical_duration_months"],
                    "exit_cost_anchor": config["exit_cost_anchor"],
                    "supporting_facts": list(set(matching_facts))
                })
        return exposures

    def identify_risk_flags(self, facts: List[Dict]) -> List[Dict]:
        """Identify risk flags from facts that may increase costs."""
        flags = []
        for flag_key, config in self.risk_flags.items():
            matching_facts = []
            for fact in facts:
                content = fact.get("content", "").lower()
                for pattern in config["patterns"]:
                    if pattern.lower() in content:
                        matching_facts.append({
                            "fact_id": fact.get("fact_id", "unknown"),
                            "content": fact.get("content", "")[:100]
                        })
                        break
            if matching_facts:
                flags.append({
                    "flag": flag_key,
                    "severity": config["severity"],
                    "description": config["description"],
                    "cost_impact_type": config["cost_impact"],
                    "impact_range": config["impact_range"],
                    "supporting_facts": matching_facts
                })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        flags.sort(key=lambda x: severity_order.get(x["severity"], 99))
        return flags

    def assess_timeline(self, facts: List[Dict], deal_type: str) -> Dict[str, Any]:
        """Assess timeline implications based on facts."""
        assessments = []

        for driver_key, config in self.timeline_drivers.items():
            assessment = {
                "workstream": driver_key,
                "description": config["description"],
                "typical_duration_months": config["typical_duration_months"],
                "critical_path": config["critical_path"],
                "accelerators_present": [],
                "blockers_present": [],
                "adjusted_duration": config["typical_duration_months"]
            }

            # Check for accelerators and blockers in facts
            for fact in facts:
                content = fact.get("content", "").lower()

                for accelerator in config["accelerators"]:
                    if accelerator.lower() in content:
                        assessment["accelerators_present"].append({
                            "accelerator": accelerator,
                            "fact_id": fact.get("fact_id", "unknown")
                        })

                for blocker in config["blockers"]:
                    if blocker.lower() in content:
                        assessment["blockers_present"].append({
                            "blocker": blocker,
                            "fact_id": fact.get("fact_id", "unknown")
                        })

            # Adjust duration based on findings
            base_low, base_high = config["typical_duration_months"]

            # Accelerators reduce time by ~20% each (capped)
            accel_factor = max(0.6, 1 - (len(assessment["accelerators_present"]) * 0.15))

            # Blockers increase time by ~25% each (capped)
            block_factor = min(2.0, 1 + (len(assessment["blockers_present"]) * 0.20))

            adjusted_low = int(base_low * accel_factor * block_factor)
            adjusted_high = int(base_high * accel_factor * block_factor)

            assessment["adjusted_duration"] = (adjusted_low, adjusted_high)
            assessments.append(assessment)

        # Calculate overall timeline
        critical_path_items = [a for a in assessments if a["critical_path"]]
        if critical_path_items:
            # Critical path is the longest critical item
            longest_low = max(a["adjusted_duration"][0] for a in critical_path_items)
            longest_high = max(a["adjusted_duration"][1] for a in critical_path_items)
        else:
            longest_low, longest_high = 6, 12  # Default

        return {
            "workstream_assessments": assessments,
            "critical_path_duration_months": (longest_low, longest_high),
            "overall_program_months": (longest_low + 1, longest_high + 3),  # Add buffer
            "deal_type": deal_type,
            "notes": [
                "Critical path items must complete before Day-1 or TSA exit",
                "Non-critical items can be phased post-close",
                "Durations assume adequate resources and prioritization"
            ]
        }

    def estimate_acquisition_costs(
        self,
        user_count: int,
        facts: List[Dict],
        site_count: int = 5,
        apps_to_rationalize: int = 10,
        dual_run_months: int = 6
    ) -> Dict[str, Any]:
        """
        Estimate acquisition-specific costs (integration into buyer).

        Different from carveout: buyer brings target into THEIR environment.
        """
        # Determine size
        if user_count < 1000:
            size = "small"
        elif user_count < 5000:
            size = "medium"
        else:
            size = "large"

        integration_costs = []

        # Identity integration
        id_anchor = self.acquisition_costs["integration_identity"][f"anchor_{size}"]
        integration_costs.append({
            "category": "Integration",
            "name": "Identity Integration",
            "range": id_anchor,
            "description": "Integrate target users into buyer's directory"
        })

        # Email integration
        email_anchor = self.acquisition_costs["integration_email"]["anchor"]
        email_cost = (email_anchor[0] * user_count, email_anchor[1] * user_count)
        integration_costs.append({
            "category": "Integration",
            "name": "Email/Collaboration Integration",
            "range": email_cost,
            "per_user": email_anchor
        })

        # Network integration
        net_anchor = self.acquisition_costs["integration_network"]["anchor"]
        net_cost = (net_anchor[0] * site_count, net_anchor[1] * site_count)
        integration_costs.append({
            "category": "Integration",
            "name": "Network Integration",
            "range": net_cost,
            "per_site": net_anchor
        })

        # Security integration
        sec_anchor = self.acquisition_costs["integration_security"]["anchor"]
        sec_cost = (sec_anchor[0] * user_count, sec_anchor[1] * user_count)
        integration_costs.append({
            "category": "Integration",
            "name": "Security Stack Integration",
            "range": sec_cost,
            "per_user": sec_anchor
        })

        # Day-1 costs
        day1_conn = self.acquisition_costs["day1_connectivity"]["anchor"]
        day1_comm = self.acquisition_costs["day1_communications"]["anchor"]
        integration_costs.append({
            "category": "Day-1",
            "name": "Day-1 Connectivity & Communications",
            "range": (day1_conn[0] + day1_comm[0], day1_conn[1] + day1_comm[1])
        })

        # App rationalization
        if apps_to_rationalize > 0:
            app_anchor = self.acquisition_costs["app_rationalization"]["anchor"]
            app_cost = (app_anchor[0] * apps_to_rationalize, app_anchor[1] * apps_to_rationalize)
            integration_costs.append({
                "category": "Rationalization",
                "name": f"Application Rationalization ({apps_to_rationalize} apps)",
                "range": app_cost,
                "per_app": app_anchor
            })

        # Calculate totals
        total_low = sum(c["range"][0] for c in integration_costs)
        total_high = sum(c["range"][1] for c in integration_costs)

        # Dual-run costs (estimated as % of combined run-rate)
        # Rough estimate: $2,000-4,000 per user annual run-rate
        estimated_runrate = user_count * 3000  # Midpoint estimate
        dual_run_anchor = self.acquisition_costs["dual_run_systems"]["anchor"]
        dual_run_monthly = (estimated_runrate * dual_run_anchor[0] / 12,
                          estimated_runrate * dual_run_anchor[1] / 12)
        dual_run_total = (dual_run_monthly[0] * dual_run_months,
                        dual_run_monthly[1] * dual_run_months)

        return {
            "integration_costs": integration_costs,
            "integration_subtotal": (round(total_low, -3), round(total_high, -3)),
            "dual_run_costs": {
                "months": dual_run_months,
                "monthly_range": (round(dual_run_monthly[0], -2), round(dual_run_monthly[1], -2)),
                "total_range": (round(dual_run_total[0], -3), round(dual_run_total[1], -3))
            },
            "grand_total": (
                round(total_low + dual_run_total[0], -3),
                round(total_high + dual_run_total[1], -3)
            ),
            "notes": [
                "Assumes buyer has capacity to absorb target",
                "Excludes synergy capture costs (tool consolidation, etc.)",
                "ERP consolidation budgeted separately if required"
            ]
        }

    def estimate_run_rate(
        self,
        user_count: int,
        facts: List[Dict],
        server_count: int = 50,
        site_count: int = 5,
        it_fte_count: int = 0,
        security_tier: str = "moderate",
        saas_intensity: str = "moderate",
        erp_tier: str = "tier2",
        m365_tier: str = "e3"
    ) -> Dict[str, Any]:
        """
        Estimate annual run-rate (steady-state costs).

        Returns Year 1 and Year 2+ projections with deltas from separation.
        """
        # Determine size
        if user_count < 1000:
            size = "small"
        elif user_count < 5000:
            size = "medium"
        else:
            size = "large"

        run_rate_items = []

        # Microsoft licensing
        m365_anchor = self.runrate_anchors["runrate_microsoft"].get(f"anchor_{m365_tier}", (396, 432))
        m365_cost = (m365_anchor[0] * user_count, m365_anchor[1] * user_count)
        run_rate_items.append({
            "category": "Licensing",
            "name": f"Microsoft 365 ({m365_tier.upper()})",
            "annual_range": m365_cost,
            "per_user": m365_anchor
        })

        # ERP licensing
        erp_anchor = self.runrate_anchors["runrate_erp_license"].get(f"anchor_{erp_tier}", (1200, 2500))
        # Assume ~30% of users are ERP users
        erp_users = int(user_count * 0.30)
        erp_cost = (erp_anchor[0] * erp_users, erp_anchor[1] * erp_users)
        run_rate_items.append({
            "category": "Licensing",
            "name": f"ERP Licensing ({erp_tier})",
            "annual_range": erp_cost,
            "per_user": erp_anchor,
            "user_count": erp_users
        })

        # Cloud hosting
        cloud_anchor = self.runrate_anchors["runrate_cloud_hosting"]["anchor"]
        cloud_cost = (cloud_anchor[0] * server_count, cloud_anchor[1] * server_count)
        run_rate_items.append({
            "category": "Infrastructure",
            "name": "Cloud Hosting",
            "annual_range": cloud_cost,
            "per_server": cloud_anchor
        })

        # Network
        network_anchor = self.runrate_anchors["runrate_network"]["anchor"]
        network_cost = (network_anchor[0] * site_count, network_anchor[1] * site_count)
        run_rate_items.append({
            "category": "Infrastructure",
            "name": "Network Services",
            "annual_range": network_cost,
            "per_site": network_anchor
        })

        # Security tools
        sec_anchor_key = f"anchor_{security_tier}"
        sec_anchor = self.runrate_anchors["runrate_security_tools"].get(sec_anchor_key, (100, 200))
        sec_cost = (sec_anchor[0] * user_count, sec_anchor[1] * user_count)
        run_rate_items.append({
            "category": "Security",
            "name": f"Security Tools ({security_tier})",
            "annual_range": sec_cost,
            "per_user": sec_anchor
        })

        # MDR/SOC
        mdr_anchor_key = f"anchor_{size}"
        mdr_anchor = self.runrate_anchors["runrate_mdr_soc"].get(mdr_anchor_key, (200000, 500000))
        run_rate_items.append({
            "category": "Security",
            "name": "MDR/SOC Services",
            "annual_range": mdr_anchor
        })

        # IT Support (MSP or internal)
        if it_fte_count > 0:
            it_anchor = self.runrate_anchors["runrate_internal_it"]["anchor"]
            it_cost = (it_anchor[0] * it_fte_count, it_anchor[1] * it_fte_count)
            run_rate_items.append({
                "category": "Support",
                "name": f"Internal IT Staff ({it_fte_count} FTEs)",
                "annual_range": it_cost,
                "per_fte": it_anchor
            })
        else:
            # Assume MSP
            msp_anchor = self.runrate_anchors["runrate_msp"]["anchor_basic"]
            msp_cost = (msp_anchor[0] * user_count, msp_anchor[1] * user_count)
            run_rate_items.append({
                "category": "Support",
                "name": "MSP/Managed Services",
                "annual_range": msp_cost,
                "per_user": msp_anchor
            })

        # SaaS portfolio
        saas_anchor_key = f"anchor_{saas_intensity}"
        saas_anchor = self.runrate_anchors["runrate_saas_portfolio"].get(saas_anchor_key, (1000, 2500))
        saas_cost = (saas_anchor[0] * user_count, saas_anchor[1] * user_count)
        run_rate_items.append({
            "category": "Applications",
            "name": f"SaaS Portfolio ({saas_intensity})",
            "annual_range": saas_cost,
            "per_user": saas_anchor
        })

        # Calculate totals
        total_low = sum(item["annual_range"][0] for item in run_rate_items)
        total_high = sum(item["annual_range"][1] for item in run_rate_items)

        # Check for deltas based on facts
        deltas = []
        for delta_key, delta_config in self.runrate_deltas.items():
            for fact in facts:
                content = fact.get("content", "").lower()
                for pattern in delta_config["trigger_patterns"]:
                    if pattern.lower() in content:
                        deltas.append({
                            "delta": delta_key,
                            "description": delta_config["description"],
                            "impact": delta_config["impact"],
                            "fact_id": fact.get("fact_id", "unknown")
                        })
                        break

        # Year 1 adjustments (higher due to transition)
        year1_uplift = 1.15  # 15% higher in Year 1 due to parallel running, inefficiencies
        year1_low = total_low * year1_uplift
        year1_high = total_high * year1_uplift

        return {
            "run_rate_items": run_rate_items,
            "annual_run_rate": (round(total_low, -3), round(total_high, -3)),
            "year1_estimate": (round(year1_low, -3), round(year1_high, -3)),
            "year2_plus_estimate": (round(total_low, -3), round(total_high, -3)),
            "deltas_identified": deltas,
            "per_user_total": (round(total_low / user_count, 0), round(total_high / user_count, 0)),
            "notes": [
                "Year 1 includes 15% uplift for transition inefficiencies",
                "Year 2+ reflects steady-state run-rate",
                "Excludes one-time separation costs"
            ]
        }

    def calculate_line_item(
        self,
        anchor_key: str,
        quantity: int = 1,
        size: str = "medium",
        matched_rules: List[Tuple[AdjustmentRule, List[str]]] = None,
        category_filter: str = None
    ) -> Dict:
        """Calculate a single cost line item with adjustments."""
        anchor = self.anchors.get(anchor_key, {})
        if not anchor:
            return None

        # Get anchor range based on unit type
        unit = anchor.get("unit", "fixed")
        if unit == "fixed_by_size":
            range_key = f"anchor_{size}"
            base_range = anchor.get(range_key, anchor.get("anchor_medium", (0, 0)))
        elif unit == "fixed_by_complexity":
            range_key = f"anchor_{size}"
            base_range = anchor.get(range_key, anchor.get("anchor_moderate", (0, 0)))
        elif unit == "fixed_by_gaps":
            range_key = f"anchor_{size}"
            base_range = anchor.get(range_key, anchor.get("anchor_moderate", (0, 0)))
        else:
            base_range = anchor.get("anchor", (0, 0))

        # Apply quantity for per-unit costs
        if unit in ["per_user", "per_app", "per_server", "per_site", "per_dc", "per_tb", "per_vendor", "per_tool"]:
            anchor_low = base_range[0] * quantity
            anchor_high = base_range[1] * quantity
        elif unit == "fixed_plus_per_user":
            fixed = anchor.get("anchor_fixed", (0, 0))
            per_user = anchor.get("anchor_per_user", (0, 0))
            anchor_low = fixed[0] + (per_user[0] * quantity)
            anchor_high = fixed[1] + (per_user[1] * quantity)
        elif unit == "percentage":
            # Will be calculated as percentage of total later
            anchor_low = base_range[0]
            anchor_high = base_range[1]
        else:
            anchor_low, anchor_high = base_range

        # Apply adjustments
        adjusted_low = anchor_low
        adjusted_high = anchor_high
        adjustments_applied = []
        facts_used = []

        if matched_rules:
            for rule, fact_ids in matched_rules:
                # Check if rule applies to this category
                if category_filter and category_filter not in rule.affected_categories and "all" not in rule.affected_categories:
                    continue

                if rule.adjustment_type == "multiply":
                    adjusted_low *= rule.adjustment_value
                    adjusted_high *= rule.adjustment_value
                    pct = (rule.adjustment_value - 1) * 100
                    direction = "+" if pct > 0 else ""
                    adjustments_applied.append(f"{direction}{pct:.0f}%: {rule.rationale}")
                    facts_used.extend(fact_ids)
                elif rule.adjustment_type == "add_fixed":
                    adjusted_low += rule.adjustment_value
                    adjusted_high += rule.adjustment_value
                    adjustments_applied.append(f"+${rule.adjustment_value:,.0f}: {rule.rationale}")
                    facts_used.extend(fact_ids)

        return {
            "name": anchor.get("name", anchor_key),
            "anchor_range": (round(anchor_low, -2), round(anchor_high, -2)),
            "adjusted_range": (round(adjusted_low, -2), round(adjusted_high, -2)),
            "adjustments": adjustments_applied if adjustments_applied else ["No adjustments"],
            "facts_used": list(set(facts_used)),
            "unit": unit,
            "quantity": quantity
        }

    def estimate_costs(
        self,
        user_count: int,
        deal_type: str,
        facts: List[Dict],
        app_count: int = 20,
        dc_count: int = 1,
        site_count: int = 5,
        server_count: int = 50,
        major_vendor_count: int = 10,
        use_cache: bool = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive cost estimate.

        Determinism guarantee:
        - Same inputs always produce same outputs
        - Facts are normalized and sorted
        - Rules applied in consistent order
        - Cache enabled by default for repeated calculations

        Args:
            user_count: Number of users
            deal_type: "carveout" or "acquisition"
            facts: List of fact dicts with "content" field
            app_count: Number of applications
            dc_count: Number of data centers
            site_count: Number of sites/locations
            server_count: Number of servers
            major_vendor_count: Number of major vendors
            use_cache: Override cache setting (None = use instance default)

        Returns:
        - Buyer one-time costs
        - TSA exit costs
        - Total ranges
        - Full breakdown with adjustments
        """
        # Determine cache usage
        should_use_cache = use_cache if use_cache is not None else self._use_cache

        # Check cache first
        cache = self._get_cache() if should_use_cache else None
        if cache:
            cached = cache.get(
                user_count=user_count,
                deal_type=deal_type,
                facts=facts,
                app_count=app_count,
                dc_count=dc_count,
                site_count=site_count,
                server_count=server_count,
                major_vendor_count=major_vendor_count,
            )
            if cached is not None:
                return cached

        # Match facts to rules (uses normalized, sorted facts)
        matched_rules = self.match_facts_to_rules(facts)

        # Identify TSA exposure
        tsa_exposure = self.identify_tsa_exposure(facts)

        # Determine size category
        if user_count < 1000:
            size = "small"
        elif user_count < 5000:
            size = "medium"
        else:
            size = "large"

        # === ONE-TIME SEPARATION COSTS ===
        separation_costs = []

        # License transition
        license_item = self.calculate_line_item(
            "license_microsoft", user_count, size, matched_rules, "license"
        )
        if license_item:
            license_item["category"] = "License & Vendor"
            separation_costs.append(license_item)

        # Vendor contract transitions
        vendor_item = self.calculate_line_item(
            "vendor_contract_transition", major_vendor_count, size, matched_rules, "vendor"
        )
        if vendor_item:
            vendor_item["category"] = "License & Vendor"
            separation_costs.append(vendor_item)

        # Identity separation (always for carveout)
        if deal_type == "carveout":
            identity_item = self.calculate_line_item(
                "identity_separation", 1, size, matched_rules, "identity"
            )
            if identity_item:
                identity_item["category"] = "Identity & Access"
                separation_costs.append(identity_item)

        # Application migration (estimate breakdown)
        simple_apps = int(app_count * 0.6)  # 60% simple
        moderate_apps = int(app_count * 0.3)  # 30% moderate
        complex_apps = int(app_count * 0.1)  # 10% complex

        if simple_apps > 0:
            app_simple = self.calculate_line_item(
                "app_migration_simple", simple_apps, size, matched_rules, "applications"
            )
            if app_simple:
                app_simple["category"] = "Applications"
                app_simple["name"] = f"Application Migration - Simple ({simple_apps} apps)"
                separation_costs.append(app_simple)

        if moderate_apps > 0:
            app_moderate = self.calculate_line_item(
                "app_migration_moderate", moderate_apps, size, matched_rules, "applications"
            )
            if app_moderate:
                app_moderate["category"] = "Applications"
                app_moderate["name"] = f"Application Migration - Moderate ({moderate_apps} apps)"
                separation_costs.append(app_moderate)

        if complex_apps > 0:
            app_complex = self.calculate_line_item(
                "app_migration_complex", complex_apps, size, matched_rules, "applications"
            )
            if app_complex:
                app_complex["category"] = "Applications"
                app_complex["name"] = f"Application Migration - Complex ({complex_apps} apps)"
                separation_costs.append(app_complex)

        # Infrastructure
        if dc_count > 0:
            dc_item = self.calculate_line_item(
                "dc_migration", dc_count, size, matched_rules, "infrastructure"
            )
            if dc_item:
                dc_item["category"] = "Infrastructure"
                separation_costs.append(dc_item)

        if server_count > 0:
            cloud_item = self.calculate_line_item(
                "cloud_migration", server_count, size, matched_rules, "infrastructure"
            )
            if cloud_item:
                cloud_item["category"] = "Infrastructure"
                separation_costs.append(cloud_item)

        # Network
        network_complexity = "moderate" if site_count > 10 else "simple"
        network_item = self.calculate_line_item(
            "network_separation", 1, network_complexity, matched_rules, "network"
        )
        if network_item:
            network_item["category"] = "Network"
            separation_costs.append(network_item)

        wan_item = self.calculate_line_item(
            "wan_setup", site_count, size, matched_rules, "network"
        )
        if wan_item:
            wan_item["category"] = "Network"
            separation_costs.append(wan_item)

        # Security
        sec_gaps = "moderate"  # Default, adjusted by rules
        for rule, _ in matched_rules:
            if rule.rule_id == "SEC-GAPS":
                sec_gaps = "significant"
            elif rule.rule_id == "SEC-MATURE":
                sec_gaps = "minimal"

        security_item = self.calculate_line_item(
            "security_remediation", 1, sec_gaps, matched_rules, "security"
        )
        if security_item:
            security_item["category"] = "Security"
            separation_costs.append(security_item)

        # Data segregation
        data_complexity = "moderate"
        for rule, _ in matched_rules:
            if rule.rule_id == "DATA-COMPLEX":
                data_complexity = "complex"

        data_item = self.calculate_line_item(
            "data_segregation", 1, data_complexity, matched_rules, "data"
        )
        if data_item:
            data_item["category"] = "Data"
            separation_costs.append(data_item)

        # Change management
        cm_item = self.calculate_line_item(
            "change_management", user_count, size, matched_rules, "change_management"
        )
        if cm_item:
            cm_item["category"] = "Change Management"
            separation_costs.append(cm_item)

        # Calculate separation subtotal
        sep_subtotal_low = sum(c["adjusted_range"][0] for c in separation_costs)
        sep_subtotal_high = sum(c["adjusted_range"][1] for c in separation_costs)

        # PMO overhead (10-15% of subtotal)
        pmo_low = sep_subtotal_low * 0.10
        pmo_high = sep_subtotal_high * 0.15
        separation_costs.append({
            "category": "PMO & Overhead",
            "name": "Project Management (10-15%)",
            "anchor_range": (round(pmo_low, -2), round(pmo_high, -2)),
            "adjusted_range": (round(pmo_low, -2), round(pmo_high, -2)),
            "adjustments": ["Calculated as 10-15% of subtotal"],
            "facts_used": []
        })

        # === TSA EXIT COSTS ===
        tsa_exit_costs = []

        for exposure in tsa_exposure:
            exit_anchor = exposure["exit_cost_anchor"]
            exit_item = self.calculate_line_item(
                exit_anchor, user_count if "per_user" in self.anchors.get(exit_anchor, {}).get("unit", "") else site_count,
                size, matched_rules, "tsa_exit"
            )
            if exit_item:
                exit_item["category"] = "TSA Exit"
                exit_item["service"] = exposure["service"]
                exit_item["criticality"] = exposure["criticality"]
                exit_item["typical_duration"] = f"{exposure['typical_duration_months'][0]}-{exposure['typical_duration_months'][1]} months"
                tsa_exit_costs.append(exit_item)

        # === TOTALS ===
        sep_total_low = sep_subtotal_low + pmo_low
        sep_total_high = sep_subtotal_high + pmo_high

        tsa_exit_total_low = sum(c["adjusted_range"][0] for c in tsa_exit_costs)
        tsa_exit_total_high = sum(c["adjusted_range"][1] for c in tsa_exit_costs)

        # Contingency (15-20%)
        contingency_low = (sep_total_low + tsa_exit_total_low) * 0.15
        contingency_high = (sep_total_high + tsa_exit_total_high) * 0.20

        grand_total_low = sep_total_low + tsa_exit_total_low + contingency_low
        grand_total_high = sep_total_high + tsa_exit_total_high + contingency_high

        # Build deterministic input hash
        input_data = {
            "user_count": user_count,
            "deal_type": deal_type.lower().strip(),
            "app_count": app_count,
            "dc_count": dc_count,
            "site_count": site_count,
            "server_count": server_count,
            "major_vendor_count": major_vendor_count,
            # Sort facts for deterministic hash
            "facts": sorted([f.get("content", "")[:50].lower().strip() for f in facts])
        }
        input_hash = hashlib.sha256(
            json.dumps(input_data, sort_keys=True).encode()
        ).hexdigest()[:12]

        result = {
            "deal_type": deal_type,
            "user_count": user_count,
            "facts_analyzed": len(facts),
            "rules_triggered": len(matched_rules),

            "separation_costs": separation_costs,
            "separation_subtotal": (round(sep_total_low, -3), round(sep_total_high, -3)),

            "tsa_exposure": tsa_exposure,
            "tsa_exit_costs": tsa_exit_costs,
            "tsa_exit_subtotal": (round(tsa_exit_total_low, -3), round(tsa_exit_total_high, -3)),

            "contingency": (round(contingency_low, -3), round(contingency_high, -3)),

            "grand_total": (round(grand_total_low, -3), round(grand_total_high, -3)),
            "grand_total_midpoint": round((grand_total_low + grand_total_high) / 2, -3),

            "methodology": "anchored_estimation_v2.1_deterministic",
            "input_hash": input_hash,
            "is_cached": False,
        }

        # Store in cache
        if cache:
            cache.set(
                result,
                user_count=user_count,
                deal_type=deal_type,
                facts=facts,
                app_count=app_count,
                dc_count=dc_count,
                site_count=site_count,
                server_count=server_count,
                major_vendor_count=major_vendor_count,
            )
            result["is_cached"] = True

        return result

    def format_for_display(self, estimate: Dict) -> str:
        """Format estimate for display."""
        lines = [
            "=" * 75,
            "IT DUE DILIGENCE COST ESTIMATE",
            "=" * 75,
            f"Deal Type: {estimate['deal_type'].upper()}",
            f"Users: {estimate['user_count']:,}",
            f"Facts Analyzed: {estimate['facts_analyzed']} | Rules Triggered: {estimate['rules_triggered']}",
            "",
        ]

        # Separation costs
        lines.extend([
            "-" * 75,
            "BUYER ONE-TIME COSTS (Separation/Migration)",
            "-" * 75,
        ])

        current_category = None
        for item in estimate["separation_costs"]:
            if item["category"] != current_category:
                current_category = item["category"]
                lines.append(f"\n{current_category}:")

            low, high = item["adjusted_range"]
            lines.append(f"  • {item['name']}: ${low:,.0f} - ${high:,.0f}")
            if item.get("adjustments") and item["adjustments"] != ["No adjustments"]:
                for adj in item["adjustments"][:2]:  # Show first 2 adjustments
                    lines.append(f"      {adj}")

        lines.extend([
            "",
            f"  SEPARATION SUBTOTAL: ${estimate['separation_subtotal'][0]:,.0f} - ${estimate['separation_subtotal'][1]:,.0f}",
        ])

        # TSA Exit costs
        if estimate["tsa_exit_costs"]:
            lines.extend([
                "",
                "-" * 75,
                "TSA EXIT COSTS (To Become Independent)",
                "-" * 75,
                "Note: These are costs to BUILD capability to exit TSA (not TSA service fees)",
                "",
            ])

            for item in estimate["tsa_exit_costs"]:
                low, high = item["adjusted_range"]
                lines.append(f"  • {item['service']}: ${low:,.0f} - ${high:,.0f}")
                lines.append(f"      Criticality: {item['criticality']} | Duration: {item['typical_duration']}")

            lines.extend([
                "",
                f"  TSA EXIT SUBTOTAL: ${estimate['tsa_exit_subtotal'][0]:,.0f} - ${estimate['tsa_exit_subtotal'][1]:,.0f}",
            ])

        # Totals
        lines.extend([
            "",
            "-" * 75,
            "TOTALS",
            "-" * 75,
            f"  Separation Costs:     ${estimate['separation_subtotal'][0]:,.0f} - ${estimate['separation_subtotal'][1]:,.0f}",
            f"  TSA Exit Costs:       ${estimate['tsa_exit_subtotal'][0]:,.0f} - ${estimate['tsa_exit_subtotal'][1]:,.0f}",
            f"  Contingency (15-20%): ${estimate['contingency'][0]:,.0f} - ${estimate['contingency'][1]:,.0f}",
            "",
            f"  GRAND TOTAL: ${estimate['grand_total'][0]:,.0f} - ${estimate['grand_total'][1]:,.0f}",
            f"  Midpoint: ${estimate['grand_total_midpoint']:,.0f}",
            "",
            "-" * 75,
            f"Methodology: {estimate['methodology']}",
            f"Input Hash: {estimate['input_hash']}",
            "=" * 75,
        ])

        return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core anchors and patterns
    'COST_ANCHORS',
    'ADJUSTMENT_RULES',
    'TSA_EXPOSURE_PATTERNS',
    # Run-rate
    'RUN_RATE_ANCHORS',
    'RUN_RATE_DELTAS',
    # Acquisition-specific
    'ACQUISITION_COSTS',
    # Risk and timeline
    'RISK_FLAGS',
    'TIMELINE_DRIVERS',
    # Data classes
    'CostLineItem',
    'TSAExposureItem',
    # Main class
    'CostModel',
]
