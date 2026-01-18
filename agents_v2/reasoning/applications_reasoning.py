"""
Applications Reasoning Agent

Analyzes application facts and produces findings with fact citations.
"""

from agents_v2.base_reasoning_agent import BaseReasoningAgent
from prompts.v2_applications_reasoning_prompt import APPLICATIONS_REASONING_PROMPT


class ApplicationsReasoningAgent(BaseReasoningAgent):
    """
    Applications reasoning agent.

    Analyzes facts about ERP, CRM, custom applications, SaaS,
    integration, development, and databases to identify:
    - Application risks (technical debt, licensing, integration complexity)
    - Strategic considerations (core vs. non-core apps, synergies)
    - Integration work items (migrations, consolidation, sunset)
    - Recommendations for the deal team

    Every finding cites supporting facts from the FactStore.
    """

    @property
    def domain(self) -> str:
        return "applications"

    @property
    def system_prompt(self) -> str:
        return APPLICATIONS_REASONING_PROMPT
