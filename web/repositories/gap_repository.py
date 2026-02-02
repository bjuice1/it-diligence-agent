"""
Gap Repository

Database operations for Gap model.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_

from web.database import db, Gap
from .base import BaseRepository


class GapRepository(BaseRepository[Gap]):
    """Repository for Gap CRUD and queries."""

    model = Gap

    # =========================================================================
    # GAP-SPECIFIC QUERIES
    # =========================================================================

    def get_by_deal(
        self,
        deal_id: str,
        run_id: str = None,
        domain: str = None,
        entity: str = None,
        importance: str = None,
        status: str = None,
        include_orphaned: bool = True
    ) -> List[Gap]:
        """
        Get gaps for a deal with optional filters.

        Args:
            include_orphaned: If True (default), includes gaps with NULL
                analysis_run_id when filtering by run_id (for legacy data).
        """
        query = self.query().filter(Gap.deal_id == deal_id)

        # Scope by analysis run (Phase 2: latest completed run)
        # Also include orphaned gaps (NULL run_id) to ensure legacy data is visible
        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Gap.analysis_run_id == run_id,
                        Gap.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Gap.analysis_run_id == run_id)

        if domain:
            query = query.filter(Gap.domain == domain)

        if entity:
            query = query.filter(Gap.entity == entity)

        if importance:
            query = query.filter(Gap.importance == importance)

        if status:
            query = query.filter(Gap.status == status)

        return query.order_by(Gap.id).all()

    def get_by_domain(self, deal_id: str, domain: str, run_id: str = None) -> List[Gap]:
        """Get all gaps for a domain."""
        return self.get_by_deal(deal_id, run_id=run_id, domain=domain)

    def get_by_entity(self, deal_id: str, entity: str, run_id: str = None) -> List[Gap]:
        """Get all gaps for an entity (target or buyer)."""
        return self.get_by_deal(deal_id, run_id=run_id, entity=entity)

    def get_by_analysis_run(self, analysis_run_id: str) -> List[Gap]:
        """Get all gaps from an analysis run."""
        return self.query().filter(Gap.analysis_run_id == analysis_run_id).all()

    def get_open_gaps(self, deal_id: str, run_id: str = None) -> List[Gap]:
        """Get all open (unresolved) gaps for a deal."""
        return self.get_by_deal(deal_id, run_id=run_id, status='open')

    def get_critical_gaps(self, deal_id: str, run_id: str = None) -> List[Gap]:
        """Get all critical gaps for a deal."""
        return self.get_by_deal(deal_id, run_id=run_id, importance='critical')

    # =========================================================================
    # SEARCH
    # =========================================================================

    def search(
        self,
        deal_id: str,
        search_term: str,
        domain: str = None,
        importance: str = None,
        limit: int = 50
    ) -> List[Gap]:
        """Search gaps by description."""
        query = self.query().filter(Gap.deal_id == deal_id)

        if domain:
            query = query.filter(Gap.domain == domain)

        if importance:
            query = query.filter(Gap.importance == importance)

        # Use LIKE for search
        search_filter = Gap.description.ilike(f'%{search_term}%')
        query = query.filter(search_filter)

        return query.limit(limit).all()

    # =========================================================================
    # SUMMARY & STATISTICS
    # =========================================================================

    def get_summary_by_domain(self, deal_id: str, run_id: str = None) -> Dict[str, Dict[str, int]]:
        """Get gap counts by domain and importance."""
        gaps = self.get_by_deal(deal_id, run_id=run_id)

        summary = {}
        for gap in gaps:
            if gap.domain not in summary:
                summary[gap.domain] = {
                    'total': 0,
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0,
                    'open': 0,
                    'resolved': 0
                }

            summary[gap.domain]['total'] += 1
            if gap.importance in summary[gap.domain]:
                summary[gap.domain][gap.importance] += 1
            if gap.status in summary[gap.domain]:
                summary[gap.domain][gap.status] += 1

        return summary

    def get_importance_summary(self, deal_id: str, run_id: str = None) -> Dict[str, int]:
        """Get gap counts by importance."""
        gaps = self.get_by_deal(deal_id, run_id=run_id)

        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for gap in gaps:
            if gap.importance in summary:
                summary[gap.importance] += 1

        return summary

    def count_by_importance(self, deal_id: str, run_id: str = None) -> Dict[str, int]:
        """Get gap counts by importance (alias for dashboard compatibility)."""
        return self.get_importance_summary(deal_id, run_id=run_id)

    # =========================================================================
    # RESOLUTION
    # =========================================================================

    def resolve_gap(
        self,
        gap: Gap,
        resolved_by: str,
        resolution_note: str = ''
    ) -> Gap:
        """Mark a gap as resolved."""
        return self.update(
            gap,
            status='resolved',
            resolved_by=resolved_by,
            resolved_at=datetime.utcnow(),
            resolution_note=resolution_note
        )

    def reopen_gap(self, gap: Gap) -> Gap:
        """Reopen a previously resolved gap."""
        return self.update(
            gap,
            status='open',
            resolved_by='',
            resolved_at=None,
            resolution_note=''
        )

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def create_many(self, gaps_data: List[Dict[str, Any]]) -> List[Gap]:
        """Create multiple gaps at once."""
        gaps = []
        for data in gaps_data:
            gap = Gap(**data)
            db.session.add(gap)
            gaps.append(gap)

        db.session.commit()
        return gaps

    def get_domains(self, deal_id: str) -> List[str]:
        """Get unique domains with gaps for a deal."""
        gaps = self.get_by_deal(deal_id)
        return list(set(gap.domain for gap in gaps))

    def delete_by_deal(self, deal_id: str):
        """Soft delete all gaps for a deal."""
        gaps = self.get_by_deal(deal_id)
        for gap in gaps:
            self.soft_delete(gap)
