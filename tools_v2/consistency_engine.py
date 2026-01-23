"""
Consistency Engine - Rule-Based Scoring & Deterministic Calculations

This module ensures consistent outputs by replacing LLM "vibes" with:
1. Rule-based complexity scoring
2. Deterministic cost calculation from lookup tables
3. Stable Top Risks selection by score
4. Confidence metrics

NO LLM judgment in this module - pure computation.

METHODOLOGY DOCUMENTATION
=========================

1. COST ESTIMATION METHODOLOGY
   - Base costs are mid-market benchmarks (100-500 employees)
   - Source: Industry research, PE deal retrospectives, consulting benchmarks
   - Costs are adjusted by: Company Size × Industry Factor × Geography Factor

2. COMPANY SIZE MULTIPLIERS (Headcount-based)
   - <50 employees: 0.4x (simpler IT, fewer systems)
   - 50-100: 0.6x
   - 100-250: 0.8x
   - 250-500: 1.0x (baseline)
   - 500-1000: 1.5x
   - 1000-2500: 2.2x
   - 2500-5000: 3.0x
   - 5000+: 4.0x (enterprise complexity)

3. INDUSTRY COMPLEXITY FACTORS
   - Healthcare/Life Sciences: 1.4x (HIPAA, FDA compliance)
   - Financial Services: 1.5x (SOX, PCI, regulatory)
   - Manufacturing: 1.2x (OT/IT convergence)
   - Technology: 1.0x (baseline)
   - Retail/E-commerce: 1.1x (PCI, multi-channel)
   - Professional Services: 0.9x (simpler IT footprint)

4. GEOGRAPHY FACTORS
   - Single country: 1.0x
   - Multi-country, same region: 1.2x
   - Multi-region (NA+EU, etc.): 1.4x
   - Global (3+ regions): 1.6x

5. COMPLEXITY SCORING
   - Critical risk: 15 points
   - High risk: 8 points
   - Medium risk: 3 points
   - Low risk: 1 point
   - Critical/High gap: 5 points
   - Other gap: 2 points
   - Each work item: 2 points

   Tier Thresholds:
   - Low: 0-14 points
   - Mid: 15-34 points
   - High: 35-59 points
   - Critical: 60+ points

   Auto-bump flags can elevate tier regardless of score.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from datetime import datetime


# =============================================================================
# COMPANY PROFILE ADJUSTMENTS (The Logic Layer)
# =============================================================================

# Company size multipliers - based on employee headcount
# Rationale: Larger companies have more systems, more complexity, more stakeholders
SIZE_MULTIPLIERS = {
    "micro": {"range": (0, 50), "multiplier": 0.4, "label": "<50 employees"},
    "small": {"range": (50, 100), "multiplier": 0.6, "label": "50-100 employees"},
    "small_mid": {"range": (100, 250), "multiplier": 0.8, "label": "100-250 employees"},
    "mid_market": {"range": (250, 500), "multiplier": 1.0, "label": "250-500 employees (baseline)"},
    "upper_mid": {"range": (500, 1000), "multiplier": 1.5, "label": "500-1000 employees"},
    "lower_enterprise": {"range": (1000, 2500), "multiplier": 2.2, "label": "1000-2500 employees"},
    "enterprise": {"range": (2500, 5000), "multiplier": 3.0, "label": "2500-5000 employees"},
    "large_enterprise": {"range": (5000, 999999), "multiplier": 4.0, "label": "5000+ employees"}
}

# Industry complexity factors
# Rationale: Regulated industries have compliance overhead; tech-heavy industries have more systems
INDUSTRY_FACTORS = {
    "healthcare": {"factor": 1.4, "reason": "HIPAA compliance, clinical systems integration"},
    "life_sciences": {"factor": 1.4, "reason": "FDA 21 CFR Part 11, GxP validation"},
    "financial_services": {"factor": 1.5, "reason": "SOX, PCI-DSS, regulatory reporting"},
    "banking": {"factor": 1.5, "reason": "Core banking systems, regulatory requirements"},
    "insurance": {"factor": 1.3, "reason": "Policy admin systems, state regulations"},
    "manufacturing": {"factor": 1.2, "reason": "OT/IT convergence, MES/ERP integration"},
    "technology": {"factor": 1.0, "reason": "Baseline - modern systems assumed"},
    "software": {"factor": 1.0, "reason": "Baseline - cloud-native assumed"},
    "retail": {"factor": 1.1, "reason": "PCI compliance, omnichannel systems"},
    "ecommerce": {"factor": 1.1, "reason": "Payment systems, platform integration"},
    "professional_services": {"factor": 0.9, "reason": "Simpler IT footprint"},
    "media": {"factor": 1.0, "reason": "Content systems, standard IT"},
    "energy": {"factor": 1.3, "reason": "SCADA/OT systems, safety requirements"},
    "logistics": {"factor": 1.1, "reason": "WMS/TMS systems, tracking integration"},
    "education": {"factor": 0.9, "reason": "Generally simpler IT requirements"},
    "government": {"factor": 1.4, "reason": "FedRAMP, security clearances"},
    "default": {"factor": 1.0, "reason": "Standard complexity assumed"}
}

# Geography factors
# Rationale: More regions = more complexity (data residency, compliance, connectivity)
GEOGRAPHY_FACTORS = {
    "single_country": {"factor": 1.0, "reason": "Single jurisdiction, unified compliance"},
    "multi_country_same_region": {"factor": 1.2, "reason": "Regional compliance (e.g., GDPR)"},
    "multi_region": {"factor": 1.4, "reason": "Multiple regulatory frameworks"},
    "global": {"factor": 1.6, "reason": "Complex data residency, 24/7 operations"},
    "default": {"factor": 1.0, "reason": "Assumed single country"}
}

# IT Maturity adjustments
# Rationale: Less mature IT = more work required
IT_MATURITY_FACTORS = {
    "advanced": {"factor": 0.8, "reason": "Modern systems, good documentation"},
    "standard": {"factor": 1.0, "reason": "Typical mid-market IT"},
    "basic": {"factor": 1.3, "reason": "Legacy systems, technical debt"},
    "minimal": {"factor": 1.6, "reason": "Significant modernization needed"},
    "default": {"factor": 1.0, "reason": "Standard maturity assumed"}
}


def get_size_multiplier(employee_count: int) -> Tuple[float, str]:
    """
    Get the cost multiplier based on company size.

    Args:
        employee_count: Number of employees

    Returns:
        (multiplier, explanation)
    """
    for size_key, config in SIZE_MULTIPLIERS.items():
        low, high = config["range"]
        if low <= employee_count < high:
            return config["multiplier"], config["label"]

    # Default to mid-market if not found
    return 1.0, "250-500 employees (baseline)"


def get_industry_factor(industry: str) -> Tuple[float, str]:
    """
    Get the complexity factor for an industry.

    Args:
        industry: Industry name (lowercase, underscores)

    Returns:
        (factor, reason)
    """
    industry_key = industry.lower().replace(" ", "_").replace("-", "_")
    config = INDUSTRY_FACTORS.get(industry_key, INDUSTRY_FACTORS["default"])
    return config["factor"], config["reason"]


def get_geography_factor(geography: str) -> Tuple[float, str]:
    """
    Get the complexity factor for geographic spread.

    Args:
        geography: One of single_country, multi_country_same_region, multi_region, global

    Returns:
        (factor, reason)
    """
    geo_key = geography.lower().replace(" ", "_").replace("-", "_")
    config = GEOGRAPHY_FACTORS.get(geo_key, GEOGRAPHY_FACTORS["default"])
    return config["factor"], config["reason"]


def get_maturity_factor(maturity: str) -> Tuple[float, str]:
    """
    Get the adjustment factor for IT maturity level.

    Args:
        maturity: One of advanced, standard, basic, minimal

    Returns:
        (factor, reason)
    """
    maturity_key = maturity.lower().replace(" ", "_")
    config = IT_MATURITY_FACTORS.get(maturity_key, IT_MATURITY_FACTORS["default"])
    return config["factor"], config["reason"]


@dataclass
class CompanyProfile:
    """
    Company profile for cost adjustment calculations.
    All factors have sensible defaults for mid-market deals.
    """
    employee_count: int = 300  # Default mid-market
    industry: str = "technology"  # Default baseline industry
    geography: str = "single_country"  # Default single country
    it_maturity: str = "standard"  # Default standard maturity
    annual_revenue: float = 50_000_000  # $50M default (not used in v1, placeholder)

    def get_total_multiplier(self) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate the total cost multiplier with full breakdown.

        Returns:
            (total_multiplier, breakdown_dict)
        """
        size_mult, size_reason = get_size_multiplier(self.employee_count)
        industry_mult, industry_reason = get_industry_factor(self.industry)
        geo_mult, geo_reason = get_geography_factor(self.geography)
        maturity_mult, maturity_reason = get_maturity_factor(self.it_maturity)

        total = size_mult * industry_mult * geo_mult * maturity_mult

        breakdown = {
            "size": {
                "multiplier": size_mult,
                "reason": size_reason,
                "input": f"{self.employee_count} employees"
            },
            "industry": {
                "multiplier": industry_mult,
                "reason": industry_reason,
                "input": self.industry
            },
            "geography": {
                "multiplier": geo_mult,
                "reason": geo_reason,
                "input": self.geography
            },
            "it_maturity": {
                "multiplier": maturity_mult,
                "reason": maturity_reason,
                "input": self.it_maturity
            },
            "total_multiplier": round(total, 2),
            "formula": f"{size_mult} × {industry_mult} × {geo_mult} × {maturity_mult} = {round(total, 2)}"
        }

        return round(total, 2), breakdown


