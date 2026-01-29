"""
Analysis Run Repository

Database operations for AnalysisRun model - tracks analysis executions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from web.database import db, AnalysisRun, DealSnapshot
from .base import BaseRepository


class AnalysisRunRepository(BaseRepository[AnalysisRun]):
    """Repository for AnalysisRun CRUD and queries."""

    model = AnalysisRun

    # =========================================================================
    # ANALYSIS RUN QUERIES
    # =========================================================================

    def get_by_deal(
        self,
        deal_id: str,
        status: str = None,
        run_type: str = None,
        limit: int = None
    ) -> List[AnalysisRun]:
        """Get analysis runs for a deal."""
        query = self.query().filter(AnalysisRun.deal_id == deal_id)

        if status:
            query = query.filter(AnalysisRun.status == status)

        if run_type:
            query = query.filter(AnalysisRun.run_type == run_type)

        query = query.order_by(AnalysisRun.run_number.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_latest(self, deal_id: str) -> Optional[AnalysisRun]:
        """Get the most recent analysis run for a deal."""
        return self.query().filter(
            AnalysisRun.deal_id == deal_id
        ).order_by(
            AnalysisRun.run_number.desc()
        ).first()

    def get_latest_completed(self, deal_id: str) -> Optional[AnalysisRun]:
        """Get the most recent completed analysis run."""
        return self.query().filter(
            AnalysisRun.deal_id == deal_id,
            AnalysisRun.status == 'completed'
        ).order_by(
            AnalysisRun.run_number.desc()
        ).first()

    def get_running(self, deal_id: str = None) -> List[AnalysisRun]:
        """Get currently running analysis runs."""
        query = self.query().filter(AnalysisRun.status == 'running')

        if deal_id:
            query = query.filter(AnalysisRun.deal_id == deal_id)

        return query.all()

    def get_next_run_number(self, deal_id: str) -> int:
        """Get the next run number for a deal."""
        latest = self.get_latest(deal_id)
        return (latest.run_number + 1) if latest else 1

    # =========================================================================
    # ANALYSIS RUN LIFECYCLE
    # =========================================================================

    def create_run(
        self,
        deal_id: str,
        run_type: str = 'full',
        domains: List[str] = None,
        entity: str = 'target',
        documents: List[str] = None,
        initiated_by: str = None
    ) -> AnalysisRun:
        """Create a new analysis run."""
        run_number = self.get_next_run_number(deal_id)

        return self.create(
            deal_id=deal_id,
            run_number=run_number,
            run_type=run_type,
            domains=domains or [],
            entity=entity,
            documents_analyzed=documents or [],
            status='pending',
            initiated_by=initiated_by
        )

    def start_run(self, run: AnalysisRun) -> AnalysisRun:
        """Mark an analysis run as started."""
        return self.update(
            run,
            status='running',
            started_at=datetime.utcnow(),
            progress=0.0
        )

    def update_progress(
        self,
        run: AnalysisRun,
        progress: float,
        current_step: str = ''
    ) -> AnalysisRun:
        """Update analysis run progress."""
        return self.update(
            run,
            progress=min(progress, 100.0),
            current_step=current_step
        )

    def complete_run(
        self,
        run: AnalysisRun,
        facts_created: int = 0,
        facts_updated: int = 0,
        facts_unchanged: int = 0,
        findings_created: int = 0,
        findings_updated: int = 0,
        errors_count: int = 0
    ) -> AnalysisRun:
        """Mark an analysis run as completed."""
        now = datetime.utcnow()
        duration = None

        if run.started_at:
            duration = (now - run.started_at).total_seconds()

        return self.update(
            run,
            status='completed',
            progress=100.0,
            completed_at=now,
            duration_seconds=duration,
            facts_created=facts_created,
            facts_updated=facts_updated,
            facts_unchanged=facts_unchanged,
            findings_created=findings_created,
            findings_updated=findings_updated,
            errors_count=errors_count
        )

    def fail_run(
        self,
        run: AnalysisRun,
        error_message: str,
        error_details: Dict = None
    ) -> AnalysisRun:
        """Mark an analysis run as failed."""
        now = datetime.utcnow()
        duration = None

        if run.started_at:
            duration = (now - run.started_at).total_seconds()

        return self.update(
            run,
            status='failed',
            completed_at=now,
            duration_seconds=duration,
            error_message=error_message,
            error_details=error_details or {}
        )

    def cancel_run(self, run: AnalysisRun) -> AnalysisRun:
        """Cancel a running analysis."""
        now = datetime.utcnow()
        duration = None

        if run.started_at:
            duration = (now - run.started_at).total_seconds()

        return self.update(
            run,
            status='cancelled',
            completed_at=now,
            duration_seconds=duration
        )

    # =========================================================================
    # SNAPSHOT MANAGEMENT
    # =========================================================================

    def create_pre_run_snapshot(
        self,
        run: AnalysisRun,
        facts_data: List[Dict],
        findings_data: List[Dict],
        documents_data: List[Dict],
        deal_context: Dict,
        created_by: str = None
    ) -> DealSnapshot:
        """Create a snapshot before running analysis."""
        # Get next snapshot number
        latest_snapshot = DealSnapshot.query.filter(
            DealSnapshot.deal_id == run.deal_id
        ).order_by(
            DealSnapshot.snapshot_number.desc()
        ).first()

        snapshot_number = (latest_snapshot.snapshot_number + 1) if latest_snapshot else 1

        # Calculate approximate size
        import json
        data_size = len(json.dumps({
            'facts': facts_data,
            'findings': findings_data,
            'documents': documents_data,
            'context': deal_context
        }))

        snapshot = DealSnapshot(
            deal_id=run.deal_id,
            snapshot_number=snapshot_number,
            snapshot_type='pre_analysis',
            description=f'Before analysis run #{run.run_number}',
            facts_data=facts_data,
            findings_data=findings_data,
            documents_data=documents_data,
            deal_context=deal_context,
            facts_count=len(facts_data),
            findings_count=len(findings_data),
            documents_count=len(documents_data),
            data_size_bytes=data_size,
            created_by=created_by
        )

        db.session.add(snapshot)
        db.session.commit()

        # Link snapshot to run
        self.update(run, pre_run_snapshot_id=snapshot.id)

        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[DealSnapshot]:
        """Get a snapshot by ID."""
        return DealSnapshot.query.get(snapshot_id)

    def get_snapshots(self, deal_id: str, limit: int = 10) -> List[DealSnapshot]:
        """Get recent snapshots for a deal."""
        return DealSnapshot.query.filter(
            DealSnapshot.deal_id == deal_id
        ).order_by(
            DealSnapshot.snapshot_number.desc()
        ).limit(limit).all()

    # =========================================================================
    # SUMMARY & STATISTICS
    # =========================================================================

    def get_run_summary(self, deal_id: str) -> Dict[str, Any]:
        """Get summary of analysis runs for a deal."""
        runs = self.get_by_deal(deal_id)

        completed = [r for r in runs if r.status == 'completed']
        failed = [r for r in runs if r.status == 'failed']

        total_duration = sum(r.duration_seconds or 0 for r in completed)
        avg_duration = (total_duration / len(completed)) if completed else 0

        return {
            'total_runs': len(runs),
            'completed': len(completed),
            'failed': len(failed),
            'running': len([r for r in runs if r.status == 'running']),
            'avg_duration_seconds': avg_duration,
            'total_facts_created': sum(r.facts_created or 0 for r in completed),
            'total_findings_created': sum(r.findings_created or 0 for r in completed),
            'last_run': runs[0].to_dict() if runs else None
        }

    def is_deal_locked(self, deal_id: str) -> bool:
        """Check if a deal has a running analysis."""
        running = self.get_running(deal_id)
        return len(running) > 0

    def cleanup_stale_runs(self, max_age_hours: int = 24) -> int:
        """Mark stale running analyses as failed."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        stale_runs = self.query().filter(
            AnalysisRun.status == 'running',
            AnalysisRun.started_at < cutoff
        ).all()

        for run in stale_runs:
            self.fail_run(
                run,
                error_message='Analysis timed out',
                error_details={'reason': 'stale_run_cleanup'}
            )

        return len(stale_runs)
