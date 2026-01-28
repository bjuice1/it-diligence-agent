"""
Session Store - Redirect Module

DEPRECATED: This module has been moved to stores/session_store.py
This file exists for backward compatibility only.

Phase E: Store Consolidation - all stores now live in the stores/ package.
Import from stores.session_store or stores directly for new code.
"""

# Re-export everything from the new location
from stores.session_store import (
    SessionStore,
    UserSession,
    session_store,
    get_or_create_session_id,
)

__all__ = [
    "SessionStore",
    "UserSession",
    "session_store",
    "get_or_create_session_id",
]
