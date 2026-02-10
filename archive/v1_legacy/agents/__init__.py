"""
Agents Module

Domain-specific analysis agents for IT diligence.

Agents:
- InfrastructureAgent: Data centers, servers, storage, cloud
- NetworkAgent: WAN, LAN, connectivity, network security
- CybersecurityAgent: Security tools, compliance, vulnerability management
- ApplicationsAgent: Application portfolio, overlap, rationalization, licensing
- OrganizationAgent: IT org structure, key person risk, outsourcing, skills
- IdentityAccessAgent: IAM, SSO, MFA, PAM, JML, access governance
- CoordinatorAgent: Cross-domain synthesis and executive summary
"""
from .base_agent import BaseAgent
from .infrastructure_agent import InfrastructureAgent
from .network_agent import NetworkAgent
from .cybersecurity_agent import CybersecurityAgent
from .applications_agent import ApplicationsAgent
from .organization_agent import OrganizationAgent
from .identity_access_agent import IdentityAccessAgent
from .coordinator_agent import CoordinatorAgent

__all__ = [
    'BaseAgent',
    'InfrastructureAgent',
    'NetworkAgent',
    'CybersecurityAgent',
    'ApplicationsAgent',
    'OrganizationAgent',
    'IdentityAccessAgent',
    'CoordinatorAgent'
]
