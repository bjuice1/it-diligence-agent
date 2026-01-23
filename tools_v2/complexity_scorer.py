"""
Deterministic Complexity Scoring for IT Due Diligence

This module provides rule-based complexity scoring that produces consistent
results given the same input data. It replaces the previous prose-based
approach that led to inconsistent ratings across runs.

Complexity is determined by specific, documented triggers - not LLM interpretation.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# COMPLEXITY SCORING RULES
# =============================================================================

@dataclass
class ComplexityTrigger:
    """A specific condition that affects complexity scoring."""
    name: str
    description: str
    points: int  # Positive = increases complexity
    category: str  # For grouping/reporting


# Trigger definitions with clear, deterministic conditions
COMPLEXITY_TRIGGERS = {
    # ----- APPLICATION LANDSCAPE -----
    "dual_erp": ComplexityTrigger(
        name="Dual ERP Systems",
        description="Multiple ERP platforms (e.g., NetSuite + SAP) requiring integration or rationalization",
        points=15,
        category="applications"
    ),
    "legacy_erp": ComplexityTrigger(
        name="Legacy/EOL ERP",
        description="ERP system at or near end-of-life requiring migration",
        points=12,
        category="applications"
    ),
    "custom_apps_critical": ComplexityTrigger(
        name="Critical Custom Applications",
        description="Business-critical custom applications with limited documentation",
        points=10,
        category="applications"
    ),
    "integration_debt": ComplexityTrigger(
        name="Integration Technical Debt",
        description="Point-to-point integrations requiring middleware or consolidation",
        points=8,
        category="applications"
    ),

    # ----- INFRASTRUCTURE -----
    "data_center_migration": ComplexityTrigger(
        name="Data Center Migration Required",
        description="Physical data center requiring exit or consolidation",
        points=15,
        category="infrastructure"
    ),
    "hybrid_cloud_ungoverned": ComplexityTrigger(
        name="Ungoverned Hybrid Cloud",
        description="Multi-cloud or hybrid environment without unified governance",
        points=10,
        category="infrastructure"
    ),
    "eol_infrastructure": ComplexityTrigger(
        name="End-of-Life Infrastructure",
        description="Significant infrastructure at or past end-of-life",
        points=8,
        category="infrastructure"
    ),
    "no_dr_capability": ComplexityTrigger(
        name="No DR Capability",
        description="Missing or untested disaster recovery capability",
        points=12,
        category="infrastructure"
    ),

    # ----- IDENTITY & ACCESS -----
    "no_iam_platform": ComplexityTrigger(
        name="No IAM Platform",
        description="No centralized identity management (IGA/PAM)",
        points=12,
        category="identity"
    ),
    "multiple_directories": ComplexityTrigger(
        name="Multiple Identity Sources",
        description="Multiple disconnected directories requiring consolidation",
        points=8,
        category="identity"
    ),
    "no_pam": ComplexityTrigger(
        name="No Privileged Access Management",
        description="No PAM solution for privileged account control",
        points=10,
        category="identity"
    ),
    "no_sso": ComplexityTrigger(
        name="No Single Sign-On",
        description="No SSO platform requiring user credential consolidation",
        points=6,
        category="identity"
    ),

    # ----- CYBERSECURITY -----
    "no_siem_soc": ComplexityTrigger(
        name="No SIEM/SOC",
        description="No security monitoring or incident detection capability",
        points=12,
        category="cybersecurity"
    ),
    "no_endpoint_protection": ComplexityTrigger(
        name="Inadequate Endpoint Protection",
        description="Missing or outdated endpoint detection and response (EDR)",
        points=10,
        category="cybersecurity"
    ),
    "compliance_gaps": ComplexityTrigger(
        name="Regulatory Compliance Gaps",
        description="Known gaps in regulatory compliance (SOC2, HIPAA, etc.)",
        points=10,
        category="cybersecurity"
    ),
    "no_vuln_management": ComplexityTrigger(
        name="No Vulnerability Management",
        description="No systematic vulnerability scanning or patching program",
        points=8,
        category="cybersecurity"
    ),

    # ----- ORGANIZATION -----
    "key_person_risk": ComplexityTrigger(
        name="Key Person Dependency",
        description="Critical IT knowledge concentrated in few individuals",
        points=8,
        category="organization"
    ),
    "understaffed_it": ComplexityTrigger(
        name="Understaffed IT Function",
        description="IT team undersized for current operational needs",
        points=6,
        category="organization"
    ),
    "no_itil_processes": ComplexityTrigger(
        name="No ITIL/Formal Processes",
        description="Missing change management or ITSM processes",
        points=5,
        category="organization"
    ),

    # ----- NETWORK -----
    "network_undocumented": ComplexityTrigger(
        name="Undocumented Network",
        description="Network architecture not documented or understood",
        points=8,
        category="network"
    ),
    "legacy_wan": ComplexityTrigger(
        name="Legacy WAN Technology",
        description="MPLS or legacy WAN requiring modernization",
        points=6,
        category="network"
    ),
}


# Complexity thresholds (score-based)
COMPLEXITY_THRESHOLDS = {
    "low": (0, 25),       # Score 0-25: Lower-complexity
    "mid": (26, 55),      # Score 26-55: Mid-complexity
    "high": (56, 999),    # Score 56+: High-complexity
}


def _check_fact_for_trigger(fact: Any, trigger_key: str) -> bool:
    """
    Check if a fact indicates a specific complexity trigger.

    This uses keyword matching on fact content - designed to be deterministic.
    """
    if not hasattr(fact, 'item') or not hasattr(fact, 'details'):
        return False

    item_lower = (fact.item or "").lower()
    details_str = str(fact.details or {}).lower()
    category_lower = (getattr(fact, 'category', '') or "").lower()
    combined = f"{item_lower} {details_str} {category_lower}"

    # Trigger-specific keyword patterns
    trigger_patterns = {
        "dual_erp": [
            ("netsuite" in combined and "sap" in combined),
            ("oracle" in combined and "sap" in combined),
            ("multiple erp" in combined),
            ("dual erp" in combined),
            (combined.count("erp") >= 2 and any(x in combined for x in ["migration", "consolidat", "integrat"]))
        ],
        "legacy_erp": [
            ("end of life" in combined and "erp" in combined),
            ("eol" in combined and "erp" in combined),
            ("legacy erp" in combined),
            ("outdated erp" in combined),
        ],
        "custom_apps_critical": [
            ("custom" in combined and "critical" in combined),
            ("proprietary application" in combined),
            ("in-house developed" in combined and any(x in combined for x in ["critical", "core", "essential"])),
        ],
        "data_center_migration": [
            ("data center" in combined and any(x in combined for x in ["exit", "migration", "consolidat", "close", "relocat"])),
            ("colocation" in combined and any(x in combined for x in ["exit", "migration"])),
            ("physical infrastructure" in combined and "migration" in combined),
        ],
        "hybrid_cloud_ungoverned": [
            ("hybrid cloud" in combined and any(x in combined for x in ["governance", "ungoverned", "inconsistent"])),
            ("multi-cloud" in combined and "governance" in combined),
            (("aws" in combined and "azure" in combined) or ("aws" in combined and "gcp" in combined)),
        ],
        "eol_infrastructure": [
            ("end of life" in combined and any(x in combined for x in ["server", "infrastructure", "hardware"])),
            ("eol" in combined and any(x in combined for x in ["server", "infrastructure", "hardware"])),
            ("aging infrastructure" in combined),
        ],
        "no_dr_capability": [
            ("no disaster recovery" in combined),
            ("no dr" in combined and "capabilit" in combined),
            ("dr not tested" in combined),
            ("disaster recovery" in combined and any(x in combined for x in ["missing", "absent", "no ", "lacking"])),
        ],
        "no_iam_platform": [
            ("no iam" in combined),
            ("no identity management" in combined),
            ("no iga" in combined),
            ("identity" in combined and any(x in combined for x in ["missing", "absent", "no centralized"])),
        ],
        "multiple_directories": [
            ("multiple director" in combined),
            ("active directory" in combined and "okta" in combined),
            ("disconnected" in combined and "director" in combined),
        ],
        "no_pam": [
            ("no pam" in combined),
            ("no privileged access" in combined),
            ("pam" in combined and any(x in combined for x in ["missing", "absent", "no ", "lacking"])),
        ],
        "no_sso": [
            ("no sso" in combined),
            ("no single sign" in combined),
            ("sso" in combined and any(x in combined for x in ["missing", "absent", "no "])),
        ],
        "no_siem_soc": [
            ("no siem" in combined),
            ("no soc" in combined),
            ("no security monitoring" in combined),
            ("siem" in combined and any(x in combined for x in ["missing", "absent", "no "])),
        ],
        "no_endpoint_protection": [
            ("no edr" in combined),
            ("no endpoint" in combined),
            ("endpoint protection" in combined and any(x in combined for x in ["missing", "inadequate", "outdated"])),
        ],
        "compliance_gaps": [
            ("compliance gap" in combined),
            ("soc2" in combined and "gap" in combined),
            ("hipaa" in combined and "gap" in combined),
            ("regulatory" in combined and any(x in combined for x in ["gap", "non-compliant", "violation"])),
        ],
        "key_person_risk": [
            ("key person" in combined),
            ("single point of failure" in combined and any(x in combined for x in ["person", "staff", "employee"])),
            ("knowledge" in combined and "concentrated" in combined),
        ],
        "understaffed_it": [
            ("understaffed" in combined),
            ("insufficient staff" in combined),
            ("it team" in combined and any(x in combined for x in ["small", "undersized", "insufficient"])),
        ],
        "network_undocumented": [
            ("network" in combined and "undocumented" in combined),
            ("network" in combined and "no documentation" in combined),
            ("network architecture" in combined and "unknown" in combined),
        ],
    }

    patterns = trigger_patterns.get(trigger_key, [])
    return any(patterns)


def _check_gap_for_trigger(gap: Any, trigger_key: str) -> bool:
    """Check if a gap indicates a specific complexity trigger."""
    if not hasattr(gap, 'description'):
        return False

    desc_lower = (gap.description or "").lower()

    # Gap-based triggers (missing information often indicates issues)
    gap_patterns = {
        "no_dr_capability": ["disaster recovery" in desc_lower, "dr capability" in desc_lower],
        "no_iam_platform": ["identity management" in desc_lower, "iga" in desc_lower, "iam" in desc_lower],
        "no_pam": ["privileged access" in desc_lower, "pam" in desc_lower],
        "no_siem_soc": ["siem" in desc_lower, "security monitoring" in desc_lower, "soc" in desc_lower],
        "network_undocumented": ["network" in desc_lower and "document" in desc_lower],
        "compliance_gaps": ["compliance" in desc_lower, "regulatory" in desc_lower],
    }

    patterns = gap_patterns.get(trigger_key, [])
    return any(patterns)


def _check_risk_for_trigger(risk: Any, trigger_key: str) -> bool:
    """Check if a risk indicates a specific complexity trigger."""
    if not hasattr(risk, 'title') or not hasattr(risk, 'description'):
        return False

    title_lower = (risk.title or "").lower()
    desc_lower = (risk.description or "").lower()
    combined = f"{title_lower} {desc_lower}"

    # Risk-based triggers
    risk_patterns = {
        "dual_erp": ["dual erp" in combined, "multiple erp" in combined, "erp consolidation" in combined],
        "data_center_migration": ["data center" in combined and any(x in combined for x in ["migration", "exit", "stranded"])],
        "no_dr_capability": ["disaster recovery" in combined, "dr " in combined and "risk" in combined],
        "key_person_risk": ["key person" in combined, "single point of failure" in combined],
        "compliance_gaps": ["compliance" in combined and "risk" in combined],
        "no_pam": ["privileged access" in combined and "risk" in combined],
    }

    patterns = risk_patterns.get(trigger_key, [])
    return any(patterns)


def calculate_complexity_score(
    facts: List[Any],
    gaps: List[Any],
    risks: List[Any],
    work_items: List[Any]
) -> Tuple[int, str, List[Dict[str, Any]]]:
    """
    Calculate deterministic complexity score based on specific triggers.

    Args:
        facts: List of Fact objects from FactStore
        gaps: List of Gap objects from FactStore
        risks: List of Risk objects from ReasoningStore
        work_items: List of WorkItem objects from ReasoningStore

    Returns:
        Tuple of (score, complexity_level, triggered_rules)
    """
    triggered_rules = []
    total_score = 0

    # Check each trigger
    for trigger_key, trigger in COMPLEXITY_TRIGGERS.items():
        triggered = False
        evidence = []

        # Check facts
        for fact in facts:
            if _check_fact_for_trigger(fact, trigger_key):
                triggered = True
                evidence.append(f"Fact: {getattr(fact, 'fact_id', 'unknown')}")

        # Check gaps
        for gap in gaps:
            if _check_gap_for_trigger(gap, trigger_key):
                triggered = True
                evidence.append(f"Gap: {getattr(gap, 'gap_id', 'unknown')}")

        # Check risks
        for risk in risks:
            if _check_risk_for_trigger(risk, trigger_key):
                triggered = True
                evidence.append(f"Risk: {getattr(risk, 'finding_id', 'unknown')}")

        if triggered:
            total_score += trigger.points
            triggered_rules.append({
                "trigger": trigger_key,
                "name": trigger.name,
                "description": trigger.description,
                "points": trigger.points,
                "category": trigger.category,
                "evidence": evidence[:3]  # Limit evidence list
            })
            logger.debug(f"Complexity trigger: {trigger.name} (+{trigger.points})")

    # Add base score from risk severity counts
    severity_bonus = 0
    for risk in risks:
        severity = getattr(risk, 'severity', 'medium').lower()
        if severity == 'critical':
            severity_bonus += 5
        elif severity == 'high':
            severity_bonus += 3
        elif severity == 'medium':
            severity_bonus += 1

    total_score += severity_bonus

    # Determine complexity level
    complexity_level = "lower"
    for level, (min_score, max_score) in COMPLEXITY_THRESHOLDS.items():
        if min_score <= total_score <= max_score:
            complexity_level = level
            break

    logger.info(f"Complexity score: {total_score} ({complexity_level}), {len(triggered_rules)} triggers matched")

    return total_score, complexity_level, triggered_rules


def get_complexity_assessment(
    score: int,
    level: str,
    triggered_rules: List[Dict[str, Any]],
    total_cost_low: float,
    total_cost_high: float,
    total_gaps: int
) -> Dict[str, Any]:
    """
    Generate a structured complexity assessment.

    Returns a dictionary that can be used for both display and JSON export.
    """
    level_labels = {
        "low": "Lower-complexity integration",
        "mid": "Mid-complexity integration",
        "high": "High-complexity integration"
    }

    level_outlooks = {
        "low": "IT environment is relatively mature. Focus will be on optimization rather than remediation.",
        "mid": "Core systems are functional but require attention. Manageable with proper planning.",
        "high": "Significant remediation work required before or immediately after close."
    }

    # Group triggers by category
    by_category = {}
    for rule in triggered_rules:
        cat = rule["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(rule)

    # Build key drivers list (top 5 by points)
    key_drivers = sorted(triggered_rules, key=lambda x: x["points"], reverse=True)[:5]

    return {
        "score": score,
        "level": level,
        "label": level_labels.get(level, level),
        "outlook": level_outlooks.get(level, ""),
        "cost_range": {
            "low": total_cost_low,
            "high": total_cost_high
        },
        "gap_count": total_gaps,
        "triggered_rules": triggered_rules,
        "triggers_by_category": by_category,
        "key_drivers": [r["name"] for r in key_drivers],
        "bottom_line": _generate_bottom_line(
            level_labels.get(level, level),
            level_outlooks.get(level, ""),
            total_cost_low,
            total_cost_high,
            total_gaps
        )
    }


def _generate_bottom_line(
    complexity_label: str,
    outlook: str,
    total_low: float,
    total_high: float,
    total_gaps: int
) -> str:
    """Generate the bottom line statement."""
    if total_high > 0:
        cost_stmt = f"Expected integration cost: ${total_low:,.0f} - ${total_high:,.0f}"
    else:
        cost_stmt = "Cost estimates pending further information"

    gap_warning = ""
    if total_gaps >= 10:
        gap_warning = f" Note: {total_gaps} information gaps remain - estimates may shift as visibility improves."
    elif total_gaps >= 5:
        gap_warning = f" {total_gaps} information gaps should be resolved before finalizing estimates."

    return f"{complexity_label}. {outlook} {cost_stmt}.{gap_warning}"
