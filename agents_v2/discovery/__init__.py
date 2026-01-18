"""
Discovery Agents Module

Domain-specific discovery agents that extract facts from documents.
"""

from agents_v2.discovery.infrastructure_discovery import InfrastructureDiscoveryAgent
from agents_v2.discovery.network_discovery import NetworkDiscoveryAgent
from agents_v2.discovery.cybersecurity_discovery import CybersecurityDiscoveryAgent
from agents_v2.discovery.applications_discovery import ApplicationsDiscoveryAgent
from agents_v2.discovery.identity_access_discovery import IdentityAccessDiscoveryAgent
from agents_v2.discovery.organization_discovery import OrganizationDiscoveryAgent

__all__ = [
    'InfrastructureDiscoveryAgent',
    'NetworkDiscoveryAgent',
    'CybersecurityDiscoveryAgent',
    'ApplicationsDiscoveryAgent',
    'IdentityAccessDiscoveryAgent',
    'OrganizationDiscoveryAgent',
]

# Domain to agent class mapping
DISCOVERY_AGENTS = {
    'infrastructure': InfrastructureDiscoveryAgent,
    'network': NetworkDiscoveryAgent,
    'cybersecurity': CybersecurityDiscoveryAgent,
    'applications': ApplicationsDiscoveryAgent,
    'identity_access': IdentityAccessDiscoveryAgent,
    'organization': OrganizationDiscoveryAgent,
}
