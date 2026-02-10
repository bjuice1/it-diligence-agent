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
        run_id: str = None,
        domain: str = None,
        entity: str = None,
        category: str = None,
        status: str = None,
        verified_only: bool = False,
        needs_review: bool = None,
        include_orphaned: bool = True
    ) -> List[Fact]:
        """
        Get facts for a deal with optional filters.

        Args:
            deal_id: The deal ID
            run_id: Filter by analysis run. If provided:
                - If include_orphaned=True (default): Returns facts from this run
                  PLUS facts with NULL analysis_run_id (legacy/orphaned data)
                - If include_orphaned=False: Returns only facts from this exact run
            include_orphaned: Whether to include facts with NULL analysis_run_id
                when filtering by run_id. Defaults to True to ensure legacy data
                is visible.
        """
        query = self.query().filter(Fact.deal_id == deal_id)

        # Scope by analysis run (Phase 2: latest completed run)
        # Also include orphaned facts (NULL run_id) to ensure legacy data is visible
        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Fact.analysis_run_id == run_id,
                        Fact.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Fact.analysis_run_id == run_id)

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

    def get_by_domain(self, deal_id: str, domain: str, run_id: str = None) -> List[Fact]:
        """Get all facts for a domain."""
        return self.get_by_deal(deal_id, run_id=run_id, domain=domain)

    def get_by_entity(self, deal_id: str, entity: str, run_id: str = None) -> List[Fact]:
        """Get all facts for an entity (target or buyer)."""
        return self.get_by_deal(deal_id, run_id=run_id, entity=entity)

    # Domain-specific convenience methods (for Phase 2 DealData facade)
    def get_applications(self, deal_id: str, run_id: str = None, entity: str = None) -> List[Fact]:
        """Get all application facts, optionally filtered by entity."""
        return self.get_by_deal(deal_id, run_id=run_id, domain='applications', entity=entity)

    def get_organization(self, deal_id: str, run_id: str = None, entity: str = None) -> List[Fact]:
        """Get all organization facts, optionally filtered by entity."""
        return self.get_by_deal(deal_id, run_id=run_id, domain='organization', entity=entity)

    def get_infrastructure(self, deal_id: str, run_id: str = None, entity: str = None) -> List[Fact]:
        """Get all infrastructure facts, optionally filtered by entity."""
        return self.get_by_deal(deal_id, run_id=run_id, domain='infrastructure', entity=entity)

    def get_cybersecurity(self, deal_id: str, run_id: str = None, entity: str = None) -> List[Fact]:
        """Get all cybersecurity facts, optionally filtered by entity."""
        return self.get_by_deal(deal_id, run_id=run_id, domain='cybersecurity', entity=entity)

    def get_network(self, deal_id: str, run_id: str = None, entity: str = None) -> List[Fact]:
        """Get all network facts, optionally filtered by entity."""
        return self.get_by_deal(deal_id, run_id=run_id, domain='network', entity=entity)

    def get_identity_access(self, deal_id: str, run_id: str = None, entity: str = None) -> List[Fact]:
        """Get all identity/access facts, optionally filtered by entity."""
        return self.get_by_deal(deal_id, run_id=run_id, domain='identity_access', entity=entity)

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

        # Always search fact_id first (works for both PostgreSQL and SQLite)
        search_filter = or_(
            Fact.fact_id.ilike(f'%{search_term}%'),
            Fact.item.ilike(f'%{search_term}%'),
            Fact.source_quote.ilike(f'%{search_term}%')
        )
        query = query.filter(search_filter)

        return query.limit(limit).all()

    # =========================================================================
    # SUMMARY & STATISTICS
    # =========================================================================

    def get_summary_by_domain(self, deal_id: str, run_id: str = None) -> Dict[str, Dict[str, int]]:
        """Get fact counts by domain and status."""
        facts = self.get_by_deal(deal_id, run_id=run_id)

        summary = {}
        for fact in facts:
            if fact.domain not in summary:
                summary[fact.domain] = {'total': 0, 'documented': 0, 'partial': 0, 'gap': 0}

            summary[fact.domain]['total'] += 1
            if fact.status in summary[fact.domain]:
                summary[fact.domain][fact.status] += 1

        return summary

    def count_by_domain(self, deal_id: str, run_id: str = None, entity: str = None, include_orphaned: bool = True) -> Dict[str, int]:
        """Get fact counts per domain for dashboard (SQL-level aggregation)."""
        query = self.query().filter(Fact.deal_id == deal_id)
        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Fact.analysis_run_id == run_id,
                        Fact.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Fact.analysis_run_id == run_id)
        if entity:
            query = query.filter(Fact.entity == entity)

        results = query.with_entities(
            Fact.domain, func.count(Fact.id)
        ).group_by(Fact.domain).all()

        return {domain: count for domain, count in results}

    def get_paginated(
        self,
        deal_id: str,
        run_id: str = None,
        domain: str = None,
        entity: str = None,
        status: str = None,
        search: str = None,
        page: int = 1,
        per_page: int = 50,
        include_orphaned: bool = True
    ):
        """
        Get paginated facts with all filtering done in SQL.

        Args:
            entity: Filter by entity ('target' or 'buyer')
            include_orphaned: If True (default), includes facts with NULL
                analysis_run_id when filtering by run_id.

        Returns:
            Tuple of (items, total_count)
        """
        query = self.query().filter(Fact.deal_id == deal_id)

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Fact.analysis_run_id == run_id,
                        Fact.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Fact.analysis_run_id == run_id)
        if domain:
            query = query.filter(Fact.domain == domain)
        if entity:
            query = query.filter(Fact.entity == entity)
        if status:
            query = query.filter(Fact.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Fact.fact_id.ilike(search_term),  # Search by fact ID (e.g., F-TGT-APP-008)
                    Fact.item.ilike(search_term),
                    Fact.source_quote.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(Fact.created_at.desc()) \
                     .offset((page - 1) * per_page) \
                     .limit(per_page) \
                     .all()

        return items, total

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

    def get_linked_findings(self, fact_id: str, exclude_deleted: bool = True) -> List[str]:
        """
        Get IDs of findings linked to this fact.

        Args:
            fact_id: The fact ID to get linked findings for
            exclude_deleted: If True (default), excludes links to soft-deleted findings

        Returns:
            List of finding IDs
        """
        from web.database import Finding

        if exclude_deleted:
            # Join with Finding to filter out soft-deleted findings
            links = db.session.query(FactFindingLink).join(
                Finding, FactFindingLink.finding_id == Finding.id
            ).filter(
                FactFindingLink.fact_id == fact_id,
                Finding.deleted_at.is_(None)
            ).all()
        else:
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
