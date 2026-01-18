"""
Applications Discovery Agent

Extracts application facts from IT documentation.
Categories: erp, crm, custom, saas, integration, development, database
"""

from typing import List
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_applications_discovery_prompt import APPLICATIONS_DISCOVERY_PROMPT


class ApplicationsDiscoveryAgent(BaseDiscoveryAgent):
    """
    Applications discovery agent.

    Extracts structured facts about:
    - ERP systems
    - CRM platforms
    - Custom/proprietary applications
    - SaaS applications
    - Integration and middleware
    - Development tools and practices
    - Databases
    """

    @property
    def domain(self) -> str:
        return "applications"

    @property
    def system_prompt(self) -> str:
        return APPLICATIONS_DISCOVERY_PROMPT

    @property
    def inventory_categories(self) -> List[str]:
        return [
            "erp",
            "crm",
            "custom",
            "saas",
            "integration",
            "development",
            "database"
        ]
