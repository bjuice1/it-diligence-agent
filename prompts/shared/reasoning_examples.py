"""
Shared examples for reasoning prompts.

These examples demonstrate well-formed findings that:
1. Are specific to the inventory (not generic)
2. Link to fact IDs as evidence
3. Include actionable mitigations/implications
4. Distinguish confidence levels appropriately
"""

# Domain-specific examples for each type of finding

INFRASTRUCTURE_RISK_EXAMPLE = '''
identify_risk(
    title="VMware 6.7 End-of-Life Creates Security and Compliance Exposure",
    description="Target runs VMware vSphere 6.7 which reached end of general support in October 2022. This version no longer receives security patches, creating exposure to known vulnerabilities. Additionally, running unsupported software may trigger compliance findings during SOC 2 or customer audits.",
    category="end_of_life",
    severity="high",
    integration_dependent=False,
    mitigation="Upgrade to vSphere 8.0 within 6 months. Budget $150-300K including licensing, professional services, and testing. Can be combined with any hardware refresh.",
    based_on_facts=["F-INFRA-003", "F-INFRA-007"],
    confidence="high",
    reasoning="F-INFRA-003 explicitly states vSphere 6.7. VMware's published EOL date is October 2022. This is a standalone risk that exists regardless of integration approach."
)
'''

CYBERSECURITY_RISK_EXAMPLE = '''
identify_risk(
    title="No MFA Enforcement for Remote Access Creates Credential Theft Exposure",
    description="VPN access does not require multi-factor authentication based on inventory. Single-factor authentication to remote access is a primary attack vector - 80%+ of breaches involve compromised credentials. This gap creates both security exposure and likely cyber insurance compliance issues.",
    category="access_control",
    severity="critical",
    integration_dependent=False,
    mitigation="Implement MFA for all remote access within 30 days. Microsoft Authenticator or similar can be deployed quickly. Budget $5-15K for implementation plus per-user licensing.",
    based_on_facts=["F-CYBER-008", "F-IAM-003"],
    confidence="high",
    reasoning="F-CYBER-008 shows VPN without MFA. F-IAM-003 confirms single-factor auth. This is a standalone risk that should be remediated regardless of deal outcome."
)
'''

APPLICATIONS_RISK_EXAMPLE = '''
identify_risk(
    title="ERP System Running Unsupported Version Creates Operational Risk",
    description="Target's SAP ECC 6.0 is approaching end of mainstream maintenance (2027). Migration to S/4HANA is a major undertaking requiring 12-18 months. If integration timeline extends beyond 2027, support costs increase significantly and security patch availability becomes uncertain.",
    category="application_lifecycle",
    severity="medium",
    integration_dependent=True,
    mitigation="Include S/4HANA migration timeline in integration planning. Consider whether buyer's ERP strategy allows consolidation. Budget $2-5M for migration if standalone upgrade required.",
    based_on_facts=["F-APP-001", "F-APP-012"],
    confidence="medium",
    reasoning="F-APP-001 shows SAP ECC 6.0. SAP's published maintenance end is 2027. Risk severity depends on integration timeline and buyer ERP strategy."
)
'''

NETWORK_RISK_EXAMPLE = '''
identify_risk(
    title="Single ISP Creates Internet Connectivity Single Point of Failure",
    description="Target has a single internet circuit with no documented failover. Loss of this circuit would impact all cloud services, SaaS applications, and remote user connectivity. For a business with cloud-hosted applications, this represents significant operational risk.",
    category="resilience",
    severity="medium",
    integration_dependent=False,
    mitigation="Add secondary ISP with automatic failover. Typical cost $1-3K/month depending on bandwidth. Can be implemented within 30-60 days.",
    based_on_facts=["F-NET-004", "F-NET-009"],
    confidence="high",
    reasoning="F-NET-004 shows single ISP (Comcast Business). F-NET-009 confirms no redundant path. Combined with cloud application dependency makes this operationally significant."
)
'''

