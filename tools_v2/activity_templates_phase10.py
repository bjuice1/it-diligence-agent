"""
Phase 10: Validation & Refinement - Activity Templates

This phase provides:
1. Cross-phase validation utilities
2. Unified activity catalog
3. Deal scenario estimation
4. Cost model calibration tools
5. Activity coverage analysis

This is the capstone module that ties all phases together.
"""

from typing import Dict, List, Tuple, Any, Optional
import json

# Import all phase modules
from tools_v2.activity_templates_v2 import (
    get_phase1_templates,
    calculate_activity_cost,
    COMPLEXITY_MULTIPLIERS,
    INDUSTRY_MODIFIERS,
)
from tools_v2.activity_templates_phase2 import (
    get_phase2_templates,
    calculate_phase2_activity_cost,
)
from tools_v2.activity_templates_phase3 import (
    get_phase3_templates,
    calculate_phase3_activity_cost,
)
from tools_v2.activity_templates_phase4 import (
    get_phase4_templates,
    calculate_phase4_activity_cost,
)
from tools_v2.activity_templates_phase5 import (
    get_phase5_templates,
    calculate_phase5_activity_cost,
)
from tools_v2.activity_templates_phase6 import (
    get_phase6_templates,
    calculate_phase6_activity_cost,
)
from tools_v2.activity_templates_phase7 import (
    get_phase7_templates,
    calculate_phase7_activity_cost,
    calculate_it_staffing_needs,
)
from tools_v2.activity_templates_phase8 import (
    get_phase8_templates,
    calculate_phase8_activity_cost,
    get_regulatory_requirements,
)
from tools_v2.activity_templates_phase9 import (
    get_phase9_templates,
    calculate_phase9_activity_cost,
    estimate_contract_transition_costs,
)


# =============================================================================
# UNIFIED ACTIVITY CATALOG
# =============================================================================

def get_all_templates() -> Dict[str, Dict]:
    """
    Get all activity templates from all phases.

    Returns:
        Dict with phase keys and their template dictionaries
    """
    return {
        "phase1_foundation": get_phase1_templates(),
        "phase2_applications": get_phase2_templates(),
        "phase3_infrastructure": get_phase3_templates(),
        "phase4_end_user": get_phase4_templates(),
        "phase5_security": get_phase5_templates(),
        "phase6_data": get_phase6_templates(),
        "phase7_operations": get_phase7_templates(),
        "phase8_compliance": get_phase8_templates(),
        "phase9_vendor": get_phase9_templates(),
    }


def get_activity_by_id(activity_id: str) -> Optional[Dict]:
    """
    Find an activity by ID across all phases.

    Args:
        activity_id: Activity identifier (e.g., "FND-DIS-001", "APP-INV-001")

    Returns:
        Activity dict or None if not found
    """
    all_templates = get_all_templates()

    for phase_name, phase_templates in all_templates.items():
        for category, workstreams in phase_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    if activity.get("id") == activity_id:
                        activity["_source_phase"] = phase_name
                        activity["_source_category"] = category
                        activity["_source_workstream"] = workstream
                        return activity

    return None


def get_unified_activity_catalog() -> List[Dict]:
    """
    Get a flat list of all activities with phase/category metadata.

    Returns:
        List of all activities with source metadata
    """
    catalog = []
    all_templates = get_all_templates()

    for phase_name, phase_templates in all_templates.items():
        for category, workstreams in phase_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    entry = activity.copy()
                    entry["_source_phase"] = phase_name
                    entry["_source_category"] = category
                    entry["_source_workstream"] = workstream
                    catalog.append(entry)

    return catalog


def get_activity_count_by_phase() -> Dict[str, int]:
    """Get activity counts by phase."""
    counts = {}
    all_templates = get_all_templates()

    for phase_name, phase_templates in all_templates.items():
        count = 0
        for category, workstreams in phase_templates.items():
            for workstream, activities in workstreams.items():
                count += len(activities)
        counts[phase_name] = count

    return counts


# =============================================================================
# DEAL SCENARIO ESTIMATION
# =============================================================================

