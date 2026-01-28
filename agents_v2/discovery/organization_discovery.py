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
        """Categories that match the v2_organization_discovery_prompt.

        These must align with:
        1. The prompt categories given to the LLM
        2. The categories expected by organization_bridge.py
        """
        return [
            "leadership",      # IT Leadership (CIO, VPs, Directors)
            "central_it",      # Central IT Teams (from Team Summary table)
            "roles",           # IT Roles (from Role & Compensation table)
            "app_teams",       # Application-specific teams
            "outsourcing",     # MSP/Vendor relationships
            "embedded_it",     # Business unit IT staff
            "shadow_it",       # Shadow IT instances
            "key_individuals", # Key persons with unique knowledge
            "skills",          # Skills and capabilities
            "budget"           # IT Budget and costs
        ]
