"""Applications Narrative Agent for Investment Thesis."""

from .base_narrative_agent import BaseNarrativeAgent


class ApplicationsNarrativeAgent(BaseNarrativeAgent):
    """Generates applications domain narrative for investment thesis."""

    @property
    def domain(self) -> str:
        return "applications"

    @property
    def domain_title(self) -> str:
        return "Applications"

    @property
    def narrative_guidance(self) -> str:
        return """APPLICATIONS NARRATIVE GUIDANCE:

Focus on:
- Core business systems - ERP, CRM, and what runs the business
- Custom/proprietary applications - what was built in-house and why?
- Integration landscape - how do systems talk to each other?
- License exposure - perpetual vs subscription, true-up risks
- Technical debt - unsupported versions, customization bloat

Key questions the buyer wants answered:
1. Is there ERP complexity (multiple systems, heavy customization)?
2. What's the integration/migration path to buyer platforms?
3. Are there licensing landmines (audit exposure, true-ups)?
4. What custom applications are critical to operations?

Common "So What" patterns:
- "Dual-ERP environment (NetSuite + Oracle). Rationalization decision required."
- "Single ERP, minimal customization. Clean integration path."
- "Heavy customization on core systems. Expect extended TSA requirements."
- "SaaS-heavy environment. License optimization opportunity."

ERP complexity is often the biggest driver of integration cost and timeline.
If there are multiple ERPs, that's a critical finding. Be specific about:
- Which systems
- User counts
- Customization level
- Integration dependencies

Don't bury the lede. If ERP rationalization is needed, lead with it."""
