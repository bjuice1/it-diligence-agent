"""
Consistency Engine - Rule-Based Scoring & Deterministic Calculations

This module ensures consistent outputs by replacing LLM "vibes" with:
1. Rule-based complexity scoring
2. Deterministic cost calculation from lookup tables
3. Stable Top Risks selection by score
4. Confidence metrics

NO LLM judgment in this module - pure computation.
"""

import re
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# =============================================================================
# COST LOOKUP TABLE (Deterministic)
# =============================================================================

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

def calculate_work_item_cost(title: str, description: str, phase: str) -> Tuple[int, int]:
    """
    Calculate cost for a single work item.

    Returns:
        (low, high) cost in dollars
    """
    category = categorize_work_item(title, description)
    costs = COST_TABLE.get(category, COST_TABLE["default"])

    # Normalize phase
    phase_map = {
        "day_1": "Day_1",
        "day_100": "Day_100",
        "day100": "Day_100",
        "post_100": "Post_100",
        "post100": "Post_100",
        "post-100": "Post_100"
    }
    normalized_phase = phase_map.get(phase.lower().replace(" ", "_"), phase)

    phase_costs = costs.get(normalized_phase, costs.get("Day_100", (50_000, 200_000)))
    return phase_costs


def calculate_total_costs(work_items: List[Dict]) -> Dict[str, Any]:
    """
    Calculate total costs across all work items.

    Args:
        work_items: List of work item dicts with 'title', 'description', 'phase'

    Returns:
        {
            "by_phase": {"Day_1": {"low": X, "high": Y}, ...},
            "total": {"low": X, "high": Y},
            "breakdown": [{"title": ..., "category": ..., "cost": ...}]
        }
    """
    totals = {
        "Day_1": {"low": 0, "high": 0, "count": 0},
        "Day_100": {"low": 0, "high": 0, "count": 0},
        "Post_100": {"low": 0, "high": 0, "count": 0}
    }
    breakdown = []

    for wi in work_items:
        title = wi.get("title", "")
        description = wi.get("description", "")
        phase = wi.get("phase", "Day_100")

        # Normalize phase
        phase_map = {
            "day_1": "Day_1", "day1": "Day_1",
            "day_100": "Day_100", "day100": "Day_100",
            "post_100": "Post_100", "post100": "Post_100", "post-100": "Post_100"
        }
        normalized_phase = phase_map.get(phase.lower().replace(" ", "_"), "Day_100")

        low, high = calculate_work_item_cost(title, description, normalized_phase)
        category = categorize_work_item(title, description)

        totals[normalized_phase]["low"] += low
        totals[normalized_phase]["high"] += high
        totals[normalized_phase]["count"] += 1

        breakdown.append({
            "title": title,
            "phase": normalized_phase,
            "category": category,
            "cost_low": low,
            "cost_high": high
        })

    grand_total = {
        "low": sum(t["low"] for t in totals.values()),
        "high": sum(t["high"] for t in totals.values())
    }

    return {
        "by_phase": totals,
        "total": grand_total,
        "breakdown": breakdown,
        "formatted": {
            "Day_1": f"${totals['Day_1']['low']:,} - ${totals['Day_1']['high']:,}",
            "Day_100": f"${totals['Day_100']['low']:,} - ${totals['Day_100']['high']:,}",
            "Post_100": f"${totals['Post_100']['low']:,} - ${totals['Post_100']['high']:,}",
            "Total": f"${grand_total['low']:,} - ${grand_total['high']:,}"
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
    source_documents: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete consistency report.

    This is the main entry point that calculates ALL deterministic metrics.

    Returns:
        {
            "complexity": {...},
            "costs": {...},
            "top_risks": [...],
            "confidence": {...},
            "counts": {...},
            "generated_at": "..."
        }
    """
    verified_fact_ids = verified_fact_ids or []
    source_documents = source_documents or []

    # Counts (deterministic)
    counts = {
        "facts": len(facts),
        "gaps": len(gaps),
        "risks": len(risks),
        "work_items": len(work_items),
        "verified_facts": len(verified_fact_ids),
        "source_documents": len(source_documents)
    }

    # Build texts for flag checking
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

    # Calculate costs
    costs = calculate_total_costs(work_items)

    # Get top risks
    top_risks = get_top_risks(risks, n=5, verified_fact_ids=verified_fact_ids)

    # Calculate confidence
    confidence = calculate_confidence(
        total_facts=len(facts),
        verified_facts=len(verified_fact_ids),
        gap_count=len(gaps),
        source_count=len(source_documents)
    )

    return {
        "complexity": complexity,
        "costs": costs,
        "top_risks": top_risks,
        "confidence": confidence,
        "counts": counts,
        "generated_at": datetime.now().isoformat()
    }
