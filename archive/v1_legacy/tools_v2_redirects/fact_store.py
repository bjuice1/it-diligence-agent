"""
Fact Store - Redirect Module

DEPRECATED: This module has been moved to stores/fact_store.py
This file exists for backward compatibility only.

Phase E: Store Consolidation - all stores now live in the stores/ package.
Import from stores.fact_store or stores directly for new code.
"""

# Re-export everything from the new location
from stores.fact_store import (
    FactStore,
    Fact,
    Gap,
    VerificationStatus,
    DOMAIN_PREFIXES,
    _generate_timestamp,
)

__all__ = [
    "FactStore",
    "Fact",
    "Gap",
    "VerificationStatus",
    "DOMAIN_PREFIXES",
    "_generate_timestamp",
]
