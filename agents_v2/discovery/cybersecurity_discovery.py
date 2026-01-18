"""
Cybersecurity Discovery Agent

Extracts cybersecurity facts from IT documentation.
Categories: endpoint, perimeter, detection, vulnerability, compliance, incident_response, governance
"""

from typing import List
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_cybersecurity_discovery_prompt import CYBERSECURITY_DISCOVERY_PROMPT


class CybersecurityDiscoveryAgent(BaseDiscoveryAgent):
    """
    Cybersecurity discovery agent.

    Extracts structured facts about:
    - Endpoint protection (AV, EDR)
    - Perimeter security (firewalls, WAF)
    - Detection capabilities (SIEM, SOC)
    - Vulnerability management
    - Compliance and certifications
    - Incident response
    - Security governance
    """

    @property
    def domain(self) -> str:
        return "cybersecurity"

    @property
    def system_prompt(self) -> str:
        return CYBERSECURITY_DISCOVERY_PROMPT

    @property
    def inventory_categories(self) -> List[str]:
        return [
            "endpoint",
            "perimeter",
            "detection",
            "vulnerability",
            "compliance",
            "incident_response",
            "governance"
        ]
