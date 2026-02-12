"""
Application Domain - Extends kernel primitives.

CRITICAL: This domain USES kernel primitives (does not reinvent them).
Ensures consistent behavior with infrastructure and organization domains.

Kernel Compliance:
- ✅ Uses kernel.Entity (not custom entity enum)
- ✅ Uses kernel.Observation (not custom observation schema)
- ✅ Uses kernel.NormalizationRules (not custom normalization)
- ✅ Uses kernel.FingerprintGenerator (not custom ID generation)
- ✅ Extends kernel.DomainRepository (not custom repository pattern)

Created: 2026-02-12 (Worker 2 - Application Domain, Task-014)
"""

from domain.applications.application import Application
from domain.applications.application_id import ApplicationId
from domain.applications.repository import ApplicationRepository

__all__ = [
    "Application",
    "ApplicationId",
    "ApplicationRepository",
]

__version__ = "1.0.0"
__author__ = "Worker 2 - Application Domain"
