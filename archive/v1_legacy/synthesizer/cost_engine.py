"""
Cost Estimation Engine for IT DD.

Provides rough order of magnitude (ROM) estimates based on finding types.
These are starting points for discussion, not precise quotes.
"""
from typing import List, Dict, Tuple
from .models import Risk, CostItem


# Cost ranges by work item type (low, high) in USD
# These should be calibrated based on your firm's experience
COST_RANGES = {
    # Application work
    "erp_migration": (500_000, 5_000_000),
    "erp_upgrade": (200_000, 1_500_000),
    "application_migration": (50_000, 500_000),
    "application_retirement": (25_000, 150_000),
    "application_integration": (50_000, 300_000),
    "saas_migration": (25_000, 200_000),
    "custom_code_remediation": (100_000, 1_000_000),

    # Infrastructure work
    "datacenter_migration": (200_000, 2_000_000),
    "datacenter_consolidation": (300_000, 3_000_000),
    "cloud_migration": (100_000, 1_000_000),
    "server_refresh": (50_000, 500_000),
    "storage_refresh": (50_000, 400_000),
    "dr_implementation": (100_000, 500_000),

    # Network work
    "network_integration": (50_000, 300_000),
    "wan_migration": (75_000, 400_000),
    "sdwan_implementation": (100_000, 500_000),
    "firewall_migration": (50_000, 200_000),

    # Security work
    "security_remediation": (50_000, 300_000),
    "edr_deployment": (25_000, 150_000),
    "siem_implementation": (75_000, 400_000),
    "pam_implementation": (100_000, 400_000),
    "mfa_rollout": (25_000, 100_000),
    "compliance_remediation": (50_000, 300_000),
    "pentest_remediation": (25_000, 200_000),

    # Identity work
    "identity_integration": (50_000, 300_000),
    "ad_consolidation": (75_000, 400_000),
    "sso_implementation": (50_000, 200_000),

    # General
    "staff_augmentation_year": (150_000, 300_000),
    "consulting_engagement": (50_000, 250_000),
    "license_consolidation": (-100_000, -25_000),  # Savings
    "unknown": (50_000, 200_000),
}


def estimate_cost_for_risk(risk: Risk) -> Tuple[int, int]:
    """
    Estimate cost range for addressing a risk.

    Returns:
        Tuple of (low_estimate, high_estimate)
    """
    # Map risk descriptions to cost categories
    risk_lower = risk.description.lower() + " " + risk.title.lower()

    # ERP-related
    if any(term in risk_lower for term in ["erp migration", "s/4hana", "sap migration"]):
        return COST_RANGES["erp_migration"]
    if any(term in risk_lower for term in ["erp upgrade", "ecc upgrade"]):
        return COST_RANGES["erp_upgrade"]

    # Application-related
    if "custom code" in risk_lower or "abap" in risk_lower:
        return COST_RANGES["custom_code_remediation"]
    if "application migration" in risk_lower:
        return COST_RANGES["application_migration"]
    if any(term in risk_lower for term in ["retire", "decommission"]):
        return COST_RANGES["application_retirement"]

    # Infrastructure-related
    if "datacenter" in risk_lower or "data center" in risk_lower:
        if "consolidat" in risk_lower:
            return COST_RANGES["datacenter_consolidation"]
        return COST_RANGES["datacenter_migration"]
    if "cloud migration" in risk_lower:
        return COST_RANGES["cloud_migration"]
    if "server" in risk_lower and any(term in risk_lower for term in ["refresh", "eol", "upgrade"]):
        return COST_RANGES["server_refresh"]
    if any(term in risk_lower for term in ["disaster recovery", "dr ", "backup"]):
        return COST_RANGES["dr_implementation"]

    # Network-related
    if any(term in risk_lower for term in ["network integration", "network consolidat"]):
        return COST_RANGES["network_integration"]
    if "sd-wan" in risk_lower or "sdwan" in risk_lower:
        return COST_RANGES["sdwan_implementation"]
    if "firewall" in risk_lower:
        return COST_RANGES["firewall_migration"]

    # Security-related
    if "mfa" in risk_lower or "multi-factor" in risk_lower:
        return COST_RANGES["mfa_rollout"]
    if "edr" in risk_lower or "endpoint" in risk_lower:
        return COST_RANGES["edr_deployment"]
    if "siem" in risk_lower:
        return COST_RANGES["siem_implementation"]
    if "pam" in risk_lower or "privileged access" in risk_lower:
        return COST_RANGES["pam_implementation"]
    if any(term in risk_lower for term in ["pentest", "penetration test", "vulnerability"]):
        return COST_RANGES["pentest_remediation"]
    if any(term in risk_lower for term in ["compliance", "sox", "pci", "hipaa"]):
        return COST_RANGES["compliance_remediation"]
    if "security" in risk_lower:
        return COST_RANGES["security_remediation"]

    # Identity-related
    if any(term in risk_lower for term in ["identity integration", "sso", "federation"]):
        return COST_RANGES["identity_integration"]
    if any(term in risk_lower for term in ["active directory", "ad consolidat"]):
        return COST_RANGES["ad_consolidation"]

    # Default
    return COST_RANGES["unknown"]


def calculate_costs(risks: List[Risk]) -> Dict:
    """
    Calculate cost estimates for all risks.

    Returns:
        Dict with totals and line items
    """
    cost_items = []
    total_low = 0
    total_high = 0

    for risk in risks:
        if risk.severity in ["Critical", "High"]:
            low, high = estimate_cost_for_risk(risk)
            cost_items.append(CostItem(
                id=f"COST-{len(cost_items)+1:03d}",
                category="Remediation" if "security" in risk.domain.lower() else "Integration",
                description=f"Address: {risk.title}",
                low_estimate=low,
                high_estimate=high,
                timing="Day 1" if risk.severity == "Critical" else "90 Days",
                driver=risk.id,
                assumptions="ROM estimate based on typical market rates"
            ))
            total_low += low
            total_high += high

    return {
        "items": cost_items,
        "total_low": total_low,
        "total_high": total_high,
        "summary": f"${total_low:,} - ${total_high:,}"
    }


def format_currency(amount: int) -> str:
    """Format integer as currency string."""
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.0f}K"
    else:
        return f"${amount:,}"


def get_cost_summary_text(costs: Dict) -> str:
    """Generate cost summary text for reports."""
    if not costs["items"]:
        return "No significant cost items identified based on current findings."

    lines = [
        f"**Estimated One-Time Costs:** {format_currency(costs['total_low'])} - {format_currency(costs['total_high'])}",
        "",
        "Key cost drivers:"
    ]

    # Group by severity/timing
    critical_items = [c for c in costs["items"] if c.timing == "Day 1"]
    other_items = [c for c in costs["items"] if c.timing != "Day 1"]

    if critical_items:
        lines.append("- Critical (Day 1):")
        for item in critical_items[:3]:
            lines.append(f"  - {item.description}: {format_currency(item.low_estimate)} - {format_currency(item.high_estimate)}")

    if other_items:
        lines.append("- Near-term (90 days):")
        for item in other_items[:3]:
            lines.append(f"  - {item.description}: {format_currency(item.low_estimate)} - {format_currency(item.high_estimate)}")

    lines.append("")
    lines.append("*Note: ROM estimates for planning purposes. Detailed scoping required.*")

    return "\n".join(lines)
