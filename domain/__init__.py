"""
EXPERIMENTAL DOMAIN MODEL - NOT FOR PRODUCTION USE

This code is under active development for the domain-first redesign.
It should NOT be imported by production code paths.

Status: PROOF OF CONCEPT → ACTIVE DEVELOPMENT
Target: Replace stores/ (FactStore, InventoryStore)
Timeline: 6-8 weeks (see ISOLATION_STRATEGY.md)

Safe usage (local development):
    export ENABLE_DOMAIN_MODEL=true
    python -m domain.cli analyze data/input/

Unsafe usage (production):
    from domain.applications import Application  # ❌ DON'T DO THIS in web/app.py!

Architecture:
- domain/kernel/ - Shared primitives (Entity, Observation, Normalization)
- domain/applications/ - Application domain
- domain/infrastructure/ - Infrastructure domain
- domain/organization/ - Organization domain

Key Principles:
- Domain entities own business rules
- Repository interfaces define contracts (implementations in infrastructure/)
- Value objects ensure invariants
- No dependencies on frameworks or I/O

Created: 2026-02-12 (POC)
Updated: 2026-02-12 (Worker 0 - Isolation Setup)
"""

# Import guard - warn if imported in production
from domain.guards import ExperimentalGuard
ExperimentalGuard.warn_if_production()

# Expose public API
from domain.value_objects.entity import Entity
from domain.entities.application import Application
from domain.repositories.application_repository import ApplicationRepository

__all__ = ['Entity', 'Application', 'ApplicationRepository']
