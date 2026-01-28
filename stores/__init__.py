"""
Stores package for IT Due Diligence System.

Phase E consolidation: All persistence layers in one place.

Contains:
- FactStore: Central fact repository with evidence chains
- DocumentStore: Source document registry with hash verification
- GranularFactsStore: Fine-grained fact storage
- SessionStore: Web session management
- ValidationStore: Validation state for facts
- CorrectionStore: Human correction audit trail
- AuditStore: Complete audit trail for all actions
"""

# Core stores (Phase E: moved from tools_v2 and web)
from stores.fact_store import (
    FactStore,
    Fact,
    Gap,
    VerificationStatus,
    DOMAIN_PREFIXES,
)
from stores.document_store import (
    DocumentStore,
    Document,
    DocumentStatus,
    AuthorityLevel,
    Entity,
)
from stores.granular_facts_store import GranularFactsStore
from stores.session_store import (
    SessionStore,
    session_store,
    get_or_create_session_id,
)

# Validation stores (existing)
from stores.validation_store import ValidationStore
from stores.correction_store import CorrectionStore
from stores.audit_store import AuditStore, AuditAction, AuditEntry

__all__ = [
    # Core stores
    "FactStore",
    "Fact",
    "Gap",
    "VerificationStatus",
    "DOMAIN_PREFIXES",
    "DocumentStore",
    "Document",
    "DocumentStatus",
    "AuthorityLevel",
    "Entity",
    "GranularFactsStore",
    "SessionStore",
    "session_store",
    "get_or_create_session_id",
    # Validation stores
    "ValidationStore",
    "CorrectionStore",
    "AuditStore",
    "AuditAction",
    "AuditEntry",
]
