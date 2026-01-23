"""
Applications Discovery Agent

Extracts application facts from IT documentation.
Categories: erp, crm, custom, saas, integration, development, database

Industry-Aware Discovery:
When an industry is specified, the discovery prompt is enriched with
industry-specific application types and questions from the
industry_application_considerations module.
"""

from typing import List, Optional
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_applications_discovery_prompt import (
    APPLICATIONS_DISCOVERY_PROMPT,
    get_applications_discovery_prompt
)


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
    - Industry-specific applications (when industry is specified)

    Industry-Aware Discovery:
        When initialized with an industry parameter, the agent will use
        an enriched prompt that includes industry-specific application
        types and questions. For example:
        - Aviation MRO: MRO systems, QMS, tech pubs, export control
        - Healthcare: EMR, PACS, RCM, patient portals
        - Manufacturing: MES, EHS, QMS, OT/SCADA
    """

    def __init__(self, *args, industry: Optional[str] = None, **kwargs):
        """
        Initialize the applications discovery agent.

        Args:
            *args: Passed to BaseDiscoveryAgent
            industry: Optional industry key for industry-specific discovery.
                      Valid keys: healthcare, financial_services, manufacturing,
                      aviation_mro, defense_contractor, life_sciences, retail,
                      logistics, energy_utilities, insurance, construction,
                      food_beverage, professional_services, education, hospitality
            **kwargs: Passed to BaseDiscoveryAgent
        """
        super().__init__(*args, **kwargs)
        self._industry = industry

        # Log if industry-specific discovery is enabled
        if industry:
            self.logger.info(f"Industry-aware discovery enabled: {industry}")

    @property
    def domain(self) -> str:
        return "applications"

    @property
    def industry(self) -> Optional[str]:
        """Return the industry for this discovery session."""
        return self._industry

    @property
    def system_prompt(self) -> str:
        """
        Return the discovery prompt, enriched with industry context if specified.
        """
        if self._industry:
            return get_applications_discovery_prompt(industry=self._industry)
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
            "database",
            "vertical"  # Industry-specific applications
        ]
