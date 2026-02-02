"""
Incremental Database Writer for Analysis Pipeline

Phase 1 of the database-first architecture: writes each fact, gap, and finding
to the database immediately after extraction, providing crash durability.

CRASH GUARANTEE: All committed writes are durable. If the process crashes,
data is preserved up to and including the last successful commit.

Design Principles:
1. Per-write commits (no cross-thread batching)
2. UPSERT semantics for idempotent retries
3. Per-thread session lifecycle management
4. Throttled progress updates for AnalysisRun
5. Explicit session cleanup in background threads

Note on commit behavior:
- Each write_* method commits immediately by default (crash durability)
- Pass commit=False to batch writes, then call session.commit() yourself
- Per-write commits add latency but guarantee no data loss on crash
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_upsert

logger = logging.getLogger(__name__)


class IncrementalDBWriter:
    """
    Thread-safe database writer for incremental persistence.

    Each write is committed immediately for crash durability.
    Uses UPSERT semantics for idempotent retry handling.

    Usage:
        writer = IncrementalDBWriter(app)

        # In analysis thread:
        with writer.session_scope() as session:
            writer.write_fact(session, fact_data, deal_id, run_id)
            writer.write_gap(session, gap_data, deal_id, run_id)
            writer.write_finding(session, finding_data, deal_id, run_id)
    """

    # Throttle progress updates to at most once per N seconds
    PROGRESS_THROTTLE_SECONDS = 2.0

    def __init__(self, app=None):
        """
        Initialize the writer.

        Args:
            app: Flask app instance (for app context in background threads)
        """
        self.app = app
        self._db = None  # Lazy init to avoid import issues

        # Cache dialect after first check
        self._dialect: Optional[str] = None

        # Per-run progress throttling (run_id -> last_progress_time)
        self._progress_timestamps: Dict[str, float] = {}
        self._progress_lock = threading.Lock()

        # Per-thread state: stats and session scope depth
        self._local = threading.local()

    def _get_db(self):
        """Get database instance (lazy init)."""
        if self._db is None:
            from web.database import db
            self._db = db
        return self._db

    def _get_dialect(self) -> str:
        """Get database dialect (cached, defaults to sqlite)."""
        if self._dialect is None:
            try:
                db = self._get_db()
                self._dialect = db.engine.dialect.name
            except Exception:
                # Default to sqlite if we can't determine
                self._dialect = 'sqlite'
        return self._dialect

    def _get_scope_depth(self) -> int:
        """Get current session scope nesting depth for this thread."""
        if not hasattr(self._local, 'scope_depth'):
            self._local.scope_depth = 0
        return self._local.scope_depth

    def _in_app_context(self) -> bool:
        """Check if we're inside a Flask app context."""
        try:
            from flask import has_app_context
            return has_app_context()
        except ImportError:
            return False

    def _in_request_context(self) -> bool:
        """Check if we're inside a Flask request context."""
        try:
            from flask import has_request_context
            return has_request_context()
        except ImportError:
            return False

    @contextmanager
    def session_scope(self):
        """
        Context manager for thread-safe database sessions.

        Handles:
        - Nested calls (only removes session on outermost exit)
        - Flask request context (doesn't remove Flask's session)
        - Existing app context (reuses it)
        - Background threads (creates app context, removes session on exit)

        Usage:
            with writer.session_scope() as session:
                writer.write_fact(session, ...)
        """
        db = self._get_db()

        # Track nesting depth
        if not hasattr(self._local, 'scope_depth'):
            self._local.scope_depth = 0

        is_outermost = self._local.scope_depth == 0
        self._local.scope_depth += 1

        in_app_ctx = self._in_app_context()
        in_request = self._in_request_context()

        try:
            # Need to create app context only if we're not already in one
            if self.app and not in_app_ctx and is_outermost:
                with self.app.app_context():
                    try:
                        yield db.session
                    finally:
                        self._local.scope_depth -= 1
                        if self._local.scope_depth == 0:
                            db.session.remove()
            else:
                # Already in app context or nested - just yield session
                try:
                    yield db.session
                finally:
                    self._local.scope_depth -= 1
                    # Only remove session if:
                    # - We're the outermost scope AND
                    # - We're NOT in a Flask request (Flask manages its own session)
                    if self._local.scope_depth == 0 and not in_request:
                        db.session.remove()
        except Exception:
            self._local.scope_depth -= 1
            raise

    def _init_thread_stats(self):
        """Initialize per-thread statistics."""
        if not hasattr(self._local, 'stats'):
            self._local.stats = {
                'facts_written': 0,
                'gaps_written': 0,
                'findings_written': 0,
                'errors': 0,
            }

    def get_thread_stats(self) -> Dict[str, int]:
        """Get statistics for current thread."""
        self._init_thread_stats()
        return dict(self._local.stats)

    def reset_thread_stats(self):
        """Reset statistics for current thread."""
        self._local.stats = {
            'facts_written': 0,
            'gaps_written': 0,
            'findings_written': 0,
            'errors': 0,
        }

    # =========================================================================
    # FACT WRITING
    # =========================================================================

    def write_fact(
        self,
        session,
        fact_data: Dict[str, Any],
        deal_id: str,
        analysis_run_id: Optional[str] = None,
        commit: bool = True
    ) -> bool:
        """
        Write a single fact to the database.

        Uses UPSERT: if fact with same ID exists, updates it.
        This makes the operation idempotent for retries.

        Args:
            session: SQLAlchemy session from session_scope()
            fact_data: Dict with fact fields (must include 'fact_id' or 'id')
            deal_id: Deal ID this fact belongs to
            analysis_run_id: Optional analysis run ID
            commit: If True (default), commit immediately for crash durability.
                    If False, caller must commit manually.

        Returns:
            True if write succeeded, False on error
        """
        from web.database import Fact

        self._init_thread_stats()

        # Normalize fact_id
        fact_id = fact_data.get('fact_id') or fact_data.get('id')
        if not fact_id:
            logger.error("Fact missing ID, cannot write")
            self._local.stats['errors'] += 1
            return False

        try:
            # Build fact record
            fact_record = {
                'id': fact_id,
                'deal_id': deal_id,
                'analysis_run_id': analysis_run_id,
                'domain': fact_data.get('domain', 'general'),
                'category': fact_data.get('category', ''),
                'entity': fact_data.get('entity', 'target'),
                'item': fact_data.get('item', ''),
                'status': fact_data.get('status', 'documented'),
                'details': fact_data.get('details', {}),
                'evidence': fact_data.get('evidence', {}),
                'source_document': fact_data.get('source_document', ''),
                'source_page_numbers': fact_data.get('source_page_numbers', []),
                'source_quote': fact_data.get('source_quote', ''),
                'confidence_score': fact_data.get('confidence_score', 0.5),
                'created_at': datetime.utcnow(),
            }

            # Perform UPSERT
            self._upsert_record(session, Fact, fact_record, 'id')

            if commit:
                session.commit()

            self._local.stats['facts_written'] += 1
            logger.debug(f"Wrote fact {fact_id} to database")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to write fact {fact_id}: {e}")
            self._local.stats['errors'] += 1
            return False

    def write_facts_batch(
        self,
        session,
        facts: List[Dict[str, Any]],
        deal_id: str,
        analysis_run_id: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Write multiple facts in a single transaction.

        Use this when you have a batch of related facts that should
        succeed or fail together. Single commit at the end.

        Args:
            session: SQLAlchemy session
            facts: List of fact dicts
            deal_id: Deal ID
            analysis_run_id: Optional analysis run ID

        Returns:
            Tuple of (written_count, skipped_count)
        """
        from web.database import Fact

        self._init_thread_stats()
        written = 0
        skipped = 0

        try:
            for fact_data in facts:
                fact_id = fact_data.get('fact_id') or fact_data.get('id')
                if not fact_id:
                    item_preview = str(fact_data.get('item', ''))[:50]
                    logger.warning(f"Skipping fact without ID: {item_preview}")
                    skipped += 1
                    continue

                fact_record = {
                    'id': fact_id,
                    'deal_id': deal_id,
                    'analysis_run_id': analysis_run_id,
                    'domain': fact_data.get('domain', 'general'),
                    'category': fact_data.get('category', ''),
                    'entity': fact_data.get('entity', 'target'),
                    'item': fact_data.get('item', ''),
                    'status': fact_data.get('status', 'documented'),
                    'details': fact_data.get('details', {}),
                    'evidence': fact_data.get('evidence', {}),
                    'source_document': fact_data.get('source_document', ''),
                    'source_page_numbers': fact_data.get('source_page_numbers', []),
                    'source_quote': fact_data.get('source_quote', ''),
                    'confidence_score': fact_data.get('confidence_score', 0.5),
                    'created_at': datetime.utcnow(),
                }

                self._upsert_record(session, Fact, fact_record, 'id')
                written += 1

            # Single commit for entire batch
            session.commit()
            self._local.stats['facts_written'] += written
            logger.debug(f"Wrote batch of {written} facts, skipped {skipped}")
            return (written, skipped)

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to write fact batch: {e}")
            self._local.stats['errors'] += 1
            return (0, len(facts))

    # =========================================================================
    # GAP WRITING
    # =========================================================================

    def write_gap(
        self,
        session,
        gap_data: Dict[str, Any],
        deal_id: str,
        analysis_run_id: Optional[str] = None,
        commit: bool = True
    ) -> bool:
        """
        Write a single gap to the database.

        Uses UPSERT for idempotent retry handling.

        Args:
            session: SQLAlchemy session
            gap_data: Dict with gap fields
            deal_id: Deal ID
            analysis_run_id: Optional analysis run ID
            commit: If True (default), commit immediately

        Returns:
            True if write succeeded, False on error
        """
        from web.database import Gap

        self._init_thread_stats()

        gap_id = gap_data.get('gap_id') or gap_data.get('id')
        if not gap_id:
            logger.error("Gap missing ID, cannot write")
            self._local.stats['errors'] += 1
            return False

        try:
            gap_record = {
                'id': gap_id,
                'deal_id': deal_id,
                'analysis_run_id': analysis_run_id,
                'domain': gap_data.get('domain', 'general'),
                'category': gap_data.get('category', ''),
                'entity': gap_data.get('entity', 'target'),
                'description': gap_data.get('description', ''),
                'importance': gap_data.get('importance', 'medium'),
                'requested_item': gap_data.get('requested_item', ''),
                'source_document': gap_data.get('source_document', ''),
                'related_facts': gap_data.get('related_facts', []),
                'status': gap_data.get('status', 'open'),
                'created_at': datetime.utcnow(),
            }

            self._upsert_record(session, Gap, gap_record, 'id')

            if commit:
                session.commit()

            self._local.stats['gaps_written'] += 1
            logger.debug(f"Wrote gap {gap_id} to database")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to write gap {gap_id}: {e}")
            self._local.stats['errors'] += 1
            return False

    # =========================================================================
    # FINDING WRITING (Risks, Work Items, Recommendations)
    # =========================================================================

    def write_finding(
        self,
        session,
        finding_data: Dict[str, Any],
        deal_id: str,
        analysis_run_id: Optional[str] = None,
        commit: bool = True
    ) -> bool:
        """
        Write a single finding to the database.

        Handles all finding types: risk, work_item, recommendation, strategic_consideration
        Uses UPSERT for idempotent retry handling.

        Args:
            session: SQLAlchemy session
            finding_data: Dict with finding fields
            deal_id: Deal ID
            analysis_run_id: Optional analysis run ID
            commit: If True (default), commit immediately

        Returns:
            True if write succeeded, False on error
        """
        from web.database import Finding

        self._init_thread_stats()

        finding_id = finding_data.get('finding_id') or finding_data.get('id')
        if not finding_id:
            logger.error("Finding missing ID, cannot write")
            self._local.stats['errors'] += 1
            return False

        try:
            finding_record = {
                'id': finding_id,
                'deal_id': deal_id,
                'analysis_run_id': analysis_run_id,
                'finding_type': finding_data.get('finding_type', 'risk'),
                'domain': finding_data.get('domain', 'general'),
                'title': finding_data.get('title', ''),
                'description': finding_data.get('description', ''),
                'reasoning': finding_data.get('reasoning', ''),
                'confidence': finding_data.get('confidence', 'medium'),
                'based_on_facts': finding_data.get('based_on_facts', []),
                'created_at': datetime.utcnow(),
            }

            # Type-specific fields
            finding_type = finding_data.get('finding_type', 'risk')

            if finding_type == 'risk':
                finding_record.update({
                    'severity': finding_data.get('severity', 'medium'),
                    'category': finding_data.get('category', ''),
                    'mitigation': finding_data.get('mitigation', ''),
                    'integration_dependent': finding_data.get('integration_dependent', False),
                    'timeline': finding_data.get('timeline'),
                })
            elif finding_type == 'work_item':
                finding_record.update({
                    'phase': finding_data.get('phase'),
                    'priority': finding_data.get('priority'),
                    'owner_type': finding_data.get('owner_type'),
                    'cost_estimate': finding_data.get('cost_estimate'),
                    'triggered_by_risks': finding_data.get('triggered_by_risks', []),
                    'dependencies': finding_data.get('dependencies', []),
                })
            elif finding_type == 'recommendation':
                finding_record.update({
                    'action_type': finding_data.get('action_type'),
                    'urgency': finding_data.get('urgency'),
                    'rationale': finding_data.get('rationale', ''),
                })
            elif finding_type == 'strategic_consideration':
                finding_record.update({
                    'lens': finding_data.get('lens'),
                    'implication': finding_data.get('implication', ''),
                })

            self._upsert_record(session, Finding, finding_record, 'id')

            if commit:
                session.commit()

            self._local.stats['findings_written'] += 1
            logger.debug(f"Wrote finding {finding_id} to database")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to write finding {finding_id}: {e}")
            self._local.stats['errors'] += 1
            return False

    # =========================================================================
    # ANALYSIS RUN MANAGEMENT
    # =========================================================================

    def create_analysis_run(
        self,
        session,
        deal_id: str,
        task_id: Optional[str] = None,
        run_type: str = 'full',
        entity: str = 'target',
        domains: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a new analysis run record.

        Args:
            session: SQLAlchemy session
            deal_id: Deal ID this run belongs to
            task_id: Optional task ID for UI tracking (should be unique)
            run_type: Type of run ('full', 'incremental', 'targeted')
            entity: Entity being analyzed ('target', 'buyer', 'both')
            domains: List of domains to analyze (None = all)

        Returns:
            The new run ID, or None on error
        """
        from web.database import AnalysisRun, generate_uuid

        try:
            # Get next run number for this deal
            last_run = session.query(AnalysisRun).filter_by(
                deal_id=deal_id
            ).order_by(AnalysisRun.run_number.desc()).first()

            run_number = (last_run.run_number + 1) if last_run else 1

            run_id = generate_uuid()
            run = AnalysisRun(
                id=run_id,
                deal_id=deal_id,
                task_id=task_id,
                run_number=run_number,
                run_type=run_type,
                entity=entity,
                domains=domains or [],
                status='running',
                progress=0.0,
                current_step='Starting analysis',
                started_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )

            session.add(run)
            session.commit()

            logger.info(f"Created analysis run {run_id} (#{run_number}) for deal {deal_id}")
            return run_id

        except IntegrityError as e:
            session.rollback()
            # Likely duplicate task_id
            logger.error(f"Failed to create analysis run (duplicate?): {e}")
            return None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create analysis run: {e}")
            return None

    def update_analysis_progress(
        self,
        session,
        run_id: str,
        progress: float,
        current_step: str = '',
        facts_created: int = 0,
        findings_created: int = 0,
        force: bool = False
    ) -> bool:
        """
        Update analysis run progress with throttling.

        To avoid excessive database writes, progress updates are throttled
        to at most once every PROGRESS_THROTTLE_SECONDS. Use force=True
        for important updates (status changes, completion).

        Args:
            session: SQLAlchemy session
            run_id: Analysis run ID
            progress: Progress percentage (0-100)
            current_step: Current step description
            facts_created: Total facts created so far
            findings_created: Total findings created so far
            force: Skip throttling for this update

        Returns:
            True if update was written, False if throttled or error
        """
        from web.database import AnalysisRun

        now = time.time()

        # Check throttle (unless forced)
        if not force:
            with self._progress_lock:
                last_update = self._progress_timestamps.get(run_id, 0)
                if now - last_update < self.PROGRESS_THROTTLE_SECONDS:
                    return False  # Throttled, skip this update

        try:
            run = session.query(AnalysisRun).filter_by(id=run_id).first()
            if not run:
                logger.warning(f"AnalysisRun {run_id} not found for progress update")
                return False

            run.progress = progress
            if current_step:
                run.current_step = current_step
            run.facts_created = facts_created
            run.findings_created = findings_created

            session.commit()

            # Update throttle timestamp
            with self._progress_lock:
                self._progress_timestamps[run_id] = now

            logger.debug(f"Updated analysis run {run_id} progress: {progress:.1f}%")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update analysis progress: {e}")
            return False

    def complete_analysis_run(
        self,
        session,
        run_id: str,
        status: str = 'completed',
        error_message: str = '',
        facts_created: Optional[int] = None,
        facts_updated: Optional[int] = None,
        findings_created: Optional[int] = None,
        findings_updated: Optional[int] = None,
        errors_count: Optional[int] = None
    ) -> bool:
        """
        Mark an analysis run as complete (or failed).

        This is always written immediately (not throttled).

        Args:
            session: SQLAlchemy session
            run_id: Analysis run ID
            status: Final status ('completed', 'failed', 'cancelled')
            error_message: Error message if failed
            facts_created: Final count of facts created
            facts_updated: Final count of facts updated
            findings_created: Final count of findings created
            findings_updated: Final count of findings updated
            errors_count: Final count of errors

        Returns:
            True if update succeeded
        """
        from web.database import AnalysisRun

        try:
            run = session.query(AnalysisRun).filter_by(id=run_id).first()
            if not run:
                logger.warning(f"AnalysisRun {run_id} not found for completion")
                return False

            run.status = status
            run.progress = 100.0 if status == 'completed' else run.progress
            run.completed_at = datetime.utcnow()

            if run.started_at:
                run.duration_seconds = (run.completed_at - run.started_at).total_seconds()

            if error_message:
                run.error_message = error_message

            # Set final counts if provided
            if facts_created is not None:
                run.facts_created = facts_created
            if facts_updated is not None:
                run.facts_updated = facts_updated
            if findings_created is not None:
                run.findings_created = findings_created
            if findings_updated is not None:
                run.findings_updated = findings_updated
            if errors_count is not None:
                run.errors_count = errors_count

            session.commit()

            # Clean up throttle tracking
            with self._progress_lock:
                self._progress_timestamps.pop(run_id, None)

            logger.info(f"Analysis run {run_id} marked as {status}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to complete analysis run: {e}")
            return False

    # =========================================================================
    # UPSERT IMPLEMENTATION
    # =========================================================================

    def _upsert_record(self, session, model_class, record: Dict[str, Any], pk_field: str) -> None:
        """
        Perform UPSERT (INSERT or UPDATE on conflict).

        Args:
            session: SQLAlchemy session
            model_class: SQLAlchemy model class
            record: Dict of field values
            pk_field: Primary key field name for conflict detection
        """
        dialect = self._get_dialect()

        if dialect == 'postgresql':
            self._upsert_postgresql(session, model_class, record, pk_field)
        else:
            # SQLite or fallback
            self._upsert_sqlite(session, model_class, record, pk_field)

    def _upsert_postgresql(self, session, model_class, record: Dict[str, Any], pk_field: str) -> None:
        """PostgreSQL UPSERT using ON CONFLICT DO UPDATE."""
        stmt = pg_upsert(model_class).values(**record)

        # On conflict, update all fields except the primary key
        update_fields = {k: v for k, v in record.items() if k != pk_field}
        update_fields['updated_at'] = datetime.utcnow()

        stmt = stmt.on_conflict_do_update(
            index_elements=[pk_field],
            set_=update_fields
        )

        session.execute(stmt)

    def _upsert_sqlite(self, session, model_class, record: Dict[str, Any], pk_field: str) -> None:
        """SQLite UPSERT - check then insert or update."""
        pk_value = record.get(pk_field)

        # Use session.get() to avoid triggering autoflush
        existing = session.get(model_class, pk_value)

        if existing:
            # Update existing record
            for key, value in record.items():
                if key != pk_field and hasattr(existing, key):
                    setattr(existing, key, value)
            if hasattr(existing, 'updated_at'):
                existing.updated_at = datetime.utcnow()
        else:
            # Insert new record
            new_record = model_class(**record)
            session.add(new_record)

    # =========================================================================
    # LINK TABLE WRITING
    # =========================================================================

    def write_fact_finding_link(
        self,
        session,
        fact_id: str,
        finding_id: str,
        relationship_type: str = 'supports',
        relevance_score: float = 1.0,
        commit: bool = True
    ) -> bool:
        """
        Create a link between a fact and a finding.

        Uses INSERT IGNORE semantics - if link already exists, silently skip.

        Args:
            session: SQLAlchemy session
            fact_id: Fact ID
            finding_id: Finding ID
            relationship_type: Type of relationship ('supports', 'contradicts', 'context')
            relevance_score: How relevant (0.0-1.0)
            commit: If True (default), commit immediately

        Returns:
            True if link created or already exists, False on error
        """
        from web.database import FactFindingLink

        try:
            # Check if link exists (unique constraint on fact_id + finding_id)
            existing = session.query(FactFindingLink).filter_by(
                fact_id=fact_id,
                finding_id=finding_id
            ).first()

            if existing:
                # Already linked, skip
                return True

            link = FactFindingLink(
                fact_id=fact_id,
                finding_id=finding_id,
                relationship_type=relationship_type,
                relevance_score=relevance_score,
                created_at=datetime.utcnow()
            )
            session.add(link)

            if commit:
                session.commit()

            return True

        except IntegrityError:
            # Unique constraint violation - link already exists
            session.rollback()
            return True  # Not an error, just a duplicate

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create fact-finding link: {e}")
            return False


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_writer_instance: Optional[IncrementalDBWriter] = None
_writer_lock = threading.Lock()


def get_db_writer(app=None) -> IncrementalDBWriter:
    """
    Get or create the singleton IncrementalDBWriter instance.

    Args:
        app: Flask app (required on first call, or in background threads)

    Returns:
        IncrementalDBWriter instance
    """
    global _writer_instance

    with _writer_lock:
        if _writer_instance is None:
            if app is None:
                raise ValueError("Flask app required to initialize IncrementalDBWriter")
            _writer_instance = IncrementalDBWriter(app)
        elif app is not None:
            # Update app reference if provided
            _writer_instance.app = app

    return _writer_instance
