"""
Deal Repository

Database operations for Deal model.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_, func

from web.database import db, Deal
from .base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    """Repository for Deal CRUD and queries."""

    model = Deal

    # =========================================================================
    # DEAL-SPECIFIC QUERIES
    # =========================================================================

    def get_by_user(
        self,
        user_id: str,
        status: str = None,
        include_archived: bool = False
    ) -> List[Deal]:
        """Get all deals for a user."""
        query = self.query()
        query = query.filter(Deal.owner_id == user_id)

        if status:
            query = query.filter(Deal.status == status)
        elif not include_archived:
            query = query.filter(Deal.status != 'archived')

        return query.order_by(Deal.last_accessed_at.desc()).all()

    def get_by_tenant(
        self,
        tenant_id: str,
        status: str = None,
        include_archived: bool = False
    ) -> List[Deal]:
        """Get all deals for a tenant."""
        query = self.query()
        query = query.filter(Deal.tenant_id == tenant_id)

        if status:
            query = query.filter(Deal.status == status)
        elif not include_archived:
            query = query.filter(Deal.status != 'archived')

        return query.order_by(Deal.last_accessed_at.desc()).all()

    def get_recent_for_user(self, user_id: str, limit: int = 5) -> List[Deal]:
        """Get recently accessed deals for a user."""
        return self.query().filter(
            Deal.owner_id == user_id,
            Deal.status != 'archived'
        ).order_by(
            Deal.last_accessed_at.desc()
        ).limit(limit).all()

    def search(
        self,
        user_id: str = None,
        tenant_id: str = None,
        search_term: str = None,
        industry: str = None,
        deal_type: str = None,
        status: str = None,
        page: int = 1,
        per_page: int = 12
    ) -> Dict[str, Any]:
        """Search deals with filters and pagination."""
        query = self.query()

        if user_id:
            query = query.filter(Deal.owner_id == user_id)

        if tenant_id:
            query = query.filter(Deal.tenant_id == tenant_id)

        if search_term:
            search_filter = or_(
                Deal.name.ilike(f'%{search_term}%'),
                Deal.target_name.ilike(f'%{search_term}%'),
                Deal.buyer_name.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)

        if industry:
            query = query.filter(Deal.industry == industry)

        if deal_type:
            query = query.filter(Deal.deal_type == deal_type)

        if status:
            query = query.filter(Deal.status == status)
        else:
            query = query.filter(Deal.status != 'archived')

        # Get total count
        total = query.count()

        # Order and paginate
        query = query.order_by(Deal.last_accessed_at.desc())
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        pages = (total + per_page - 1) // per_page

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
        }

    # =========================================================================
    # DEAL LIFECYCLE
    # =========================================================================

    def create_deal(
        self,
        owner_id: str,
        target_name: str,
        name: str = None,
        buyer_name: str = '',
        deal_type: str = 'acquisition',
        industry: str = '',
        sub_industry: str = '',
        tenant_id: str = None,
        context: Dict = None,
        created_by: str = None
    ) -> Deal:
        """Create a new deal."""
        return self.create(
            owner_id=owner_id,
            tenant_id=tenant_id,
            name=name or target_name,
            target_name=target_name,
            buyer_name=buyer_name,
            deal_type=deal_type,
            industry=industry,
            sub_industry=sub_industry,
            status='draft',
            context=context or {},
            created_by=created_by or owner_id,
        )

    def archive_deal(self, deal: Deal, archived_by: str = None) -> Deal:
        """Archive a deal (soft archive via status)."""
        return self.update(
            deal,
            status='archived',
            updated_by=archived_by
        )

    def restore_deal(self, deal: Deal, restored_by: str = None) -> Deal:
        """Restore an archived deal."""
        return self.update(
            deal,
            status='active',
            updated_by=restored_by
        )

    def update_access_time(self, deal: Deal) -> Deal:
        """Update the last accessed timestamp."""
        deal.last_accessed_at = datetime.utcnow()
        db.session.commit()
        return deal

    def update_progress(
        self,
        deal: Deal,
        documents_uploaded: int = None,
        facts_extracted: int = None,
        findings_count: int = None,
        analysis_runs_count: int = None,
        review_percent: float = None
    ) -> Deal:
        """Update deal progress counters."""
        updates = {}

        if documents_uploaded is not None:
            updates['documents_uploaded'] = documents_uploaded
        if facts_extracted is not None:
            updates['facts_extracted'] = facts_extracted
        if findings_count is not None:
            updates['findings_count'] = findings_count
        if analysis_runs_count is not None:
            updates['analysis_runs_count'] = analysis_runs_count
        if review_percent is not None:
            updates['review_percent'] = review_percent

        if updates:
            return self.update(deal, **updates)
        return deal

    def recalculate_stats(self, deal: Deal) -> Deal:
        """Recalculate deal statistics from related data."""
        from web.database import Document, Fact, Finding, AnalysisRun

        doc_count = Document.query.filter(
            Document.deal_id == deal.id,
            Document.deleted_at.is_(None),
            Document.is_current == True
        ).count()

        fact_count = Fact.query.filter(
            Fact.deal_id == deal.id,
            Fact.deleted_at.is_(None)
        ).count()

        finding_count = Finding.query.filter(
            Finding.deal_id == deal.id,
            Finding.deleted_at.is_(None)
        ).count()

        run_count = AnalysisRun.query.filter(
            AnalysisRun.deal_id == deal.id
        ).count()

        # Calculate review percentage
        verified_facts = Fact.query.filter(
            Fact.deal_id == deal.id,
            Fact.deleted_at.is_(None),
            Fact.verified == True
        ).count()

        review_percent = (verified_facts / fact_count * 100) if fact_count > 0 else 0

        return self.update_progress(
            deal,
            documents_uploaded=doc_count,
            facts_extracted=fact_count,
            findings_count=finding_count,
            analysis_runs_count=run_count,
            review_percent=round(review_percent, 1)
        )

    # =========================================================================
    # ENTITY LOCKING
    # =========================================================================

    def lock_entity(
        self,
        deal: Deal,
        entity: str,
        locked_by: str
    ) -> Deal:
        """Lock an entity (target or buyer) for analysis."""
        now = datetime.utcnow()

        if entity == 'target':
            return self.update(deal, target_locked=True, locked_at=now, locked_by=locked_by)
        elif entity == 'buyer':
            return self.update(deal, buyer_locked=True, locked_at=now, locked_by=locked_by)
        else:
            raise ValueError(f"Invalid entity: {entity}")

    def unlock_entity(self, deal: Deal, entity: str) -> Deal:
        """Unlock an entity."""
        if entity == 'target':
            return self.update(deal, target_locked=False, locked_at=None, locked_by=None)
        elif entity == 'buyer':
            return self.update(deal, buyer_locked=False, locked_at=None, locked_by=None)
        else:
            raise ValueError(f"Invalid entity: {entity}")

    def is_entity_locked(self, deal: Deal, entity: str) -> bool:
        """Check if an entity is locked."""
        if entity == 'target':
            return deal.target_locked
        elif entity == 'buyer':
            return deal.buyer_locked
        return False

    # =========================================================================
    # DEAL DUPLICATION
    # =========================================================================

    def duplicate_deal(
        self,
        deal: Deal,
        new_name: str,
        new_owner_id: str = None,
        include_documents: bool = False
    ) -> Deal:
        """
        Duplicate a deal as a template.

        Note: Does not copy facts/findings, only deal metadata.
        """
        new_deal = self.create_deal(
            owner_id=new_owner_id or deal.owner_id,
            tenant_id=deal.tenant_id,
            name=new_name,
            target_name=deal.target_name,
            buyer_name=deal.buyer_name,
            deal_type=deal.deal_type,
            industry=deal.industry,
            sub_industry=deal.sub_industry,
            context=deal.context.copy() if deal.context else {},
            created_by=new_owner_id or deal.owner_id,
        )

        # TODO: If include_documents, copy document references

        return new_deal
