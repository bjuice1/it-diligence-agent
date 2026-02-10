"""
Document Store - Redirect Module

DEPRECATED: This module has been moved to stores/document_store.py
This file exists for backward compatibility only.

Phase E: Store Consolidation - all stores now live in the stores/ package.
Import from stores.document_store or stores directly for new code.
"""

# Re-export everything from the new location
from stores.document_store import (
    DocumentStore,
    Document,
    DocumentStatus,
    AuthorityLevel,
    Entity,
)

__all__ = [
    "DocumentStore",
    "Document",
    "DocumentStatus",
    "AuthorityLevel",
    "Entity",
]
