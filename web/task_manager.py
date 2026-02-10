"""
Analysis Task Manager for IT Due Diligence Agent.

Manages background analysis tasks with:
- Thread-based async execution
- Progress tracking
- Result storage
- Timeout handling
- Cancellation support
"""

import threading
import uuid
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback


class TaskStatus(Enum):
    """Analysis task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AnalysisPhase(Enum):
    """Analysis pipeline phases."""
    INITIALIZING = "initializing"
    PARSING_DOCUMENTS = "parsing_documents"
    # Phase 1: Target Company Analysis (clean extraction)
    TARGET_ANALYSIS_START = "target_analysis_start"
    DISCOVERY_INFRASTRUCTURE = "discovery_infrastructure"
    DISCOVERY_NETWORK = "discovery_network"
    DISCOVERY_CYBERSECURITY = "discovery_cybersecurity"
    DISCOVERY_APPLICATIONS = "discovery_applications"
    DISCOVERY_IDENTITY = "discovery_identity"
    DISCOVERY_ORGANIZATION = "discovery_organization"
    TARGET_ANALYSIS_COMPLETE = "target_analysis_complete"
    # Phase 2: Buyer Company Analysis (with Target context)
    BUYER_ANALYSIS_START = "buyer_analysis_start"
    BUYER_DISCOVERY_INFRASTRUCTURE = "buyer_discovery_infrastructure"
    BUYER_DISCOVERY_NETWORK = "buyer_discovery_network"
    BUYER_DISCOVERY_CYBERSECURITY = "buyer_discovery_cybersecurity"
    BUYER_DISCOVERY_APPLICATIONS = "buyer_discovery_applications"
    BUYER_DISCOVERY_IDENTITY = "buyer_discovery_identity"
    BUYER_DISCOVERY_ORGANIZATION = "buyer_discovery_organization"
    BUYER_ANALYSIS_COMPLETE = "buyer_analysis_complete"
    # Phase 3.5: Overlap Generation
    OVERLAP_GENERATION = "overlap_generation"
    # Phase 4: Reasoning & Synthesis
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    FINALIZING = "finalizing"
    COMPLETE = "complete"


PHASE_DISPLAY_NAMES = {
    AnalysisPhase.INITIALIZING: "Initializing analysis...",
    AnalysisPhase.PARSING_DOCUMENTS: "Parsing documents...",
    # Phase 1: Target
    AnalysisPhase.TARGET_ANALYSIS_START: "Starting TARGET company analysis...",
    AnalysisPhase.DISCOVERY_INFRASTRUCTURE: "Analyzing TARGET infrastructure...",
    AnalysisPhase.DISCOVERY_NETWORK: "Analyzing TARGET network...",
    AnalysisPhase.DISCOVERY_CYBERSECURITY: "Analyzing TARGET cybersecurity...",
    AnalysisPhase.DISCOVERY_APPLICATIONS: "Analyzing TARGET applications...",
    AnalysisPhase.DISCOVERY_IDENTITY: "Analyzing TARGET identity & access...",
    AnalysisPhase.DISCOVERY_ORGANIZATION: "Analyzing TARGET organization...",
    AnalysisPhase.TARGET_ANALYSIS_COMPLETE: "TARGET analysis complete - locking facts...",
    # Phase 2: Buyer
    AnalysisPhase.BUYER_ANALYSIS_START: "Starting BUYER company analysis...",
    AnalysisPhase.BUYER_DISCOVERY_INFRASTRUCTURE: "Analyzing BUYER infrastructure...",
    AnalysisPhase.BUYER_DISCOVERY_NETWORK: "Analyzing BUYER network...",
    AnalysisPhase.BUYER_DISCOVERY_CYBERSECURITY: "Analyzing BUYER cybersecurity...",
    AnalysisPhase.BUYER_DISCOVERY_APPLICATIONS: "Analyzing BUYER applications...",
    AnalysisPhase.BUYER_DISCOVERY_IDENTITY: "Analyzing BUYER identity & access...",
    AnalysisPhase.BUYER_DISCOVERY_ORGANIZATION: "Analyzing BUYER organization...",
    AnalysisPhase.BUYER_ANALYSIS_COMPLETE: "BUYER analysis complete...",
    # Phase 3.5: Overlap
    AnalysisPhase.OVERLAP_GENERATION: "Generating overlap map...",
    # Phase 4: Final
    AnalysisPhase.REASONING: "Generating findings...",
    AnalysisPhase.SYNTHESIS: "Synthesizing results...",
    AnalysisPhase.FINALIZING: "Finalizing analysis...",
    AnalysisPhase.COMPLETE: "Analysis complete",
}

PHASE_ORDER = list(AnalysisPhase)


@dataclass
class AnalysisProgress:
    """Tracks analysis progress."""
    phase: AnalysisPhase = AnalysisPhase.INITIALIZING
    phase_display: str = "Initializing..."
    percent_complete: int = 0
    current_document: Optional[str] = None
    documents_processed: int = 0
    total_documents: int = 0
    facts_extracted: int = 0
    risks_identified: int = 0
    work_items_created: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "phase_display": self.phase_display,
            "percent_complete": self.percent_complete,
            "current_document": self.current_document,
            "documents_processed": self.documents_processed,
            "total_documents": self.total_documents,
            "facts_extracted": self.facts_extracted,
            "risks_identified": self.risks_identified,
            "work_items_created": self.work_items_created,
            "errors": self.errors,
        }

    def update_phase(self, phase: AnalysisPhase):
        """Update the current phase and calculate progress."""
        self.phase = phase
        self.phase_display = PHASE_DISPLAY_NAMES.get(phase, str(phase.value))

        # Calculate percent based on phase order
        if phase in PHASE_ORDER:
            phase_index = PHASE_ORDER.index(phase)
            self.percent_complete = int((phase_index / (len(PHASE_ORDER) - 1)) * 100)


@dataclass
class AnalysisTask:
    """Represents an analysis task."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Input configuration
    file_paths: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    deal_context: Dict[str, str] = field(default_factory=dict)

    # Progress tracking
    progress: AnalysisProgress = field(default_factory=AnalysisProgress)

    # Results
    result_path: Optional[str] = None
    facts_file: Optional[str] = None
    findings_file: Optional[str] = None
    error_message: Optional[str] = None

    # Runtime
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _cancelled: bool = field(default=False, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "file_paths": self.file_paths,
            "domains": self.domains,
            "deal_context": self.deal_context,
            "progress": self.progress.to_dict(),
            "result_path": self.result_path,
            "facts_file": self.facts_file,
            "findings_file": self.findings_file,
            "error_message": self.error_message,
        }


