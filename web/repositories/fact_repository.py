"""
Fact Repository

Database operations for Fact model with full-text search support.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_, func, text

from web.database import db, Fact, FactFindingLink
from .base import BaseRepository


class FactRepository(BaseRepository[Fact]):
    """Repository for Fact CRUD and queries."""

    model = Fact

    # =========================================================================
    # FACT-SPECIFIC QUERIES
    # =========================================================================

    def get_by_deal(
        self,
        deal_id: str,
        domain: str = None,
        entity: str = None,
        category: str = None,
        status: str = None,
        verified_only: bool = False,
        needs_review: bool = None
    ) -> List[Fact]:
        """Get facts for a deal with optional filters."""
        query = self.query().filter(Fact.deal_id == deal_id)

        if domain:
            query = query.filter(Fact.domain == domain)

        if entity:
            query = query.filter(Fact.entity == entity)

        if category:
            query = query.filter(Fact.category == category)

        if status:
            query = query.filter(Fact.status == status)

        if verified_only:
            query = query.filter(Fact.verified == True)

        if needs_review is not None:
            query = query.filter(Fact.needs_review == needs_review)

        return query.order_by(Fact.id).all()

    def get_by_domain(self, deal_id: str, domain: str) -> List[Fact]:
        """Get all facts for a domain."""
        return self.get_by_deal(deal_id, domain=domain)

    def get_by_entity(self, deal_id: str, entity: str) -> List[Fact]:
        """Get all facts for an entity (target or buyer)."""
        return self.get_by_deal(deal_id, entity=entity)

    def get_by_document(self, document_id: str) -> List[Fact]:
        """Get all facts extracted from a document."""
        return self.query().filter(Fact.document_id == document_id).all()

    def get_by_analysis_run(self, analysis_run_id: str) -> List[Fact]:
        """Get all facts from an analysis run."""
        return self.query().filter(Fact.analysis_run_id == analysis_run_id).all()

    # =========================================================================
    # FULL-TEXT SEARCH
    # =========================================================================

    def search(
        self,
        deal_id: str,
        search_term: str,
        domain: str = None,
        entity: str = None,
        limit: int = 50
    ) -> List[Fact]:
        """
        Full-text search across fact item and evidence.

        Uses PostgreSQL full-text search when available,
        falls back to LIKE for SQLite.
        """
        query = self.query().filter(Fact.deal_id == deal_id)

        if domain:
            query = query.filter(Fact.domain == domain)

        if entity:
            query = query.filter(Fact.entity == entity)

        # Check if PostgreSQL (has full-text search)
        bind = db.session.get_bind()
        if 'postgresql' in str(bind.dialect.name):
            # Use PostgreSQL full-text search
            search_query = func.plainto_tsquery('english', search_term)
            query = query.filter(
                text("to_tsvector('english', item || ' ' || COALESCE(source_quote, '')) @@ plainto_tsquery('english', :term)")
            ).params(term=search_term)
        else:
            # Fallback to LIKE for SQLite
            search_filter = or_(
                Fact.item.ilike(f'%{search_term}%'),
                Fact.source_quote.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)

        return query.limit(limit).all()

    # =========================================================================
    # SUMMARY & STATISTICS
    # =========================================================================

    def get_summary_by_domain(self, deal_id: str) -> Dict[str, Dict[str, int]]:
        """Get fact counts by domain and status."""
        facts = self.get_by_deal(deal_id)

        summary = {}
        for fact in facts:
            if fact.domain not in summary:
                summary[fact.domain] = {'total': 0, 'documented': 0, 'partial': 0, 'gap': 0}

            summary[fact.domain]['total'] += 1
            if fact.status in summary[fact.domain]:
                summary[fact.domain][fact.status] += 1

        return summary

    def get_review_queue(
        self,
        deal_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Get facts needing review, paginated."""
        return self.paginate(
            page=page,
            per_page=per_page,
            deal_id=deal_id,
            needs_review=True,
            order_by='confidence_score',
            descending=False  # Lowest confidence first
        )

    def get_unverified(self, deal_id: str) -> List[Fact]:
        """Get all unverified facts for a deal."""
        return self.query().filter(
            Fact.deal_id == deal_id,
            Fact.verified == False
        ).all()

    # =========================================================================
    # VERIFICATION
    # =========================================================================

    def verify_fact(
        self,
        fact: Fact,
        verified_by: str,
        verification_note: str = ''
    ) -> Fact:
        """Mark a fact as verified."""
        return self.update(
            fact,
            verified=True,
            verified_by=verified_by,
            verified_at=datetime.utcnow(),
            verification_status='verified',
            verification_note=verification_note,
            needs_review=False
        )

    def reject_fact(
        self,
        fact: Fact,
        verified_by: str,
        rejection_note: str
    ) -> Fact:
        """Mark a fact as rejected (incorrect)."""
        return self.update(
            fact,
            verified=False,
            verified_by=verified_by,
            verified_at=datetime.utcnow(),
            verification_status='rejected',
            verification_note=rejection_note,
            needs_review=False
        )

    def flag_for_review(
        self,
        fact: Fact,
        reason: str
    ) -> Fact:
        """Flag a fact for human review."""
        return self.update(
            fact,
            needs_review=True,
            needs_review_reason=reason
        )

    # =========================================================================
    # CHANGE TRACKING
    # =========================================================================

    def get_new_facts(self, deal_id: str, since_run_id: str = None) -> List[Fact]:
        """Get facts marked as new."""
        query = self.query().filter(
            Fact.deal_id == deal_id,
            Fact.change_type == 'new'
        )

        if since_run_id:
            query = query.filter(Fact.analysis_run_id == since_run_id)

        return query.all()

    def get_updated_facts(self, deal_id: str, since_run_id: str = None) -> List[Fact]:
        """Get facts marked as updated."""
        query = self.query().filter(
            Fact.deal_id == deal_id,
            Fact.change_type == 'updated'
        )

        if since_run_id:
            query = query.filter(Fact.analysis_run_id == since_run_id)

        return query.all()

    def get_changes_summary(self, deal_id: str) -> Dict[str, int]:
        """Get summary of change types for a deal."""
        facts = self.get_by_deal(deal_id)

        summary = {'new': 0, 'updated': 0, 'unchanged': 0}
        for fact in facts:
            if fact.change_type in summary:
                summary[fact.change_type] += 1

        return summary

    # =========================================================================
    # FACT-FINDING LINKS
    # =========================================================================

    def link_to_finding(
        self,
        fact_id: str,
        finding_id: str,
        relationship_type: str = 'supports',
        relevance_score: float = 1.0
    ) -> FactFindingLink:
        """Create a link between a fact and a finding."""
        link = FactFindingLink(
            fact_id=fact_id,
            finding_id=finding_id,
            relationship_type=relationship_type,
            relevance_score=relevance_score
        )
        db.session.add(link)
        db.session.commit()
        return link

    def get_linked_findings(self, fact_id: str) -> List[str]:
        """Get IDs of findings linked to this fact."""
        links = FactFindingLink.query.filter(
            FactFindingLink.fact_id == fact_id
        ).all()
        return [link.finding_id for link in links]

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def create_many(self, facts_data: List[Dict[str, Any]]) -> List[Fact]:
        """Create multiple facts at once."""
        facts = []
        for data in facts_data:
            fact = Fact(**data)
            db.session.add(fact)
            facts.append(fact)

        db.session.commit()
        return facts

    def update_change_type(
        self,
        deal_id: str,
        change_type: str,
        fact_ids: List[str] = None
    ):
        """Bulk update change_type for facts."""
        query = Fact.query.filter(Fact.deal_id == deal_id)

        if fact_ids:
            query = query.filter(Fact.id.in_(fact_ids))

        query.update({'change_type': change_type}, synchronize_session=False)
        db.session.commit()