STRATEGIC_CONSIDERATION_EXAMPLE = '''
create_strategic_consideration(
    title="Platform Mismatch Will Require Migration Investment",
    description="Target runs primarily AWS while buyer operates Azure. Full integration will require either workload migration ($500K-1M+) or ongoing multi-cloud management overhead. This is not a blocker but affects synergy realization timeline.",
    lens="synergy_realization",
    implication="Factor migration costs into synergy model. Consider phased approach: Day 1 connectivity, Day 100+ workload migration. Multi-cloud tools may be interim solution.",
    based_on_facts=["F-INFRA-010", "F-INFRA-011"],
    confidence="high",
    reasoning="F-INFRA-010 shows target's AWS footprint. Deal context indicates buyer is Azure-centric. Platform mismatch is factual; cost estimate based on typical migration projects."
)
'''

WORK_ITEM_EXAMPLE = '''
create_work_item(
    title="Establish Network Connectivity to Buyer Environment",
    description="Implement site-to-site VPN or MPLS connection between target's Chicago DC and buyer's primary data centers. Required for identity integration, shared services access, and application connectivity during transition.",
    phase="Day_1",
    priority="critical",
    owner_type="joint",
    triggered_by=["F-INFRA-001", "F-NET-002"],
    based_on_facts=["F-INFRA-001", "F-NET-002"],
    cost_estimate="25k_to_100k",
    reasoning="Network connectivity is prerequisite for all integration activities. F-INFRA-001 shows target location, F-NET-002 shows current WAN topology. Joint ownership as both parties need to configure their network equipment."
)
'''

RECOMMENDATION_EXAMPLE = '''
create_recommendation(
    title="Request Complete Server Inventory with Age Data",
    description="Current documentation shows server counts but not hardware age or refresh dates. Request detailed inventory including purchase dates, warranty status, and planned refresh timeline. This directly impacts integration cost estimates.",
    action_type="request_info",
    urgency="high",
    rationale="Without hardware age data, cannot accurately estimate refresh spend or identify EOL hardware risks. Server age typically correlates with reliability issues and support costs.",
    based_on_facts=["F-INFRA-004"],
    confidence="high",
    reasoning="F-INFRA-004 shows 45 physical servers but no age/warranty information. This is a common gap that significantly affects cost modeling."
)
'''

# Bad examples to avoid
BAD_RISK_EXAMPLES = '''
### Examples to AVOID

```python
# TOO GENERIC - applies to any company
identify_risk(
    title="Legacy Systems Risk",
    description="The company has legacy systems that may need updating.",
    ...
)

# NO EVIDENCE LINKAGE - where did this come from?
identify_risk(
    title="Possible Database Performance Issues",
    description="Database may have performance problems under load.",
    based_on_facts=[],  # Empty!
    ...
)

# FABRICATED SPECIFICS - numbers not in inventory
identify_risk(
    title="Server Capacity Risk",
    description="The 47 servers are running at approximately 85% capacity...",
    # But inventory only said "multiple servers" with no count or utilization data
    ...
)

# ASSUMED FACTS - gap treated as knowledge
identify_risk(
    title="DR Site Needs Upgrade",
    description="The DR site likely needs infrastructure refresh...",
    # But inventory shows DR is a GAP - we don't know if DR exists
    ...
)
```
'''


def get_examples_for_domain(domain: str) -> str:
    """Get formatted examples section for a domain's reasoning prompt."""

    # Select domain-specific risk example
    if domain == "infrastructure":
        risk_example = INFRASTRUCTURE_RISK_EXAMPLE
    elif domain == "cybersecurity":
        risk_example = CYBERSECURITY_RISK_EXAMPLE
    elif domain == "applications":
        risk_example = APPLICATIONS_RISK_EXAMPLE
    elif domain == "network":
        risk_example = NETWORK_RISK_EXAMPLE
    else:
        risk_example = INFRASTRUCTURE_RISK_EXAMPLE  # Default

    return f'''## EXAMPLES OF GOOD OUTPUT

Below are examples of well-formed findings. Notice the specificity, evidence linkage, and actionable content.

### Example Risk (Good)
```python
{risk_example.strip()}
```

### Example Strategic Consideration (Good)
```python
{STRATEGIC_CONSIDERATION_EXAMPLE.strip()}
```

### Example Work Item (Good)
```python
{WORK_ITEM_EXAMPLE.strip()}
```

### Example Recommendation (Good)
```python
{RECOMMENDATION_EXAMPLE.strip()}
```

{BAD_RISK_EXAMPLES}
'''
