"""
Buyer Context Configuration

Controls which domains include buyer facts in reasoning prompts.
This allows token cost optimization by only sending buyer context
where it's most valuable for integration analysis.

RATIONALE:
- Applications: HIGH value (ERP/CRM consolidation decisions)
- Infrastructure: HIGH value (cloud region, datacenter overlaps)
- Cybersecurity: HIGH value (security tool standardization)
- Organization: MEDIUM value (team structure comparison)
- Network: MEDIUM value (network topology overlaps)
- Identity & Access: LOW value (often buyer-agnostic)

TOKEN IMPACT:
- With buyer facts: ~6,000-8,000 tokens per domain
- Without buyer facts: ~3,000-5,000 tokens per domain
- Cost difference: ~$0.003-$0.006 per reasoning call
"""

# Configuration for buyer context inclusion per domain
BUYER_CONTEXT_CONFIG = {
    "applications": {
        "include_buyer_facts": True,
        "buyer_fact_limit": 50,  # Top 50 most relevant facts
        "reason": "ERP/CRM consolidation decisions require specific platform comparison"
    },
    "infrastructure": {
        "include_buyer_facts": True,
        "buyer_fact_limit": 30,
        "reason": "Cloud region, datacenter, hosting overlaps drive integration strategy"
    },
    "cybersecurity": {
        "include_buyer_facts": True,
        "buyer_fact_limit": 25,
        "reason": "Security tool standardization and posture comparison critical"
    },
    "organization": {
        "include_buyer_facts": True,
        "buyer_fact_limit": 20,
        "reason": "Team size and structure comparison for absorption/integration decisions"
    },
    "network": {
        "include_buyer_facts": True,
        "buyer_fact_limit": 20,
        "reason": "Network architecture overlaps affect Day-1 connectivity"
    },
    "identity_access": {
        "include_buyer_facts": True,
        "buyer_fact_limit": 15,
        "reason": "Identity provider consolidation and SSO integration"
    },
}


def should_include_buyer_facts(domain: str) -> bool:
    """Check if buyer facts should be included for this domain."""
    config = BUYER_CONTEXT_CONFIG.get(domain, {})
    return config.get("include_buyer_facts", False)


def get_buyer_fact_limit(domain: str) -> int:
    """Get max number of buyer facts to include for this domain."""
    config = BUYER_CONTEXT_CONFIG.get(domain, {})
    return config.get("buyer_fact_limit", 0)


def get_config_reason(domain: str) -> str:
    """Get rationale for buyer context inclusion decision."""
    config = BUYER_CONTEXT_CONFIG.get(domain, {})
    return config.get("reason", "No specific reason provided")
