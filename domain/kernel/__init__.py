"""
Domain Kernel - Shared Primitives Layer

CRITICAL: This is THE kernel layer for the entire domain model.
All domains (applications, infrastructure, organization) use these shared primitives.

Purpose:
    Prevents cross-domain inconsistency by providing a single source of truth for:
    - Entity (target vs buyer)
    - Observation schema (how data is extracted and stored)
    - Normalization rules (how names are deduplicated)
    - Entity inference (how to determine target vs buyer from context)
    - Fingerprint generation (stable ID generation)
    - Repository patterns (deduplication and query patterns)
    - Extraction coordination (prevents double-counting)

Fixes:
    - P0-3: Normalization collisions (SAP ERP vs SAP SuccessFactors)
    - P0-2: O(n²) reconciliation (circuit breaker + database fuzzy search)

Created: 2026-02-12 (Worker 1 - Kernel Foundation)
"""

# Core primitives
from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

# Normalization and inference
from domain.kernel.normalization import NormalizationRules, DomainType
from domain.kernel.entity_inference import EntityInference

# ID generation
from domain.kernel.fingerprint import FingerprintGenerator

# Repository pattern
from domain.kernel.repository import DomainRepository

# Extraction coordination
from domain.kernel.extraction import ExtractionCoordinator

__all__ = [
    # Core primitives
    "Entity",
    "Observation",

    # Normalization and inference
    "NormalizationRules",
    "DomainType",
    "EntityInference",

    # ID generation
    "FingerprintGenerator",

    # Repository pattern
    "DomainRepository",

    # Extraction coordination
    "ExtractionCoordinator",
]

__version__ = "1.0.0"
__author__ = "Worker 1 - Kernel Foundation"
