"""
Identity & Access Discovery Agent

Extracts identity and access management facts from IT documentation.
Categories: directory, authentication, privileged_access, provisioning, sso, mfa, governance
"""

from typing import List
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_identity_access_discovery_prompt import IDENTITY_ACCESS_DISCOVERY_PROMPT


class IdentityAccessDiscoveryAgent(BaseDiscoveryAgent):
    """
    Identity & Access Management discovery agent.

    Extracts structured facts about:
    - Directory services (AD, LDAP)
    - Authentication mechanisms
    - Privileged access management (PAM)
    - User provisioning and lifecycle
    - Single sign-on (SSO)
    - Multi-factor authentication (MFA)
    - IAM governance
    """

    @property
    def domain(self) -> str:
        return "identity_access"

    @property
    def system_prompt(self) -> str:
        return IDENTITY_ACCESS_DISCOVERY_PROMPT

    @property
    def inventory_categories(self) -> List[str]:
        return [
            "directory",
            "authentication",
            "privileged_access",
            "provisioning",
            "sso",
            "mfa",
            "governance"
        ]
