"""
Organization domain - Deduplication and identity management for people/teams/departments.

CRITICAL: Uses kernel primitives (not POC).
This domain handles people, teams, departments, and roles.

Public API:
- Person: Aggregate root
- PersonId: Value object (stable IDs)
- PersonRepository: Deduplication engine

Created: 2026-02-12 (Worker 4 - Organization Domain, Task-023)
"""

from domain.organization.person import Person
from domain.organization.person_id import PersonId
from domain.organization.repository import PersonRepository

__all__ = [
    "Person",
    "PersonId",
    "PersonRepository",
]