# =============================================================================
# BASE COST LOOKUP TABLE (Mid-market benchmarks)
# =============================================================================

# These are BASE costs for a 250-500 employee, single-country, standard-maturity company
# Actual costs = Base cost × Total multiplier

COST_TABLE = {
    # Category -> Phase -> (low, high) in dollars
    "erp_integration": {
        "Day_1": (50_000, 150_000),
        "Day_100": (200_000, 500_000),
        "Post_100": (100_000, 300_000)
    },
    "identity_consolidation": {
        "Day_1": (25_000, 75_000),
        "Day_100": (100_000, 250_000),
        "Post_100": (50_000, 150_000)
    },
    "infrastructure_migration": {
        "Day_1": (25_000, 100_000),
        "Day_100": (150_000, 400_000),
        "Post_100": (75_000, 200_000)
    },
    "security_remediation": {
        "Day_1": (50_000, 150_000),
        "Day_100": (100_000, 300_000),
        "Post_100": (50_000, 150_000)
    },
    "application_rationalization": {
        "Day_1": (10_000, 50_000),
        "Day_100": (100_000, 300_000),
        "Post_100": (200_000, 500_000)
    },
    "network_integration": {
        "Day_1": (25_000, 75_000),
        "Day_100": (75_000, 200_000),
        "Post_100": (25_000, 75_000)
    },
    "data_migration": {
        "Day_1": (25_000, 100_000),
        "Day_100": (100_000, 300_000),
        "Post_100": (50_000, 150_000)
    },
    "compliance_remediation": {
        "Day_1": (25_000, 100_000),
        "Day_100": (50_000, 200_000),
        "Post_100": (25_000, 100_000)
    },
    "vendor_consolidation": {
        "Day_1": (10_000, 50_000),
        "Day_100": (50_000, 150_000),
        "Post_100": (100_000, 300_000)
    },
    "staffing_transition": {
        "Day_1": (50_000, 150_000),
        "Day_100": (100_000, 300_000),
        "Post_100": (50_000, 150_000)
    },
    "default": {
        "Day_1": (25_000, 100_000),
        "Day_100": (50_000, 200_000),
        "Post_100": (25_000, 100_000)
    }
}

