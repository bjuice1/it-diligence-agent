"""
Cybersecurity Reasoning Agent

Analyzes cybersecurity facts and produces findings with fact citations.
"""

from agents_v2.base_reasoning_agent import BaseReasoningAgent
from prompts.v2_cybersecurity_reasoning_prompt import CYBERSECURITY_REASONING_PROMPT


class CybersecurityReasoningAgent(BaseReasoningAgent):
    """
    Cybersecurity reasoning agent.

    Analyzes facts about endpoint protection, perimeter security,
    detection, vulnerability management, compliance, and incident response to identify:
    - Security risks (gaps in protection, compliance issues)
    - Strategic considerations (buyer security alignment, remediation needs)
    - Integration work items (security tool consolidation, policy alignment)
    - Recommendations for the deal team

    Every finding cites supporting facts from the FactStore.
    """

    @property
    def domain(self) -> str:
        return "cybersecurity"

    @property
    def system_prompt(self) -> str:
        return CYBERSECURITY_REASONING_PROMPT