class AnalysisTaskManager:
    """
    Manages analysis tasks with background execution.

    Thread-safe singleton that handles:
    - Task creation and queuing
    - Background execution (threading or Celery)
    - Progress tracking
    - Result storage
    - Cleanup

    Phase 4: Supports both threading (fallback) and Celery (when available).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tasks: Dict[str, AnalysisTask] = {}
        self._celery_tasks: Dict[str, str] = {}  # task_id -> celery_task_id mapping
        self._tasks_lock = threading.Lock()
        self._max_concurrent = 2
        self._running_count = 0
        self._task_timeout = 1800  # 30 minutes
        self._results_dir: Optional[Path] = None
        self._use_celery = False
        self._initialized = True

    def configure(self, results_dir: Path, max_concurrent: int = 2, timeout: int = 1800, use_celery: bool = False):
        """Configure the task manager."""
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._max_concurrent = max_concurrent
        self._task_timeout = timeout
        self._use_celery = use_celery

        if use_celery:
            try:
                from web.celery_app import is_celery_available
                if is_celery_available():
                    self._use_celery = True
                else:
                    self._use_celery = False
            except Exception:
                self._use_celery = False

    def create_task(
        self,
        file_paths: List[str],
        domains: List[str],
        deal_context: Dict[str, str]
    ) -> AnalysisTask:
        """Create a new analysis task."""
        task_id = f"analysis_{uuid.uuid4().hex[:12]}"

        task = AnalysisTask(
            task_id=task_id,
            file_paths=file_paths,
            domains=domains,
            deal_context=deal_context,
        )

        with self._tasks_lock:
            self._tasks[task_id] = task

        # Persist to database for resilience (survives server restart)
        self._save_task_to_db(task, deal_context.get('deal_id'))

        return task

    def start_task(self, task_id: str, run_analysis_fn: Callable, deal_id: str = None) -> bool:
        """
        Start a task in background.

        Uses Celery if available and configured, otherwise falls back to threading.
        """
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status != TaskStatus.PENDING:
                return False

        # Try Celery first if configured
        if self._use_celery and deal_id:
            return self._start_task_celery(task, deal_id)

        # Fall back to threading
        return self._start_task_threaded(task, run_analysis_fn)

    def _start_task_celery(self, task: AnalysisTask, deal_id: str) -> bool:
        """Start task using Celery."""
        try:
            from web.tasks import run_analysis_task

            # Submit to Celery
            celery_result = run_analysis_task.delay(
                deal_id=deal_id,
                domains=task.domains,
                entity=task.deal_context.get('entity', 'target'),
                user_id=task.deal_context.get('user_id')
            )

            # Store mapping
            with self._tasks_lock:
                self._celery_tasks[task.task_id] = celery_result.id
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now().isoformat()

            return True

        except Exception as e:
            # Fall back to threading if Celery fails
            return False

    def _start_task_threaded(self, task: AnalysisTask, run_analysis_fn: Callable) -> bool:
        """Start task using threading (fallback)."""
        with self._tasks_lock:
            if self._running_count >= self._max_concurrent:
                # Queue it - will be started when a slot opens
                return True

            self._running_count += 1

        # Start background thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task, run_analysis_fn),
            daemon=True
        )
        task._thread = thread
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()

        # Persist running status to database
        self._save_task_to_db(task)

        thread.start()

        return True

    def _run_task(self, task: AnalysisTask, run_analysis_fn: Callable):
        """Execute analysis in background thread."""
        start_time = time.time()

        try:
            # Import Flask app for context in background thread
            from web.app import app

            # Wrap entire analysis in app context for database access
            with app.app_context():
                # Run the actual analysis
                # Pass app for incremental database writes
                result = run_analysis_fn(
                    task=task,
                    progress_callback=lambda p: self._update_progress(task.task_id, p),
                    app=app
                )

                # Check for timeout
                if time.time() - start_time > self._task_timeout:
                    task.status = TaskStatus.TIMEOUT
                    task.error_message = f"Analysis timed out after {self._task_timeout} seconds"
                elif task._cancelled:
                    task.status = TaskStatus.CANCELLED
                else:
                    task.status = TaskStatus.COMPLETED
                    task.progress.update_phase(AnalysisPhase.COMPLETE)

                    # Store result paths
                    if result:
                        task.facts_file = result.get("facts_file")
                        task.findings_file = result.get("findings_file")
                        task.result_path = result.get("result_path")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = f"{type(e).__name__}: {str(e)}"
            task.progress.errors.append(traceback.format_exc())

        finally:
            task.completed_at = datetime.now().isoformat()

            with self._tasks_lock:
                self._running_count = max(0, self._running_count - 1)

            # Save task state
            self._save_task_state(task)

    def _update_progress(self, task_id: str, progress_update: Dict[str, Any]):
        """Update task progress from callback."""
        should_save_to_db = False

        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            if "phase" in progress_update:
                phase = progress_update["phase"]
                if isinstance(phase, str):
                    phase = AnalysisPhase(phase)
                task.progress.update_phase(phase)
                # Save to DB when phase changes (not too frequent)
                should_save_to_db = True

            for key in ["current_document", "documents_processed", "total_documents",
                       "facts_extracted", "risks_identified", "work_items_created", "phase_display"]:
                if key in progress_update:
                    setattr(task.progress, key, progress_update[key])

        # Persist phase changes to database (outside lock to avoid deadlock)
        if should_save_to_db:
            self._save_task_to_db(task)

    def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        """Get task by ID (checks memory first, then database)."""
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if task:
                return task

        # Not in memory - check database (for recovery after server restart)
        return self._load_task_from_db(task_id)

    def _load_task_from_db(self, task_id: str) -> Optional[AnalysisTask]:
        """Load task state from database (for recovery after restart)."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            from web.database import db, AnalysisRun
            from web.app import app

            with app.app_context():
                logger.debug(f"Looking up task {task_id} in database...")
                run = AnalysisRun.query.filter_by(task_id=task_id).first()
                if not run:
                    logger.info(f"Task {task_id} not found in database (new task or migration pending)")
                    return None

                logger.info(f"Recovered task {task_id} from database: status={run.status}, progress={run.progress}%")

                # Reconstruct task from database
                task = AnalysisTask(
                    task_id=task_id,
                    file_paths=[],  # Not stored in DB
                    domains=run.domains or [],
                    deal_context={'deal_id': run.deal_id},
                )

                # Map status
                status_map = {
                    'pending': TaskStatus.PENDING,
                    'running': TaskStatus.RUNNING,
                    'completed': TaskStatus.COMPLETED,
                    'failed': TaskStatus.FAILED,
                    'cancelled': TaskStatus.CANCELLED,
                }
                task.status = status_map.get(run.status, TaskStatus.PENDING)
                task.started_at = run.started_at.isoformat() if run.started_at else None
                task.completed_at = run.completed_at.isoformat() if run.completed_at else None
                task.error_message = run.error_message or None

                # Set progress
                task.progress.percent_complete = int(run.progress or 0)
                task.progress.phase_display = run.current_step or "Unknown"
                task.progress.facts_extracted = run.facts_created or 0
                task.progress.risks_identified = run.findings_created or 0

                # Cache in memory for subsequent calls
                with self._tasks_lock:
                    self._tasks[task_id] = task

                return task

        except Exception as e:
            logger.error(f"Failed to load task {task_id} from DB: {type(e).__name__}: {e}")
            # Log if this might be a migration issue (column doesn't exist)
            if 'task_id' in str(e).lower() or 'column' in str(e).lower():
                logger.error("This may indicate the task_id migration hasn't run. Check database schema.")
            return None

    def _save_task_to_db(self, task: AnalysisTask, deal_id: str = None):
        """Save task state to database for resilience."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            from web.database import db, AnalysisRun
            from web.app import app
            from sqlalchemy import func

            with app.app_context():
                # Check if run exists
                run = AnalysisRun.query.filter_by(task_id=task.task_id).first()

                if not run:
                    # Get deal_id from task context
                    deal_id = deal_id or task.deal_context.get('deal_id')
                    if not deal_id:
                        logger.warning(f"Cannot save task {task.task_id} - no deal_id")
                        return  # Can't save without deal_id

                    # Get next run number
                    max_run = db.session.query(func.max(AnalysisRun.run_number)).filter_by(deal_id=deal_id).scalar()
                    run_number = (max_run or 0) + 1

                    run = AnalysisRun(
                        deal_id=deal_id,
                        task_id=task.task_id,
                        run_number=run_number,
                        run_type='full',
                        domains=task.domains,
                    )
                    db.session.add(run)
                    logger.info(f"Created DB record for task {task.task_id} (deal={deal_id}, run={run_number})")

                # Update status
                run.status = task.status.value
                run.progress = task.progress.percent_complete
                run.current_step = task.progress.phase_display
                run.facts_created = task.progress.facts_extracted
                run.findings_created = task.progress.risks_identified + task.progress.work_items_created

                if task.started_at:
                    from datetime import datetime
                    run.started_at = datetime.fromisoformat(task.started_at)
                if task.completed_at:
                    from datetime import datetime
                    run.completed_at = datetime.fromisoformat(task.completed_at)
                if task.error_message:
                    run.error_message = task.error_message

                db.session.commit()
                logger.debug(f"Saved task {task.task_id} to DB: status={run.status}, progress={run.progress}%")

        except Exception as e:
            logger.error(f"Failed to save task {task.task_id} to DB: {type(e).__name__}: {e}")
            # Log if this might be a migration issue
            if 'task_id' in str(e).lower() or 'column' in str(e).lower():
                logger.error("This may indicate the task_id migration hasn't run. Check database schema.")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status as dict for API response."""
        task = self.get_task(task_id)
        if not task:
            return None

        # Check Celery task status if applicable
        celery_task_id = self._celery_tasks.get(task_id)
        if celery_task_id and self._use_celery:
            celery_status = self._get_celery_task_status(celery_task_id)
            if celery_status:
                # Update local task with Celery status
                self._sync_celery_status(task, celery_status)

        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "complete": task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED,
                                         TaskStatus.CANCELLED, TaskStatus.TIMEOUT],
            "success": task.status == TaskStatus.COMPLETED,
            "progress": task.progress.to_dict(),
            "error": task.error_message,
            "facts_file": task.facts_file,
            "findings_file": task.findings_file,
        }

    def _get_celery_task_status(self, celery_task_id: str) -> Optional[Dict[str, Any]]:
        """Get status from Celery task."""
        try:
            from web.celery_app import get_task_status
            return get_task_status(celery_task_id)
        except Exception:
            return None

    def _sync_celery_status(self, task: AnalysisTask, celery_status: Dict[str, Any]):
        """Sync local task with Celery status."""
        status_map = {
            'pending': TaskStatus.PENDING,
            'started': TaskStatus.RUNNING,
            'progress': TaskStatus.RUNNING,
            'completed': TaskStatus.COMPLETED,
            'failed': TaskStatus.FAILED,
            'cancelled': TaskStatus.CANCELLED,
        }

        celery_state = celery_status.get('status', 'pending')
        task.status = status_map.get(celery_state, TaskStatus.RUNNING)

        # Update progress
        progress = celery_status.get('progress', 0)
        task.progress.percent_complete = progress

        if celery_status.get('message'):
            task.progress.phase_display = celery_status['message']

        if celery_status.get('error'):
            task.error_message = celery_status['error']

        if celery_state == 'completed':
            task.completed_at = datetime.now().isoformat()
            task.progress.update_phase(AnalysisPhase.COMPLETE)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            # Cancel Celery task if applicable
            celery_task_id = self._celery_tasks.get(task_id)
            if celery_task_id and self._use_celery:
                try:
                    from web.celery_app import cancel_task as celery_cancel
                    celery_cancel(celery_task_id)
                except Exception:
                    pass

            if task.status == TaskStatus.RUNNING:
                task._cancelled = True
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                return True
            elif task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                return True

        return False

    def _save_task_state(self, task: AnalysisTask):
        """Save task state to disk and database for persistence."""
        # Save to JSON file (local backup)
        if self._results_dir:
            state_file = self._results_dir / f"{task.task_id}_state.json"
            try:
                with open(state_file, "w") as f:
                    json.dump(task.to_dict(), f, indent=2)
            except Exception:
                pass  # Non-critical

        # Save to database (survives server restarts on Railway)
        self._save_task_to_db(task)

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove completed tasks older than max_age_hours."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        with self._tasks_lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.completed_at:
                    completed_time = datetime.fromisoformat(task.completed_at).timestamp()
                    if completed_time < cutoff:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active (pending or running) tasks."""
        with self._tasks_lock:
            return [
                task.to_dict() for task in self._tasks.values()
                if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
            ]


# Global instance
task_manager = AnalysisTaskManager()
