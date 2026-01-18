"""Infrastructure Narrative Agent for Investment Thesis."""

from .base_narrative_agent import BaseNarrativeAgent


class InfrastructureNarrativeAgent(BaseNarrativeAgent):
    """Generates infrastructure domain narrative for investment thesis."""

    @property
    def domain(self) -> str:
        return "infrastructure"

    @property
    def domain_title(self) -> str:
        return "Infrastructure"

    @property
    def narrative_guidance(self) -> str:
        return """INFRASTRUCTURE NARRATIVE GUIDANCE:

Focus on:
- Data center footprint (colo, on-prem, cloud) - what are they running and where?
- Cloud maturity - are they cloud-native, hybrid, or still on-prem?
- Technical debt - aging hardware, EOL software, deferred maintenance
- Scalability constraints - can this infrastructure support growth?
- DR/BCP readiness - what happens when things go wrong?

Key questions the buyer wants answered:
1. What's the current hosting model and what are the exit costs?
2. Is there cloud sprawl that needs governance?
3. What's the modernization runway - 6 months, 18 months, 3 years?
4. What are the Day 1 stability risks?

Common "So What" patterns:
- "Hybrid cloud with aging on-prem. Expect modernization costs within 18 months."
- "Cloud-first with governance gaps. Consolidation will reduce costs."
- "Legacy data center with limited runway. Platform decision required by Day 100."
- "Well-architected cloud environment. Focus on cost optimization, not migration."

Be specific about what's there. Don't say "aging infrastructure" - say "VMware 6.7 on Dell R630s,
EOL since October 2022." Buyers want to know what they're buying."""