# Deal type profiles with typical activity scopes
DEAL_PROFILES = {
    "carveout_small": {
        "description": "Small carveout (< 500 users)",
        "user_count": 300,
        "app_count": 15,
        "vm_count": 30,
        "database_count": 10,
        "site_count": 3,
        "vendor_count": 25,
        "contract_count": 40,
        "complexity": "simple",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data",
                          "phase8_compliance", "phase9_vendor"],
        "annual_ops_needed": True,
    },
    "carveout_medium": {
        "description": "Medium carveout (500-2,000 users)",
        "user_count": 1200,
        "app_count": 50,
        "vm_count": 150,
        "database_count": 35,
        "site_count": 8,
        "vendor_count": 75,
        "contract_count": 120,
        "complexity": "moderate",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data",
                          "phase8_compliance", "phase9_vendor"],
        "annual_ops_needed": True,
    },
    "carveout_large": {
        "description": "Large carveout (2,000-10,000 users)",
        "user_count": 5000,
        "app_count": 150,
        "vm_count": 500,
        "database_count": 100,
        "site_count": 20,
        "vendor_count": 150,
        "contract_count": 250,
        "complexity": "complex",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data",
                          "phase8_compliance", "phase9_vendor"],
        "annual_ops_needed": True,
    },
    "carveout_enterprise": {
        "description": "Enterprise carveout (10,000+ users)",
        "user_count": 15000,
        "app_count": 300,
        "vm_count": 1500,
        "database_count": 250,
        "site_count": 50,
        "vendor_count": 300,
        "contract_count": 500,
        "complexity": "highly_complex",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data",
                          "phase8_compliance", "phase9_vendor"],
        "annual_ops_needed": True,
    },
    "bolt_on_small": {
        "description": "Small bolt-on acquisition",
        "user_count": 100,
        "app_count": 8,
        "vm_count": 15,
        "database_count": 5,
        "site_count": 1,
        "vendor_count": 10,
        "contract_count": 15,
        "complexity": "simple",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data", "phase9_vendor"],
        "annual_ops_needed": False,  # Usually absorb into acquirer ops
    },
    "bolt_on_medium": {
        "description": "Medium bolt-on acquisition",
        "user_count": 500,
        "app_count": 25,
        "vm_count": 60,
        "database_count": 15,
        "site_count": 3,
        "vendor_count": 30,
        "contract_count": 50,
        "complexity": "moderate",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data",
                          "phase8_compliance", "phase9_vendor"],
        "annual_ops_needed": False,
    },
    "standalone": {
        "description": "Standalone company acquisition",
        "user_count": 2000,
        "app_count": 80,
        "vm_count": 200,
        "database_count": 50,
        "site_count": 10,
        "vendor_count": 100,
        "contract_count": 150,
        "complexity": "moderate",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data",
                          "phase7_operations", "phase8_compliance", "phase9_vendor"],
        "annual_ops_needed": True,  # Keep ops as-is
    },
    "integration_full": {
        "description": "Full integration into acquirer",
        "user_count": 3000,
        "app_count": 100,
        "vm_count": 300,
        "database_count": 75,
        "site_count": 15,
        "vendor_count": 80,
        "contract_count": 120,
        "complexity": "complex",
        "phases_included": ["phase1_foundation", "phase2_applications", "phase3_infrastructure",
                          "phase4_end_user", "phase5_security", "phase6_data", "phase9_vendor"],
        "annual_ops_needed": False,  # Will use acquirer ops
    },
}


