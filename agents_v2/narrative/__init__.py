"""
Narrative Agents for Investment Thesis Generation.

Each domain has a dedicated narrative agent that synthesizes
facts and findings into presentation-ready content.

Architecture:
- 6 domain narrative agents run in parallel (Sonnet)
- 1 cost synthesis agent runs after to aggregate costs
- Outputs feed into presentation.py for HTML generation
"""

from .base_narrative_agent import BaseNarrativeAgent, NarrativeMetrics
from .infrastructure_narrative import InfrastructureNarrativeAgent
from .network_narrative import NetworkNarrativeAgent
from .cybersecurity_narrative import CybersecurityNarrativeAgent
from .applications_narrative import ApplicationsNarrativeAgent
from .identity_narrative import IdentityNarrativeAgent
from .organization_narrative import OrganizationNarrativeAgent
from .cost_synthesis_agent import CostSynthesisAgent, CostMetrics

# Map domain names to narrative agent classes
NARRATIVE_AGENTS = {
    'infrastructure': InfrastructureNarrativeAgent,
    'network': NetworkNarrativeAgent,
    'cybersecurity': CybersecurityNarrativeAgent,
    'applications': ApplicationsNarrativeAgent,
    'identity_access': IdentityNarrativeAgent,
    'organization': OrganizationNarrativeAgent
}

__all__ = [
    'BaseNarrativeAgent',
    'NarrativeMetrics',
    'InfrastructureNarrativeAgent',
    'NetworkNarrativeAgent',
    'CybersecurityNarrativeAgent',
    'ApplicationsNarrativeAgent',
    'IdentityNarrativeAgent',
    'OrganizationNarrativeAgent',
    'CostSynthesisAgent',
    'CostMetrics',
    'NARRATIVE_AGENTS'
]
