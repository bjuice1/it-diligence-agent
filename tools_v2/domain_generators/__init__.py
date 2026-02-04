"""
Domain Report Generators

Each generator produces DomainReportData for a specific domain.
Follows the 5-section PE framework:
1. What You're Getting (Inventory)
2. What It Costs Today (Run-Rate)
3. How It Compares (Benchmark Assessment)
4. What Needs to Happen (Actions/Work Items)
5. Team Implications (Resources)
"""

from tools_v2.domain_generators.organization import OrganizationDomainGenerator
from tools_v2.domain_generators.applications import ApplicationsDomainGenerator
from tools_v2.domain_generators.infrastructure import InfrastructureDomainGenerator
from tools_v2.domain_generators.network import NetworkDomainGenerator
from tools_v2.domain_generators.cybersecurity import CybersecurityDomainGenerator
from tools_v2.domain_generators.identity import IdentityDomainGenerator
from tools_v2.domain_generators.base import BaseDomainGenerator

__all__ = [
    "BaseDomainGenerator",
    "OrganizationDomainGenerator",
    "ApplicationsDomainGenerator",
    "InfrastructureDomainGenerator",
    "NetworkDomainGenerator",
    "CybersecurityDomainGenerator",
    "IdentityDomainGenerator",
]

# Domain to generator mapping
DOMAIN_GENERATORS = {
    "organization": OrganizationDomainGenerator,
    "applications": ApplicationsDomainGenerator,
    "infrastructure": InfrastructureDomainGenerator,
    "network": NetworkDomainGenerator,
    "cybersecurity": CybersecurityDomainGenerator,
    "identity_access": IdentityDomainGenerator,
}


def get_generator(domain: str) -> type:
    """Get generator class for a domain."""
    return DOMAIN_GENERATORS.get(domain, BaseDomainGenerator)
