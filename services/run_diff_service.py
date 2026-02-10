"""
Run Diff Service - Generates metric-driven diffs between analysis runs.

Phase 1a: Analysis Reasoning Layer

This service computes what changed between analysis runs:
- Documents added/removed
- Facts created/updated/deleted
- Risks created/updated/deleted with severity changes
- Scope changes (entity, domains)

The output is metrics, not narrative - designed for debugging and audit.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Set

from web.database import db, RunDiff, AnalysisRun, Document, Fact, Finding, Deal

logger = logging.getLogger(__name__)


class RunDiffService:
    """
    Generates and retrieves run diffs.

    Usage:
        service = RunDiffService()
        diff = service.generate_diff(deal_id, current_run_id)
        # or
        diff = service.get_diff_for_run(current_run_id)
    """

    def generate_diff(
        self,
        deal_id: str,
        current_run_id: str,
        previous_run_id: Optional[str] = None
    ) -> Optional[RunDiff]:
        """
        Generate a diff between current run and previous run.

        If previous_run_id is not provided, finds the most recent prior run.
        For the first run, creates a baseline diff (everything is "new").

        Args:
            deal_id: The deal ID
            current_run_id: The current analysis run ID
            previous_run_id: Optional specific previous run to compare against

        Returns:
            RunDiff object (already committed to DB)
        """
        try:
            # Get current run
            current_run = AnalysisRun.query.get(current_run_id)
            if not current_run:
                logger.error(f"Current run {current_run_id} not found")
                return None

            # Find previous run if not specified
            previous_run = None
            if previous_run_id:
                previous_run = AnalysisRun.query.get(previous_run_id)
            else:
                # Get most recent completed run before this one
                previous_run = (
                    AnalysisRun.query
                    .filter(AnalysisRun.deal_id == deal_id)
                    .filter(AnalysisRun.id != current_run_id)
                    .filter(AnalysisRun.status == 'completed')
                    .filter(AnalysisRun.run_number < current_run.run_number)
                    .order_by(AnalysisRun.run_number.desc())
                    .first()
                )

            # Compute the diff
            diff_data = self._compute_diff(deal_id, current_run, previous_run)

            # Create and save RunDiff
            run_diff = RunDiff(
                deal_id=deal_id,
                previous_run_id=previous_run.id if previous_run else None,
                current_run_id=current_run_id,
                previous_run_number=previous_run.run_number if previous_run else None,
                current_run_number=current_run.run_number,
                **diff_data
            )

            db.session.add(run_diff)
            db.session.commit()

            logger.info(
                f"Generated diff for run #{current_run.run_number}: "
                f"+{diff_data['facts_created']} facts, "
                f"+{diff_data['risks_created']} risks"
            )

            return run_diff

        except Exception as e:
            logger.error(f"Failed to generate run diff: {e}")
            db.session.rollback()
            return None

    def _compute_diff(
        self,
        deal_id: str,
        current_run: AnalysisRun,
        previous_run: Optional[AnalysisRun]
    ) -> Dict[str, Any]:
        """
        Compute the actual diff metrics.

        Returns dict of all diff fields (without id/deal_id/run_ids).
        """
        diff = {}

        # === Document Changes ===
        diff.update(self._compute_document_diff(deal_id, current_run, previous_run))

        # === Fact Changes ===
        diff.update(self._compute_fact_diff(deal_id, current_run, previous_run))

        # === Risk Changes ===
        diff.update(self._compute_risk_diff(deal_id, current_run, previous_run))

        # === Scope Changes ===
        diff.update(self._compute_scope_diff(current_run, previous_run))

        return diff

    def _compute_document_diff(
        self,
        deal_id: str,
        current_run: AnalysisRun,
        previous_run: Optional[AnalysisRun]
    ) -> Dict[str, Any]:
        """Compute document-level changes."""
        # Get current documents
        current_docs = Document.query.filter(
            Document.deal_id == deal_id,
            Document.deleted_at.is_(None),
            Document.is_current == True
        ).all()

        current_doc_ids = {d.id for d in current_docs}
        current_doc_map = {d.id: d for d in current_docs}

        # Get previous run's documents
        previous_doc_ids: Set[str] = set()
        previous_doc_map: Dict[str, Document] = {}

        if previous_run and previous_run.documents_analyzed:
            previous_doc_ids = set(previous_run.documents_analyzed)
            prev_docs = Document.query.filter(Document.id.in_(previous_doc_ids)).all()
            previous_doc_map = {d.id: d for d in prev_docs}

        # Compute changes
        added_ids = current_doc_ids - previous_doc_ids
        removed_ids = previous_doc_ids - current_doc_ids

        docs_added = [
            {'id': d_id, 'filename': current_doc_map.get(d_id, {}).filename if d_id in current_doc_map else 'unknown'}
            for d_id in added_ids
        ]
        docs_removed = [
            {'id': d_id, 'filename': previous_doc_map.get(d_id, {}).filename if d_id in previous_doc_map else 'unknown'}
            for d_id in removed_ids
        ]

        # Count chunks (word count as proxy)
        chunks_before = sum(d.word_count or 0 for d in previous_doc_map.values())
        chunks_after = sum(d.word_count or 0 for d in current_docs)

        return {
            'docs_added': docs_added,
            'docs_removed': docs_removed,
            'docs_updated': [],  # TODO: detect re-processed docs
            'docs_total_before': len(previous_doc_ids),
            'docs_total_after': len(current_doc_ids),
            'chunks_before': chunks_before,
            'chunks_after': chunks_after,
        }

    def _compute_fact_diff(
        self,
        deal_id: str,
        current_run: AnalysisRun,
        previous_run: Optional[AnalysisRun]
    ) -> Dict[str, Any]:
        """Compute fact-level changes."""
        # Get all current facts
        current_facts = Fact.query.filter(
            Fact.deal_id == deal_id,
            Fact.deleted_at.is_(None)
        ).all()

        current_fact_ids = {f.id for f in current_facts}
        current_fact_map = {f.id: f for f in current_facts}

        # Get previous facts (from previous run or snapshot)
        previous_fact_ids: Set[str] = set()
        previous_fact_map: Dict[str, Fact] = {}

        if previous_run:
            # Get facts that existed at end of previous run
            # Use facts created before or during previous run
            prev_facts = Fact.query.filter(
                Fact.deal_id == deal_id,
                Fact.created_at <= previous_run.completed_at if previous_run.completed_at else True
            ).all()
            previous_fact_ids = {f.id for f in prev_facts if f.deleted_at is None or
                                 (previous_run.completed_at and f.deleted_at > previous_run.completed_at)}
            previous_fact_map = {f.id: f for f in prev_facts}

        # Compute changes
        # Facts in current run
        run_facts = Fact.query.filter(
            Fact.deal_id == deal_id,
            Fact.analysis_run_id == current_run.id
        ).all()

        facts_created_ids = [f.id for f in run_facts if f.change_type == 'new' or f.id not in previous_fact_ids]
        facts_updated_ids = [f.id for f in run_facts if f.change_type == 'updated']

        # Deleted = was in previous, not in current (and marked deleted)
        deleted_facts = Fact.query.filter(
            Fact.deal_id == deal_id,
            Fact.deleted_at.isnot(None)
        ).all()
        facts_deleted_ids = [
            f.id for f in deleted_facts
            if previous_run and previous_run.completed_at and
               f.deleted_at > previous_run.completed_at
        ]

        facts_created = len(facts_created_ids)
        facts_updated = len(facts_updated_ids)
        facts_deleted = len(facts_deleted_ids)
        facts_unchanged = len(current_fact_ids) - facts_created - facts_updated

        return {
            'facts_created': facts_created,
            'facts_updated': facts_updated,
            'facts_deleted': facts_deleted,
            'facts_unchanged': max(0, facts_unchanged),
            'facts_total_before': len(previous_fact_ids),
            'facts_total_after': len(current_fact_ids),
            'facts_created_ids': facts_created_ids[:100],  # Limit for storage
            'facts_updated_ids': facts_updated_ids[:100],
            'facts_deleted_ids': facts_deleted_ids[:100],
            'net_facts_change': len(current_fact_ids) - len(previous_fact_ids),
        }

    def _compute_risk_diff(
        self,
        deal_id: str,
        current_run: AnalysisRun,
        previous_run: Optional[AnalysisRun]
    ) -> Dict[str, Any]:
        """Compute risk/finding-level changes."""
        # Get current risks
        current_risks = Finding.query.filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'risk',
            Finding.deleted_at.is_(None)
        ).all()

        current_risk_ids = {r.id for r in current_risks}
        current_risk_map = {r.id: r for r in current_risks}

        # Get previous risks
        previous_risk_ids: Set[str] = set()
        previous_risk_map: Dict[str, Finding] = {}

        if previous_run and previous_run.completed_at:
            prev_risks = Finding.query.filter(
                Finding.deal_id == deal_id,
                Finding.finding_type == 'risk',
                Finding.created_at <= previous_run.completed_at
            ).all()
            previous_risk_ids = {r.id for r in prev_risks if r.deleted_at is None or
                                 r.deleted_at > previous_run.completed_at}
            previous_risk_map = {r.id: r for r in prev_risks}

        # Compute changes
        run_risks = Finding.query.filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'risk',
            Finding.analysis_run_id == current_run.id
        ).all()

        risks_created = len([r for r in run_risks if r.id not in previous_risk_ids])
        risks_updated = len([r for r in run_risks if r.change_type == 'updated'])

        # Deleted risks
        deleted_risks = Finding.query.filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'risk',
            Finding.deleted_at.isnot(None)
        ).all()
        risks_deleted = len([
            r for r in deleted_risks
            if previous_run and previous_run.completed_at and
               r.deleted_at > previous_run.completed_at
        ])

        # Severity changes
        severity_changes = []
        for risk_id in current_risk_ids & previous_risk_ids:
            current = current_risk_map.get(risk_id)
            previous = previous_risk_map.get(risk_id)
            if current and previous and current.severity != previous.severity:
                severity_changes.append({
                    'risk_id': risk_id,
                    'old_severity': previous.severity,
                    'new_severity': current.severity,
                    'title': current.title[:100] if current.title else ''
                })

        return {
            'risks_created': risks_created,
            'risks_updated': risks_updated,
            'risks_deleted': risks_deleted,
            'risks_total_before': len(previous_risk_ids),
            'risks_total_after': len(current_risk_ids),
            'net_risks_change': len(current_risk_ids) - len(previous_risk_ids),
            'severity_changes': severity_changes[:50],  # Limit for storage
        }

    def _compute_scope_diff(
        self,
        current_run: AnalysisRun,
        previous_run: Optional[AnalysisRun]
    ) -> Dict[str, Any]:
        """Compute scope changes (entity, domains)."""
        return {
            'entity_scope_before': previous_run.entity if previous_run else '',
            'entity_scope_after': current_run.entity or 'target',
            'domains_before': previous_run.domains if previous_run else [],
            'domains_after': current_run.domains or [],
        }

    def get_diff_for_run(self, run_id: str) -> Optional[RunDiff]:
        """Get the diff for a specific run (if exists)."""
        return RunDiff.query.filter_by(current_run_id=run_id).first()

    def get_diffs_for_deal(self, deal_id: str, limit: int = 10) -> List[RunDiff]:
        """Get recent diffs for a deal."""
        return (
            RunDiff.query
            .filter_by(deal_id=deal_id)
            .order_by(RunDiff.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_latest_diff(self, deal_id: str) -> Optional[RunDiff]:
        """Get the most recent diff for a deal."""
        return (
            RunDiff.query
            .filter_by(deal_id=deal_id)
            .order_by(RunDiff.created_at.desc())
            .first()
        )


# Singleton instance
run_diff_service = RunDiffService()


def generate_run_diff(deal_id: str, current_run_id: str) -> Optional[RunDiff]:
    """
    Convenience function to generate a run diff.

    Call this after an analysis run completes.
    """
    return run_diff_service.generate_diff(deal_id, current_run_id)
