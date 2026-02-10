"""
Granular Facts Store - Redirect Module

DEPRECATED: This module has been moved to stores/granular_facts_store.py
This file exists for backward compatibility only.

Phase E: Store Consolidation - all stores now live in the stores/ package.
Import from stores.granular_facts_store or stores directly for new code.
"""

# Re-export everything from the new location
from stores.granular_facts_store import GranularFactsStore

__all__ = ["GranularFactsStore"]
