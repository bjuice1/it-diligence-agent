"""
Finding Repository

Database operations for Finding model (risks, work items, recommendations).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_, func

from web.database import db, Finding, FactFindingLink
from .base import BaseRepository


class FindingRepository(BaseRepository[Finding]):
    """Repository for Finding CRUD and queries."""

    model = Finding

    # =========================================================================
    # FINDING-SPECIFIC QUERIES
    # =========================================================================

    def get_by_deal(
        self,
        deal_id: str,
        run_id: str = None,
        finding_type: str = None,
        domain: str = None,
        severity: str = None,
        include_orphaned: bool = True
    ) -> List[Finding]:
        """
        Get findings for a deal with optional filters.

        Args:
            include_orphaned: If True (default), includes findings with NULL
                analysis_run_id when filtering by run_id (for legacy data).
        """
        query = self.query().filter(Finding.deal_id == deal_id)

        # Scope by analysis run (Phase 2: latest completed run)
        # Also include orphaned findings (NULL run_id) to ensure legacy data is visible
        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)

        if finding_type:
            query = query.filter(Finding.finding_type == finding_type)

        if domain:
            query = query.filter(Finding.domain == domain)

        if severity:
            query = query.filter(Finding.severity == severity)

        return query.order_by(Finding.id).all()

    def get_risks(self, deal_id: str, run_id: str = None, severity: str = None, include_orphaned: bool = True) -> List[Finding]:
        """Get all risks for a deal."""
        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'risk'
        )

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)

        if severity:
            query = query.filter(Finding.severity == severity)

        # Order by severity: critical > high > medium > low
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return sorted(query.all(), key=lambda r: severity_order.get(r.severity, 4))

    def get_work_items(self, deal_id: str, run_id: str = None, phase: str = None, include_orphaned: bool = True) -> List[Finding]:
        """Get all work items for a deal."""
        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'work_item'
        )

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)

        if phase:
            query = query.filter(Finding.phase == phase)

        return query.order_by(Finding.phase, Finding.priority).all()

    def get_recommendations(self, deal_id: str, run_id: str = None, urgency: str = None, include_orphaned: bool = True) -> List[Finding]:
        """Get all recommendations for a deal."""
        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'recommendation'
        )

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)

        if urgency:
            query = query.filter(Finding.urgency == urgency)

        return query.all()

    def get_strategic_considerations(self, deal_id: str, run_id: str = None, include_orphaned: bool = True) -> List[Finding]:
        """Get all strategic considerations for a deal."""
        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'strategic_consideration'
        )

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)

        return query.all()

    def get_top_risks(self, deal_id: str, run_id: str = None, limit: int = 5, include_orphaned: bool = True) -> List[Finding]:
        """Get highest severity risks for dashboard."""
        from sqlalchemy import case

        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'risk'
        )

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)

        # Order by severity (critical > high > medium > low)
        severity_order = case(
            (Finding.severity == 'critical', 1),
            (Finding.severity == 'high', 2),
            (Finding.severity == 'medium', 3),
            (Finding.severity == 'low', 4),
            else_=5
        )
        return query.order_by(severity_order).limit(limit).all()

    def get_paginated(
        self,
        deal_id: str,
        run_id: str = None,
        finding_type: str = None,
        domain: str = None,
        severity: str = None,
        phase: str = None,
        search: str = None,
        page: int = 1,
        per_page: int = 50,
        include_orphaned: bool = True,
        order_by_severity: bool = False
    ):
        """
        Get paginated findings with filtering in SQL.

        Args:
            include_orphaned: If True (default), includes findings with NULL
                analysis_run_id when filtering by run_id.
            order_by_severity: If True, order risks by severity (critical > high > medium > low)
            phase: Filter work items by phase (Day_1, Day_100, Post_100)

        Returns:
            Tuple of (items, total_count)
        """
        query = self.query().filter(Finding.deal_id == deal_id)

        if run_id:
            if include_orphaned:
                query = query.filter(
                    or_(
                        Finding.analysis_run_id == run_id,
                        Finding.analysis_run_id.is_(None)
                    )
                )
            else:
                query = query.filter(Finding.analysis_run_id == run_id)
        if finding_type:
            query = query.filter(Finding.finding_type == finding_type)
        if domain:
            query = query.filter(Finding.domain == domain)
        if severity:
            query = query.filter(Finding.severity == severity)
        if phase:
            query = query.filter(Finding.phase == phase)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Finding.title.ilike(search_term),
                    Finding.description.ilike(search_term)
                )
            )

        total = query.count()

        # Order by severity for risks if requested
        if order_by_severity:
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            items = query.all()
            items = sorted(items, key=lambda r: severity_order.get(r.severity, 4))
            # Apply pagination in Python after sorting
            start = (page - 1) * per_page
            items = items[start:start + per_page]
        else:
            items = query.order_by(Finding.created_at.desc()) \
                         .offset((page - 1) * per_page) \
                         .limit(per_page) \
                         .all()

        return items, total

    def get_by_analysis_run(self, analysis_run_id: str) -> List[Finding]:
        """Get all findings from an analysis run."""
        return self.query().filter(Finding.analysis_run_id == analysis_run_id).all()

    # =========================================================================
    # SUMMARY & STATISTICS
    # =========================================================================

    def get_risk_summary(self, deal_id: str, run_id: str = None) -> Dict[str, int]:
        """Get risk counts by severity."""
        risks = self.get_risks(deal_id, run_id=run_id)

        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'total': 0}
        for risk in risks:
            summary['total'] += 1
            if risk.severity in summary:
                summary[risk.severity] += 1

        return summary

    def get_work_item_summary(self, deal_id: str, run_id: str = None) -> Dict[str, int]:
        """Get work item counts by phase."""
        work_items = self.get_work_items(deal_id, run_id=run_id)

        summary = {'Day_1': 0, 'Day_100': 0, 'Post_100': 0, 'total': 0}
        for wi in work_items:
            summary['total'] += 1
            if wi.phase in summary:
                summary[wi.phase] += 1

        return summary

    def get_summary_by_domain(self, deal_id: str, run_id: str = None) -> Dict[str, Dict[str, int]]:
        """Get finding counts by domain and type."""
        findings = self.get_by_deal(deal_id, run_id=run_id)

        summary = {}
        for finding in findings:
            if finding.domain not in summary:
                summary[finding.domain] = {
                    'risk': 0,
                    'work_item': 0,
                    'recommendation': 0,
                    'strategic_consideration': 0
                }

            if finding.finding_type in summary[finding.domain]:
                summary[finding.domain][finding.finding_type] += 1

        return summary

    def get_cost_estimate_total(self, deal_id: str) -> Dict[str, int]:
        """Get aggregated cost estimates from work items."""
        work_items = self.get_work_items(deal_id)

        # Map cost ranges to midpoint estimates
        cost_ranges = {
            'under_25k': 12500,
            '25k_to_100k': 62500,
            '100k_to_500k': 300000,
            '500k_to_1m': 750000,
            'over_1m': 1500000,
        }

        low_total = 0
        high_total = 0

        for wi in work_items:
            if wi.cost_estimate in cost_ranges:
                mid = cost_ranges[wi.cost_estimate]
                # Estimate low as 50% of mid, high as 150% of mid
                low_total += int(mid * 0.5)
                high_total += int(mid * 1.5)

        return {
            'low_estimate': low_total,
            'high_estimate': high_total,
            'midpoint': (low_total + high_total) // 2
        }

    # =========================================================================
    # FACT RELATIONSHIPS
    # =========================================================================

    def get_linked_facts(self, finding_id: str, exclude_deleted: bool = True) -> List[str]:
        """
        Get IDs of facts linked to this finding.

        Args:
            finding_id: The finding ID to get linked facts for
            exclude_deleted: If True (default), excludes links to soft-deleted facts

        Returns:
            List of fact IDs
        """
        from web.database import Fact

        if exclude_deleted:
            # Join with Fact to filter out soft-deleted facts
            links = db.session.query(FactFindingLink).join(
                Fact, FactFindingLink.fact_id == Fact.id
            ).filter(
                FactFindingLink.finding_id == finding_id,
                Fact.deleted_at.is_(None)
            ).all()
        else:
            links = FactFindingLink.query.filter(
                FactFindingLink.finding_id == finding_id
            ).all()

        return [link.fact_id for link in links]

    def link_facts(
        self,
        finding_id: str,
        fact_ids: List[str],
        relationship_type: str = 'supports'
    ):
        """Link multiple facts to a finding."""
        for fact_id in fact_ids:
            # Check if link already exists
            existing = FactFindingLink.query.filter(
                FactFindingLink.fact_id == fact_id,
                FactFindingLink.finding_id == finding_id
            ).first()

            if not existing:
                link = FactFindingLink(
                    fact_id=fact_id,
                    finding_id=finding_id,
                    relationship_type=relationship_type
                )
                db.session.add(link)

        db.session.commit()

    def update_fact_links_from_json(self, finding: Finding):
        """
        Sync FactFindingLink table with based_on_facts JSON array.

        Call this after creating/updating a finding that has based_on_facts.
        """
        if not finding.based_on_facts:
            return

        # Get existing links
        existing_links = set(self.get_linked_facts(finding.id))

        # Add new links
        for fact_id in finding.based_on_facts:
            if fact_id not in existing_links:
                link = FactFindingLink(
                    fact_id=fact_id,
                    finding_id=finding.id,
                    relationship_type='supports'
                )
                db.session.add(link)

        db.session.commit()

    # =========================================================================
    # CHANGE TRACKING
    # =========================================================================

    def get_new_findings(self, deal_id: str, since_run_id: str = None) -> List[Finding]:
        """Get findings marked as new."""
        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.change_type == 'new'
        )

        if since_run_id:
            query = query.filter(Finding.analysis_run_id == since_run_id)

        return query.all()

    def get_updated_findings(self, deal_id: str, since_run_id: str = None) -> List[Finding]:
        """Get findings marked as updated."""
        query = self.query().filter(
            Finding.deal_id == deal_id,
            Finding.change_type == 'updated'
        )

        if since_run_id:
            query = query.filter(Finding.analysis_run_id == since_run_id)

        return query.all()

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def create_many(self, findings_data: List[Dict[str, Any]]) -> List[Finding]:
        """Create multiple findings at once."""
        findings = []
        for data in findings_data:
            finding = Finding(**data)
            db.session.add(finding)
            findings.append(finding)

        db.session.commit()

        # Sync fact links
        for finding in findings:
            self.update_fact_links_from_json(finding)

        return findings
