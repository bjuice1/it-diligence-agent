"""
Identity & Access Reasoning Agent

Analyzes identity and access management facts and produces findings with fact citations.
"""

from agents_v2.base_reasoning_agent import BaseReasoningAgent
from prompts.v2_identity_access_reasoning_prompt import IDENTITY_ACCESS_REASONING_PROMPT


class IdentityAccessReasoningAgent(BaseReasoningAgent):
    """
    Identity & Access Management reasoning agent.

    Analyzes facts about directory services, authentication, PAM,
    provisioning, SSO, and MFA to identify:
    - IAM risks (security gaps, complexity, compliance issues)
    - Strategic considerations (identity consolidation, integration needs)
    - Integration work items (directory migrations, SSO implementation)
    - Recommendations for the deal team

    Every finding cites supporting facts from the FactStore.
    """

    @property
    def domain(self) -> str:
        return "identity_access"

    @property
    def system_prompt(self) -> str:
        return IDENTITY_ACCESS_REASONING_PROMPT