# Keywords for work item categorization
CATEGORY_KEYWORDS = {
    "erp_integration": ["erp", "sap", "oracle", "netsuite", "dynamics", "workday", "epicor"],
    "identity_consolidation": ["identity", "iam", "sso", "active directory", "azure ad", "okta", "ldap", "authentication"],
    "infrastructure_migration": ["migrate", "infrastructure", "datacenter", "data center", "cloud", "aws", "azure", "vmware"],
    "security_remediation": ["security", "vulnerability", "compliance", "soc2", "penetration", "firewall", "siem", "antivirus"],
    "application_rationalization": ["application", "rationalize", "consolidate", "saas", "software", "license"],
    "network_integration": ["network", "vpn", "wan", "lan", "firewall", "routing", "dns", "connectivity"],
    "data_migration": ["data migration", "database", "backup", "restore", "etl", "data transfer"],
    "compliance_remediation": ["audit", "compliance", "regulation", "gdpr", "hipaa", "pci", "sox"],
    "vendor_consolidation": ["vendor", "contract", "msp", "outsource", "supplier", "third party"],
    "staffing_transition": ["staff", "team", "hire", "transition", "knowledge transfer", "training", "retention"]
}

# Complexity flags that auto-bump tier
COMPLEXITY_FLAGS = {
    "dual_erp": {
        "pattern": r"dual.*erp|two.*erp|multiple.*erp|separate.*erp",
        "bump_to": "high",
        "description": "Dual ERP systems detected"
    },
    "no_disaster_recovery": {
        "pattern": r"no.*disaster.*recovery|missing.*dr|lacks.*dr|no.*backup.*strategy",
        "bump_to": "high",
        "description": "Missing disaster recovery"
    },
    "identity_governance_gap": {
        "pattern": r"identity.*governance.*gap|no.*iam|lacks.*identity|manual.*access",
        "bump_to": "mid",
        "description": "Identity governance gap"
    },
    "legacy_system": {
        "pattern": r"end.of.life|eol|unsupported|legacy|outdated|deprecated",
        "bump_to": "mid",
        "description": "Legacy/EOL systems present"
    },
    "no_security_monitoring": {
        "pattern": r"no.*siem|no.*monitoring|lacks.*security.*monitor|no.*logging",
        "bump_to": "high",
        "description": "No security monitoring"
    },
    "critical_skill_dependency": {
        "pattern": r"single.*person|key.*man|sole.*admin|one.*person.*knows",
        "bump_to": "mid",
        "description": "Critical skill dependency"
    }
}

