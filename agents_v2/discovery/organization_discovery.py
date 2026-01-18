"""
Organization Discovery Agent

Extracts IT organization facts from documentation.
Categories: structure, staffing, vendors, skills, processes, budget, roadmap
"""

from typing import List
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_organization_discovery_prompt import ORGANIZATION_DISCOVERY_PROMPT


class OrganizationDiscoveryAgent(BaseDiscoveryAgent):
    """
    IT Organization discovery agent.

    Extracts structured facts about:
    - Organizational structure
    - IT staffing and roles
    - Vendor relationships
    - Skills and capabilities
    - IT processes and maturity
    - Budget and spending
    - Technology roadmap
    """

    @property
    def domain(self) -> str:
        return "organization"

    @property
    def system_prompt(self) -> str:
        return ORGANIZATION_DISCOVERY_PROMPT

    @property
    def inventory_categories(self) -> List[str]:
        return [
            "structure",
            "staffing",
            "vendors",
            "skills",
            "processes",
            "budget",
            "roadmap"
        ]
