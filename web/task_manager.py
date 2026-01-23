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
    DISCOVERY_INFRASTRUCTURE = "discovery_infrastructure"
    DISCOVERY_NETWORK = "discovery_network"
    DISCOVERY_CYBERSECURITY = "discovery_cybersecurity"
    DISCOVERY_APPLICATIONS = "discovery_applications"
    DISCOVERY_IDENTITY = "discovery_identity"
    DISCOVERY_ORGANIZATION = "discovery_organization"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    FINALIZING = "finalizing"
    COMPLETE = "complete"


PHASE_DISPLAY_NAMES = {
    AnalysisPhase.INITIALIZING: "Initializing analysis...",
    AnalysisPhase.PARSING_DOCUMENTS: "Parsing documents...",
    AnalysisPhase.DISCOVERY_INFRASTRUCTURE: "Analyzing infrastructure...",
    AnalysisPhase.DISCOVERY_NETWORK: "Analyzing network...",
    AnalysisPhase.DISCOVERY_CYBERSECURITY: "Analyzing cybersecurity...",
    AnalysisPhase.DISCOVERY_APPLICATIONS: "Analyzing applications...",
    AnalysisPhase.DISCOVERY_IDENTITY: "Analyzing identity & access...",
    AnalysisPhase.DISCOVERY_ORGANIZATION: "Analyzing organization...",
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
    - Background execution
    - Progress tracking
    - Result storage
    - Cleanup
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
        self._tasks_lock = threading.Lock()
        self._max_concurrent = 2
        self._running_count = 0
        self._task_timeout = 1800  # 30 minutes
        self._results_dir: Optional[Path] = None
        self._initialized = True

    def configure(self, results_dir: Path, max_concurrent: int = 2, timeout: int = 1800):
        """Configure the task manager."""
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._max_concurrent = max_concurrent
        self._task_timeout = timeout

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

        return task

    def start_task(self, task_id: str, run_analysis_fn: Callable) -> bool:
        """Start a task in background thread."""
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status != TaskStatus.PENDING:
                return False

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
        thread.start()

        return True

    def _run_task(self, task: AnalysisTask, run_analysis_fn: Callable):
        """Execute analysis in background thread."""
        start_time = time.time()

        try:
            # Run the actual analysis
            result = run_analysis_fn(
                task=task,
                progress_callback=lambda p: self._update_progress(task.task_id, p)
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
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            if "phase" in progress_update:
                phase = progress_update["phase"]
                if isinstance(phase, str):
                    phase = AnalysisPhase(phase)
                task.progress.update_phase(phase)

            for key in ["current_document", "documents_processed", "total_documents",
                       "facts_extracted", "risks_identified", "work_items_created"]:
                if key in progress_update:
                    setattr(task.progress, key, progress_update[key])

    def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        """Get task by ID."""
        with self._tasks_lock:
            return self._tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status as dict for API response."""
        task = self.get_task(task_id)
        if not task:
            return None

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

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status == TaskStatus.RUNNING:
                task._cancelled = True
                return True
            elif task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                return True

        return False

    def _save_task_state(self, task: AnalysisTask):
        """Save task state to disk for persistence."""
        if not self._results_dir:
            return

        state_file = self._results_dir / f"{task.task_id}_state.json"
        try:
            with open(state_file, "w") as f:
                json.dump(task.to_dict(), f, indent=2)
        except Exception:
            pass  # Non-critical

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
