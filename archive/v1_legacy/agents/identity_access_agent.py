"""
Identity & Access Domain Agent

Analyzes IT identity and access management through multiple lenses:
- Directory Services & Identity Providers
- Authentication (SSO, MFA)
- Privileged Access Management (PAM/PIM)
- Joiner/Mover/Leaver (JML) Processes
- Access Governance & Certification
- Federation & External Identity
"""
from agents.base_agent import BaseAgent
from prompts.identity_access_prompt import IDENTITY_ACCESS_SYSTEM_PROMPT


class IdentityAccessAgent(BaseAgent):
    """
    Specialized agent for identity and access management domain analysis.

    Applies systematic analysis through:
    1. Current State Assessment (directories, IdPs, authentication tools, PAM)
    2. Coverage Analysis (MFA %, SSO scope, PAM coverage)
    3. Process Maturity (JML automation, access reviews, certification)
    4. Integration Complexity (directory mergers, federation requirements)
    5. Risk & Compliance (orphan accounts, excessive privileges, audit gaps)

    Key areas analyzed:
    - Identity Providers: Azure AD, Okta, Ping, AD, LDAP
    - Authentication: SSO, MFA, passwordless, certificate-based
    - Privileged Access: CyberArk, BeyondTrust, Delinea, Azure PIM
    - Access Governance: SailPoint, Saviynt, access certifications
    - Process: JML automation, access request workflows
    """

    @property
    def domain(self) -> str:
        return "identity_access"

    @property
    def system_prompt(self) -> str:
        return IDENTITY_ACCESS_SYSTEM_PROMPT
