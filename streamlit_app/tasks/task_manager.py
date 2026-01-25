"""
Task Manager - Background Task Execution for Streamlit

Manages background task execution with progress tracking,
cancellation support, and result caching.

Steps 39-48 of the alignment plan.

Note: Streamlit has limitations with background processing.
This implementation uses threading with careful state management.
For production, consider using Celery or similar task queues.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import streamlit as st


# =============================================================================
# ENUMS
# =============================================================================

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TaskProgress:
    """Progress information for a task."""
    percent: float = 0.0
    message: str = ""
    phase: str = ""
    updated_at: str = ""

    def update(self, percent: float, message: str, phase: str = ""):
        """Update progress."""
        self.percent = percent
        self.message = message
        self.phase = phase
        self.updated_at = datetime.now().isoformat()


@dataclass
class TaskInfo:
    """Information about a task."""
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    progress: TaskProgress = field(default_factory=TaskProgress)
    result: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self):
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat()

    def complete(self, result: Any = None):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now().isoformat()
        self.progress.update(1.0, "Complete", "done")

    def fail(self, error: str, traceback: Optional[str] = None):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.traceback = traceback
        self.completed_at = datetime.now().isoformat()

    def cancel(self):
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now().isoformat()

    def is_done(self) -> bool:
        """Check if task is done (completed, failed, or cancelled)."""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "progress": {
                "percent": self.progress.percent,
                "message": self.progress.message,
                "phase": self.progress.phase,
            },
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


# =============================================================================
# TASK MANAGER
# =============================================================================

class TaskManager:
    """
    Manages background task execution.

    Provides:
    - Task queue with priority support
    - Progress tracking
    - Task cancellation
    - Result caching
    - Automatic cleanup of old tasks
    """

    SESSION_KEY = "_itdd_task_manager"
    MAX_WORKERS = 2  # Keep low for Streamlit
    MAX_COMPLETED_TASKS = 10
    TASK_RETENTION_HOURS = 24

    def __init__(self):
        """Initialize the task manager."""
        self.tasks: Dict[str, TaskInfo] = {}
        self.futures: Dict[str, Future] = {}
        self.cancel_flags: Dict[str, threading.Event] = {}
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Get or create the thread pool executor."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self.MAX_WORKERS,
                thread_name_prefix="itdd_task_"
            )
        return self._executor

    # -------------------------------------------------------------------------
    # Task Submission
    # -------------------------------------------------------------------------

    def submit(
        self,
        func: Callable,
        name: str = "Task",
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for execution.

        Args:
            func: The function to execute
            name: Human-readable task name
            priority: Task priority
            metadata: Optional metadata
            **kwargs: Arguments to pass to the function

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]

        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            priority=priority,
            metadata=metadata or {},
        )

        # Create cancel flag
        cancel_event = threading.Event()

        with self._lock:
            self.tasks[task_id] = task_info
            self.cancel_flags[task_id] = cancel_event

        # Create progress callback
        def progress_callback(percent: float, message: str, phase: str = ""):
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].progress.update(percent, message, phase)

        # Wrap function to handle lifecycle
        def wrapped():
            try:
                task_info.start()

                # Add progress callback to kwargs if function accepts it
                if "progress_callback" in func.__code__.co_varnames:
                    kwargs["progress_callback"] = progress_callback

                # Add cancel check if function accepts it
                if "cancel_check" in func.__code__.co_varnames:
                    kwargs["cancel_check"] = lambda: cancel_event.is_set()

                result = func(**kwargs)
                task_info.complete(result)
                return result

            except Exception as e:
                import traceback
                task_info.fail(str(e), traceback.format_exc())
                raise

        # Submit to executor
        future = self.executor.submit(wrapped)

        with self._lock:
            self.futures[task_id] = future

        return task_id

    # -------------------------------------------------------------------------
    # Task Status
    # -------------------------------------------------------------------------

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task info by ID."""
        with self._lock:
            return self.tasks.get(task_id)

    def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress by ID."""
        task = self.get_task(task_id)
        return task.progress if task else None

    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get task result, waiting if necessary.

        Args:
            task_id: Task ID
            timeout: Optional timeout in seconds

        Returns:
            Task result

        Raises:
            ValueError: If task not found
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        with self._lock:
            future = self.futures.get(task_id)

        if future is None:
            raise ValueError(f"Task not found: {task_id}")

        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            raise TimeoutError(f"Task {task_id} did not complete within timeout")

    def is_running(self, task_id: str) -> bool:
        """Check if task is running."""
        task = self.get_task(task_id)
        return task.status == TaskStatus.RUNNING if task else False

    def is_done(self, task_id: str) -> bool:
        """Check if task is done."""
        task = self.get_task(task_id)
        return task.is_done() if task else True

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[TaskInfo]:
        """List tasks, optionally filtered by status."""
        with self._lock:
            tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    # -------------------------------------------------------------------------
    # Task Control
    # -------------------------------------------------------------------------

    def cancel(self, task_id: str) -> bool:
        """
        Request task cancellation.

        Note: The task function must check the cancel_check callback
        for this to work.

        Returns:
            True if cancellation was requested, False if task not found
        """
        with self._lock:
            if task_id not in self.cancel_flags:
                return False

            self.cancel_flags[task_id].set()
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.RUNNING:
                task.cancel()

        return True

    def wait(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for task to complete.

        Args:
            task_id: Task ID
            timeout: Optional timeout in seconds

        Returns:
            True if task completed, False if timeout
        """
        with self._lock:
            future = self.futures.get(task_id)

        if future is None:
            return True

        try:
            future.result(timeout=timeout)
            return True
        except TimeoutError:
            return False
        except Exception:
            return True  # Task completed (with error)

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup_old_tasks(self):
        """Remove old completed tasks."""
        now = datetime.now()
        cutoff = self.TASK_RETENTION_HOURS * 3600

        with self._lock:
            to_remove = []

            for task_id, task in self.tasks.items():
                if task.is_done() and task.completed_at:
                    completed = datetime.fromisoformat(task.completed_at)
                    age = (now - completed).total_seconds()

                    if age > cutoff:
                        to_remove.append(task_id)

            # Remove old tasks
            for task_id in to_remove:
                del self.tasks[task_id]
                self.futures.pop(task_id, None)
                self.cancel_flags.pop(task_id, None)

            # Limit completed tasks
            completed = [t for t in self.tasks.values() if t.is_done()]
            if len(completed) > self.MAX_COMPLETED_TASKS:
                # Sort by completed_at and remove oldest
                completed.sort(key=lambda t: t.completed_at or "")
                for task in completed[:-self.MAX_COMPLETED_TASKS]:
                    del self.tasks[task.task_id]
                    self.futures.pop(task.task_id, None)
                    self.cancel_flags.pop(task.task_id, None)

    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None


# =============================================================================
# STREAMLIT INTEGRATION
# =============================================================================

def get_task_manager() -> TaskManager:
    """
    Get the task manager from Streamlit session state.

    Creates a new manager if one doesn't exist.
    """
    if TaskManager.SESSION_KEY not in st.session_state:
        st.session_state[TaskManager.SESSION_KEY] = TaskManager()

    manager = st.session_state[TaskManager.SESSION_KEY]

    # Cleanup old tasks periodically
    manager.cleanup_old_tasks()

    return manager


# =============================================================================
# POLLING HELPER
# =============================================================================

def poll_task_progress(
    task_id: str,
    interval: float = 0.5,
    timeout: float = 300
) -> TaskInfo:
    """
    Poll task progress until complete.

    Args:
        task_id: Task ID to poll
        interval: Polling interval in seconds
        timeout: Maximum wait time in seconds

    Returns:
        Final TaskInfo

    Note: This is blocking. For Streamlit, use st.empty() with a loop instead.
    """
    manager = get_task_manager()
    start = time.time()

    while True:
        task = manager.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if task.is_done():
            return task

        if time.time() - start > timeout:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

        time.sleep(interval)
