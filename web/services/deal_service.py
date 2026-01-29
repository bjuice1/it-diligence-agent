"""
Deal Service - Business logic for deal management

Handles deal lifecycle, validation, and coordination between
repositories. Provides the main interface for deal operations.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
import json

from flask import session, g

from web.database import db, Deal, Fact, Finding, Document, AnalysisRun
from web.repositories.deal_repository import DealRepository
from web.redis_client import deal_cache, is_redis_available

logger = logging.getLogger(__name__)


# Deal status constants
class DealStatus:
    DRAFT = 'draft'
    ACTIVE = 'active'
    ANALYZING = 'analyzing'
    COMPLETE = 'complete'
    ARCHIVED = 'archived'

# Valid status transitions
VALID_TRANSITIONS = {
    DealStatus.DRAFT: [DealStatus.ACTIVE, DealStatus.ARCHIVED],
    DealStatus.ACTIVE: [DealStatus.ANALYZING, DealStatus.COMPLETE, DealStatus.ARCHIVED],
    DealStatus.ANALYZING: [DealStatus.ACTIVE, DealStatus.COMPLETE],
    DealStatus.COMPLETE: [DealStatus.ACTIVE, DealStatus.ARCHIVED],
    DealStatus.ARCHIVED: [DealStatus.ACTIVE],  # Can restore
}


class DealService:
    """
    Service layer for deal management.

    Provides high-level operations for creating, updating, and managing deals.
    Handles business logic, validation, and coordination.
    """

    def __init__(self):
        self.repo = DealRepository()

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_deal(
        self,
        user_id: str,
        name: str,
        target_name: str,
        buyer_name: Optional[str] = None,
        deal_type: str = 'acquisition',
        industry: Optional[str] = None,
        sub_industry: Optional[str] = None,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Deal, Optional[str]]:
        """
        Create a new deal.

        Args:
            user_id: Owner user ID
            name: Deal name (must be unique per user)
            target_name: Target company name
            buyer_name: Buyer company name (optional)
            deal_type: Type of deal (acquisition, merger, etc.)
            industry: Industry sector
            sub_industry: Sub-industry
            tenant_id: Tenant ID for multi-tenancy
            context: Additional context data

        Returns:
            Tuple of (Deal object, error message or None)
        """
        # Validate required fields
        if not name or not name.strip():
            return None, "Deal name is required"
        if not target_name or not target_name.strip():
            return None, "Target company name is required"

        # Check for duplicate name
        existing = Deal.query.filter_by(
            owner_id=user_id,
            name=name.strip(),
            deleted_at=None
        ).first()
        if existing:
            return None, f"A deal named '{name}' already exists"

        try:
            deal = self.repo.create(
                owner_id=user_id,
                tenant_id=tenant_id,
                name=name.strip(),
                target_name=target_name.strip(),
                buyer_name=buyer_name.strip() if buyer_name else None,
                deal_type=deal_type,
                industry=industry,
                sub_industry=sub_industry,
                status=DealStatus.DRAFT,
                context=context or {}
            )

            logger.info(f"Created deal {deal.id}: {deal.name}")
            return deal, None

        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            return None, str(e)

    def get_deal(self, deal_id: str, include_stats: bool = True) -> Optional[Deal]:
        """
        Get a deal by ID with optional statistics.

        Args:
            deal_id: Deal ID
            include_stats: Whether to include computed statistics

        Returns:
            Deal object or None
        """
        deal = self.repo.get_by_id(deal_id)
        if deal and include_stats:
            self._load_deal_stats(deal)
        return deal

    def get_deals_for_user(
        self,
        user_id: str,
        include_archived: bool = False,
        include_stats: bool = True
    ) -> List[Deal]:
        """
        Get all deals for a user.

        Args:
            user_id: User ID
            include_archived: Include archived deals
            include_stats: Include computed statistics

        Returns:
            List of Deal objects
        """
        deals = self.repo.get_by_user(user_id, include_archived=include_archived)

        if not include_archived:
            deals = [d for d in deals if d.status != DealStatus.ARCHIVED]

        if include_stats:
            for deal in deals:
                self._load_deal_stats(deal)

        return deals

    def update_deal(
        self,
        deal_id: str,
        user_id: str,
        **updates
    ) -> Tuple[Optional[Deal], Optional[str]]:
        """
        Update a deal with optimistic locking.

        Args:
            deal_id: Deal ID
            user_id: User making the update (for audit)
            **updates: Fields to update

        Returns:
            Tuple of (Updated Deal or None, error message or None)
        """
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return None, "Deal not found"

        # Validate name uniqueness if being changed
        if 'name' in updates and updates['name'] != deal.name:
            existing = Deal.query.filter(
                Deal.owner_id == deal.owner_id,
                Deal.name == updates['name'],
                Deal.id != deal_id,
                Deal.deleted_at.is_(None)
            ).first()
            if existing:
                return None, f"A deal named '{updates['name']}' already exists"

        try:
            # Handle status transition validation
            if 'status' in updates:
                error = self._validate_status_transition(deal, updates['status'])
                if error:
                    return None, error

            deal = self.repo.update(deal, **updates)

            # Invalidate cache
            self._invalidate_deal_cache(deal_id)

            logger.info(f"Updated deal {deal_id}")
            return deal, None

        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            return None, str(e)

    def archive_deal(self, deal_id: str) -> Tuple[bool, Optional[str]]:
        """
        Archive a deal (soft delete).

        Returns:
            Tuple of (success, error message)
        """
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return False, "Deal not found"

        if deal.status == DealStatus.ANALYZING:
            return False, "Cannot archive a deal while analysis is running"

        try:
            deal.status = DealStatus.ARCHIVED
            deal.deleted_at = datetime.utcnow()
            db.session.commit()

            self._invalidate_deal_cache(deal_id)
            logger.info(f"Archived deal {deal_id}")
            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def restore_deal(self, deal_id: str) -> Tuple[bool, Optional[str]]:
        """
        Restore an archived deal.

        Returns:
            Tuple of (success, error message)
        """
        deal = Deal.query.filter_by(id=deal_id).first()  # Include deleted
        if not deal:
            return False, "Deal not found"

        try:
            deal.status = DealStatus.ACTIVE
            deal.deleted_at = None
            db.session.commit()

            self._invalidate_deal_cache(deal_id)
            logger.info(f"Restored deal {deal_id}")
            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def delete_deal(self, deal_id: str, hard_delete: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Delete a deal.

        Args:
            deal_id: Deal ID
            hard_delete: If True, permanently delete; otherwise soft delete

        Returns:
            Tuple of (success, error message)
        """
        deal = self.repo.get_by_id(deal_id, include_deleted=True)
        if not deal:
            return False, "Deal not found"

        try:
            if hard_delete:
                # Delete all related data
                Fact.query.filter_by(deal_id=deal_id).delete()
                Finding.query.filter_by(deal_id=deal_id).delete()
                Document.query.filter_by(deal_id=deal_id).delete()
                AnalysisRun.query.filter_by(deal_id=deal_id).delete()
                db.session.delete(deal)
            else:
                deal.deleted_at = datetime.utcnow()
                deal.status = DealStatus.ARCHIVED

            db.session.commit()
            self._invalidate_deal_cache(deal_id)
            logger.info(f"Deleted deal {deal_id} (hard={hard_delete})")
            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def duplicate_deal(
        self,
        deal_id: str,
        new_name: str,
        user_id: str,
        include_documents: bool = False
    ) -> Tuple[Optional[Deal], Optional[str]]:
        """
        Duplicate a deal as a template.

        Args:
            deal_id: Source deal ID
            new_name: Name for the new deal
            user_id: User creating the duplicate
            include_documents: Whether to copy document references

        Returns:
            Tuple of (New Deal or None, error message or None)
        """
        source = self.repo.get_by_id(deal_id)
        if not source:
            return None, "Source deal not found"

        return self.create_deal(
            user_id=user_id,
            name=new_name,
            target_name=source.target_name,
            buyer_name=source.buyer_name,
            deal_type=source.deal_type,
            industry=source.industry,
            sub_industry=source.sub_industry,
            tenant_id=source.tenant_id,
            context=source.context.copy() if source.context else {}
        )

    # =========================================================================
    # Session/Context Management
    # =========================================================================

    def get_active_deal_for_session(self, session_id: str = None) -> Optional[Deal]:
        """
        Get the currently active deal for a session.

        Args:
            session_id: Session ID (uses Flask session if not provided)

        Returns:
            Active Deal or None
        """
        deal_id = session.get('current_deal_id')
        if not deal_id:
            return None

        return self.get_deal(deal_id)

    def set_active_deal_for_session(self, deal_id: str, session_id: str = None) -> bool:
        """
        Set the active deal for a session.

        Args:
            deal_id: Deal ID to set as active
            session_id: Session ID (uses Flask session if not provided)

        Returns:
            True if successful
        """
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return False

        session['current_deal_id'] = deal_id

        # Update last accessed
        deal.last_accessed_at = datetime.utcnow()
        db.session.commit()

        logger.debug(f"Set active deal to {deal_id}")
        return True

    def clear_active_deal(self, session_id: str = None):
        """Clear the active deal for a session."""
        session.pop('current_deal_id', None)

    def get_current_deal(self) -> Optional[Deal]:
        """
        Get the current deal from Flask g object or session.

        Caches the deal in g for the request duration.
        """
        if hasattr(g, 'current_deal'):
            return g.current_deal

        deal = self.get_active_deal_for_session()
        if deal:
            g.current_deal = deal

        return deal

    # =========================================================================
    # Statistics & Summary
    # =========================================================================

    def get_deal_summary(self, deal_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a deal.

        Returns:
            Dict with deal summary data
        """
        # Check cache first
        cache_key = f"summary:{deal_id}"
        if is_redis_available():
            cached = deal_cache.get(cache_key)
            if cached:
                return cached

        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return {}

        # Compute statistics
        facts_count = Fact.query.filter_by(deal_id=deal_id, deleted_at=None).count()
        findings_count = Finding.query.filter_by(deal_id=deal_id, deleted_at=None).count()
        documents_count = Document.query.filter_by(deal_id=deal_id, deleted_at=None).count()
        analysis_runs = AnalysisRun.query.filter_by(deal_id=deal_id).count()

        # Count by type
        risks_count = Finding.query.filter_by(
            deal_id=deal_id, finding_type='risk', deleted_at=None
        ).count()
        work_items_count = Finding.query.filter_by(
            deal_id=deal_id, finding_type='work_item', deleted_at=None
        ).count()

        # Calculate review progress
        verified_facts = Fact.query.filter_by(deal_id=deal_id, verified=True, deleted_at=None).count()
        review_percent = (verified_facts / max(1, facts_count)) * 100

        summary = {
            'deal_id': str(deal_id),
            'name': deal.name,
            'target_name': deal.target_name,
            'buyer_name': deal.buyer_name,
            'status': deal.status,
            'deal_type': deal.deal_type,
            'industry': deal.industry,
            'documents_count': documents_count,
            'facts_count': facts_count,
            'findings_count': findings_count,
            'risks_count': risks_count,
            'work_items_count': work_items_count,
            'analysis_runs': analysis_runs,
            'review_percent': round(review_percent, 1),
            'verified_facts': verified_facts,
            'target_locked': deal.target_locked,
            'buyer_locked': deal.buyer_locked,
            'created_at': deal.created_at.isoformat() if deal.created_at else None,
            'updated_at': deal.updated_at.isoformat() if deal.updated_at else None,
            'last_accessed_at': deal.last_accessed_at.isoformat() if deal.last_accessed_at else None,
        }

        # Cache for 5 minutes
        if is_redis_available():
            deal_cache.set(cache_key, summary, ttl=300)

        return summary

    def get_deal_progress(self, deal_id: str) -> Dict[str, Any]:
        """
        Get deal completion progress.

        Returns:
            Dict with progress indicators
        """
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return {}

        # Define progress stages
        has_documents = Document.query.filter_by(deal_id=deal_id, deleted_at=None).count() > 0
        has_target_facts = Fact.query.filter_by(deal_id=deal_id, entity='target', deleted_at=None).count() > 0
        has_buyer_facts = Fact.query.filter_by(deal_id=deal_id, entity='buyer', deleted_at=None).count() > 0
        has_findings = Finding.query.filter_by(deal_id=deal_id, deleted_at=None).count() > 0

        stages = [
            {'name': 'Documents uploaded', 'complete': has_documents},
            {'name': 'Target analysis', 'complete': has_target_facts},
            {'name': 'Buyer analysis', 'complete': has_buyer_facts},
            {'name': 'Findings generated', 'complete': has_findings},
            {'name': 'Review complete', 'complete': deal.review_percent == 100 if deal.review_percent else False},
        ]

        completed = sum(1 for s in stages if s['complete'])
        total = len(stages)

        return {
            'stages': stages,
            'completed': completed,
            'total': total,
            'percent': round((completed / total) * 100, 1)
        }

    # =========================================================================
    # Export/Import
    # =========================================================================

    def export_deal(self, deal_id: str) -> Dict[str, Any]:
        """
        Export a deal to JSON format for portability.

        Returns:
            Dict containing all deal data
        """
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return {}

        # Get all related data
        facts = Fact.query.filter_by(deal_id=deal_id, deleted_at=None).all()
        findings = Finding.query.filter_by(deal_id=deal_id, deleted_at=None).all()
        documents = Document.query.filter_by(deal_id=deal_id, deleted_at=None).all()

        return {
            'version': '1.0',
            'exported_at': datetime.utcnow().isoformat(),
            'deal': deal.to_dict(),
            'facts': [f.to_dict() for f in facts],
            'findings': [f.to_dict() for f in findings],
            'documents': [d.to_dict() for d in documents],
            'summary': self.get_deal_summary(deal_id)
        }

    def import_deal(
        self,
        data: Dict[str, Any],
        user_id: str,
        new_name: Optional[str] = None
    ) -> Tuple[Optional[Deal], Optional[str]]:
        """
        Import a deal from JSON data.

        Args:
            data: Exported deal data
            user_id: User importing the deal
            new_name: Optional new name for the deal

        Returns:
            Tuple of (Imported Deal or None, error message or None)
        """
        if 'deal' not in data:
            return None, "Invalid import data: missing 'deal' key"

        deal_data = data['deal']
        name = new_name or f"{deal_data.get('name', 'Imported')} (Imported)"

        # Create the deal
        deal, error = self.create_deal(
            user_id=user_id,
            name=name,
            target_name=deal_data.get('target_name', 'Unknown'),
            buyer_name=deal_data.get('buyer_name'),
            deal_type=deal_data.get('deal_type', 'acquisition'),
            industry=deal_data.get('industry'),
            sub_industry=deal_data.get('sub_industry'),
            context=deal_data.get('context')
        )

        if error:
            return None, error

        # Import facts
        for fact_data in data.get('facts', []):
            try:
                Fact.from_dict({**fact_data, 'deal_id': deal.id})
            except Exception as e:
                logger.warning(f"Error importing fact: {e}")

        # Import findings
        for finding_data in data.get('findings', []):
            try:
                Finding.from_dict({**finding_data, 'deal_id': deal.id})
            except Exception as e:
                logger.warning(f"Error importing finding: {e}")

        db.session.commit()
        logger.info(f"Imported deal {deal.id} with {len(data.get('facts', []))} facts")

        return deal, None

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _load_deal_stats(self, deal: Deal):
        """Load computed statistics into deal object."""
        deal.documents_uploaded = Document.query.filter_by(
            deal_id=deal.id, deleted_at=None
        ).count()
        deal.facts_extracted = Fact.query.filter_by(
            deal_id=deal.id, deleted_at=None
        ).count()
        deal.findings_count = Finding.query.filter_by(
            deal_id=deal.id, deleted_at=None
        ).count()

    def _validate_status_transition(self, deal: Deal, new_status: str) -> Optional[str]:
        """
        Validate a status transition.

        Returns:
            Error message if invalid, None if valid
        """
        current = deal.status
        if new_status == current:
            return None  # No change

        valid = VALID_TRANSITIONS.get(current, [])
        if new_status not in valid:
            return f"Cannot transition from '{current}' to '{new_status}'"

        # Additional validation for specific transitions
        if new_status == DealStatus.COMPLETE:
            facts_count = Fact.query.filter_by(deal_id=deal.id, deleted_at=None).count()
            if facts_count == 0:
                return "Cannot mark as complete: no facts extracted"

        return None

    def _invalidate_deal_cache(self, deal_id: str):
        """Invalidate cached data for a deal."""
        if is_redis_available():
            deal_cache.delete(f"summary:{deal_id}")


# Singleton instance
_deal_service = None


def get_deal_service() -> DealService:
    """Get the DealService singleton instance."""
    global _deal_service
    if _deal_service is None:
        _deal_service = DealService()
    return _deal_service
