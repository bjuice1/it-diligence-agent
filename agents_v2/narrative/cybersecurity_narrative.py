"""Cybersecurity Narrative Agent for Investment Thesis."""

from .base_narrative_agent import BaseNarrativeAgent


class CybersecurityNarrativeAgent(BaseNarrativeAgent):
    """Generates cybersecurity domain narrative for investment thesis."""

    @property
    def domain(self) -> str:
        return "cybersecurity"

    @property
    def domain_title(self) -> str:
        return "Cybersecurity"

    @property
    def narrative_guidance(self) -> str:
        return """CYBERSECURITY NARRATIVE GUIDANCE:

Focus on:
- Security tooling - EDR, SIEM, vulnerability management, etc.
- Privileged Access Management (PAM) - is admin access controlled?
- Incident Response - do they have a plan and have they tested it?
- Compliance posture - SOC 2, ISO 27001, industry-specific (HIPAA, PCI, etc.)
- Third-party risk - MSP access, SaaS dependencies, supply chain

Key questions the buyer wants answered:
1. What's the cyber insurance exposure? Can they get/renew coverage?
2. What's the Day 1 security risk if we close tomorrow?
3. What will regulators or auditors flag first?
4. Is there an existing security program or are we building from scratch?

Common "So What" patterns:
- "No PAM, no documented IR plan. Day 1 security work required if in regulated industry."
- "Security foundation exists but needs uplift. Budget for improvements, not overhaul."
- "Mature security program. Focus on integration, not remediation."
- "Significant gaps across the board. Consider security carve-out budget."

Security findings are often the most impactful for deal terms. Be specific:
- Don't say "inadequate security controls"
- Say "No privileged access management. 47 admin accounts with no oversight."

If they've had incidents, note them. If there's no IR plan, that's a finding.
Cyber insurance carriers will ask these questions - the buyer needs to know."""
