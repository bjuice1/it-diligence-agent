"""
EXPERIMENTAL DOMAIN MODEL - NOT FOR PRODUCTION USE

This code is under active development for the domain-first redesign.
It should NOT be imported by production code paths.

Status: KERNEL COMPLETE (Worker 1) → Building domains (Workers 2-4)
Target: Replace stores/ (FactStore, InventoryStore)
Timeline: 6-8 weeks (see ISOLATION_STRATEGY.md)

Safe usage (local development):
    export ENABLE_DOMAIN_MODEL=true
    python -m domain.DEMO_NEW

Unsafe usage (production):
    from domain.kernel import Entity  # ❌ DON'T DO THIS in web/app.py!

Architecture:
- domain/kernel/ - ✅ COMPLETE - Shared primitives (Entity, Observation, Normalization)
- domain/applications/ - ⏳ TODO (Worker 2)
- domain/infrastructure/ - ⏳ TODO (Worker 3)
- domain/organization/ - ⏳ TODO (Worker 4)

Key Principles:
- Kernel provides single source of truth for ALL domains
- Domain entities own business rules
- Repository interfaces define contracts
- Value objects ensure invariants
- No dependencies on frameworks or I/O

Created: 2026-02-12 (POC)
Updated: 2026-02-12 (Worker 1 - Kernel Foundation)
Cleaned: 2026-02-12 (Removed old POC, kernel is canonical)
"""

# Import guard - warn if imported in production
from domain.guards import ExperimentalGuard
ExperimentalGuard.warn_if_production()

# ✅ KERNEL FOUNDATION (Worker 1) - CANONICAL SOURCE OF TRUTH
from domain.kernel.entity import Entity
from domain.kernel.observation import Observation
from domain.kernel.normalization import NormalizationRules
from domain.kernel.entity_inference import EntityInference
from domain.kernel.fingerprint import FingerprintGenerator
from domain.kernel.extraction import ExtractionCoordinator

# Note: Repository is ABC, not directly exported
# from domain.kernel.repository import DomainRepository

__all__ = [
    # Kernel primitives (Worker 1)
    'Entity',
    'Observation',
    'NormalizationRules',
    'EntityInference',
    'FingerprintGenerator',
    'ExtractionCoordinator',
    # Domain aggregates (Workers 2-4)
    # 'Application',  # TODO: Worker 2
    # 'Infrastructure',  # TODO: Worker 3
    # 'OrganizationMember',  # TODO: Worker 4
]
