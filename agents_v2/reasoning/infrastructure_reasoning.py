"""
Infrastructure Reasoning Agent

Analyzes infrastructure facts and produces findings with fact citations.
"""

from agents_v2.base_reasoning_agent import BaseReasoningAgent
from prompts.v2_infrastructure_reasoning_prompt import INFRASTRUCTURE_REASONING_PROMPT


class InfrastructureReasoningAgent(BaseReasoningAgent):
    """
    Infrastructure reasoning agent.

    Analyzes facts about data centers, compute, storage, backup/DR,
    cloud, and legacy systems to identify:
    - Infrastructure risks (EOL, capacity, resilience)
    - Strategic considerations (buyer alignment, TSA needs)
    - Integration work items (migrations, upgrades)
    - Recommendations for the deal team

    Every finding cites supporting facts from the FactStore.
    """

    @property
    def domain(self) -> str:
        return "infrastructure"

    @property
    def system_prompt(self) -> str:
        return INFRASTRUCTURE_REASONING_PROMPT
