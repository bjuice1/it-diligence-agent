"""
Infrastructure Domain Agent

Analyzes IT infrastructure through multiple lenses:
- Hosting Model Analysis
- Compute & Server Analysis
- Storage & Data Analysis
- Cloud Infrastructure Analysis
- Legacy & Mainframe Analysis
- Platform Alignment Analysis
"""
from agents.base_agent import BaseAgent
from prompts.infrastructure_prompt import INFRASTRUCTURE_SYSTEM_PROMPT


class InfrastructureAgent(BaseAgent):
    """
    Specialized agent for infrastructure domain analysis.
    
    Applies systematic analysis through:
    1. Current State Assessment (hosting, compute, storage, cloud, legacy)
    2. Integration Complexity (platform alignment, dependencies, data migration)
    3. Cost & Financial Analysis (one-time costs, run-rate impact)
    4. Risk & Opportunity Identification
    """
    
    @property
    def domain(self) -> str:
        return "infrastructure"
    
    @property
    def system_prompt(self) -> str:
        return INFRASTRUCTURE_SYSTEM_PROMPT