def estimate_deal_costs(
    deal_type: str = "carveout_medium",
    industry: str = "standard",
    custom_params: Dict = None,
    include_annual_ops: bool = None,
) -> Dict[str, Any]:
    """
    Estimate total IT M&A costs for a deal scenario.

    Args:
        deal_type: One of DEAL_PROFILES keys
        industry: Industry for cost modifiers
        custom_params: Override default parameters
        include_annual_ops: Override whether to include Phase 7 annual ops

    Returns:
        Dict with cost breakdown by phase and total
    """
    if deal_type not in DEAL_PROFILES:
        raise ValueError(f"Unknown deal type: {deal_type}. Valid: {list(DEAL_PROFILES.keys())}")

    profile = DEAL_PROFILES[deal_type].copy()
    if custom_params:
        profile.update(custom_params)

    # Determine if annual ops should be included
    if include_annual_ops is not None:
        include_ops = include_annual_ops
    else:
        include_ops = profile.get("annual_ops_needed", True)

    # Build base parameters for cost calculation
    base_params = {
        "user_count": profile.get("user_count", 1000),
        "app_count": profile.get("app_count", 30),
        "vm_count": profile.get("vm_count", 100),
        "database_count": profile.get("database_count", 20),
        "site_count": profile.get("site_count", 8),
        "vendor_count": profile.get("vendor_count", 50),
        "contract_count": profile.get("contract_count", 100),
        "complexity": profile.get("complexity", "moderate"),
        "industry": industry,
    }

    # Define parameter sets accepted by each phase's calculation function
    # (Different phases have different parameter signatures based on their focus)
    phase_params = {
        "phase1_foundation": ["user_count", "app_count", "vm_count", "database_count", "complexity", "industry"],
        "phase2_applications": ["user_count", "site_count", "complexity", "industry"],
        "phase3_infrastructure": ["user_count", "app_count", "contract_count", "complexity", "industry"],
        "phase4_end_user": ["user_count", "database_count", "site_count", "complexity", "industry"],
        "phase5_security": ["user_count", "database_count", "vm_count", "app_count", "complexity", "industry"],
        "phase6_data": ["user_count", "site_count", "vm_count", "app_count", "complexity", "industry"],
        "phase7_operations": ["user_count", "vm_count", "database_count", "app_count", "site_count", "complexity", "industry"],
        "phase8_compliance": ["user_count", "vendor_count", "site_count", "complexity", "industry"],
        "phase9_vendor": ["contract_count", "vendor_count", "complexity", "industry"],
    }

    # Map phases to their calculation functions
    phase_calculators = {
        "phase1_foundation": (get_phase1_templates, calculate_activity_cost),
        "phase2_applications": (get_phase2_templates, calculate_phase2_activity_cost),
        "phase3_infrastructure": (get_phase3_templates, calculate_phase3_activity_cost),
        "phase4_end_user": (get_phase4_templates, calculate_phase4_activity_cost),
        "phase5_security": (get_phase5_templates, calculate_phase5_activity_cost),
        "phase6_data": (get_phase6_templates, calculate_phase6_activity_cost),
        "phase7_operations": (get_phase7_templates, calculate_phase7_activity_cost),
        "phase8_compliance": (get_phase8_templates, calculate_phase8_activity_cost),
        "phase9_vendor": (get_phase9_templates, calculate_phase9_activity_cost),
    }

    # Store all params for reference but use phase-specific when calculating
    params = base_params

    results = {
        "deal_type": deal_type,
        "description": profile.get("description", ""),
        "parameters": params,
        "phases": {},
        "one_time_costs": {"low": 0, "high": 0},
        "annual_costs": {"low": 0, "high": 0},
        "total_costs": {"low": 0, "high": 0},
    }

    # Calculate costs for each included phase
    phases_to_include = profile.get("phases_included", list(phase_calculators.keys()))

    # Skip Phase 7 if not including annual ops
    if not include_ops and "phase7_operations" in phases_to_include:
        phases_to_include = [p for p in phases_to_include if p != "phase7_operations"]

    for phase_name in phases_to_include:
        if phase_name not in phase_calculators:
            continue

        get_templates, calc_cost = phase_calculators[phase_name]
        templates = get_templates()

        # Get phase-specific parameters
        allowed_params = phase_params.get(phase_name, list(base_params.keys()))
        calc_params = {k: v for k, v in base_params.items() if k in allowed_params}

        phase_low = 0
        phase_high = 0
        activity_count = 0

        for category, workstreams in templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    low, high, _ = calc_cost(activity, **calc_params)
                    phase_low += low
                    phase_high += high
                    activity_count += 1

        results["phases"][phase_name] = {
            "low": phase_low,
            "high": phase_high,
            "activities": activity_count,
        }

        # Phase 7 is annual, others are one-time
        if phase_name == "phase7_operations":
            results["annual_costs"]["low"] += phase_low
            results["annual_costs"]["high"] += phase_high
        else:
            results["one_time_costs"]["low"] += phase_low
            results["one_time_costs"]["high"] += phase_high

    results["total_costs"]["low"] = results["one_time_costs"]["low"] + results["annual_costs"]["low"]
    results["total_costs"]["high"] = results["one_time_costs"]["high"] + results["annual_costs"]["high"]

    return results


def compare_deal_scenarios(
    scenarios: List[str] = None,
    industry: str = "standard",
) -> Dict[str, Dict]:
    """
    Compare costs across multiple deal scenarios.

    Args:
        scenarios: List of deal types to compare (default: all)
        industry: Industry for cost modifiers

    Returns:
        Dict with comparison data
    """
    if scenarios is None:
        scenarios = list(DEAL_PROFILES.keys())

    comparison = {}

    for scenario in scenarios:
        if scenario in DEAL_PROFILES:
            comparison[scenario] = estimate_deal_costs(scenario, industry)

    return comparison


# =============================================================================
# ACTIVITY COVERAGE ANALYSIS
# =============================================================================

