"""Identity & Access Narrative Agent for Investment Thesis."""

from .base_narrative_agent import BaseNarrativeAgent


class IdentityNarrativeAgent(BaseNarrativeAgent):
    """Generates identity & access domain narrative for investment thesis."""

    @property
    def domain(self) -> str:
        return "identity_access"

    @property
    def domain_title(self) -> str:
        return "Identity & Access"

    @property
    def narrative_guidance(self) -> str:
        return """IDENTITY & ACCESS NARRATIVE GUIDANCE:

Focus on:
- Identity provider - Azure AD/Entra, Okta, on-prem AD, or fragmented?
- SSO coverage - what percentage of apps are behind SSO?
- MFA deployment - where is it enforced, where is it not?
- Privileged Access Management (PAM) - are admin credentials controlled?
- Lifecycle management - joiner/mover/leaver automation

Key questions the buyer wants answered:
1. Can we integrate identity with buyer's environment?
2. Is there a single source of truth for identity?
3. What's the security posture around privileged access?
4. How automated is user provisioning/deprovisioning?

Common "So What" patterns:
- "Azure AD deployed but no PAM. Privileged access is a security gap."
- "Fragmented identity across AD and Okta. Consolidation required."
- "Modern identity stack with SSO and MFA. Clean integration path."
- "On-prem AD only. Cloud identity migration needed."

Identity is foundational for integration. If it's a mess, everything else is harder.
Be specific about:
- User counts
- MFA coverage percentage (if known)
- SSO app count vs total app count
- PAM presence or absence

PAM absence is always a finding. If there's no privileged access management,
say so clearly - it's a Day 1 security item for most buyers."""