# Severity scores
SEVERITY_SCORES = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1
}


# =============================================================================
# WORK ITEM CATEGORIZATION
# =============================================================================

def categorize_work_item(title: str, description: str = "") -> str:
    """
    Categorize a work item based on keywords.
    Returns the cost category for lookup.
    """
    text = f"{title} {description}".lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "default"


# =============================================================================
# DETERMINISTIC COST CALCULATION
# =============================================================================

def normalize_phase(phase: str) -> str:
    """Normalize phase string to standard format."""
    phase_map = {
        "day_1": "Day_1", "day1": "Day_1", "day 1": "Day_1",
        "day_100": "Day_100", "day100": "Day_100", "day 100": "Day_100",
        "post_100": "Post_100", "post100": "Post_100", "post-100": "Post_100", "post 100": "Post_100"
    }
    return phase_map.get(phase.lower().replace(" ", "_"), "Day_100")


def calculate_work_item_cost(
    title: str,
    description: str,
    phase: str,
    company_profile: CompanyProfile = None
) -> Tuple[int, int]:
    """
    Calculate cost for a single work item.

    Args:
        title: Work item title
        description: Work item description
        phase: Integration phase (Day_1, Day_100, Post_100)
        company_profile: Optional company profile for cost adjustment

    Returns:
        (low, high) cost in dollars, adjusted for company profile
    """
    category = categorize_work_item(title, description)
    costs = COST_TABLE.get(category, COST_TABLE["default"])
    normalized_phase = normalize_phase(phase)

    base_low, base_high = costs.get(normalized_phase, costs.get("Day_100", (50_000, 200_000)))

    # Apply company profile multiplier if provided
    if company_profile:
        multiplier, _ = company_profile.get_total_multiplier()
        adjusted_low = int(base_low * multiplier)
        adjusted_high = int(base_high * multiplier)
        return adjusted_low, adjusted_high

    return base_low, base_high