def analyze_activity_coverage() -> Dict[str, Any]:
    """
    Analyze activity coverage across all phases.

    Returns:
        Dict with coverage analysis
    """
    catalog = get_unified_activity_catalog()

    analysis = {
        "total_activities": len(catalog),
        "by_phase": {},
        "by_activity_type": {},
        "tsa_activities": [],
        "cost_model_distribution": {},
    }

    # Analyze by phase
    for activity in catalog:
        phase = activity.get("_source_phase", "unknown")
        if phase not in analysis["by_phase"]:
            analysis["by_phase"][phase] = {"count": 0, "workstreams": set()}
        analysis["by_phase"][phase]["count"] += 1
        analysis["by_phase"][phase]["workstreams"].add(activity.get("_source_workstream", "unknown"))

        # By activity type
        act_type = activity.get("activity_type", "unknown")
        if act_type not in analysis["by_activity_type"]:
            analysis["by_activity_type"][act_type] = 0
        analysis["by_activity_type"][act_type] += 1

        # TSA tracking
        if activity.get("requires_tsa"):
            analysis["tsa_activities"].append({
                "id": activity.get("id"),
                "name": activity.get("name"),
                "duration": activity.get("tsa_duration", (0, 0)),
            })

        # Cost model distribution
        cost_fields = ["base_cost", "per_user_cost", "per_vm_cost", "per_app_cost",
                      "per_site_cost", "per_contract_cost", "per_vendor_cost"]
        for field in cost_fields:
            if field in activity:
                if field not in analysis["cost_model_distribution"]:
                    analysis["cost_model_distribution"][field] = 0
                analysis["cost_model_distribution"][field] += 1

    # Convert sets to lists for JSON serialization
    for phase in analysis["by_phase"]:
        analysis["by_phase"][phase]["workstreams"] = list(analysis["by_phase"][phase]["workstreams"])

    return analysis


def get_activities_by_type(activity_type: str) -> List[Dict]:
    """Get all activities of a specific type."""
    catalog = get_unified_activity_catalog()
    return [a for a in catalog if a.get("activity_type") == activity_type]


def get_tsa_activities() -> List[Dict]:
    """Get all activities that require TSA."""
    catalog = get_unified_activity_catalog()
    return [a for a in catalog if a.get("requires_tsa")]


