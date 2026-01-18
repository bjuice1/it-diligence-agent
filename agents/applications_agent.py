"""
Applications Domain Agent

Analyzes IT application portfolio through multiple lenses:
- Application Inventory & Portfolio
- Technical Debt & Modernization
- Licensing & Vendor Risk
- Application Overlap (Target vs Buyer)
- Integration Complexity
- Rationalization Recommendations
"""
from agents.base_agent import BaseAgent
from prompts.applications_prompt import APPLICATIONS_SYSTEM_PROMPT


class ApplicationsAgent(BaseAgent):
    """
    Specialized agent for application portfolio domain analysis.

    Applies systematic analysis through:
    1. Current State Assessment (inventory, architecture, hosting)
    2. Technical Debt Analysis (versions, EOL, customizations)
    3. Overlap Analysis (target vs buyer applications)
    4. Rationalization Strategy (consolidate, migrate, retire, maintain)
    5. Licensing & Vendor Risk
    6. Integration Complexity Scoring

    Key areas analyzed:
    - ERP Systems: SAP, Oracle, NetSuite, Microsoft Dynamics
    - CRM: Salesforce, HubSpot, Dynamics 365
    - HR/HCM: Workday, ADP, UKG, SAP SuccessFactors
    - Core Business: Policy Admin, Claims, Manufacturing, etc.
    - Collaboration: M365, Google Workspace
    - Custom Applications: Technical debt, dependencies
    """

    @property
    def domain(self) -> str:
        return "applications"

    @property
    def system_prompt(self) -> str:
        return APPLICATIONS_SYSTEM_PROMPT
