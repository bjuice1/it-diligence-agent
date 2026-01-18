"""IT Organization Narrative Agent for Investment Thesis."""

from .base_narrative_agent import BaseNarrativeAgent


class OrganizationNarrativeAgent(BaseNarrativeAgent):
    """Generates IT organization domain narrative for investment thesis."""

    @property
    def domain(self) -> str:
        return "organization"

    @property
    def domain_title(self) -> str:
        return "IT Organization"

    @property
    def narrative_guidance(self) -> str:
        return """IT ORGANIZATION NARRATIVE GUIDANCE:

Focus on:
- Team structure - headcount, roles, reporting lines
- Outsourcing dependency - what percentage is outsourced and to whom?
- Key person risk - who knows where the bodies are buried?
- Capability gaps - what skills are missing?
- Vendor relationships - MSPs, contractors, strategic partners

Key questions the buyer wants answered:
1. What's the TSA requirement if the CIO leaves?
2. Is the team staying through integration?
3. What's the true cost of IT operations (FTEs + outsourcing)?
4. Are there capability gaps that need hiring or contracting?

Common "So What" patterns:
- "Heavy outsourcing (44% of IT ops). TSA requirements and transition risk."
- "Lean internal team with key person dependencies. Retention critical."
- "Well-staffed IT org. Focus on integration, not backfill."
- "CIO retiring post-close. Leadership succession needed Day 1."

Organization findings often impact deal structure (TSA terms, holdbacks, retention).
Be specific about:
- Total IT headcount (internal + outsourced)
- Outsourcing percentage
- Key roles and who fills them
- Known departures or retirements

If there's heavy outsourcing, call out the TSA implications.
If the CIO is leaving, that's a material finding.

Don't be diplomatic about organizational risk. If the team is thin or
there's key person dependency, say it directly."""
