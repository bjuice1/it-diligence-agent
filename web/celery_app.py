"""
Celery Application for Background Tasks

Phase 4: Distributed task processing with Celery and Redis.
Replaces threading-based task manager for scalability.
"""

import os
from celery import Celery, Task
from celery.result import AsyncResult

# Redis URL from environment
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery = Celery(
    'diligence',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['web.tasks']  # Import task modules
)

# Celery configuration
celery.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,  # Store additional task metadata

    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    task_time_limit=1800,  # 30 minute hard limit
    task_soft_time_limit=1500,  # 25 minute soft limit (raises exception)

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_concurrency=2,  # Number of concurrent tasks per worker

    # Beat scheduler (for periodic tasks)
    beat_schedule={
        # Clean up old tasks every hour
        'cleanup-old-tasks': {
            'task': 'web.tasks.cleanup_old_tasks',
            'schedule': 3600.0,  # Every hour
        },
    },
)


class FlaskTask(Task):
    """
    Celery Task that runs within Flask application context.

    This allows tasks to access Flask extensions like SQLAlchemy.
    """
    _flask_app = None

    @property
    def flask_app(self):
        if self._flask_app is None:
            from web.app import app
            self._flask_app = app
        return self._flask_app

    def __call__(self, *args, **kwargs):
        with self.flask_app.app_context():
            return self.run(*args, **kwargs)


# Set default task base class
celery.Task = FlaskTask


def get_task_status(task_id: str) -> dict:
    """
    Get the status of a Celery task.

    Returns dict with:
    - task_id: The task ID
    - status: pending, started, progress, success, failure, revoked
    - progress: Progress percentage (0-100) if available
    - result: Task result if completed
    - error: Error message if failed
    """
    result = AsyncResult(task_id, app=celery)

    response = {
        'task_id': task_id,
        'status': result.status.lower(),
    }

    if result.status == 'PENDING':
        response['status'] = 'pending'
        response['progress'] = 0
    elif result.status == 'STARTED':
        response['status'] = 'started'
        response['progress'] = 0
    elif result.status == 'PROGRESS':
        response['status'] = 'progress'
        response['progress'] = result.info.get('progress', 0) if result.info else 0
        response['message'] = result.info.get('message', '') if result.info else ''
        response['phase'] = result.info.get('phase', '') if result.info else ''
    elif result.status == 'SUCCESS':
        response['status'] = 'completed'
        response['progress'] = 100
        response['result'] = result.result
    elif result.status == 'FAILURE':
        response['status'] = 'failed'
        response['progress'] = 0
        response['error'] = str(result.result) if result.result else 'Unknown error'
    elif result.status == 'REVOKED':
        response['status'] = 'cancelled'
        response['progress'] = 0

    return response


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running Celery task.

    Returns True if task was cancelled, False otherwise.
    """
    result = AsyncResult(task_id, app=celery)

    if result.status in ('PENDING', 'STARTED', 'PROGRESS'):
        result.revoke(terminate=True)
        return True

    return False


# Check if Celery/Redis is available
def is_celery_available() -> bool:
    """Check if Celery broker (Redis) is available."""
    try:
        # Try to ping Redis
        import redis
        r = redis.from_url(REDIS_URL)
        r.ping()
        return True
    except Exception:
        return False


# Export
__all__ = ['celery', 'get_task_status', 'cancel_task', 'is_celery_available', 'REDIS_URL']
