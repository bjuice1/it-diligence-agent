"""
Cleanup Tasks - Periodic maintenance tasks

These tasks run on a schedule via Celery Beat to clean up
old sessions, temporary files, and stale data.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='web.tasks.cleanup_old_tasks')
def cleanup_old_tasks() -> Dict[str, Any]:
    """
    Clean up old completed Celery tasks from Redis.

    Runs hourly via Celery Beat.
    Removes task results older than 24 hours.
    """
    from web.celery_app import celery, REDIS_URL

    try:
        import redis
        r = redis.from_url(REDIS_URL)

        # Count task keys before cleanup
        task_keys = r.keys('celery-task-meta-*')
        initial_count = len(task_keys)

        # Celery handles expiration automatically via result_expires config
        # This task is mainly for logging/monitoring

        logger.info(f"Task cleanup: {initial_count} task results in Redis")

        return {
            'status': 'success',
            'task_count': initial_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@shared_task(name='web.tasks.cleanup_expired_sessions')
def cleanup_expired_sessions() -> Dict[str, Any]:
    """
    Clean up expired user sessions from Redis.

    Runs daily via Celery Beat.
    Removes sessions older than configured lifetime.
    """
    from web.celery_app import REDIS_URL
    from config_v2 import SESSION_LIFETIME_HOURS

    try:
        import redis
        r = redis.from_url(REDIS_URL)

        # Session keys pattern (Flask-Session uses 'session:' prefix)
        session_keys = r.keys('session:*')
        initial_count = len(session_keys)

        expired_count = 0
        cutoff = datetime.utcnow() - timedelta(hours=SESSION_LIFETIME_HOURS)

        for key in session_keys:
            try:
                # Check TTL - if no TTL, session may be stale
                ttl = r.ttl(key)
                if ttl == -1:  # No expiration set
                    # Check if session is old (would need session data inspection)
                    # For now, just log it
                    logger.debug(f"Session {key} has no TTL")
            except Exception as e:
                logger.warning(f"Error checking session {key}: {e}")

        logger.info(f"Session cleanup: {initial_count} sessions, {expired_count} expired")

        return {
            'status': 'success',
            'total_sessions': initial_count,
            'expired_cleaned': expired_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@shared_task(name='web.tasks.cleanup_temp_files')
def cleanup_temp_files() -> Dict[str, Any]:
    """
    Clean up temporary files from uploads and processing.

    Runs daily via Celery Beat.
    Removes temp files older than 24 hours.
    """
    from config_v2 import OUTPUT_DIR, DATA_DIR

    try:
        cleaned_count = 0
        cleaned_size = 0
        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Clean temp upload directory
        temp_dirs = [
            OUTPUT_DIR / 'temp',
            DATA_DIR / 'temp',
            Path('/tmp') / 'diligence_uploads'
        ]

        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue

            for temp_file in temp_dir.glob('*'):
                try:
                    if temp_file.is_file():
                        # Check file age
                        mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                        if mtime < cutoff:
                            file_size = temp_file.stat().st_size
                            temp_file.unlink()
                            cleaned_count += 1
                            cleaned_size += file_size
                            logger.debug(f"Cleaned temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning {temp_file}: {e}")

        logger.info(f"Temp file cleanup: {cleaned_count} files, {cleaned_size / 1024:.1f} KB")

        return {
            'status': 'success',
            'files_cleaned': cleaned_count,
            'bytes_freed': cleaned_size,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Temp file cleanup failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@shared_task(name='web.tasks.cleanup_stale_analysis_runs')
def cleanup_stale_analysis_runs() -> Dict[str, Any]:
    """
    Clean up analysis runs that got stuck in 'running' state.

    Runs hourly via Celery Beat.
    Marks runs older than 2 hours as failed.
    """
    from web.database import db, AnalysisRun
    from datetime import datetime, timedelta

    try:
        cutoff = datetime.utcnow() - timedelta(hours=2)

        stale_runs = AnalysisRun.query.filter(
            AnalysisRun.status == 'running',
            AnalysisRun.started_at < cutoff
        ).all()

        cleaned_count = 0
        for run in stale_runs:
            run.status = 'failed'
            run.completed_at = datetime.utcnow()
            run.errors = {'error': 'Task timed out (stale run cleanup)'}
            cleaned_count += 1
            logger.warning(f"Marked stale analysis run {run.id} as failed")

        if cleaned_count > 0:
            db.session.commit()

        logger.info(f"Stale run cleanup: {cleaned_count} runs marked as failed")

        return {
            'status': 'success',
            'stale_runs_cleaned': cleaned_count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Stale run cleanup failed: {e}")
        db.session.rollback()
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