def calculate_total_costs(
    work_items: List[Dict],
    company_profile: CompanyProfile = None
) -> Dict[str, Any]:
    """
    Calculate total costs across all work items with full methodology breakdown.

    Args:
        work_items: List of work item dicts with 'title', 'description', 'phase'
        company_profile: Optional company profile for cost adjustment

    Returns:
        {
            "by_phase": {"Day_1": {"low": X, "high": Y}, ...},
            "total": {"low": X, "high": Y},
            "breakdown": [{"title": ..., "category": ..., "cost": ...}],
            "methodology": {...}  # Full explanation of how costs were calculated
        }
    """
    # Get multiplier info
    if company_profile:
        total_multiplier, multiplier_breakdown = company_profile.get_total_multiplier()
    else:
        total_multiplier = 1.0
        multiplier_breakdown = {
            "note": "No company profile provided - using mid-market baseline",
            "total_multiplier": 1.0
        }

    totals = {
        "Day_1": {"low": 0, "high": 0, "count": 0, "base_low": 0, "base_high": 0},
        "Day_100": {"low": 0, "high": 0, "count": 0, "base_low": 0, "base_high": 0},
        "Post_100": {"low": 0, "high": 0, "count": 0, "base_low": 0, "base_high": 0}
    }
    breakdown = []

    for wi in work_items:
        title = wi.get("title", "")
        description = wi.get("description", "")
        phase = wi.get("phase", "Day_100")
        normalized_phase = normalize_phase(phase)

        # Get base cost (without multiplier)
        category = categorize_work_item(title, description)
        base_costs = COST_TABLE.get(category, COST_TABLE["default"])
        base_low, base_high = base_costs.get(normalized_phase, (50_000, 200_000))

        # Get adjusted cost (with multiplier)
        adjusted_low, adjusted_high = calculate_work_item_cost(
            title, description, normalized_phase, company_profile
        )

        # Track both base and adjusted
        totals[normalized_phase]["base_low"] += base_low
        totals[normalized_phase]["base_high"] += base_high
        totals[normalized_phase]["low"] += adjusted_low
        totals[normalized_phase]["high"] += adjusted_high
        totals[normalized_phase]["count"] += 1

        breakdown.append({
            "title": title,
            "phase": normalized_phase,
            "category": category,
            "base_cost_low": base_low,
            "base_cost_high": base_high,
            "adjusted_cost_low": adjusted_low,
            "adjusted_cost_high": adjusted_high,
            "multiplier_applied": total_multiplier
        })

    # Calculate totals
    base_total = {
        "low": sum(t["base_low"] for t in totals.values()),
        "high": sum(t["base_high"] for t in totals.values())
    }
    adjusted_total = {
        "low": sum(t["low"] for t in totals.values()),
        "high": sum(t["high"] for t in totals.values())
    }

    # Build methodology explanation
    methodology = {
        "approach": "Deterministic cost calculation using category-based lookup tables",
        "base_costs": "Mid-market benchmarks (250-500 employees, single country, standard IT maturity)",
        "adjustments_applied": multiplier_breakdown,
        "formula": f"Final Cost = Base Cost × {total_multiplier}",
        "base_total": f"${base_total['low']:,} - ${base_total['high']:,}",
        "adjusted_total": f"${adjusted_total['low']:,} - ${adjusted_total['high']:,}",
        "categories_used": list(set(item["category"] for item in breakdown)),
        "work_item_count": len(work_items),
        "sources": [
            "Industry research and benchmarks",
            "PE deal retrospectives",
            "IT integration consulting data"
        ],
        "notes": [
            "Costs are estimates and should be validated with target-specific data",
            "Actual costs may vary ±30% based on target IT complexity",
            "Excludes internal labor costs unless explicitly stated"
        ]
    }

    return {
        "by_phase": totals,
        "total": adjusted_total,
        "base_total": base_total,
        "breakdown": breakdown,
        "methodology": methodology,
        "multiplier_applied": total_multiplier,
        "formatted": {
            "Day_1": f"${totals['Day_1']['low']:,} - ${totals['Day_1']['high']:,}",
            "Day_100": f"${totals['Day_100']['low']:,} - ${totals['Day_100']['high']:,}",
            "Post_100": f"${totals['Post_100']['low']:,} - ${totals['Post_100']['high']:,}",
            "Total": f"${adjusted_total['low']:,} - ${adjusted_total['high']:,}",
            "Base_Total": f"${base_total['low']:,} - ${base_total['high']:,} (before adjustments)"
        }
    }


