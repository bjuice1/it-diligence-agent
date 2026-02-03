"""
Dual Write Store - Write to Both JSON and PostgreSQL

Wraps the existing FactStore to provide dual-write capability during migration.
This ensures data consistency while transitioning from JSON to PostgreSQL.

Usage:
    from stores.dual_write_store import DualWriteFactStore

    # Create dual-write enabled store
    store = DualWriteFactStore(deal_id="deal-123")

    # Use normally - writes go to both JSON and PostgreSQL
    fact_id = store.add_fact(
        domain="infrastructure",
        category="compute",
        item="VMware Environment",
        details={"platform": "VMware"},
        status="documented",
        evidence={"exact_quote": "..."}
    )
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from stores.fact_store import FactStore, Fact

logger = logging.getLogger(__name__)


class DualWriteFactStore(FactStore):
    """
    FactStore with dual-write capability to PostgreSQL.

    When USE_DATABASE is enabled, writes go to both:
    1. In-memory store (and JSON on save())
    2. PostgreSQL database

    This provides:
    - Backwards compatibility with existing code
    - Data redundancy during migration
    - Ability to verify JSON/DB consistency
    """

    def __init__(self, deal_id: Optional[str] = None, enable_dual_write: Optional[bool] = None):
        """
        Initialize dual-write fact store.

        Args:
            deal_id: Deal ID to associate facts with in PostgreSQL
            enable_dual_write: Override for dual-write (defaults to USE_DATABASE env var)
        """
        super().__init__()

        self.deal_id = deal_id
        self._db_enabled = self._check_db_enabled(enable_dual_write)
        self._db_fact_ids: Dict[str, str] = {}  # Maps JSON fact_id to DB fact_id
        self._write_errors: List[Dict[str, Any]] = []

        if self._db_enabled:
            logger.info(f"DualWriteFactStore initialized with deal_id={deal_id}, dual-write ENABLED")
        else:
            logger.info("DualWriteFactStore initialized, dual-write DISABLED (JSON only)")

    def _check_db_enabled(self, override: Optional[bool] = None) -> bool:
        """Check if database dual-write is enabled."""
        if override is not None:
            return override

        # Check environment
        use_db = os.environ.get('USE_DATABASE', 'false').lower() == 'true'

        # Verify database is actually available
        if use_db:
            try:
                from web.database import db
                # Quick connectivity check
                return True
            except ImportError:
                logger.warning("USE_DATABASE=true but web.database not available")
                return False
            except Exception as e:
                logger.warning(f"Database not available: {e}")
                return False

        return False

    def add_fact(self, domain: str, category: str, item: str,
                 details: Dict[str, Any], status: str,
                 evidence: Dict[str, str], entity: str = "target",
                 source_document: str = "", needs_review: bool = False,
                 needs_review_reason: str = "",
                 analysis_phase: str = None,
                 is_integration_insight: bool = False) -> str:
        """
        Add a fact to both JSON store and PostgreSQL.

        Args:
            (same as FactStore.add_fact)

        Returns:
            Unique fact ID (e.g., F-INFRA-001)
        """
        # First, add to JSON store (parent class)
        fact_id = super().add_fact(
            domain=domain,
            category=category,
            item=item,
            details=details,
            status=status,
            evidence=evidence,
            entity=entity,
            source_document=source_document,
            needs_review=needs_review,
            needs_review_reason=needs_review_reason,
            analysis_phase=analysis_phase,
            is_integration_insight=is_integration_insight
        )

        # Then, write to PostgreSQL if enabled
        if self._db_enabled:
            self._write_to_db(fact_id)

        return fact_id

    def _write_to_db(self, fact_id: str) -> bool:
        """
        Write a fact to PostgreSQL.

        Args:
            fact_id: The fact ID to write

        Returns:
            True if successful, False otherwise
        """
        try:
            from flask import current_app
            from web.database import db, Fact as DBFact

            # Get the fact from in-memory store
            fact = self.get_fact_by_id(fact_id)
            if not fact:
                logger.error(f"Fact {fact_id} not found in store for DB write")
                return False

            # Check if we're in app context
            app_ctx = current_app._get_current_object() if current_app else None

            def do_write():
                # Check if fact already exists in DB
                existing = DBFact.query.filter_by(id=fact_id).first()
                if existing:
                    # Update existing
                    existing.domain = fact.domain
                    existing.category = fact.category
                    existing.item = fact.item
                    existing.status = fact.status
                    existing.entity = fact.entity
                    existing.details = fact.details
                    existing.evidence = fact.evidence
                    existing.source_document = fact.source_document
                    existing.confidence_score = fact.confidence_score
                    existing.verified = fact.verified
                    existing.verification_status = fact.verification_status
                    existing.updated_at = datetime.utcnow()
                    logger.debug(f"Updated existing fact {fact_id} in PostgreSQL")
                else:
                    # Create new
                    db_fact = DBFact(
                        id=fact_id,
                        deal_id=self.deal_id,
                        domain=fact.domain,
                        category=fact.category,
                        item=fact.item,
                        status=fact.status,
                        entity=fact.entity,
                        details=fact.details,
                        evidence=fact.evidence,
                        source_document=fact.source_document,
                        confidence_score=fact.confidence_score,
                        verified=fact.verified,
                        verification_status=fact.verification_status,
                        source_quote=fact.evidence.get('exact_quote', '') if fact.evidence else '',
                    )
                    db.session.add(db_fact)
                    logger.debug(f"Created new fact {fact_id} in PostgreSQL")

                db.session.commit()
                self._db_fact_ids[fact_id] = fact_id
                return True

            if app_ctx:
                return do_write()
            else:
                # Create app context for standalone usage
                from web.app import create_app
                app = create_app()
                with app.app_context():
                    return do_write()

        except Exception as e:
            logger.error(f"Failed to write fact {fact_id} to PostgreSQL: {e}")
            self._write_errors.append({
                'fact_id': fact_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return False

    def update_fact(self, fact_id: str, **updates) -> bool:
        """
        Update a fact in both JSON store and PostgreSQL.

        Args:
            fact_id: The fact ID to update
            **updates: Fields to update

        Returns:
            True if successful
        """
        # Update in JSON store
        fact = self.get_fact_by_id(fact_id)
        if not fact:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(fact, key):
                setattr(fact, key, value)

        fact.updated_at = datetime.now().isoformat()

        # Recalculate confidence if relevant fields changed
        if any(k in updates for k in ['evidence', 'details', 'source_document', 'verified']):
            fact.confidence_score = fact.calculate_confidence()

        # Update in PostgreSQL
        if self._db_enabled:
            self._write_to_db(fact_id)

        return True

    def verify_fact(self, fact_id: str, verified_by: str,
                    verification_status: str = "confirmed",
                    verification_note: str = "") -> bool:
        """
        Verify a fact in both JSON store and PostgreSQL.

        Args:
            fact_id: The fact ID to verify
            verified_by: User who verified
            verification_status: Status (confirmed, incorrect, needs_info, skipped)
            verification_note: Optional note

        Returns:
            True if successful
        """
        # Call parent method
        result = super().verify_fact(fact_id, verified_by, verification_status, verification_note)

        # Sync to PostgreSQL
        if result and self._db_enabled:
            self._write_to_db(fact_id)

        return result

    def sync_to_db(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync all facts to PostgreSQL.

        Args:
            force: If True, overwrite existing facts in DB

        Returns:
            Sync statistics
        """
        if not self._db_enabled:
            return {'status': 'skipped', 'reason': 'Database not enabled'}

        stats = {
            'total': len(self.facts),
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

        for fact in self.facts:
            try:
                if self._write_to_db(fact.fact_id):
                    if fact.fact_id in self._db_fact_ids:
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1
                else:
                    stats['errors'] += 1
            except Exception as e:
                logger.error(f"Error syncing fact {fact.fact_id}: {e}")
                stats['errors'] += 1

        logger.info(f"Sync complete: {stats}")
        return stats

    def get_write_errors(self) -> List[Dict[str, Any]]:
        """Get list of write errors that occurred during dual-write."""
        return self._write_errors.copy()

    def clear_write_errors(self):
        """Clear the write error log."""
        self._write_errors.clear()

    @property
    def db_enabled(self) -> bool:
        """Check if database dual-write is enabled."""
        return self._db_enabled

    @property
    def synced_fact_count(self) -> int:
        """Number of facts successfully written to DB."""
        return len(self._db_fact_ids)


def create_fact_store(deal_id: Optional[str] = None,
                      use_dual_write: Optional[bool] = None) -> FactStore:
    """
    Factory function to create the appropriate FactStore.

    Args:
        deal_id: Deal ID for database association
        use_dual_write: Override dual-write setting (defaults to USE_DATABASE)

    Returns:
        FactStore or DualWriteFactStore depending on configuration
    """
    use_db = use_dual_write
    if use_db is None:
        use_db = os.environ.get('USE_DATABASE', 'false').lower() == 'true'

    if use_db:
        return DualWriteFactStore(deal_id=deal_id, enable_dual_write=True)
    else:
        return FactStore(deal_id=deal_id)
