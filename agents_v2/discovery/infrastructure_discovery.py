"""
Infrastructure Discovery Agent

Extracts infrastructure facts from IT documentation.
Categories: hosting, compute, storage, backup_dr, cloud, legacy, tooling
"""

from typing import List
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_infrastructure_discovery_prompt import INFRASTRUCTURE_DISCOVERY_PROMPT


class InfrastructureDiscoveryAgent(BaseDiscoveryAgent):
    """
    Infrastructure discovery agent.

    Extracts structured facts about:
    - Data centers and hosting
    - Compute (physical/virtual/containers)
    - Storage systems
    - Backup and DR
    - Cloud infrastructure
    - Legacy/mainframe systems
    - Infrastructure tooling
    """

    @property
    def domain(self) -> str:
        return "infrastructure"

    @property
    def system_prompt(self) -> str:
        return INFRASTRUCTURE_DISCOVERY_PROMPT

    @property
    def inventory_categories(self) -> List[str]:
        return [
            "hosting",
            "compute",
            "storage",
            "backup_dr",
            "cloud",
            "legacy",
            "tooling"
        ]