# =============================================================================
# RULE-BASED COMPLEXITY SCORING
# =============================================================================

def check_complexity_flags(texts: List[str]) -> List[Dict]:
    """
    Check for complexity flags in a list of texts.

    Args:
        texts: List of text strings to check (titles, descriptions, etc.)

    Returns:
        List of triggered flags with their bump levels
    """
    combined_text = " ".join(texts).lower()
    triggered = []

    for flag_name, flag_config in COMPLEXITY_FLAGS.items():
        if re.search(flag_config["pattern"], combined_text, re.IGNORECASE):
            triggered.append({
                "flag": flag_name,
                "bump_to": flag_config["bump_to"],
                "description": flag_config["description"]
            })

    return triggered


def calculate_complexity_score(
    risks: List[Dict],
    gaps: List[Dict],
    work_items: List[Dict],
    all_texts: List[str] = None
) -> Dict[str, Any]:
    """
    Calculate complexity tier using RULES, not LLM vibes.

    Args:
        risks: List of risk dicts with 'severity'
        gaps: List of gap dicts with 'importance'
        work_items: List of work item dicts
        all_texts: Optional list of all text for flag checking

    Returns:
        {
            "tier": "low" | "mid" | "high" | "critical",
            "score": int,
            "breakdown": {...},
            "flags_triggered": [...]
        }
    """
    score = 0
    breakdown = {
        "critical_risks": 0,
        "high_risks": 0,
        "medium_risks": 0,
        "low_risks": 0,
        "critical_gaps": 0,
        "high_gaps": 0,
        "work_item_count": len(work_items),
        "base_score": 0,
        "flag_adjustments": []
    }

    # Count risks by severity
    for risk in risks:
        severity = risk.get("severity", "medium").lower()
        if severity == "critical":
            breakdown["critical_risks"] += 1
            score += 15
        elif severity == "high":
            breakdown["high_risks"] += 1
            score += 8
        elif severity == "medium":
            breakdown["medium_risks"] += 1
            score += 3
        else:
            breakdown["low_risks"] += 1
            score += 1

    # Count gaps by importance
    for gap in gaps:
        importance = gap.get("importance", "medium").lower()
        if importance in ["critical", "high"]:
            breakdown["critical_gaps"] += 1
            score += 5
        else:
            breakdown["high_gaps"] += 1
            score += 2

    # Work item complexity
    score += len(work_items) * 2

    breakdown["base_score"] = score

    # Check for complexity flags
    if all_texts:
        flags = check_complexity_flags(all_texts)
    else:
        # Build texts from provided data
        texts = []
        for r in risks:
            texts.append(r.get("title", ""))
            texts.append(r.get("description", ""))
        for g in gaps:
            texts.append(g.get("description", ""))
        for w in work_items:
            texts.append(w.get("title", ""))
            texts.append(w.get("description", ""))
        flags = check_complexity_flags(texts)

    breakdown["flags_triggered"] = flags

    # Determine tier from score
    if score >= 60:
        tier = "critical"
    elif score >= 35:
        tier = "high"
    elif score >= 15:
        tier = "mid"
    else:
        tier = "low"

    # Apply flag bumps (can only increase tier)
    tier_order = ["low", "mid", "high", "critical"]
    current_tier_idx = tier_order.index(tier)

    for flag in flags:
        flag_tier_idx = tier_order.index(flag["bump_to"])
        if flag_tier_idx > current_tier_idx:
            current_tier_idx = flag_tier_idx
            breakdown["flag_adjustments"].append(
                f"Bumped to {flag['bump_to']} due to: {flag['description']}"
            )

    final_tier = tier_order[current_tier_idx]

    return {
        "tier": final_tier,
        "score": score,
        "breakdown": breakdown,
        "flags_triggered": flags
    }


