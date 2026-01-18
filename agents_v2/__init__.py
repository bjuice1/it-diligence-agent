"""
V2 Agents Module

Discovery-Reasoning split architecture agents:
- BaseDiscoveryAgent: Extract facts from documents (Haiku model)
- BaseReasoningAgent: Analyze facts and produce findings (Sonnet model)
- Domain-specific agents in discovery/ and reasoning/ submodules
"""

from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from agents_v2.base_reasoning_agent import BaseReasoningAgent
from agents_v2.discovery.infrastructure_discovery import InfrastructureDiscoveryAgent
from agents_v2.reasoning.infrastructure_reasoning import InfrastructureReasoningAgent

__all__ = [
    # Base classes
    'BaseDiscoveryAgent',
    'BaseReasoningAgent',
    # Infrastructure agents
    'InfrastructureDiscoveryAgent',
    'InfrastructureReasoningAgent'
]
