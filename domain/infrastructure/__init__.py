"""
Infrastructure domain - Deduplication and identity management for infrastructure.

CRITICAL: Uses kernel primitives (not POC).
This domain handles servers, databases, networks, SaaS, and storage.

Public API:
- Infrastructure: Aggregate root
- InfrastructureId: Value object (stable IDs)
- InfrastructureRepository: Deduplication engine

Created: 2026-02-12 (Worker 3 - Infrastructure Domain, Task-018)
"""

from domain.infrastructure.infrastructure import Infrastructure
from domain.infrastructure.infrastructure_id import InfrastructureId
from domain.infrastructure.repository import InfrastructureRepository

__all__ = [
    "Infrastructure",
    "InfrastructureId",
    "InfrastructureRepository",
]