# =============================================================================
# STABLE TOP RISKS SELECTION
# =============================================================================

def score_risk(risk: Dict, verified_fact_ids: List[str] = None) -> int:
    """
    Score a risk deterministically for ranking.

    Higher score = more important = more likely to be Top Risk.
    """
    score = 0
    verified_fact_ids = verified_fact_ids or []

    # Base severity score
    severity = risk.get("severity", "medium").lower()
    severity_base = {
        "critical": 100,
        "high": 75,
        "medium": 50,
        "low": 25
    }
    score += severity_base.get(severity, 50)

    # Evidence strength (more citations = stronger)
    citations = risk.get("based_on_facts", [])
    score += len(citations) * 10

    # Verified citations boost
    verified_count = sum(1 for fid in citations if fid in verified_fact_ids)
    score += verified_count * 15

    # Integration-dependent risks get boost
    if risk.get("integration_dependent", False):
        score += 20

    # Domain priority
    domain_priority = {
        "cybersecurity": 15,
        "infrastructure": 10,
        "applications": 10,
        "identity_access": 8,
        "organization": 5,
        "network": 5
    }
    score += domain_priority.get(risk.get("domain", ""), 0)

    # Confidence boost
    confidence = risk.get("confidence", "medium").lower()
    confidence_boost = {"high": 10, "medium": 5, "low": 0}
    score += confidence_boost.get(confidence, 5)

    return score


