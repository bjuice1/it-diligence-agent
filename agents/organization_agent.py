"""
Organization Domain Agent

Analyzes IT organization through multiple lenses:
- IT Organization Structure
- Key Person Risk
- Outsourcing & Vendor Dependencies
- Skill Gaps & Capabilities
- Retention Risk
- TSA Staffing Implications
"""
from agents.base_agent import BaseAgent
from prompts.organization_prompt import ORGANIZATION_SYSTEM_PROMPT


class OrganizationAgent(BaseAgent):
    """
    Specialized agent for IT organization domain analysis.

    Applies systematic analysis through:
    1. Current State Assessment (structure, headcount, teams, roles)
    2. Key Person Risk Identification (critical knowledge holders)
    3. Outsourcing Dependency Analysis (MSPs, contractors, vendors)
    4. Skill Gap Assessment (capabilities vs. needs)
    5. Retention Risk Evaluation (flight risk, compensation, morale)
    6. TSA & Integration Staffing Implications

    Key areas analyzed:
    - IT Leadership: CIO, VPs, Directors
    - Team Structure: Infrastructure, Apps, Security, Service Desk
    - Outsourcing: MSPs, contractors, offshore teams
    - Key Personnel: Critical knowledge holders, single points of failure
    - Skills: Gaps, training needs, hiring requirements
    - Compensation: Market alignment, retention risk
    """

    @property
    def domain(self) -> str:
        return "organization"

    @property
    def system_prompt(self) -> str:
        return ORGANIZATION_SYSTEM_PROMPT
