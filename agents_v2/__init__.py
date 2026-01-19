"""
V2 Agents Module

Discovery-Reasoning split architecture agents:
- BaseDiscoveryAgent: Extract facts from documents (Haiku model)
- BaseReasoningAgent: Analyze facts and produce findings (Sonnet model)
- NarrativeSynthesisAgent: Produce executive narratives from all domain findings
- NarrativeReviewAgent: Validate narrative quality before delivery
- Domain-specific agents in discovery/ and reasoning/ submodules
"""

from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from agents_v2.base_reasoning_agent import BaseReasoningAgent
from agents_v2.discovery.infrastructure_discovery import InfrastructureDiscoveryAgent
from agents_v2.reasoning.infrastructure_reasoning import InfrastructureReasoningAgent
from agents_v2.narrative_synthesis_agent import NarrativeSynthesisAgent, create_narrative_agent
from agents_v2.narrative_review_agent import NarrativeReviewAgent, create_review_agent, quick_review

__all__ = [
    # Base classes
    'BaseDiscoveryAgent',
    'BaseReasoningAgent',
    # Infrastructure agents
    'InfrastructureDiscoveryAgent',
    'InfrastructureReasoningAgent',
    # Narrative Synthesis
    'NarrativeSynthesisAgent',
    'create_narrative_agent',
    # Narrative Review
    'NarrativeReviewAgent',
    'create_review_agent',
    'quick_review'
]