def get_top_risks(risks: List[Dict], n: int = 5, verified_fact_ids: List[str] = None) -> List[Dict]:
    """
    Get top N risks by deterministic score.

    Args:
        risks: List of risk dicts
        n: Number of top risks to return
        verified_fact_ids: List of verified fact IDs for scoring boost

    Returns:
        Top N risks, sorted by score descending
    """
    verified_fact_ids = verified_fact_ids or []

    # Score all risks
    scored = []
    for risk in risks:
        risk_score = score_risk(risk, verified_fact_ids)
        scored.append((risk, risk_score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return top N with scores attached
    top = []
    for risk, risk_score in scored[:n]:
        risk_with_score = dict(risk)
        risk_with_score["_consistency_score"] = risk_score
        top.append(risk_with_score)

    return top


# =============================================================================
# CONFIDENCE CALCULATION
# =============================================================================

def calculate_confidence(
    total_facts: int,
    verified_facts: int,
    gap_count: int,
    source_count: int,
    expected_sources: int = 5
) -> Dict[str, Any]:
    """
    Calculate data confidence score.

    Returns:
        {
            "score": 0.0-1.0,
            "label": "High" | "Medium" | "Low",
            "percentage": "75%",
            "factors": {...}
        }
    """
    if total_facts == 0:
        return {
            "score": 0.0,
            "label": "Low",
            "percentage": "0%",
            "factors": {"note": "No facts available"}
        }

    # Verification rate (50% weight)
    verification_rate = verified_facts / total_facts

    # Source coverage (30% weight)
    source_coverage = min(source_count / expected_sources, 1.0)

    # Gap penalty (up to 20% penalty)
    gap_penalty = min(gap_count * 0.03, 0.20)

    # Calculate final score
    score = (verification_rate * 0.50) + (source_coverage * 0.30) - gap_penalty
    score = max(0.0, min(1.0, score))  # Clamp to 0-1

    # Determine label
    if score >= 0.70:
        label = "High"
    elif score >= 0.40:
        label = "Medium"
    else:
        label = "Low"

    return {
        "score": round(score, 2),
        "label": label,
        "percentage": f"{int(score * 100)}%",
        "factors": {
            "verification_rate": f"{int(verification_rate * 100)}%",
            "verified_facts": f"{verified_facts}/{total_facts}",
            "source_coverage": f"{source_count}/{expected_sources} sources",
            "gap_count": gap_count,
            "gap_penalty": f"-{int(gap_penalty * 100)}%"
        }
    }


# =============================================================================
# MAIN CONSISTENCY REPORT
# =============================================================================

def generate_consistency_report(
    facts: List[Dict],
    gaps: List[Dict],
    risks: List[Dict],
    work_items: List[Dict],
    verified_fact_ids: List[str] = None,
    source_documents: List[str] = None,
    company_profile: CompanyProfile = None,
    all_texts: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete consistency report with full methodology documentation.

    This is the main entry point that calculates ALL deterministic metrics.

    Args:
        facts: List of fact dicts
        gaps: List of gap dicts
        risks: List of risk dicts
        work_items: List of work item dicts
        verified_fact_ids: List of verified fact IDs
        source_documents: List of source document names
        company_profile: Optional CompanyProfile for cost adjustments
        all_texts: Optional list of all text for flag checking

    Returns:
        {
            "complexity": {...},
            "costs": {...},
            "top_risks": [...],
            "confidence": {...},
            "counts": {...},
            "company_profile": {...},
            "methodology_summary": "...",
            "generated_at": "..."
        }
    """
    verified_fact_ids = verified_fact_ids or []
    source_documents = source_documents or []

    # Use default mid-market profile if none provided
    if company_profile is None:
        company_profile = CompanyProfile()  # Defaults to mid-market

    # Counts (deterministic)
    counts = {
        "facts": len(facts),
        "gaps": len(gaps),
        "risks": len(risks),
        "work_items": len(work_items),
        "verified_facts": len(verified_fact_ids),
        "source_documents": len(source_documents)
    }

    # Build texts for flag checking if not provided
    if all_texts is None:
        all_texts = []
        for f in facts:
            all_texts.append(f.get("item", ""))
        for g in gaps:
            all_texts.append(g.get("description", ""))
        for r in risks:
            all_texts.append(r.get("title", ""))
            all_texts.append(r.get("description", ""))
        for w in work_items:
            all_texts.append(w.get("title", ""))
            all_texts.append(w.get("description", ""))

    # Calculate complexity
    complexity = calculate_complexity_score(risks, gaps, work_items, all_texts)

    # Calculate costs with company profile adjustment
    costs = calculate_total_costs(work_items, company_profile)

    # Get top risks
    top_risks = get_top_risks(risks, n=5, verified_fact_ids=verified_fact_ids)

    # Calculate confidence
    confidence = calculate_confidence(
        total_facts=len(facts),
        verified_facts=len(verified_fact_ids),
        gap_count=len(gaps),
        source_count=len(source_documents)
    )

    # Get company profile breakdown
    total_multiplier, profile_breakdown = company_profile.get_total_multiplier()

    # Build methodology summary
    methodology_summary = f"""
COST METHODOLOGY:
- Base costs: Mid-market benchmarks (250-500 employees)
- Company size: {company_profile.employee_count} employees → {profile_breakdown['size']['multiplier']}x
- Industry: {company_profile.industry} → {profile_breakdown['industry']['multiplier']}x
- Geography: {company_profile.geography} → {profile_breakdown['geography']['multiplier']}x
- IT Maturity: {company_profile.it_maturity} → {profile_breakdown['it_maturity']['multiplier']}x
- Total multiplier: {total_multiplier}x

COMPLEXITY METHODOLOGY:
- Score: {complexity['score']} points
- Tier: {complexity['tier'].upper()}
- Critical risks: {complexity['breakdown']['critical_risks']} (15 pts each)
- High risks: {complexity['breakdown']['high_risks']} (8 pts each)
- Flags triggered: {len(complexity['flags_triggered'])}

CONFIDENCE: {confidence['label']} ({confidence['percentage']})
    """.strip()

    return {
        "complexity": complexity,
        "costs": costs,
        "top_risks": top_risks,
        "confidence": confidence,
        "counts": counts,
        "company_profile": {
            "employee_count": company_profile.employee_count,
            "industry": company_profile.industry,
            "geography": company_profile.geography,
            "it_maturity": company_profile.it_maturity,
            "multiplier_breakdown": profile_breakdown
        },
        "methodology_summary": methodology_summary,
        "generated_at": datetime.now().isoformat()
    }
