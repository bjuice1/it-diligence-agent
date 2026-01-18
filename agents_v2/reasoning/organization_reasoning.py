"""
Organization Reasoning Agent

Analyzes IT organization facts and produces findings with fact citations.
"""

from agents_v2.base_reasoning_agent import BaseReasoningAgent
from prompts.v2_organization_reasoning_prompt import ORGANIZATION_REASONING_PROMPT


class OrganizationReasoningAgent(BaseReasoningAgent):
    """
    IT Organization reasoning agent.

    Analyzes facts about organizational structure, staffing, vendors,
    skills, processes, budget, and roadmap to identify:
    - Organization risks (key person dependency, skill gaps, vendor lock-in)
    - Strategic considerations (retention needs, synergies, cost savings)
    - Integration work items (team transitions, vendor negotiations)
    - Recommendations for the deal team

    Every finding cites supporting facts from the FactStore.
    """

    @property
    def domain(self) -> str:
        return "organization"

    @property
    def system_prompt(self) -> str:
        return ORGANIZATION_REASONING_PROMPT
