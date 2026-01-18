"""
Reasoning Agents Module

Domain-specific reasoning agents that analyze facts and produce findings.
"""

from agents_v2.reasoning.infrastructure_reasoning import InfrastructureReasoningAgent
from agents_v2.reasoning.network_reasoning import NetworkReasoningAgent
from agents_v2.reasoning.cybersecurity_reasoning import CybersecurityReasoningAgent
from agents_v2.reasoning.applications_reasoning import ApplicationsReasoningAgent
from agents_v2.reasoning.identity_access_reasoning import IdentityAccessReasoningAgent
from agents_v2.reasoning.organization_reasoning import OrganizationReasoningAgent

__all__ = [
    'InfrastructureReasoningAgent',
    'NetworkReasoningAgent',
    'CybersecurityReasoningAgent',
    'ApplicationsReasoningAgent',
    'IdentityAccessReasoningAgent',
    'OrganizationReasoningAgent',
]

# Domain to agent class mapping
REASONING_AGENTS = {
    'infrastructure': InfrastructureReasoningAgent,
    'network': NetworkReasoningAgent,
    'cybersecurity': CybersecurityReasoningAgent,
    'applications': ApplicationsReasoningAgent,
    'identity_access': IdentityAccessReasoningAgent,
    'organization': OrganizationReasoningAgent,
}