def get_activities_by_workstream(workstream: str) -> List[Dict]:
    """Get all activities in a specific workstream."""
    catalog = get_unified_activity_catalog()
    return [a for a in catalog if a.get("_source_workstream") == workstream]


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_activity_structure(activity: Dict) -> List[str]:
    """
    Validate an activity has required structure.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_vm_cost", "per_app_cost",
                  "per_site_cost", "per_contract_cost", "per_vendor_cost",
                  "per_database_cost", "per_device_cost", "per_integration_cost"]

    for field in required_fields:
        if field not in activity:
            errors.append(f"Missing required field: {field}")

    # Must have at least one cost field
    has_cost = any(f in activity for f in cost_fields)
    if not has_cost:
        errors.append("Missing cost field (need at least one cost model)")

    # Validate cost ranges
    for field in cost_fields:
        if field in activity:
            value = activity[field]
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                errors.append(f"{field} must be (low, high) tuple")
            elif value[0] > value[1]:
                errors.append(f"{field} low > high: {value}")

    # Validate TSA duration if requires_tsa is True
    if activity.get("requires_tsa") and "tsa_duration" not in activity:
        errors.append("requires_tsa=True but missing tsa_duration")

    return errors


def validate_all_activities() -> Dict[str, List[str]]:
    """
    Validate all activities across all phases.

    Returns:
        Dict mapping activity IDs to their validation errors
    """
    catalog = get_unified_activity_catalog()
    issues = {}

    for activity in catalog:
        errors = validate_activity_structure(activity)
        if errors:
            issues[activity.get("id", "UNKNOWN")] = errors

    return issues


def check_id_uniqueness() -> List[str]:
    """Check for duplicate activity IDs."""
    catalog = get_unified_activity_catalog()

    seen_ids = {}
    duplicates = []

    for activity in catalog:
        act_id = activity.get("id")
        if act_id in seen_ids:
            duplicates.append(f"{act_id}: Found in {seen_ids[act_id]} and {activity.get('_source_phase')}")
        else:
            seen_ids[act_id] = activity.get("_source_phase")

    return duplicates


# =============================================================================
# COST MODEL CALIBRATION
# =============================================================================

def calibrate_to_target(
    target_total: float,
    deal_type: str = "carveout_medium",
    industry: str = "standard",
) -> Dict[str, Any]:
    """
    Calculate adjustment factor to match a target total cost.

    Args:
        target_total: Target total cost
        deal_type: Deal scenario
        industry: Industry modifier

    Returns:
        Dict with calibration analysis
    """
    estimate = estimate_deal_costs(deal_type, industry)

    current_low = estimate["total_costs"]["low"]
    current_high = estimate["total_costs"]["high"]
    current_mid = (current_low + current_high) / 2

    return {
        "target_total": target_total,
        "current_estimate": {
            "low": current_low,
            "high": current_high,
            "midpoint": current_mid,
        },
        "adjustment_factors": {
            "to_match_low": target_total / current_low if current_low > 0 else 0,
            "to_match_mid": target_total / current_mid if current_mid > 0 else 0,
            "to_match_high": target_total / current_high if current_high > 0 else 0,
        },
        "interpretation": _interpret_calibration(target_total, current_low, current_high),
    }


def _interpret_calibration(target: float, low: float, high: float) -> str:
    """Generate interpretation of calibration result."""
    if target < low:
        return f"Target ${target:,.0f} is below estimate range. Consider reducing scope or using simpler complexity."
    elif target > high:
        return f"Target ${target:,.0f} is above estimate range. May need additional activities or higher complexity."
    else:
        return f"Target ${target:,.0f} is within estimate range. Current cost models appear aligned."


# =============================================================================
# SUMMARY REPORTING
# =============================================================================

def generate_executive_summary(
    deal_type: str = "carveout_medium",
    industry: str = "standard",
) -> str:
    """
    Generate executive summary of IT M&A costs.

    Args:
        deal_type: Deal scenario
        industry: Industry

    Returns:
        Formatted summary string
    """
    estimate = estimate_deal_costs(deal_type, industry)
    profile = DEAL_PROFILES.get(deal_type, {})

    lines = [
        "=" * 70,
        "IT M&A COST ESTIMATE - EXECUTIVE SUMMARY",
        "=" * 70,
        "",
        f"Deal Type: {deal_type}",
        f"Description: {profile.get('description', '')}",
        f"Industry: {industry}",
        f"Complexity: {estimate['parameters']['complexity']}",
        "",
        "KEY METRICS:",
        f"  Users: {estimate['parameters']['user_count']:,}",
        f"  Applications: {estimate['parameters']['app_count']}",
        f"  VMs/Servers: {estimate['parameters']['vm_count']}",
        f"  Sites: {estimate['parameters']['site_count']}",
        f"  Vendors: {estimate['parameters']['vendor_count']}",
        f"  Contracts: {estimate['parameters']['contract_count']}",
        "",
        "COST SUMMARY:",
        f"  One-Time Costs: ${estimate['one_time_costs']['low']:,.0f} - ${estimate['one_time_costs']['high']:,.0f}",
        f"  Annual Run-Rate: ${estimate['annual_costs']['low']:,.0f} - ${estimate['annual_costs']['high']:,.0f}",
        "",
        f"  TOTAL (Year 1): ${estimate['total_costs']['low']:,.0f} - ${estimate['total_costs']['high']:,.0f}",
        "",
        "PHASE BREAKDOWN:",
    ]

    for phase_name, phase_data in sorted(estimate["phases"].items()):
        phase_label = phase_name.replace("_", " ").title()
        lines.append(f"  {phase_label}: ${phase_data['low']:,.0f} - ${phase_data['high']:,.0f} ({phase_data['activities']} activities)")

    lines.extend([
        "",
        "=" * 70,
    ])

    return "\n".join(lines)


def get_phase_summary() -> Dict[str, Dict]:
    """Get summary of all phases."""
    counts = get_activity_count_by_phase()

    phase_info = {
        "phase1_foundation": "Discovery & Planning",
        "phase2_applications": "Application Portfolio",
        "phase3_infrastructure": "Infrastructure & Network",
        "phase4_end_user": "End User Computing",
        "phase5_security": "Security & Identity",
        "phase6_data": "Data & Integration",
        "phase7_operations": "Operational Run-Rate (Annual)",
        "phase8_compliance": "Compliance & Regulatory",
        "phase9_vendor": "Vendor & Contract",
    }

    summary = {}
    for phase, count in counts.items():
        summary[phase] = {
            "name": phase_info.get(phase, phase),
            "activity_count": count,
        }

    return summary
